#!/usr/bin/env python3
"""make_chat_cells.py -- frozen cell list and one prompt file per cell for the
chat-app consistency check (prereg AMENDMENT-8 sec.5-6). Contacts no app or API:
the author pastes every prompt by hand.

Input: --items = chat_items_v13.json written by draw_chat_items_v13.py. The script
recomputes sha256(",".join(items18)) and checks it against the file (and against
--expect-items-sha256 when given), checks items18 = VG_CHAT + 8 non-VG items, and checks
that sha256(--suite) equals the suite_sha256 recorded by the draw (the draw and the
prompts must come from the same suite). A DRAFT suite (file name or build_status) is
refused when --out lies under a folder named results (same rule as grade_v13n.py).

Cells per app (28; identical prompt bytes for the three apps):
  pre-shuffle order = Form A x TH x VG_CHAT (10) + Form B x TH x VG_CHAT (10)
                      + Form B x TH x NONVG (8)
  pre_shuffle_sha256 = sha256 of the lines "<form>\t<lang>\t<qid>\n" in that order
  then random.Random(20261012).shuffle(cells)
Form A = the run-of-record prompt of the RC1 runner, base arm, pasted as one user
  message: build_prompt(item, "th", "base") -> system + "\n\n" + user, asserted
  equal to SYSTEM.format(ddl=DDL_<schema>) + "\n\n" + question_th.
Form B = FORM_B_TH below, verbatim from AMENDMENT-8 sec.5.
prompts/TURN2.txt = TURN2_TEXT below, verbatim from AMENDMENT-8 sec.6.

Outputs under --out (refuses to overwrite cells.tsv, cells_meta.json or prompts/):
  prompts/<order:03d>_<form>_<lang>_<qid>.txt   (UTF-8, no trailing newline)
  prompts/TURN2.txt
  cells.tsv        order, prompt_id, form, lang, qid, prompt_file, prompt_sha256 (full)
  cells_meta.json  items/suite/runner sha256, pre_shuffle_sha256, cells_tsv_sha256,
                   prompts_manifest_sha256 (sha256 of "<prompt_id>\t<sha256>\n" lines),
                   turn2_sha256, created_at_ict (wall clock of this build, ICT;
                   chat_log_export.py refuses a --not-before earlier than it, so the
                   Gate 1b NOT_BEFORE cannot stand in for CHAT_NOT_BEFORE)
No log_index.tsv is written here (chat_log_export.py writes it from CHAT_LOG.xlsx).

The DEFAULT decisions of the whole chat kit (details that AMENDMENT-8 and OQ33 leave
open) are in the block below the frozen constants, one constant each, and each is written
into an AMENDMENT-8 before->after text for the author's approval.

Usage (from harness/):
  python3 -I -B "chatapp/make_chat_cells.py" --items "../results/chat/chat_items_v13.json"
      --suite "../suite/k3n_suite_v1.3n.tsv" --out "../results/chat"
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import csv  # noqa: E402
import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import random  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draw_chat_items_v13 import (SEED, VG_CHAT, N_NONVG, die, harness_dir,  # noqa: E402
                                 load_suite, primary_ids, refuse_draft_suite, sha256_file)

# ---- frozen kit constants (AMENDMENT-8 sec.2, 5, 6, 7); imported by the other kit scripts ----
APPS = ["chatgpt", "gemini", "claude"]
APP_PROXY = {"chatgpt": "gpt-mini", "gemini": "gemini-flash", "claude": "claude-sonnet"}
APP_LABEL = {"chatgpt": "ChatGPT", "gemini": "Gemini app", "claude": "Claude.ai"}
FORMS = ("A", "B")
FORM_B_TH = "ช่วยเขียนคำสั่ง SQL (PostgreSQL) ให้หน่อย\n\nโครงสร้างตาราง:\n{ddl}\n\nโจทย์: {q}"
TURN2_TEXT = "ช่วยเขียนคำสั่ง SQL ให้เลย ตามสมมติฐานที่คิดว่าน่าจะถูกที่สุด"
TURN2_FILE = "TURN2.txt"
CELLS_PER_APP = 28
# time windows of AMENDMENT-8 sec.6 and sec.9 as made checkable by the OQ33.9 default
CHAT_SPAN_MAX_DAYS = 2   # all sent chats within 3 consecutive calendar days (ICT): max - min <= 2
CONCURRENT_DAYS = 7      # every chat date within [first B date - 7, last B date + 7]
CELLS_COLUMNS = ["order", "prompt_id", "form", "lang", "qid", "prompt_file", "prompt_sha256"]
# CHAT_LOG.xlsx sheet 'log' and log_index.tsv: AMENDMENT-8 sec.7 columns + attempt
LOG_COLUMNS = ["app", "order", "prompt_id", "attempt", "status", "ts_sent_ict", "ts_done_ict",
               "ui_model_label", "limit_banner", "tools_visible", "turn2_sent",
               "raw_file", "raw2_file", "screenshot", "note"]
ICT = dt.timezone(dt.timedelta(hours=7))
TS_FMT = "%Y-%m-%dT%H:%M:%S"

# ---- DEFAULT decisions of the chat kit (assistant, triage rule; 14 Oct 2026) ----------------
# None of these is a GENUINE author question (TRIAGE_OQ sec.2): each fills a detail that
# AMENDMENT-8 and OQ33 leave open, and each is written into the AMENDMENT-8 before->after text
# named in its comment, which the author approves in Gate 0 step 3. The value set here is the
# one the kit runs with; if the author changes a text, only this constant changes. Nothing
# else in the kit hard-codes these choices.
#
# AMENDMENT-8 sec.5: cell i is done in all three apps before cell i+1 starts. A breach of
# that cross-app order (A8-06 text):
#   "note"  the export passes; chat_log_export.py prints the count and chat_report.py writes
#           it to chat_rules.tsv, chat_report.txt and meta.json as a deviation (default)
#   "fail"  chat_log_export.py fails and writes nothing
CELL_MAJOR_BREACH = "note"  # DEFAULT (A8-06)
CELL_MAJOR_BREACH_CHOICES = ("note", "fail")
#
# AMENDMENT-8 sec.10, second silence sentence "most wrong replies gave no warning (x of n)"
# (new before->after edit of AM-8 l.178): m = FLAGGED + ASKED is the count of the first
# sentence; the second sentence describes the silent replies, so
#   "s"  x = number of SILENT replies = n - m (default; "most ... (6 of 10)" reads true)
#   "m"  x = m, as the draft line reads literally ("most ... gave no warning (2 of 10)")
SILENCE_MOSTLY_SILENT_COUNT = "s"  # DEFAULT (A8 sec.10 l.178)
SILENCE_MOSTLY_SILENT_COUNT_CHOICES = ("s", "m")
#
# AMENDMENT-8 sec.9 comparator when an app's chats fall outside +-7 days of its proxy's
# October TH base arm (A8-09 text, rewritten to match):
#   "oct-base"  the October base arm itself, labelled 'not concurrent' (default; brief 1.0
#               D10: the October session is the primary data, and the August log is two
#               months away, so it is no more concurrent)
#   "aug-k3n"   the August log re-graded on k3n (--fallback-graded / --fallback-results)
# A proxy whose base arm is unusable under AMENDMENT-7 A5 (--unusable-models) always uses
# the August fallback, because no usable October base arm exists for it.
FALLBACK_WINDOW_FAIL = "oct-base"  # DEFAULT (A8-09)
FALLBACK_WINDOW_FAIL_CHOICES = ("oct-base", "aug-k3n")
#
# SQL extraction details that OQ33.1-33.3 do not settle (chatapp_to_results.py; A8-07 text;
# frozen cases in tests/fixtures_chat/extract_cases.json):
#   fences      "commonmark" (default): a fence opens at a run of 3 or more backticks (anywhere
#               in the text, as runner.extract_sql splits on ``` anywhere) or of 3 or more
#               tildes at a line start; a backtick run followed on the same line by another
#               backtick opens an inline code span, not a fence (CommonMark: an info string
#               holds no backtick); the fence closes at the next run of the same character
#               at least as long. "triple-backtick": the first ``` and the next ``` only.
#               In both, the rest of the opening line is the CommonMark info string, whose
#               first word is the tag: the line is dropped, unless the info string starts
#               with SELECT or WITH (then it is code) or is a tag followed by SELECT or WITH
#               (then the text after the tag is code).
#   prose_case  "upper-or-lower" (default): a fence-less Form B statement may start with SELECT
#               or select but not with sentence-case 'Select', which is read as English
#               prose; "any": any letter case (WITH needs 'name AS (' in every setting, so
#               its case is not tested)
# The NO_SQL test (OQ33.3) is one rule for both forms: the text that the form's extraction
# rule returns has no line that starts with SELECT, or with WITH [RECURSIVE] name [(cols)]
# AS (, in any letter case.
EXTRACT_DETAILS = {"fences": "commonmark", "prose_case": "upper-or-lower"}  # DEFAULT (A8-07)
EXTRACT_DETAILS_CHOICES = {"fences": ("commonmark", "triple-backtick"),
                           "prose_case": ("upper-or-lower", "any")}


def cell_major_breaches(rows):
    """AMENDMENT-8 sec.5 cell-major order: orders o whose next cell (o + 1) was first sent
    before cell o was done in all apps, over done rows with both times. rows: dicts with
    order (int), status, ts_sent and ts_done (datetime or None). Shared by
    chat_log_export.py and chat_report.py."""
    first_sent, last_done = {}, {}
    for r in rows:
        if r["status"] == "done" and r["ts_sent"] and r["ts_done"]:
            o = int(r["order"])
            first_sent[o] = min(first_sent.get(o, r["ts_sent"]), r["ts_sent"])
            last_done[o] = max(last_done.get(o, r["ts_done"]), r["ts_done"])
    return sorted(o for o in last_done if o + 1 in first_sent and first_sent[o + 1] < last_done[o])


def check_switches():
    """exit 2 when a DEFAULT switch holds a value outside its choices."""
    bad = []
    if CELL_MAJOR_BREACH not in CELL_MAJOR_BREACH_CHOICES:
        bad.append("CELL_MAJOR_BREACH")
    if SILENCE_MOSTLY_SILENT_COUNT not in SILENCE_MOSTLY_SILENT_COUNT_CHOICES:
        bad.append("SILENCE_MOSTLY_SILENT_COUNT")
    if FALLBACK_WINDOW_FAIL not in FALLBACK_WINDOW_FAIL_CHOICES:
        bad.append("FALLBACK_WINDOW_FAIL")
    for k, choices in EXTRACT_DETAILS_CHOICES.items():
        if EXTRACT_DETAILS.get(k) not in choices:
            bad.append(f"EXTRACT_DETAILS[{k!r}]")
    if bad:
        die("DEFAULT switch outside its choices: " + ", ".join(bad))


def switches():
    """the switch values, for meta files and printed headers."""
    return {"CELL_MAJOR_BREACH": CELL_MAJOR_BREACH,
            "SILENCE_MOSTLY_SILENT_COUNT": SILENCE_MOSTLY_SILENT_COUNT,
            "FALLBACK_WINDOW_FAIL": FALLBACK_WINDOW_FAIL,
            "EXTRACT_DETAILS": dict(EXTRACT_DETAILS)}


def prompt_id(order, form, lang, qid):
    return f"{order:03d}_{form}_{lang}_{qid}"


def raw_name(app, pid, attempt=1, turn=1):
    """File names pre-filled in CHAT_LOG.xlsx (attempt >= 2 is typed by the author)."""
    a = "" if int(attempt) == 1 else f"_a{int(attempt)}"
    t = "" if int(turn) == 1 else "_turn2"
    return f"{app}_{pid}{a}{t}.md"


def shot_name(app, pid, attempt=1):
    a = "" if int(attempt) == 1 else f"_a{int(attempt)}"
    return f"{app}_{pid}{a}.png"


def sha256_text(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_cells(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows or list(rows[0].keys()) != CELLS_COLUMNS:
        die(f"{os.path.basename(path)}: header is not {CELLS_COLUMNS}")
    for r in rows:
        r["order"] = int(r["order"])
    return rows


def load_items(path, expect_sha=None):
    with open(path, encoding="utf-8") as fh:
        d = json.load(fh)
    items18 = d.get("items18") or []
    nonvg = d.get("nonvg") or []
    got = hashlib.sha256(",".join(items18).encode("utf-8")).hexdigest()
    if got != d.get("items_sha256"):
        die(f"items_sha256 in {os.path.basename(path)} does not match its items18 ({got})")
    if expect_sha and got != expect_sha.strip().lower():
        die(f"items sha256 {got} != --expect-items-sha256 {expect_sha}")
    if items18[:len(VG_CHAT)] != VG_CHAT or items18[len(VG_CHAT):] != nonvg:
        die("items18 must be VG_CHAT followed by nonvg")
    if len(nonvg) != N_NONVG or len(set(nonvg)) != N_NONVG or set(nonvg) & set(VG_CHAT):
        die(f"nonvg must be {N_NONVG} distinct items outside VG_CHAT")
    return d, got


def form_a_text(runner, item):
    """Form A = RC1 base-arm prompt, system + blank line + user (AMENDMENT-8 sec.5)."""
    n_params = len(inspect.signature(runner.build_prompt).parameters)
    args = (item, "th", "base", None) if n_params >= 4 else (item, "th", "base")
    system, user = runner.build_prompt(*args)
    text = system + "\n\n" + user
    ddl = runner.DDL_P if item["schema"] == "P" else runner.DDL_E
    expect = runner.SYSTEM.format(ddl=ddl) + "\n\n" + item["question_th"]
    if text != expect:
        die(f"Form A for {item['id']} differs from SYSTEM.format(ddl) + blank line + question_th")
    return text


def form_b_text(runner, item):
    ddl = runner.DDL_P if item["schema"] == "P" else runner.DDL_E
    return FORM_B_TH.format(ddl=ddl, q=item["question_th"])


def pre_shuffle_cells(nonvg):
    return ([("A", "th", q) for q in VG_CHAT] + [("B", "th", q) for q in VG_CHAT]
            + [("B", "th", q) for q in nonvg])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--items", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--out", required=True, help="results/chat folder")
    ap.add_argument("--expect-items-sha256")
    ap.add_argument("--harness-dir", help="folder with runner.py (default: parent of chatapp/)")
    a = ap.parse_args()
    check_switches()

    out = os.path.abspath(a.out)
    for name in ("cells.tsv", "cells_meta.json", "prompts"):
        if os.path.exists(os.path.join(out, name)):
            die(f"{name} exists under --out, refusing to overwrite")

    hdir = harness_dir(a.harness_dir)
    sys.path.insert(0, hdir)
    import runner  # noqa: E402  (constants and build_prompt only; main() is guarded)

    d, items_sha = load_items(a.items, a.expect_items_sha256)
    suite = load_suite(a.suite)
    refuse_draft_suite(a.suite, suite, [os.path.join(out, "cells.tsv")])
    suite_sha = sha256_file(a.suite)
    if d.get("suite_sha256") != suite_sha:
        die(f"sha256 of --suite is {suite_sha}, but the draw in {os.path.basename(a.items)} used "
            f"{d.get('suite_sha256')}: the prompts must come from the suite of the draw")
    prim = set(primary_ids(suite))
    for q in d["items18"]:
        if q not in prim:
            die(f"item {q} is not a primary item of the suite")

    cells = pre_shuffle_cells(d["nonvg"])
    pre_sha = sha256_text("".join(f"{f}\t{l}\t{q}\n" for f, l, q in cells))
    random.Random(SEED).shuffle(cells)
    if len(cells) != CELLS_PER_APP:
        die(f"{len(cells)} cells, expected {CELLS_PER_APP}")

    os.makedirs(os.path.join(out, "prompts"))
    rows = []
    for i, (form, lang, qid) in enumerate(cells, 1):
        item = suite[qid]
        text = form_a_text(runner, item) if form == "A" else form_b_text(runner, item)
        pid = prompt_id(i, form, lang, qid)
        rel = f"prompts/{pid}.txt"
        with open(os.path.join(out, rel), "xb") as fh:
            fh.write(text.encode("utf-8"))
        rows.append([i, pid, form, lang, qid, rel, sha256_text(text)])
    with open(os.path.join(out, "prompts", TURN2_FILE), "xb") as fh:
        fh.write(TURN2_TEXT.encode("utf-8"))

    with open(os.path.join(out, "cells.tsv"), "x", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(CELLS_COLUMNS)
        w.writerows(rows)
    manifest_sha = sha256_text("".join(f"{r[1]}\t{r[6]}\n" for r in rows))
    meta = {
        "tool": "make_chat_cells.py",
        "tool_sha256": sha256_file(os.path.abspath(__file__)),
        "items_file": os.path.basename(a.items),
        "items_file_sha256": sha256_file(a.items),
        "items_sha256": items_sha,
        "suite_file": os.path.basename(a.suite),
        "suite_sha256": suite_sha,
        "runner_sha256": sha256_file(os.path.join(hdir, "runner.py")),
        "seed": SEED,
        "n_cells": len(rows),
        "pre_shuffle_sha256": pre_sha,
        "cells_tsv_sha256": sha256_file(os.path.join(out, "cells.tsv")),
        "prompts_manifest_sha256": manifest_sha,
        "turn2_sha256": sha256_text(TURN2_TEXT),
        "created_at_ict": dt.datetime.now(ICT).strftime(TS_FMT),
    }
    with open(os.path.join(out, "cells_meta.json"), "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, ensure_ascii=False, indent=1) + "\n")

    n_a = sum(1 for r in rows if r[2] == "A")
    print(f"{len(rows)} cells per app x {len(APPS)} apps = {len(rows) * len(APPS)} chats "
          f"(Form A {n_a}, Form B {len(rows) - n_a})")
    print(f"items_sha256={items_sha}")
    print(f"pre_shuffle_sha256={pre_sha}")
    print(f"cells_tsv_sha256={meta['cells_tsv_sha256']}")
    print(f"prompts_manifest_sha256={manifest_sha}")
    print(f"turn2_sha256={meta['turn2_sha256']}")
    print(f"created_at_ict={meta['created_at_ict']} (CHAT_NOT_BEFORE, the Gate 2 commit time of RUNBOOK step "
          f"2.38b, comes later)")


if __name__ == "__main__":
    main()
