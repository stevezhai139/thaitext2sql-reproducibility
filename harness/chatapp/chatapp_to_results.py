#!/usr/bin/env python3
"""chatapp_to_results.py -- turn the checked chat log into runner-format JSONL that
grade_v13n.py grades on k3n with suite v1.3n (RUNBOOK C4/C5 pass --arms chat).

Inputs: log_index.tsv and raw_manifest.tsv from chat_log_export.py (every raw file is
re-hashed against the manifest before it is read), cells.tsv (default: next to
log_index.tsv) and the suite. Only done rows are converted; there must be exactly one
done row per (app, prompt_id) and 28 x 3 = 84 in total. A DRAFT suite is refused when
an output lies under a folder named results.

SQL extraction (AMENDMENT-8 sec.8 as set by OQ33.1-33.3 and the DEFAULT switch
EXTRACT_DETAILS in make_chat_cells.py, A8-07 text; frozen table in
tests/fixtures_chat/extract_cases.json):
  Form A  runner.extract_sql(reply) unchanged (the API-arm rule): first fenced block,
          'sql' tag stripped (case-insensitive); other tags such as postgresql/pgsql or
          ' sql' are not stripped and therefore fail to parse; two statements in one
          block fail to parse.                                  extract_rule = runner
          When runner.extract_sql raises (a fence that starts with 'sql' and has no line
          break, e.g. a one-line fence or an empty sql fence), the reply is a declared
          parse failure: sql = the stripped reply, parse_ok False.
                                                         extract_rule = runner-raised
  Form B  fenced reply: first block (fences per EXTRACT_DETAILS['fences']: a backtick run
          followed on the same line by another backtick is an inline code span, not a
          fence); the rest of the opening line is the CommonMark info string, whose first
          word is the tag: the line is dropped, unless the info string starts with SELECT
          or WITH (then it is code) or is a tag followed by SELECT or WITH (then the text
          after the tag is code); then the first top-level statement (split at the first
          ';' outside quotes, comments and dollar quotes); leading SQL comments are dropped.
                                                 extract_rule = first-block-first-stmt
          no fence: the first line that starts (after spaces) with SELECT, or with
          WITH [RECURSIVE] name [(cols)] AS (, up to the first top-level ';' or the
          end of the reply (blank lines do not end it); under EXTRACT_DETAILS['prose_case']
          a sentence-case 'Select ...' line is prose.        extract_rule = prose-first-stmt
  sql_present (NO_SQL = not sql_present, OQ33.3), one rule for both forms: the text that
          the form's rule returns has a line that starts with SELECT, or with WITH
          [RECURSIVE] name [(cols)] AS (, in any letter case. SQL that is
          present but fails to parse or execute is "SQL present, wrong" (for Form A, a
          ```postgresql block or a prose line before the SQL). Both count as wrong; NO_SQL
          is never a GF. SQL given only in an inline code span is NO_SQL in both forms.
Pre-declared Form A sensitivity (OQ33.1): one-word fence tags sql/postgresql/pgsql/psql
(case-insensitive, surrounding spaces allowed) are accepted. The script always prints
how many Form A cells change; --out-tagsens writes the 84 records with Form A
re-extracted under that rule (Form B unchanged) for a separate grading.
AMENDMENT-8 sec.6: turn 2 is sent only when the app asked back instead of giving SQL.
A done row with turn2_sent = Y whose turn 1 has SQL is printed as a deviation (NOTE);
its turn 2 is still converted (secondary result).

Record fields (design 3.7): ts (ts_done_ict), model_key app-<app>-<form>, model_echo
(UI model label or null), lang th, qid, tier, schema, run 1, latency_s null, raw, sql,
parse_ok, error null, arm chat, app, form, attempt, turn, extract_rule, prompt_sha256,
plus sql_present. --out holds turn 1 (primary); --out-turn2 holds turn 2 of the rows
with turn2_sent = Y (secondary). No output may exist. The outputs are written to
temporary files in the same folders and put in place only when every record is written,
so a failure leaves no partial file.

Usage (from harness/):
  python3 -I -B "chatapp/chatapp_to_results.py" --log-index "../results/chat/log_index.tsv"
      --raw-manifest "../results/chat/raw_manifest.tsv" --suite "../suite/k3n_suite_v1.3n.tsv"
      --out "../results/chat/results_chat.jsonl" --out-turn2 "../results/chat/results_chat_turn2.jsonl"
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import csv  # noqa: E402
import errno  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
import tempfile  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draw_chat_items_v13 import die, harness_dir, load_suite, refuse_draft_suite, sha256_file  # noqa: E402
from make_chat_cells import (APPS, CELLS_PER_APP, EXTRACT_DETAILS, LOG_COLUMNS,  # noqa: E402
                             check_switches, read_cells)

FENCE = "```"
SENS_TAGS = ("sql", "postgresql", "pgsql", "psql")
PROSE_START = re.compile(
    r"(?im)^[ \t]*(?:select\b|with[ \t]+(?:recursive[ \t]+)?(?:[A-Za-z_]\w*|\"[^\"]+\")[ \t]*"
    r"(?:\([^)]*\)[ \t]*)?as[ \t]*(?:(?:not[ \t]+)?materialized[ \t]*)?\()")
DOLLAR = re.compile(r"\$([A-Za-z_]\w*)?\$")
OPEN_CM = re.compile(r"`{3,}|(?m:^[ \t]{0,3})~{3,}")


def sql_present(text):
    """OQ33.3 NO_SQL test, the same for both forms: some line of the extracted text starts
    with SELECT, or with WITH [RECURSIVE] name [(cols)] AS (, in any letter case. (The
    prose_case filter decides only where a fence-less Form B statement starts; text from a
    code block is code, so 'Select ...' there is SQL.)"""
    return bool(text) and PROSE_START.search(text) is not None


def first_top_level_statement(text):
    """Text up to the first ';' outside quotes, comments and dollar quotes (in an E'...'
    escape string a backslash escapes the next character, as in PostgreSQL)."""
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "'" or ch == '"':
            esc = (ch == "'" and i > 0 and text[i - 1] in "eE"
                   and (i < 2 or not (text[i - 2].isalnum() or text[i - 2] == "_")))
            j = i + 1
            while j < n:
                if esc and text[j] == "\\":
                    j += 2
                    continue
                if text[j] == ch:
                    if j + 1 < n and text[j + 1] == ch:
                        j += 2
                        continue
                    break
                j += 1
            i = j + 1
            continue
        if text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            continue
        if ch == "$":
            m = DOLLAR.match(text, i)
            if m:
                j = text.find(m.group(0), m.end())
                i = n if j < 0 else j + len(m.group(0))
                continue
        if ch == ";":
            return text[:i]
        i += 1
    return text


def strip_leading_comments(s):
    while True:
        s = s.lstrip()
        if s.startswith("--"):
            j = s.find("\n")
            s = "" if j < 0 else s[j + 1:]
        elif s.startswith("/*"):
            j = s.find("*/")
            s = "" if j < 0 else s[j + 2:]
        else:
            return s


STMT_WORD = re.compile(r"(?i)(?:select|with)\b")


def drop_info_string(body):
    """the rest of a fence's opening line is the CommonMark info string; its first word is
    the tag. Drop the line, unless the info string starts with SELECT or WITH (the line is
    code) or is a tag followed by SELECT or WITH (the text after the tag is code)."""
    info, sep, rest = body.partition("\n")
    words = info.split()
    if not words:
        return rest
    if STMT_WORD.match(words[0]):
        return body
    tail = info.strip()[len(words[0]):].lstrip()
    if STMT_WORD.match(tail):
        return tail + sep + rest
    return rest


def fence_span(text):
    """(start, body_start, end) of the first fenced block, or None.
    'commonmark': 3+ backticks anywhere or 3+ tildes at a line start; a backtick run with
    another backtick later on its line opens an inline code span (an info string holds no
    backtick), so the search goes on from the next line; closed by the next run of the
    same character at least as long. 'triple-backtick': the first ``` and the next ```."""
    if EXTRACT_DETAILS["fences"] == "triple-backtick":
        i = text.find(FENCE)
        if i < 0:
            return None
        j = text.find(FENCE, i + 3)
        return i, i + 3, (len(text) if j < 0 else j)
    pos = 0
    while True:
        m = OPEN_CM.search(text, pos)
        if not m:
            return None
        run = m.group(0).strip(" \t")
        ch, width = run[0], len(run)
        eol = text.find("\n", m.end())
        eol = len(text) if eol < 0 else eol
        if ch == "`" and "`" in text[m.end():eol]:
            pos = eol
            continue
        if ch == "`":
            close = re.compile("`{%d,}" % width)
        else:
            close = re.compile(r"(?m)^[ \t]{0,3}~{%d,}" % width)
        c = close.search(text, m.end())
        return m.start(), m.end(), (len(text) if c is None else c.start())


def first_block(text):
    """(start, end, body) of the first fenced block; body without the info string."""
    span = fence_span(text)
    if span is None:
        return None
    i, b, end = span
    return i, end, drop_info_string(text[b:end])


def prose_start(text):
    """index of the first fence-less statement start, or None. Under
    EXTRACT_DETAILS['prose_case'] = 'upper-or-lower' a line that starts with 'Select' in
    sentence case is prose (WITH needs 'name AS (' anyway, so its case is not tested)."""
    for m in PROSE_START.finditer(text):
        word = re.match(r"[ \t]*([A-Za-z]+)", text[m.start():]).group(1)
        if (EXTRACT_DETAILS["prose_case"] == "any" or word.lower() != "select"
                or word.isupper() or word.islower()):
            return m.start()
    return None


def extract_form_b(raw):
    t = (raw or "").replace("\r\n", "\n")
    blk = first_block(t)
    if blk is not None:
        stmt = first_top_level_statement(blk[2])
        rule = "first-block-first-stmt"
    else:
        s = prose_start(t)
        stmt = first_top_level_statement(t[s:]) if s is not None else ""
        rule = "prose-first-stmt"
    stmt = strip_leading_comments(stmt).strip()
    return stmt, sql_present(stmt), rule


def runner_rule(runner, text, rule):
    """runner.extract_sql; an exception of the runner is a declared parse failure."""
    try:
        sql, ok = runner.extract_sql(text)
        return sql, bool(ok), rule
    except Exception:  # noqa: BLE001  (IndexError on a one-line or empty 'sql' fence)
        return (text or "").strip(), False, rule + "-raised"


def extract_form_a(runner, raw):
    return runner_rule(runner, raw or "", "runner")


def extract_form_a_tagsens(runner, raw):
    """OQ33.1 sensitivity: accept one-word tags sql/postgresql/pgsql/psql, else runner rule."""
    t = raw or ""
    i = t.find(FENCE)
    if i >= 0:
        j = t.find(FENCE, i + 3)
        end = len(t) if j < 0 else j
        first, sep, rest = t[i + 3:end].partition("\n")
        if sep and first.strip().lower() in SENS_TAGS:
            t = t[:i + 3] + "sql\n" + rest + t[end:]
    return runner_rule(runner, t, "runner+tags")


def extract(runner, form, raw, tagsens=False):
    if form == "A":
        return extract_form_a_tagsens(runner, raw) if tagsens else extract_form_a(runner, raw)
    return extract_form_b(raw)


def present(form, sql):
    """sql_present of a record (OQ33.3): the same test for both forms, applied to the text
    the form's extraction rule returned (`form` is kept for the callers)."""
    return sql_present(sql)


def load_manifest(path):
    base = os.path.dirname(os.path.abspath(path))
    man = {}
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            p = os.path.join(base, r["path"])
            if not os.path.isfile(p):
                die(f"raw file listed in the manifest is missing: {r['path']}", 1)
            if str(os.path.getsize(p)) != r["bytes"] or sha256_file(p) != r["sha256"]:
                die(f"raw file differs from raw_manifest.tsv: {r['path']}", 1)
            man[r["path"]] = p
    return man


def read_raw(man, rel):
    if rel not in man:
        die(f"raw file is not in raw_manifest.tsv: {rel}", 1)
    with open(man[rel], encoding="utf-8") as fh:
        return fh.read()


class Outputs:
    """temporary files beside each output; put in place (no overwrite) only by commit()."""

    def __init__(self, paths):
        self.items = []
        for p in paths:
            d = os.path.dirname(os.path.abspath(p))
            os.makedirs(d, exist_ok=True)
            fd, tmp = tempfile.mkstemp(prefix="." + os.path.basename(p) + ".", suffix=".partial", dir=d)
            self.items.append((os.fdopen(fd, "w", encoding="utf-8", newline="\n"), tmp, p))

    def handle(self, i):
        return self.items[i][0]

    def discard(self):
        for fh, tmp, _p in self.items:
            fh.close()
            if os.path.exists(tmp):
                os.unlink(tmp)

    def commit(self):
        for fh, _tmp, _p in self.items:
            fh.close()
        placed = []
        try:
            for _fh, tmp, p in self.items:
                try:
                    os.link(tmp, p)
                    os.unlink(tmp)
                except OSError as e:
                    if e.errno == errno.EEXIST or os.path.exists(p):
                        die(f"output appeared while writing, refusing to overwrite: {os.path.basename(p)}")
                    os.replace(tmp, p)
                placed.append(p)
        except BaseException:
            for p in placed:
                os.unlink(p)
            self.discard()
            raise


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--log-index", required=True)
    ap.add_argument("--raw-manifest", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-turn2", required=True)
    ap.add_argument("--cells", help="cells.tsv (default: next to --log-index)")
    ap.add_argument("--out-tagsens", help="optional: turn-1 records with the OQ33.1 Form A tag sensitivity")
    ap.add_argument("--harness-dir", help="folder with runner.py (default: parent of chatapp/)")
    a = ap.parse_args()
    check_switches()
    outs = [p for p in (a.out, a.out_turn2, a.out_tagsens) if p]
    for p in outs:
        if os.path.exists(p):
            die(f"output exists, refusing to overwrite: {os.path.basename(p)}")

    sys.path.insert(0, harness_dir(a.harness_dir))
    import runner  # noqa: E402  (extract_sql only)

    suite = load_suite(a.suite)
    refuse_draft_suite(a.suite, suite, outs)
    cells_path = a.cells or os.path.join(os.path.dirname(os.path.abspath(a.log_index)), "cells.tsv")
    cells = {c["prompt_id"]: c for c in read_cells(cells_path)}
    man = load_manifest(a.raw_manifest)
    with open(a.log_index, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows or list(rows[0].keys()) != LOG_COLUMNS:
        die(f"log_index.tsv header is not {LOG_COLUMNS}")
    done = [r for r in rows if r["status"] == "done"]
    seen = set()
    for r in done:
        k = (r["app"], r["prompt_id"])
        if k in seen:
            die(f"duplicate done row for {k[0]} {k[1]}", 1)
        seen.add(k)
        if r["app"] not in APPS or r["prompt_id"] not in cells:
            die(f"unknown app or prompt_id in log_index.tsv: {k[0]} {k[1]}", 1)
    expected = CELLS_PER_APP * len(APPS)
    if len(done) != expected or len(cells) != CELLS_PER_APP:
        die(f"{len(done)} done rows, expected {expected}", 1)

    app_rank = {x: i for i, x in enumerate(APPS)}
    done.sort(key=lambda r: (int(r["order"]), app_rank[r["app"]]))
    n1 = n2 = n_sens_changed = 0
    counts = {"no_sql": 0, "parse_fail_with_sql": 0, "runner_raised": 0}
    t2_deviation = []
    out = Outputs(outs)
    f1, f2 = out.handle(0), out.handle(1)
    fs = out.handle(2) if a.out_tagsens else None
    try:
        for r in done:
            c = cells[r["prompt_id"]]
            item = suite[c["qid"]]
            turns = [(1, r["raw_file"])]
            if r["turn2_sent"] == "Y":
                turns.append((2, r["raw2_file"]))
            for turn, rel in turns:
                raw = read_raw(man, rel)
                sql, ok, rule = extract(runner, c["form"], raw)
                rec = {"ts": r["ts_done_ict"], "model_key": f"app-{r['app']}-{c['form']}",
                       "model_echo": r["ui_model_label"] or None, "lang": c["lang"], "qid": c["qid"],
                       "tier": item["tier"], "schema": item["schema"], "run": 1, "latency_s": None,
                       "raw": raw, "sql": sql, "parse_ok": ok, "error": None, "arm": "chat",
                       "app": r["app"], "form": c["form"], "attempt": int(r["attempt"]), "turn": turn,
                       "extract_rule": rule, "prompt_sha256": c["prompt_sha256"],
                       "sql_present": present(c["form"], sql)}
                line = json.dumps(rec, ensure_ascii=False) + "\n"
                if turn == 1:
                    f1.write(line)
                    n1 += 1
                    counts["no_sql"] += not rec["sql_present"]
                    counts["parse_fail_with_sql"] += rec["sql_present"] and not ok
                    counts["runner_raised"] += rule.endswith("-raised")
                    if r["turn2_sent"] == "Y" and rec["sql_present"]:
                        t2_deviation.append(f"{r['app']} {r['prompt_id']}")
                    s_sql, s_ok, s_rule = extract(runner, c["form"], raw, tagsens=True)
                    if c["form"] == "A" and (s_sql, s_ok) != (sql, ok):
                        n_sens_changed += 1
                    if fs:
                        srec = dict(rec, sql=s_sql, parse_ok=s_ok, extract_rule=s_rule,
                                    sql_present=present(c["form"], s_sql))
                        fs.write(json.dumps(srec, ensure_ascii=False) + "\n")
                else:
                    f2.write(line)
                    n2 += 1
    except BaseException:
        out.discard()
        raise
    out.commit()
    print(f"turn 1 records: {n1} (NO_SQL {counts['no_sql']}, SQL present but parse failure "
          f"{counts['parse_fail_with_sql']}); turn 2 records: {n2}")
    print(f"Form A replies on which runner.extract_sql raised (declared parse failures): "
          f"{counts['runner_raised']}")
    if t2_deviation:
        print(f"NOTE (AMENDMENT-8 sec.6 deviation): turn 2 was sent although turn 1 has SQL in "
              f"{len(t2_deviation)} rows: " + ", ".join(t2_deviation))
    print(f"OQ33.1 sensitivity: Form A cells whose extraction changes under one-word tags "
          f"{'/'.join(SENS_TAGS)}: {n_sens_changed}"
          + ("" if a.out_tagsens or not n_sens_changed else " (rerun with --out-tagsens to grade them)"))
    print(f"[out] {os.path.basename(a.out)} sha256={sha256_file(a.out)}")
    print(f"[out] {os.path.basename(a.out_turn2)} sha256={sha256_file(a.out_turn2)}")
    if a.out_tagsens:
        print(f"[out] {os.path.basename(a.out_tagsens)} sha256={sha256_file(a.out_tagsens)}")


if __name__ == "__main__":
    main()
