#!/usr/bin/env python3
"""make_table_rc1.py -- LaTeX table of the value-hint arm (AMENDMENT-7 A10: numbers of
the values arm in the paper come from analyze_rc1.py and this script only).

Reads analyze_rc1.py outputs in --in-dir (it never recomputes GF; fix of the draft
l.26-29): rc1_accuracy.csv, rc1_gf.csv, rc1_gap.csv, rc1_decisions.json, meta.json.
Columns: Thai correct items on VG_cov (/n_cov from the data) and on the rest
(/n_rest), Thai grounding failures GF_B -> GF_V on VG_cov, EN-TH gap Gap_B -> Gap_V on
the analysed items (/n). A pooled frontier row carries the share remaining [CI], except
in band G-d (sum Gap_B <= 2; AM-7 A7 H2 and A9 G-d): the share is then not reported
because its denominator is unstable, the row shows the item counts Gap_B -> Gap_V only and
the caption says why.
Local rows carry the label 'exploratory'. OQ26.2 default: two files are written,
--out (frontier + local rows) and <out stem>_frontier.tex (frontier rows only); the
paper uses the first unless a page cut is approved before -> after.

Usage: python3 -I -B make_table_rc1.py --in-dir ../results/rc1/h1h4 --out ../results/rc1/h1h4/tab_values.tex
"""
import argparse
import csv
import json
import os
import sys

sys.dont_write_bytecode = True

LABEL = {"claude-sonnet": "claude-sonnet-5", "gpt-mini": "gpt-5.4-mini",
         "gemini-flash": "gemini-3.6-flash", "qwen25-coder-7b": "qwen2.5-coder 7B",
         "llama31-8b": "llama3.1 8B", "typhoon2-8b": "typhoon2 8B (Thai)"}
FRONTIER = ["claude-sonnet", "gpt-mini", "gemini-flash"]
LOCAL = ["qwen25-coder-7b", "llama31-8b", "typhoon2-8b"]


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def fmt_ci(v):
    return "unbounded" if v in (None, "unbounded") else f"{float(v):.2f}"


POOLED_GD = (r"""Pooled frontier row: EN$-$TH gap in items only; the share of the gap
remaining is not reported because the base-arm gap is at most two items (Amendment 7, H2).""")
POOLED_SHARE = (r"""Pooled frontier row: share of the gap remaining with
item-bootstrap 95\% CI.""")


def build(rows, n_cov, n_rest, n_all, pooled, with_local, gd=False):
    cap = (r"""\caption{Stored-values condition (preregistered, Amendment 7): DDL-only
prompt $\to$ DDL plus the stored values of every text column, asked
concurrently. Thai correct items on the """ + str(n_cov) + r""" value-grounding items whose
target value the list shows (/""" + str(n_cov) + r""") and on the other items (/""" + str(n_rest)
           + r"""); Thai grounding failures (a Thai word copied into, or an English value
invented for, a filter; item majority) on the first set; EN$-$TH gap in
items (/""" + str(n_all) + r"""). """ + (POOLED_GD if gd else POOLED_SHARE)
           + (r""" Local models (\textsuperscript{\dag}) are exploratory."""
              if with_local else "") + "}")
    return (r"""\begin{table}[t]
""" + cap + r"""
\label{tab:valuehints}
\centering\footnotesize\setlength{\tabcolsep}{3pt}
\begin{tabular}{lcccc}
\toprule
Model & TH VG & TH other & Ground.\ fail & Gap \\
\midrule
""" + "\n".join(rows) + "\n" + pooled + r"""
\bottomrule
\end{tabular}
\end{table}
""")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    D = a.in_dir
    acc = {(r["model"], r["arm"], r["lang"], r["subset"]): r
           for r in read(os.path.join(D, "rc1_accuracy.csv"))}
    gf = {(r["model"], r["arm"], r["subset"]): r for r in read(os.path.join(D, "rc1_gf.csv"))}
    gap = {r["model"]: r for r in read(os.path.join(D, "rc1_gap.csv"))}
    dec = json.load(open(os.path.join(D, "rc1_decisions.json"), encoding="utf-8"))
    meta = json.load(open(os.path.join(D, "meta.json"), encoding="utf-8"))
    if meta.get("producers", {}).get("analyze_rc1.py", {}).get("mode") != "rc1":
        print("in-dir is not an analyze_rc1.py --mode rc1 output")
        sys.exit(2)
    models = [m for m in FRONTIER + LOCAL if (m, "values", "th", "all") in acc]
    if not models:
        print("no model with a values arm in rc1_accuracy.csv")
        sys.exit(2)
    m0 = models[0]
    n_cov = acc[(m0, "base", "th", "vg_cov")]["n"]
    n_rest = acc[(m0, "base", "th", "rest_cov")]["n"]
    n_all = acc[(m0, "base", "th", "all")]["n"]

    def row(m):
        b, v = acc[(m, "base", "th", "vg_cov")], acc[(m, "values", "th", "vg_cov")]
        rb, rv = acc[(m, "base", "th", "rest_cov")], acc[(m, "values", "th", "rest_cov")]
        g = gap[m]
        name = LABEL.get(m, m) + (r"\textsuperscript{\dag}" if m in LOCAL else "")
        return (f"{name} & {b['correct']}$\\to${v['correct']} & "
                f"{rb['correct']}$\\to${rv['correct']} & "
                f"{gf[(m, 'base', 'vg_cov')]['gf']}$\\to${gf[(m, 'values', 'vg_cov')]['gf']} & "
                f"{int(g['gap_base_all']):+d}$\\to${int(g['gap_values_all']):+d} \\\\")

    h1, h2 = dec["h1"], dec["h2"]
    fr = dec["frontier"]
    gd = h2["h2_band"] == "G-d"
    if gd:
        share_txt = ""
    else:
        share = "--" if h2["share"] is None else f"{h2['share']:.2f}"
        ci = "" if h2["share"] is None else f" [{fmt_ci(h2['ci_lo'])}, {fmt_ci(None if h2['ci_hi_unbounded'] else h2['ci_hi'])}]"
        share_txt = f"; share {share}{ci}"
    th_b = sum(int(acc[(m, "base", "th", "vg_cov")]["correct"]) for m in fr)
    th_v = sum(int(acc[(m, "values", "th", "vg_cov")]["correct"]) for m in fr)
    rb = sum(int(acc[(m, "base", "th", "rest_cov")]["correct"]) for m in fr)
    rv = sum(int(acc[(m, "values", "th", "rest_cov")]["correct"]) for m in fr)
    pooled = (r"\midrule" + "\n" + f"Frontier pooled ({len(fr)}) & {th_b}$\\to${th_v} & {rb}$\\to${rv} & "
              f"{h1['gf_b']}$\\to${h1['gf_v']} & {h2['sum_gap_b']:+d}$\\to${h2['sum_gap_v']:+d}"
              f"{share_txt} \\\\")
    full = build([row(m) for m in models], n_cov, n_rest, n_all, pooled,
                 any(m in LOCAL for m in models), gd)
    front = build([row(m) for m in models if m in FRONTIER], n_cov, n_rest, n_all, pooled, False, gd)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(full)
    stem, ext = os.path.splitext(a.out)
    fpath = stem + "_frontier" + (ext or ".tex")
    with open(fpath, "w", encoding="utf-8") as fh:
        fh.write(front)
    print(f"wrote {a.out} ({len(models)} models) and {fpath} (frontier only); H1 band "
          f"{h1['h1_band']}, H2 band {h2['h2_band']}"
          + ("; G-d: share and CI not reported (item counts only)" if gd else ""))


if __name__ == "__main__":
    main()
