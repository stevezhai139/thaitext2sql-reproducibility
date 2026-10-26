#!/usr/bin/env python3
"""consistency_aug_oct.py -- short, descriptive consistency comparison between the
August log re-graded on k3n with key v1.3n (data of the submitted version) and the base
arm of the October session (primary data; brief 1.0 / D10, AM-7 Part 0 item 3, OQ37).
Not a parity target, no test, no pooling of the two sessions; graded files only (no
jsonl, no raw).

D11 (brief 1.0b): Q27 is repaired for the October session only, so the two sessions
share 59 items. The comparison runs on these shared items only:
  --aug-suite  the August suite (analyze.suite_session 'august': every repaired item of
               analyze.D11_REPAIRED excluded, the original question);
  --oct-suite  the October core suite (session 'october': every repaired item primary);
  shared items = primary in both suites, minus the repaired items; every shared item
  must carry the same question, gold, accepted alternatives and grading columns in both
  suites (exit 2 otherwise), and the count must equal the August primary count (59).
  There is no n=60 comparison (Q27 is a different question in the two sessions).
Per model x language: majority-correct items in August and October, items whose verdict
differs by direction (August correct -> October wrong, and the reverse), unanimity rate of
the cells in each session. Local models carry the label exploratory.
Outputs in --out: consistency.csv (paper), consistency_items.csv (per item, artifact),
consistency_summary.txt and meta.json. --arm applies to both files (contract of
analyze.py; rows without arm are base).
D10 guard: --aug and --oct must come from two different sessions (not the same file, and
session fingerprints that differ on the shared items: analyze.same_session); --oct must be
the two-arm October core log (analyze.d11_check on the October core suite) and --aug a file
without the values arm (the August log holds the base arm only). Each graded file is read
once; the shared items may carry rows of the repaired items in either file (e.g. the
August file graded with --keep-excluded): those rows are left out.

Usage (Gate 3 step 50):
  python3 -I -B consistency_aug_oct.py --aug ../results/v13n/graded_v13n.csv \
    --oct ../results/rc1/graded_rc1.csv --aug-suite ../suite/k3n_suite_v1.3n.tsv \
    --oct-suite ../suite/k3n_suite_v1.3n_oct.tsv --arm base --out ../results/rc1/consistency
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402

ORDER = ["claude-sonnet", "gpt-mini", "gemini-flash", "qwen25-coder-7b", "llama31-8b",
         "typhoon2-8b"]
LOCAL = {"qwen25-coder-7b", "llama31-8b", "typhoon2-8b"}
# columns that decide the verdict of an item; a shared item must agree on every one of
# them that both suites carry (D11: only the repaired items may differ)
SAME_COLUMNS = ("question_en", "question_th", "gold_sql_draft", "alt_gold_en", "alt_gold_th",
                "order_en", "order_th", "sort_keys", "norm", "v13_status", "col_roles",
                "mi_instances")


def cells_of(rows_all, arm, runs, qids, excluded, label):
    """{(model, lang, qid): [correct, ...]} of the shared items (rows of other items, e.g.
    the repaired ones, are left out); every shared cell must have exactly `runs` runs."""
    rows = ac.filter_arm(rows_all, arm, excluded, label)
    ac.require_complete(rows, runs, qids, label)
    keep = set(qids)
    c = defaultdict(list)
    for r in rows:
        if r["qid"] in keep:
            c[(r["model_key"], r["lang"], r["qid"])].append(r["correct"] == "True")
    return c


def shared_items(aug_rows, oct_rows, aug_name, oct_name):
    """D11: the items both sessions asked in the same form (sorted list)."""
    sa = ac.suite_session(aug_rows, aug_name)
    so = ac.suite_session(oct_rows, oct_name)
    if sa != ac.SESSION_AUG:
        ac.die(2, f"[D11] --aug-suite {aug_name} is of session {sa!r}; the August suite keeps the "
                  f"repaired items {list(ac.D11_REPAIRED)} excluded")
    if so != ac.SESSION_OCT:
        ac.die(2, f"[D11] --oct-suite {oct_name} is of session {so!r}; the October core suite "
                  f"carries the repaired items {list(ac.D11_REPAIRED)} as primary")
    pa = set(ac.primary_suite(aug_rows, False))
    po = set(ac.primary_suite(oct_rows, False))
    shared = sorted(ac.d11_shared(sorted(pa & po), ac.SESSION_OCT))
    if set(shared) != pa or set(shared) != po - set(ac.D11_REPAIRED):
        ac.die(2, f"[D11] the primary items of the two suites differ beyond the repaired items "
                  f"{list(ac.D11_REPAIRED)}: August only {sorted(pa - po)}, October only "
                  f"{sorted(po - pa - set(ac.D11_REPAIRED))}")
    diff = []
    for q in shared:
        for col in SAME_COLUMNS:
            if col in aug_rows[q] and col in oct_rows[q] and \
                    (aug_rows[q][col] or "").strip() != (oct_rows[q][col] or "").strip():
                diff.append((q, col))
    if diff:
        ac.die(2, f"[D11] {len(diff)} shared items differ between the two suites (first "
                  f"{diff[:5]}); only the repaired items {list(ac.D11_REPAIRED)} may differ")
    return shared


def check_sessions(recs):
    """D10: August and October are two sessions."""
    same, why = ac.same_session(recs["aug"], recs["oct"])
    if same:
        ac.die(2, f"[D10] --aug and --oct come from the same session ({why}): "
                  f"{recs['aug']['basename']} / {recs['oct']['basename']}; refused")
    for k, r in recs.items():
        print(f"[D10] --{k}: {ac.describe(r)}")


def compare(aug, octo, qids, n_label):
    out, items = [], []
    models = [m for m in ORDER if any(k[0] == m for k in aug) or any(k[0] == m for k in octo)]
    models += sorted({k[0] for k in list(aug) + list(octo)} - set(models))
    for m in models:
        for lg in ("en", "th"):
            if (m, lg, qids[0]) not in aug or (m, lg, qids[0]) not in octo:
                out.append({"n": n_label, "model": m, "lang": lg, "status": "not in both sessions"})
                continue
            ma = {q: sum(aug[(m, lg, q)]) > len(aug[(m, lg, q)]) / 2 for q in qids}
            mo = {q: sum(octo[(m, lg, q)]) > len(octo[(m, lg, q)]) / 2 for q in qids}
            ua = sum(len(set(aug[(m, lg, q)])) == 1 for q in qids)
            uo = sum(len(set(octo[(m, lg, q)])) == 1 for q in qids)
            a2w = sorted(q for q in qids if ma[q] and not mo[q])
            w2a = sorted(q for q in qids if mo[q] and not ma[q])
            out.append({"n": n_label, "model": m, "lang": lg, "status": "ok",
                        "items": len(qids), "aug_correct": sum(ma.values()),
                        "oct_correct": sum(mo.values()),
                        "aug_correct_oct_wrong": len(a2w), "aug_wrong_oct_correct": len(w2a),
                        "aug_unanimity": f"{ua / len(qids):.3f}",
                        "oct_unanimity": f"{uo / len(qids):.3f}",
                        "exploratory": m in LOCAL})
            for q in qids:
                items.append({"n": n_label, "model": m, "lang": lg, "qid": q,
                              "aug_majority": ma[q], "oct_majority": mo[q],
                              "aug_correct_runs": sum(aug[(m, lg, q)]),
                              "oct_correct_runs": sum(octo[(m, lg, q)]),
                              "differs": ma[q] != mo[q]})
    return out, items


def write(path, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def main():
    ap = argparse.ArgumentParser(description="August (k3n, v1.3n) vs October base arm, on the "
                                             "items shared by the two sessions (D11)")
    ap.add_argument("--aug", required=True, help="August log re-graded on k3n (graded_v13n.csv)")
    ap.add_argument("--oct", required=True, help="October core log (graded_rc1.csv, two arms)")
    ap.add_argument("--aug-suite", required=True, help="August suite (Q27 excluded)")
    ap.add_argument("--oct-suite", required=True, help="October core suite (Q27 repaired, primary)")
    ap.add_argument("--out", required=True)
    ac.add_arm_contract(ap)
    ac.add_draft_flag(ap)
    a = ap.parse_args()
    excluded = ac.split_list(a.exclude_models)
    aug_rows = ac.load_suite_rows(a.aug_suite)
    oct_rows = ac.load_suite_rows(a.oct_suite)
    ac.draft_guard(a.aug_suite, aug_rows, a.allow_draft_testonly, out_dirs=[a.out])
    ac.draft_guard(a.oct_suite, oct_rows, a.allow_draft_testonly, out_dirs=[a.out])
    shared = shared_items(aug_rows, oct_rows, os.path.basename(a.aug_suite),
                          os.path.basename(a.oct_suite))
    print(f"[D11] comparison on the {len(shared)} items shared by the two sessions "
          f"({', '.join(ac.D11_REPAIRED)} repaired for the October session only, left out)")
    aug_all = ac.read_csv_rows(a.aug)
    oct_all = ac.read_csv_rows(a.oct)
    recs = {"aug": ac.graded_record(a.aug, aug_all, a.arm),
            "oct": ac.graded_record(a.oct, oct_all, a.arm)}
    if "values" in recs["aug"]["arms_in_file"]:
        ac.die(2, f"[D10] --aug {ac.describe(recs['aug'])} holds the values arm; the August log "
                  f"holds the base arm only (is it the October core log?); refused")
    ac.d11_check(aug_rows, False, recs["aug"], "--aug-suite")
    ac.d11_check(oct_rows, False, recs["oct"], "--oct-suite")
    check_sessions(recs)                   # before any output is written
    os.makedirs(a.out, exist_ok=True)
    common = ac.common_meta(a.arm, a.oct_suite, False, len(shared))
    common["suite_session"] = "shared (D11: items of both suites, repaired items left out)"
    ac.guard_dir_meta(a.out, common)       # before any output is written
    aug = cells_of(aug_all, a.arm, a.runs, shared, excluded, "aug")
    octo = cells_of(oct_all, a.arm, a.runs, shared, excluded, "oct")
    rows, items = compare(aug, octo, shared, str(len(shared)))
    write(os.path.join(a.out, "consistency.csv"), rows)
    write(os.path.join(a.out, "consistency_items.csv"), items)
    lines = [f"August (k3n, v1.3n) vs October base arm on the {len(shared)} shared items -- "
             f"descriptive, no test (D10, D11)"]
    for r in rows:
        if r["status"] != "ok":
            lines.append(f"  n={r['n']} {r['model']:16} {r['lang']}: {r['status']}")
            continue
        lines.append(f"  n={r['n']} {r['model']:16} {r['lang']}: Aug {r['aug_correct']} / Oct "
                     f"{r['oct_correct']}; Aug->Oct correct->wrong {r['aug_correct_oct_wrong']}, "
                     f"wrong->correct {r['aug_wrong_oct_correct']}; unanimity "
                     f"{r['aug_unanimity']} / {r['oct_unanimity']}"
                     + (" (exploratory)" if r["exploratory"] else ""))
    with open(os.path.join(a.out, "consistency_summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    detail = {"inputs": dict(recs, aug_suite=ac.input_record(a.aug_suite),
                             oct_suite=ac.input_record(a.oct_suite)),
              "runs": a.runs, "excluded_models": sorted(excluded), "shared_items": len(shared),
              "left_out_d11": list(ac.D11_REPAIRED)}
    ac.update_dir_meta(a.out, "consistency_aug_oct.py", common, detail)


if __name__ == "__main__":
    main()
