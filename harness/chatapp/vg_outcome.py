#!/usr/bin/env python3
"""vg_outcome.py -- mechanical value-grounding code of every chat cell (prereg
AMENDMENT-8 sec.8, AMENDMENT-7 B2.2-B2.3). No rater; the classifier is the single
implementation in harness/vg_classifier.py (shared with analyze_rc1.py, never copied).

Per cell (one run per cell, turn 1):
  exec_class  correct | loud (exec_ok False) | silent-empty (n_rows 0) |
              silent-non-empty (n_rows >= 1)                       (AMENDMENT-7 B1)
  vg_code     VG_CHAT items only: CORRECT when graded correct; NO_SQL when no SQL was
              extracted (record field sql_present, OQ33.3); otherwise the B2.3 class of
              vg_classifier.classify_run(text, targets, vocabulary) where text is the SQL
              when the record's parse_ok is True and '' when it is False (classified_sql
              below; the rule analyze_rc1.py applies to the API runs, so a reply whose SQL
              fails to parse, e.g. two statements under the Form A runner rule, is NO_PRED
              and never GF in both places): THAI_COPY | INVENTED | GROUNDED | STORED |
              NO_PRED.  Non-VG items: NA.
  gf          wrong and vg_code in {THAI_COPY, INVENTED}  (B2.2 with a single run)
  clean       correct, or vg_code in {GROUNDED, STORED}
  class_extracted  diagnostic only (never a rule): for a wrong VG cell with SQL, the B2.3
              class of the extracted SQL text itself, whatever its parse_ok; it differs
              from vg_code only after a parse failure, so chat_report.py can show how many
              GF cells the parse-failure rule hides (e.g. two Form A statements, the
              second with a Thai literal)
  lit_elsewhere  Y when a gold value-grounding literal appears quoted ('...') in the
              reply outside the graded SQL span (span removed after collapsing white
              space in both texts) and not inside the graded SQL; a mechanical hint only.
Vocabulary: full_values of value_hints_v1.json through vg_classifier.build_vocab, so the
classifier's single OQ6 switch (Q48_VOCAB_RULE) applies here as in analyze_rc1.py. Q48 (OQ6,
dropped): B2.3 applies unchanged; the script prints how many wrong Q48 cells compare
RunnerUp with 'None'.
--vocab-db k3 (OQ33.7 sensitivity on k3 only): the hint file is built from k3n, where the 6
cells that hold the string 'None' on k3 are NULL (brief 1.1: SpouseName, VicePresidentName,
RunnerUp). On k3 'None' is a stored value of those three columns, so the k3 vocabulary is the
k3n vocabulary plus 'None' on exactly those columns (K3_NONE_COLUMNS; checked TEST-ONLY on
the scratch k3/k3n: 1 + 4 + 1 cells). Default k3n.

Also writes <out stem>_audit_rows.csv (or --audit-rows): one row per wrong VG cell
with SQL (app, form, qid, targets, sql, classifier_class) for the blind B2.3 audit of
OQ33.4 (chat_silence_sheet.py --vg-audit builds the sheet). As in analyze_rc1.py's
audit rows, the sql column holds the text the classifier saw ('' after a parse failure).
And <out stem>_meta.json: sha256 of the graded, results, suite and hint files, of both
outputs, the vocabulary database and the Q48 rule. chat_report.py refuses a vg_codes file
whose meta does not match its own inputs (built from another graded file, another hint file
or another vocabulary, or edited afterwards).
--hints-sha256 is required (the vocabulary decides INVENTED). A DRAFT suite is refused
when an output lies under a folder named results. Any correct/parse_ok/exec_ok value other
than True or False is refused.

The results JSONL is read with a reader that keeps only the needed fields and reduces
'error' to a boolean while parsing.

Usage (from harness/):
  python3 -I -B "chatapp/vg_outcome.py" --graded "../results/chat/graded_chat_k3n.csv"
      --results "../results/chat/results_chat.jsonl" --suite "../suite/k3n_suite_v1.3n.tsv"
      --hints "../suite/value_hints_v1.json" --hints-sha256 "<sha256 from the FREEZE STAMP>"
      --out "../results/chat/vg_codes_chat.tsv" [--vocab-db k3]
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import csv  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from collections import Counter  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draw_chat_items_v13 import (VG_CHAT, check_bool_fields, die, harness_dir, load_suite,  # noqa: E402
                                 primary_ids, refuse_draft_suite, sha256_file)
from make_chat_cells import APPS, FORMS, check_switches  # noqa: E402

B23_CLASSES = ("THAI_COPY", "INVENTED", "NO_PRED", "GROUNDED", "STORED")  # AMENDMENT-7 B2.3, check order
GF_CLASSES = ("THAI_COPY", "INVENTED")                                    # AMENDMENT-7 B2.2
CLEAN_CLASSES = ("GROUNDED", "STORED")
VG_COLUMNS = ["app", "form", "lang", "qid", "vg", "correct", "exec_ok", "n_rows", "fail_reason",
              "exec_class", "sql_present", "vg_code", "gf", "clean", "lit_elsewhere",
              "extract_rule", "attempt", "class_extracted"]
AUDIT_COLUMNS = ["app", "form", "qid", "targets", "sql", "classifier_class"]
MODEL_KEY = re.compile(r"^app-(chatgpt|gemini|claude)-(A|B)$")
RESULT_FIELDS = ("model_key", "lang", "qid", "run", "sql", "raw", "parse_ok", "arm", "app", "form",
                 "sql_present", "attempt", "extract_rule", "turn", "ts")
VOCAB_DBS = ("k3n", "k3")
# k3 = k3n with 'None' stored instead of NULL in 6 cells of these columns (brief 1.1)
K3_NONE_COLUMNS = ("spousename", "vicepresidentname", "runnerup")


def read_jsonl(path, fields):
    """Keep only `fields`; 'error' becomes error_is_set (bool) at parse time and is never kept."""
    keep = set(fields)

    def hook(pairs):
        d = {}
        for k, v in pairs:
            if k == "error":
                d["error_is_set"] = v is not None
            elif k in keep:
                d[k] = v
        return d

    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            if line.strip():
                out.append(json.loads(line, object_pairs_hook=hook))
    return out


def exec_class(correct, exec_ok, n_rows):
    if correct:
        return "correct"
    if not exec_ok:
        return "loud"
    return "silent-empty" if int(n_rows or 0) == 0 else "silent-non-empty"


def load_vocab(vg_classifier, path, targets=None, vocab_db="k3n"):
    """Vocabulary of B2.3 through the classifier, so its single OQ6 switch
    (Q48_VOCAB_RULE) applies here exactly as in analyze_rc1.py. vocab_db 'k3' adds the
    stored 'None' of K3_NONE_COLUMNS (OQ33.7 sensitivity on k3)."""
    if vocab_db not in VOCAB_DBS:
        die(f"unknown vocabulary database {vocab_db!r}")
    if callable(getattr(vg_classifier, "build_vocab", None)) and callable(getattr(vg_classifier, "load_hints", None)):
        hints, _sha = vg_classifier.load_hints(path)
        gold = [t for ts in (targets or {}).values() for t in ts]
        rule = getattr(vg_classifier, "Q48_VOCAB_RULE", "?")
        vocab, src = vg_classifier.build_vocab(hints, gold_targets=gold), f"vg_classifier.build_vocab (Q48 rule '{rule}')"
    elif callable(getattr(vg_classifier, "load_vocab", None)):
        vocab, src = vg_classifier.load_vocab(path), "vg_classifier.load_vocab"
    else:
        with open(path, encoding="utf-8") as fh:
            hints = json.load(fh)
        vocab = {}
        for s in hints["schemas"].values():
            for c in s["columns"]:
                if c.get("full_values") is not None:
                    vocab.setdefault(c["column"].lower(), set()).update(c["full_values"])
        src = "local reader of full_values"
    vocab = {k: set(v) for k, v in vocab.items()}
    if vocab_db == "k3":
        missing = [c for c in K3_NONE_COLUMNS if c not in vocab]
        if missing:
            die(f"--vocab-db k3: columns {missing} have no full_values in the hint file")
        for c in K3_NONE_COLUMNS:
            vocab[c].add("None")
        src += "; k3 rule: stored 'None' added to " + ", ".join(K3_NONE_COLUMNS)
    return vocab, src


def _ws(s):
    return re.sub(r"\s+", " ", s or "").strip()


def lit_elsewhere(raw, sql, lits):
    rest = _ws(raw)
    nsql = _ws(sql)
    if nsql:
        rest = rest.replace(nsql, " ", 1)
    return any(("'" + x + "'") in rest for x in lits if ("'" + x + "'") not in (sql or ""))


def lits_on(vg_classifier, sql, col):
    out = []
    for x in vg_classifier.literals_on_column(sql, col):
        out.append(x[-1] if isinstance(x, (tuple, list)) else x)
    return out


def bool_field(v):
    return str(v).strip() == "True"


def classified_sql(sql, parse_ok):
    """The text B2.3 classifies for one failing run: the SQL when it parsed, else ''.
    This is the rule analyze_rc1.py applies when it builds sql_of for the API runs
    (sql if parse_ok else ''): a run whose SQL failed to parse is classified as a run
    without SQL (NO_PRED, never GF). The chat kit applies it to the chat cells
    (vg_outcome) and to the proxy runs (chat_report) so that both agree with the B2.2 GF of
    analyze_rc1.py; selftest_chat.py checks that agreement on the same synthetic data."""
    return (sql or "") if bool_field(parse_ok) else ""


def classify_record(vgc, sql, parse_ok, targets, vocab):
    """B2.3 class of one failing run from its record fields (see classified_sql)."""
    return vgc.classify_run(classified_sql(sql, parse_ok), targets, vocab)


def load_classifier(hdir):
    """Import the shared B2.3 classifier and vg_rule from the harness folder."""
    if hdir not in sys.path:
        sys.path.insert(0, hdir)
    import vg_classifier  # noqa: E402
    import vg_rule  # noqa: E402
    return vg_classifier, vg_rule


def load_chat_graded_runs(path, label="graded"):
    """{(model_key, lang, qid, run): row} of a chat graded file (arm chat only, no duplicate,
    verdicts True/False)."""
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    check_bool_fields(rows, label)
    graded = {}
    for r in rows:
        if (r.get("arm") or "") != "chat":
            die(f"{label}: graded file holds a row whose arm is not 'chat'")
        k = (r["model_key"], r["lang"], r["qid"], str(r["run"]))
        if k in graded:
            die(f"{label}: duplicate graded row {k}")
        graded[k] = r
    return graded


def load_chat_results(path, graded, label="results"):
    """chat records (error-free, arm chat, no duplicate) matching `graded` one to one."""
    recs = read_jsonl(path, RESULT_FIELDS)
    keys = set()
    for rec in recs:
        if rec.get("error_is_set") or rec.get("arm") != "chat":
            die(f"{label}: an error record or a record whose arm is not 'chat'")
        k = (rec["model_key"], rec["lang"], rec["qid"], str(rec["run"]))
        if k in keys:
            die(f"{label}: duplicate result record {k}")
        keys.add(k)
    if keys != set(graded):
        die(f"{label}: graded rows ({len(graded)}) and result records ({len(recs)}) do not match one to one")
    return recs


def vg_setup(suite, vg_classifier, vg_rule):
    """(literals, targets) of VG_CHAT; exits when the suite's VG set differs from VG_CHAT."""
    prim = primary_ids(suite)
    vg = [q for q in prim if vg_rule.is_value_grounding(suite[q]["gold_sql_draft"], suite[q]["question_th"])]
    if vg != VG_CHAT:
        die(f"VG set of the suite {vg} != VG_CHAT")
    lits = {q: vg_rule.value_grounding_literals(suite[q]["gold_sql_draft"], suite[q]["question_th"])
            for q in VG_CHAT}
    targets = {q: vg_classifier.vg_targets(suite[q]["gold_sql_draft"], lits[q]) for q in VG_CHAT}
    return lits, targets


def code_cells(recs, graded, lits, targets, vocab, vg_classifier):
    """B2.3 coding of every chat cell (the rule of the module docstring). Shared with
    chat_report.py, which applies it to the OQ33.1 tag-sensitivity records.
    Returns (rows sorted app/form/qid, audit rows, tally, q48_none, n_parse_fail)."""
    rows, audit = [], []
    tally = Counter()
    q48_none = n_parse_fail = 0
    for rec in recs:
        m = MODEL_KEY.match(rec["model_key"])
        if not m:
            die(f"unexpected model_key {rec['model_key']}")
        app, form = m.group(1), m.group(2)
        g = graded[(rec["model_key"], rec["lang"], rec["qid"], str(rec["run"]))]
        correct, ex_ok = bool_field(g["correct"]), bool_field(g["exec_ok"])
        sql = rec.get("sql") or ""
        present = rec["sql_present"] if "sql_present" in rec else (
            bool(sql) and sql.lower().lstrip().startswith(("select", "with")))
        q = rec["qid"]
        row = {"app": app, "form": form, "lang": rec["lang"], "qid": q, "vg": "yes" if q in VG_CHAT else "no",
               "correct": "Y" if correct else "N", "exec_ok": "Y" if ex_ok else "N",
               "n_rows": g.get("n_rows", ""), "fail_reason": g.get("fail_reason", ""),
               "exec_class": exec_class(correct, ex_ok, g.get("n_rows")),
               "sql_present": "Y" if present else "N", "vg_code": "NA", "gf": "", "clean": "",
               "lit_elsewhere": "", "extract_rule": rec.get("extract_rule", ""), "attempt": rec.get("attempt", ""),
               "class_extracted": ""}
        if q in VG_CHAT:
            if correct:
                code = "CORRECT"
            elif not present:
                code = "NO_SQL"
            else:
                seen = classified_sql(sql, rec.get("parse_ok"))
                code = classify_record(vg_classifier, sql, rec.get("parse_ok"), targets[q], vocab)
                row["class_extracted"] = vg_classifier.classify_run(sql, targets[q], vocab)
                n_parse_fail += not bool_field(rec.get("parse_ok"))
                audit.append([app, form, q, "; ".join(f"{c}='{v}'" for c, v in targets[q]), seen, code])
                if q == "Q48" and "None" in lits_on(vg_classifier, seen, "runnerup"):
                    q48_none += 1
            gf = (not correct) and code in GF_CLASSES
            clean = correct or code in CLEAN_CLASSES
            row.update({"vg_code": code, "gf": "Y" if gf else "N", "clean": "Y" if clean else "N",
                        "lit_elsewhere": "Y" if lit_elsewhere(rec.get("raw"), sql, lits[q]) else "N"})
            tally[(app, form, "vg_cells")] += 1
            tally[(app, form, code)] += 1
            tally[(app, form, "GF")] += gf
            tally[(app, form, "clean")] += clean
        rows.append(row)
    app_rank = {x: i for i, x in enumerate(APPS)}
    rows.sort(key=lambda r: (app_rank[r["app"]], r["form"], r["qid"]))
    audit.sort(key=lambda x: (app_rank[x[0]], x[1], x[2]))
    return rows, audit, tally, q48_none, n_parse_fail


def meta_path_of(vg_codes_path):
    return os.path.splitext(vg_codes_path)[0] + "_meta.json"


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--graded", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--hints", required=True)
    ap.add_argument("--hints-sha256", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--audit-rows", help="default: <out without extension>_audit_rows.csv")
    ap.add_argument("--vocab-db", choices=VOCAB_DBS, default="k3n",
                    help="k3n (default) or k3 (OQ33.7 sensitivity: stored 'None' added, see the docstring)")
    ap.add_argument("--harness-dir", help="folder with vg_rule.py and vg_classifier.py")
    a = ap.parse_args()
    check_switches()
    audit_path = a.audit_rows or os.path.splitext(a.out)[0] + "_audit_rows.csv"
    meta_path = meta_path_of(a.out)
    for p in (a.out, audit_path, meta_path):
        if os.path.exists(p):
            die(f"output exists, refusing to overwrite: {os.path.basename(p)}")
    hs = sha256_file(a.hints)
    if hs != a.hints_sha256.strip().lower():
        die(f"sha256 of --hints is {hs}, expected {a.hints_sha256}")

    vg_classifier, vg_rule = load_classifier(harness_dir(a.harness_dir))
    suite = load_suite(a.suite)
    refuse_draft_suite(a.suite, suite, [a.out, audit_path])
    lits, targets = vg_setup(suite, vg_classifier, vg_rule)
    vocab, vocab_src = load_vocab(vg_classifier, a.hints, targets, a.vocab_db)
    graded = load_chat_graded_runs(a.graded)
    recs = load_chat_results(a.results, graded)
    rows, audit, tally, q48_none, n_parse_fail = code_cells(recs, graded, lits, targets, vocab, vg_classifier)

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "x", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(VG_COLUMNS)
        for r in rows:
            w.writerow([r[k] for k in VG_COLUMNS])
    with open(audit_path, "x", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(AUDIT_COLUMNS)
        w.writerows(audit)
    meta = {"tool": "vg_outcome.py", "tool_sha256": sha256_file(os.path.abspath(__file__)),
            "graded_file": os.path.basename(a.graded), "graded_sha256": sha256_file(a.graded),
            "results_file": os.path.basename(a.results), "results_sha256": sha256_file(a.results),
            "suite_file": os.path.basename(a.suite), "suite_sha256": sha256_file(a.suite),
            "hints_sha256": hs, "vocab_db": a.vocab_db, "vocab_source": vocab_src,
            "q48_vocab_rule": getattr(vg_classifier, "Q48_VOCAB_RULE", "?"), "n_cells": len(rows),
            "vg_codes_file": os.path.basename(a.out), "vg_codes_sha256": sha256_file(a.out),
            "audit_rows_file": os.path.basename(audit_path), "audit_rows_sha256": sha256_file(audit_path)}
    with open(meta_path, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True) + "\n")

    print(f"vocabulary: {vocab_src}; database {a.vocab_db}; hints sha256 {hs}")
    print(f"cells: {len(rows)} (VG cells {sum(1 for r in rows if r['vg'] == 'yes')})")
    for app in APPS:
        for form in FORMS:
            n = tally[(app, form, "vg_cells")]
            if not n:
                continue
            classes = ", ".join(f"{c} {tally[(app, form, c)]}" for c in
                                ("CORRECT", "NO_SQL", "THAI_COPY", "INVENTED", "GROUNDED", "STORED", "NO_PRED")
                                if tally[(app, form, c)])
            print(f"  {app:8} Form {form}: VG cells {n}; GF {tally[(app, form, 'GF')]}; "
                  f"clean {tally[(app, form, 'clean')]}; {classes}")
    print(f"wrong VG cells with SQL that failed to parse (classified as without SQL, as in "
          f"analyze_rc1.py): {n_parse_fail}")
    print(f"Q48 wrong cells comparing RunnerUp with 'None': {q48_none} (B2.3 applied unchanged; OQ6)")
    print(f"[out] {os.path.basename(a.out)} sha256={meta['vg_codes_sha256']}")
    print(f"[out] {os.path.basename(audit_path)} rows={len(audit)} sha256={meta['audit_rows_sha256']}")
    print(f"[out] {os.path.basename(meta_path)}")


if __name__ == "__main__":
    main()
