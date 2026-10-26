#!/usr/bin/env python3
"""paper_numbers_v13n.py -- paper-level numbers from a graded file (from
kst_rev/wf_d7/tools/paper_numbers_v13.py + flagged_gap_v13.py).

Run on the base arm of the October session with the October core suite (primary numbers
of the revised paper; D11: Q27 repaired and primary, n=60) and on the August log
re-graded on k3n with the August suite (n=59; numbers of the consistency comparison only;
D10). analyze.d11_check pairs the suite with the graded file.
  * frontier failed runs and the share that executed (silent), split empty / non-empty
  * grade-unanimous cells, API vs local and per model x language
  * API mean single-run accuracy vs majority accuracy
  * pooled EN->TH gap on the clarity-flagged items (sheets A and B) vs the rest
    (the rest = analysed items minus the flagged list; 53 under n=60 on the October core
    suite, 52 under n=59 on the August suite)
  * Q13 correct for every model in both languages
--arm contract of analyze.py (required; rows without arm = base; every cell must have
--runs runs); every ratio guards a zero denominator. Silent empty / non-empty come
from analyze.b1_class (a blank n_rows on an executed run stops, as in every B1 script).
Writes --out (text) and <out>.meta.json.

Usage: python3 -I -B paper_numbers_v13n.py --graded ../results/rc1/graded_rc1.csv \
         --suite ../suite/k3n_suite_v1.3n_oct.tsv --arm base --out ../results/rc1/paper_numbers_oct.txt
"""
import argparse
import collections
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402

FR = {"claude-sonnet", "gemini-flash", "gpt-mini"}
LOC = {"llama31-8b", "qwen25-coder-7b", "typhoon2-8b"}
FLAGGED = ["Q03", "Q10", "Q12", "Q13", "Q37", "Q52", "Q60"]   # score_annotation.py, sheets A+B
Q_ALL_SIX = "Q13"


def T(s):
    return s == "True"


def pct(x, n):
    return f"{100 * x / n:.1f}%" if n else "n/a (0 denominator)"


def main():
    ap = argparse.ArgumentParser(description="paper-level numbers")
    ap.add_argument("--graded", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep-excluded", action="store_true")
    ac.add_arm_contract(ap)
    ac.add_draft_flag(ap)
    a = ap.parse_args()
    suite_rows = ac.load_suite_rows(a.suite)
    ac.draft_guard(a.suite, suite_rows, a.allow_draft_testonly, out_files=[a.out])
    suite = ac.primary_suite(suite_rows, a.keep_excluded)
    excluded = ac.split_list(a.exclude_models)
    rows_all = ac.read_csv_rows(a.graded)
    grec = ac.graded_record(a.graded, rows_all, a.arm)
    ac.d11_check(suite_rows, a.keep_excluded, grec, os.path.basename(a.suite))
    g = ac.filter_arm(rows_all, a.arm, excluded)
    ac.require_complete(g, a.runs, sorted(suite))
    g = [r for r in g if r["qid"] in suite]
    out = []

    def P(s):
        print(s)
        out.append(s)

    P(f"paper numbers: arm {a.arm}; items {len(suite)}; graded {os.path.basename(a.graded)}")
    fail = [r for r in g if r["model_key"] in FR and not T(r["correct"])]
    silent = [r for r in fail if T(r["exec_ok"])]
    P(f"frontier failed runs {len(fail)}, silent (executed) {len(silent)} = {pct(len(silent), len(fail))}")
    if g and "n_rows" in g[0]:
        cls = collections.Counter(ac.b1_class(r) for r in silent)
        P(f"  silent non-empty {cls['silent_nonempty']} ({pct(cls['silent_nonempty'], len(fail))} "
          f"of failed runs), silent empty {cls['silent_empty']}")
    runs = collections.defaultdict(list)
    for r in g:
        runs[(r["model_key"], r["lang"], r["qid"])].append(T(r["correct"]))
    for grp, ms in (("API", FR), ("local", LOC)):
        ks = [k for k in runs if k[0] in ms]
        un = sum(1 for k in ks if len(set(runs[k])) == 1)
        P(f"{grp}: grade-unanimous cells {un}/{len(ks)}")
        for m in sorted(ms):
            for lg in ("en", "th"):
                kk = [k for k in ks if k[0] == m and k[1] == lg]
                u = sum(1 for k in kk if len(set(runs[k])) == 1)
                P(f"   {m:16s} {lg} unanimity {u}/{len(kk)} = {pct(u, len(kk))}")
    api = [k for k in runs if k[0] in FR]
    n_runs = sum(len(runs[k]) for k in api)
    single = sum(sum(runs[k]) for k in api)
    maj = sum(1 for k in api if sum(runs[k]) > len(runs[k]) / 2)
    P(f"API mean single-run acc {pct(single, n_runs)} vs majority {pct(maj, len(api))}")

    item = {k: sum(v) > len(v) / 2 for k, v in runs.items()}
    models = sorted({k[0] for k in item})
    qids = sorted(suite)
    fl = [q for q in FLAGGED if q in suite]
    rest = [q for q in qids if q not in fl]

    def gap(qs):
        en = sum(item.get((m, "en", q), False) for m in models for q in qs)
        th = sum(item.get((m, "th", q), False) for m in models for q in qs)
        den = len(models) * len(qs)
        return f"{100 * (en - th) / den:+.1f} pts" if den else "n/a (0 denominator)"

    P(f"flagged {len(fl)}: gap {gap(fl)} | rest {len(rest)}: gap {gap(rest)}")
    if Q_ALL_SIX in suite:
        P(f"{Q_ALL_SIX} correct for all {len(models)} models in both languages: "
          f"{all(item.get((m, l, Q_ALL_SIX), False) for m in models for l in ('en', 'th'))}")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write("\n".join(out) + "\n")
    detail = {"inputs": {"graded": grec}, "runs": a.runs,
              "excluded_models": sorted(excluded), "flagged": fl}
    ac.write_file_meta(a.out, "paper_numbers_v13n.py",
                       ac.common_meta(a.arm, a.suite, a.keep_excluded, len(suite)), detail)


if __name__ == "__main__":
    main()
