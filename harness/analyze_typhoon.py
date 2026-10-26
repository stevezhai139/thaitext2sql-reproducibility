#!/usr/bin/env python3
"""analyze_typhoon.py — I-1 of the revision checklist (committed, reproducible):

(a) the missing significance test for the paper's sharpest claim: PAIRED
    exact McNemar, typhoon2-8b vs its base llama31-8b, per language, on
    item-level majority correctness (same convention as analyze.py);
(b) error taxonomy for the pair: parse_fail / exec_error (bucketed) /
    wrong-result (silent), per language + per tier + value-grounding overlap
    (set derived from the canonical vg_rule.py, or read from --vg-set).

Gate 0 (KST 2027 revision; GATE0 design 2.6):
  * --arm contract of analyze.py (required, rows without arm = base, every cell must
    have --runs runs after the filter, meta.json in the output folder);
  * graded rows are restricted to the items of the (filtered) suite, so an excluded
    item (Q27 on the August suite v1.3/v1.3n) no longer leaks into the taxonomy (fix of
    l.69-74); D11 (analyze.d11_check): on the October core suite Q27 is repaired and
    primary (n=60, the primary October analysis) and only the two-arm October core log is
    accepted; --keep-excluded with the August suite on the October log is refused;
  * --b6 (AMENDMENT-7 B6) adds rows 'b6_runs' with loud / silent-empty /
    silent-non-empty per model x language (analyze.b1_class: needs the n_rows column of
    grade_v13n; a blank n_rows on an executed run stops) and 'b6_schema_shaped'
    (schema_shaped = loud runs whose PostgreSQL message says a column or a function
    does not exist, the definition of analyze.B6_BAD_COLUMN / B6_BAD_FUNCTION shared
    with analyze_log_v13.py; 'operator does not exist' and 'relation ... does not exist'
    are reported in their own columns outside schema_shaped);
  * if typhoon2-8b or llama31-8b is absent (--exclude-models, AM-7 A5.6, or not in the
    data), the paired McNemar (A) and the value-grounding overlap (D) are not computed:
    the rows say 'pair model absent' instead of counts (an absent model is never
    counted as 0 correct);
  * --graded, --suite and --out are required (no default pointing at the submitted
    results/tables or results/graded.csv; D10); --allow-draft-testonly as analyze.py;
  * without --b6 the output on v1.2 (results/graded.csv, suite v1.2, --arm base) is
    byte-identical to the submitted results/tables/typhoon_analysis.csv.

Usage: python3 -I -B analyze_typhoon.py --graded ../results/rc1/graded_rc1.csv \
         --suite ../suite/k3n_suite_v1.3n_oct.tsv --arm base --b6 --out ../results/rc1/base60/tables
"""
from __future__ import annotations
import argparse
import csv
import os
import sys
from collections import defaultdict
from math import comb

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402  (single implementation of the --arm contract)

PAIR = ("typhoon2-8b", "llama31-8b")


def exact_mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    tail = sum(comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n
    return min(1.0, 2 * tail)


def bucket(reason):
    r = (reason or "").lower()
    if not r:
        return "ok"
    if r == "wrong-result":
        return "wrong_result_silent"
    if r.startswith("exec-error"):
        if "column" in r:
            return "exec_bad_column"
        if "function" in r or "operator" in r:
            return "exec_bad_function_op"
        if "syntax" in r or "invalid input" in r:
            return "exec_syntax_type"
        if "from-clause" in r:
            return "exec_bad_from"
        return "exec_other"
    return "parse_fail"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graded", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--out", required=True, help="output folder (no default: D10)")
    ap.add_argument("--keep-excluded", action="store_true",
                    help="v1.3: keep items with v13_status=excluded (n=60 sensitivity of the "
                         "August log; the October core suite has no excluded item, D11)")
    ap.add_argument("--vg-set", help="VG list file (one qid per line); default vg_rule")
    ap.add_argument("--b6", action="store_true",
                    help="AM-7 B6 rows: loud/silent split and schema-shaped loud runs")
    ac.add_arm_contract(ap)
    ac.add_draft_flag(ap)
    a = ap.parse_args()
    suite = {r["id"]: r for r in csv.DictReader(open(a.suite, encoding="utf-8"),
                                                delimiter="\t")}
    ac.draft_guard(a.suite, suite, a.allow_draft_testonly, out_dirs=[a.out])
    rows_all = ac.read_csv_rows(a.graded)
    grec = ac.graded_record(a.graded, rows_all, a.arm)
    ac.d11_check(suite, a.keep_excluded, grec, os.path.basename(a.suite))
    os.makedirs(a.out, exist_ok=True)
    if not a.keep_excluded:  # v1.3 (D7)
        suite = {k: v for k, v in suite.items()
                 if (v.get("v13_status") or "primary").strip() != "excluded"}
    if a.vg_set:
        vgs = set(ac.read_vg_set(a.vg_set, universe=suite))
        val_tr = {qid: qid in vgs for qid in suite}
    else:
        from vg_rule import is_value_grounding
        val_tr = {qid: is_value_grounding(r["gold_sql_draft"], r["question_th"])
                  for qid, r in suite.items()}

    common = ac.common_meta(a.arm, a.suite, a.keep_excluded, len(suite))
    ac.guard_dir_meta(a.out, common, grec)  # before any output is written
    excluded_models = ac.split_list(a.exclude_models)
    graded = ac.filter_arm(rows_all, a.arm, excluded_models)
    ac.require_complete(graded, a.runs, sorted(suite))
    n_out = sum(1 for r in graded if r["qid"] not in suite)
    graded = [r for r in graded if r["qid"] in suite]   # fix: excluded items stay out
    if n_out:
        print(f"[suite] {n_out} graded rows of items outside the analysed suite ignored")

    runs = defaultdict(list)
    fails = defaultdict(lambda: defaultdict(int))   # (model,lang) -> bucket -> n
    tier_fail = defaultdict(lambda: defaultdict(int))
    for row in graded:
        m, lang, qid = row["model_key"], row["lang"], row["qid"]
        runs[(m, lang, qid)].append(row["correct"] == "True")
        if m in PAIR and row["correct"] != "True":
            fails[(m, lang)][bucket(row["fail_reason"])] += 1
            tier_fail[(m, lang)][row["tier"]] += 1

    item = {k: (sum(v) > len(v) / 2) for k, v in runs.items()}
    qids = sorted(suite)
    present = {r["model_key"] for r in graded}
    absent = [m for m in PAIR if m not in present]

    out_rows = []
    print("=" * 72)
    print("A) Paired exact McNemar — typhoon2-8b vs llama31-8b (item majority)")
    print("=" * 72)
    if absent:
        print(f"  not computed: pair model absent {absent} (excluded or not in the data)")
        for lang in ("en", "th"):
            out_rows.append({"section": "mcnemar_pair", "lang": lang,
                             "status": f"pair model absent: {' '.join(absent)}"})
    for lang in (() if absent else ("en", "th")):
        b = sum(1 for q in qids if item.get((PAIR[1], lang, q)) and not item.get((PAIR[0], lang, q)))
        c = sum(1 for q in qids if item.get((PAIR[0], lang, q)) and not item.get((PAIR[1], lang, q)))
        p = exact_mcnemar(b, c)
        n_t = sum(1 for q in qids if item.get((PAIR[0], lang, q)))
        n_l = sum(1 for q in qids if item.get((PAIR[1], lang, q)))
        print(f"  {lang.upper()}: typhoon {n_t}/{len(qids)} vs llama {n_l}/{len(qids)} | "
              f"b(llama-only)={b} c(typhoon-only)={c} | exact p={p:.4f}")
        out_rows.append({"section": "mcnemar_pair", "lang": lang, "typhoon": n_t,
                         "llama": n_l, "b": b, "c": c, "p_exact": round(p, 4)})

    print("\nB) Error taxonomy (failed runs, n per bucket)")
    print("=" * 72)
    for (m, lang), bk in sorted(fails.items()):
        tot = sum(bk.values())
        top = ", ".join(f"{k}={v}" for k, v in sorted(bk.items(), key=lambda x: -x[1]))
        print(f"  {m:14} {lang}: total_fail_runs={tot:4} | {top}")
        for k, v in bk.items():
            out_rows.append({"section": "taxonomy", "lang": lang, "model": m,
                             "bucket": k, "n": v})

    print("\nC) Failed runs per tier")
    print("=" * 72)
    for (m, lang), tk in sorted(tier_fail.items()):
        print(f"  {m:14} {lang}: " + ", ".join(f"T{t}={n}" for t, n in sorted(tk.items())))

    print("\nD) Value-grounding overlap (TH wrong items in the value-grounding set)")
    print("=" * 72)
    vg = [q for q in qids if val_tr[q]]
    for m in PAIR:
        if m in absent:
            print(f"  {m:14}: not computed (model absent)")
            out_rows.append({"section": "value_grounding", "model": m, "status": "model absent"})
            continue
        wrong_th = [q for q in qids if not item.get((m, "th", q))]
        inter = [q for q in wrong_th if q in vg]
        print(f"  {m:14}: TH wrong={len(wrong_th)}; in value-grounding set={len(inter)}/{len(vg)}")
        out_rows.append({"section": "value_grounding", "model": m,
                         "th_wrong": len(wrong_th), "vg_wrong": len(inter), "vg_total": len(vg)})

    if a.b6:
        print("\nE) AM-7 B6 (exploratory): loud / silent-empty / silent-non-empty and "
              "schema-shaped loud runs")
        print("=" * 72)
        models = sorted({r["model_key"] for r in graded})
        for m in models:
            for lang in ("en", "th"):
                wrong = [r for r in graded if r["model_key"] == m and r["lang"] == lang
                         and r["correct"] != "True"]
                cls = defaultdict(int)
                col = fn = op = rel = shaped = 0
                for r in wrong:
                    cls[ac.b1_class(r)] += 1
                    c_, f_, o_, r_ = ac.b6_flags(r["fail_reason"])
                    col += c_
                    fn += f_
                    op += o_
                    rel += r_
                    shaped += c_ or f_
                print(f"  {m:16} {lang}: wrong={len(wrong):4} loud={cls['loud']:4} "
                      f"silent_empty={cls['silent_empty']:4} silent_nonempty={cls['silent_nonempty']:4}"
                      f" | schema-shaped loud {shaped} (column={col} function={fn}); apart: "
                      f"operator={op} relation={rel}")
                out_rows.append({"section": "b6_runs", "model": m, "lang": lang,
                                 "wrong_runs": len(wrong), "loud": cls["loud"],
                                 "silent_empty": cls["silent_empty"],
                                 "silent_nonempty": cls["silent_nonempty"]})
                out_rows.append({"section": "b6_schema_shaped", "model": m, "lang": lang,
                                 "bad_column": col, "bad_function": fn, "bad_operator": op,
                                 "bad_relation": rel, "schema_shaped": shaped})

    with open(os.path.join(a.out, "typhoon_analysis.csv"), "w", newline="",
              encoding="utf-8") as fh:
        keys = sorted({k for r in out_rows for k in r})
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(out_rows)
    print(f"\n[out] {os.path.join(a.out, 'typhoon_analysis.csv')}")
    detail = {"inputs": {"graded": grec}, "runs": a.runs,
              "excluded_models": sorted(excluded_models), "b6": bool(a.b6),
              "pair_absent": absent,
              "vg_set": ac.input_record(a.vg_set) if a.vg_set else "vg_rule.is_value_grounding",
              "files": ["typhoon_analysis.csv"]}
    ac.update_dir_meta(a.out, "analyze_typhoon.py", common, detail)


if __name__ == "__main__":
    main()
