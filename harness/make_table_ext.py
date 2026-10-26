#!/usr/bin/env python3
"""make_table_ext.py -- LaTeX tables of the 40-item extension (AMENDMENT-9), generated
from analyze_ext.py outputs (no hand-typed number). Exploratory/descriptive caption.

  --out              one row per model: EN and TH correct items out of n (from the data)
                     with Wilson 95% interval (%)
  <out stem>_family.tex  rows F1-F10 (items per family) x model columns 'EN/TH'

Usage: python3 -I -B make_table_ext.py --in-dir ../results/ext/tables --out ../results/ext/tables/tab_ext.tex
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
ORDER = list(LABEL)
SHORT = {"claude-sonnet": "claude", "gpt-mini": "gpt", "gemini-flash": "gemini",
         "qwen25-coder-7b": "qwen", "llama31-8b": "llama", "typhoon2-8b": "typhoon"}
FAMILIES = [f"F{i}" for i in range(1, 11)]


def read(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in-dir", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    meta = json.load(open(os.path.join(a.in_dir, "meta.json"), encoding="utf-8"))
    if "analyze_ext.py" not in meta.get("producers", {}) or meta.get("arm") != "base":
        print("in-dir is not an analyze_ext.py output of the base arm")
        sys.exit(2)
    acc = {(r["model"], r["lang"]): r for r in read(os.path.join(a.in_dir, "ext_accuracy.csv"))}
    fam = {(r["model"], r["lang"], r["family"]): r for r in read(os.path.join(a.in_dir, "ext_family.csv"))}
    models = [m for m in ORDER if (m, "en") in acc] + sorted(
        {m for m, _ in acc} - set(ORDER))
    n = acc[(models[0], "en")]["n"]
    rows = []
    for m in models:
        en, th = acc[(m, "en")], acc[(m, "th")]
        rows.append(f"{LABEL.get(m, m)} & {en['correct']} & {float(en['acc']) * 100:.1f} "
                    f"[{float(en['ci_lo']) * 100:.0f},{float(en['ci_hi']) * 100:.0f}] & "
                    f"{th['correct']} & {float(th['acc']) * 100:.1f} "
                    f"[{float(th['ci_lo']) * 100:.0f},{float(th['ci_hi']) * 100:.0f}] \\\\")
    tab = (r"""\begin{table}[t]
\caption{Extension of """ + n + r""" items (Amendment 9; DDL-only prompt, base arm, 5 runs;
exploratory and descriptive): correct items $n$ out of """ + n + r""" per language
(item majority). Brackets: Wilson 95\% CI (\%).}
\label{tab:extension}
\centering\footnotesize\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{lcccc}
\toprule
 & \multicolumn{2}{c}{English} & \multicolumn{2}{c}{Thai} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Model & $n$ & \% [CI] & $n$ & \% [CI] \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")
    frows = []
    for f in FAMILIES:
        k = fam.get((models[0], "en", f))
        if k is None or k["n_items"] == "0":
            continue
        frows.append(f"{f} ({k['n_items']}) & " + " & ".join(
            f"{fam[(m, 'en', f)]['correct']}/{fam[(m, 'th', f)]['correct']}" for m in models) + r" \\")
    ftab = (r"""\begin{table}[t]
\caption{Extension by family (exploratory): correct items EN/TH per family
(number of items in brackets).}
\label{tab:extension-family}
\centering\footnotesize\setlength{\tabcolsep}{2.5pt}
\begin{tabular}{l""" + "c" * len(models) + r"""}
\toprule
Family & """ + " & ".join(SHORT.get(m, m) for m in models) + r""" \\
\midrule
""" + "\n".join(frows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", encoding="utf-8") as fh:
        fh.write(tab)
    stem, ext = os.path.splitext(a.out)
    with open(stem + "_family" + (ext or ".tex"), "w", encoding="utf-8") as fh:
        fh.write(ftab)
    print(f"wrote {a.out} and {stem}_family{ext or '.tex'} ({len(models)} models, n={n})")


if __name__ == "__main__":
    main()
