#!/usr/bin/env python3
"""phi_tableiv.py -- AMENDMENT-7 D-1: the condition for the word "conservative" in the
Table IV interval label (D8 path A).

Per model: the item-level 2x2 table of English x Thai majority correctness on the
analysed items (a = both correct, b = EN only, c = TH only, d = both wrong) and
  phi = (a*d - b*c) / sqrt((a+b)(c+d)(a+c)(b+d)).
Label of Table IV (registered before the re-grade):
  every row phi >= 0  -> CI_LABEL_CONSERVATIVE
  some row phi < 0    -> CI_LABEL_NOT_CORRECTED (and that row is disclosed)
A zero margin leaves phi undefined; ZERO_MARGIN_RULE (OQ27, triage default) sets phi = 0
for that row and keeps the footnote 'phi undefined (zero margin), set to 0'.
The column all_rows_positive (phi > 0 strictly in every row) is the separate condition
of the Response text (TEXTS_D4_D9_D7 l.196-198).

--arm contract of analyze.py. D11 (analyze.d11_check): the October core log runs on the
October core suite (Q27 repaired and primary, n=60: the label of the paper's Table IV);
the August log runs on the August suite (n=59, and n=60 with --keep-excluded).
Writes the CSV at --out and <out>.meta.json; make_tables.py reads the label from it.

Usage: python3 -I -B phi_tableiv.py --graded ../results/rc1/graded_rc1.csv \
         --suite ../suite/k3n_suite_v1.3n_oct.tsv --arm base \
         --out ../results/rc1/base60/tables/phi_tableiv.csv
"""
import argparse
import csv
import math
import os
import sys
from collections import defaultdict

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402

CI_LABEL_BASE = "Newcombe hybrid-score interval without the paired correlation correction"
CI_LABEL_CONSERVATIVE = CI_LABEL_BASE + " (conservative)"
CI_LABEL_NOT_CORRECTED = CI_LABEL_BASE + " (not corrected for pairing)"
# OQ27 (triage DEFAULT, approved by the author with the 58 defaults on 14 Oct 2026, brief
# 1.0c): "set_zero" = phi of a zero-margin row is set to 0 (footnote below);
# "undefined" = the row blocks the word 'conservative'. One switch:
ZERO_MARGIN_RULE = "set_zero"
ZERO_MARGIN_RULES = ("set_zero", "undefined")
ZERO_MARGIN_FOOTNOTE = "phi undefined (zero margin), set to 0"


def phi_2x2(a, b, c, d):
    """(phi or None when a margin is zero)."""
    den = (a + b) * (c + d) * (a + c) * (b + d)
    if den == 0:
        return None
    return (a * d - b * c) / math.sqrt(den)


def table_label(phis, rule=None):
    """phis: list of (phi or None). Returns (label, nonneg, all_positive)."""
    rule = rule or ZERO_MARGIN_RULE
    if rule not in ZERO_MARGIN_RULES:
        raise SystemExit(f"unknown ZERO_MARGIN_RULE {rule!r} (one of {ZERO_MARGIN_RULES})")
    vals = []
    for p in phis:
        if p is None:
            if rule == "set_zero":
                vals.append(0.0)
            else:
                return CI_LABEL_NOT_CORRECTED, False, False
        else:
            vals.append(p)
    nonneg = all(v >= 0 for v in vals)
    positive = all(v > 0 for v in vals)
    return (CI_LABEL_CONSERVATIVE if nonneg else CI_LABEL_NOT_CORRECTED), nonneg, positive


def main():
    ap = argparse.ArgumentParser(description="phi of Table IV rows (AM-7 D-1)")
    ap.add_argument("--graded", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--out", required=True, help="CSV path (e.g. .../tables/phi_tableiv.csv)")
    ap.add_argument("--keep-excluded", action="store_true",
                    help="n=60 sensitivity of the August log; only for the August re-grade "
                         "graded_v13n_withQ27.csv (analyze.d11_check, D11)")
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
    graded = ac.filter_arm(rows_all, a.arm, excluded)
    models = ac.require_complete(graded, a.runs, sorted(suite))
    runs = defaultdict(list)
    for r in graded:
        if r["qid"] in suite:
            runs[(r["model_key"], r["lang"], r["qid"])].append(r["correct"] == "True")
    item = {k: sum(v) > len(v) / 2 for k, v in runs.items()}

    rows, phis = [], []
    for m in models:
        cnt = {"a": 0, "b": 0, "c": 0, "d": 0}
        for q in suite:
            en, th = item[(m, "en", q)], item[(m, "th", q)]
            cnt["a" if en and th else "b" if en else "c" if th else "d"] += 1
        p = phi_2x2(cnt["a"], cnt["b"], cnt["c"], cnt["d"])
        phis.append(p)
        rows.append([m, len(suite), cnt["a"], cnt["b"], cnt["c"], cnt["d"],
                     "" if p is None else f"{p:.4f}",
                     "yes" if p is None else "no"])
    label, nonneg, positive = table_label(phis)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["model", "n_items", "both_correct", "en_only", "th_only", "both_wrong",
                    "phi", "zero_margin", "ci_label", "all_rows_nonnegative",
                    "all_rows_positive", "zero_margin_rule"])
        for r in rows:
            w.writerow(r + [label, nonneg, positive, ZERO_MARGIN_RULE])
    for r in rows:
        print(f"  {r[0]:16} n={r[1]} a={r[2]} b={r[3]} c={r[4]} d={r[5]} phi="
              f"{r[6] or 'undefined'}")
    neg = [r[0] for r, p in zip(rows, phis) if p is not None and p < 0]
    zm = [r[0] for r, p in zip(rows, phis) if p is None]
    print(f"Table IV label: {label}")
    if neg:
        print(f"  rows with phi < 0 (disclose): {neg}")
    if zm and ZERO_MARGIN_RULE == "set_zero":
        print(f"  zero-margin rows ({ZERO_MARGIN_RULE}): {zm}; footnote: {ZERO_MARGIN_FOOTNOTE}")
    elif zm:
        print(f"  zero-margin rows ({ZERO_MARGIN_RULE}): {zm}; phi undefined, the word "
              f"'conservative' is not used")
    print(f"  all rows phi > 0 (Response wording condition): {positive}")
    detail = {"inputs": {"graded": grec}, "runs": a.runs,
              "excluded_models": sorted(excluded), "ci_label": label,
              "zero_margin_rule": ZERO_MARGIN_RULE}
    ac.write_file_meta(a.out, "phi_tableiv.py",
                       ac.common_meta(a.arm, a.suite, a.keep_excluded, len(suite)), detail)
    print(f"[out] {a.out} (+ .meta.json)")


if __name__ == "__main__":
    main()
