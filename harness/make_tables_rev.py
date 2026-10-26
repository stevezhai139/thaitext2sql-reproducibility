"""Revised Tables II-V for the KST revision (checkpoint 1, 22 Oct 2026; claim rows C88-C91, ADD-T2/T4/CAP).

Builds new .tex files next to the frozen generators' output; frozen scripts are not changed.
- Table II: core cells re-derived from accuracy.csv with exact Wilson rounding + column 'Ext.' (EN/TH of 40)
- Table III / V: caption text + dagger on local rows
- Table IV: column Delta_V from analyze_rc1 rc1_gap.csv (gap_values_all / n) + caption
Acceptance: every number already printed in the input tables must be unchanged, except a Wilson bound
that the frozen generator rounded twice (listed in diff.txt); the script stops on any other change.
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys

LABEL = {"claude-sonnet": "claude-sonnet-5", "gpt-mini": "gpt-5.4-mini", "gemini-flash": "gemini-3.6-flash",
         "qwen25-coder-7b": "qwen2.5-coder 7B", "llama31-8b": "llama3.1 8B", "typhoon2-8b": "typhoon2 8B (Thai)"}
KEY = {v: k for k, v in LABEL.items()}
LOCAL = ("qwen25-coder-7b", "llama31-8b", "typhoon2-8b")
DAG = r"\textsuperscript{\dag}"

CAP_II = (r"Item-level accuracy on the 60 core items (majority of 5 runs): correct items $n$ out of 60 per language. "
          r"Brackets: Wilson 95\% CI (\%). Ext.: correct items EN/TH out of 40 on the Amendment-9 extension (exploratory, "
          r"descriptive; not part of the 60-item result; Wilson intervals in the artifact); claude-sonnet-5's Ext. counts score "
          r"14 answers cut off by its 1,024-token output cap as wrong (12 Thai, 2 English); \textsuperscript{\ddag}typhoon2 Thai "
          r"item X28 has 3 of 5 runs (two timeouts), and its majority cannot change. Local models (\textsuperscript{\dag}) are "
          r"exploratory (Amendment~7). Engine of record: PostgreSQL.")
CAP_III_OLD = re.compile(r"At \$n\{=\}15\$ per cell, a Wilson 95\\% interval spans up to\s*\$\\pm23\$ points;\s*tier-level contrasts are indicative only\.")
CAP_III_NEW = (r"At $n{=}15$ per cell, a Wilson 95\% interval is up to 45 points wide (e.g., 12/15: 55--93\%); tier-level "
               r"contrasts are indicative only. Local models (\textsuperscript{\dag}) are exploratory.")
CAP_IV = (r"Paired EN$-$TH contrast per model under the schema-only prompt: discordant items (EN-only correct $b$, TH-only "
          r"correct $c$), accuracy difference in points with a 95\% Newcombe hybrid-score interval without the paired "
          r"correlation correction (conservative), exact McNemar $p$, and Holm-corrected $p$ across six models ($^{*}$: "
          r"$p_{\text{Holm}}<0.05$). Last column ($\Delta_V$): the same difference when the prompt also lists each text "
          r"column's stored values (concurrent re-run, Amendment~7; Section~V-B); descriptive, no interval or test. Pooled "
          r"frontier EN$-$TH gap: 9$\to$4 items, share 0.44 (item-bootstrap 95\% CI [$-$0.30, 2.00]; resamples with no positive "
          r"schema-only gap: 22 of 10,000, 147 without claude-sonnet-5, 1,622 without gpt-5.4-mini). Local models "
          r"(\textsuperscript{\dag}) are exploratory.")
CAP_V_OLD = re.compile(r"Five-run unanimity and parse rate \(\\%\)\. Local models are run\s*at temperature 0 with fixed seed; "
                       r"API models at their pinned or\s*provider-default sampling \(Section IV, Protocol\)\.")
CAP_V_NEW = (r"Five-run grade unanimity and parse rate (\%). Local models (\textsuperscript{\dag}; exploratory) are run at "
             r"temperature 0 with fixed seed; API models at their configured or provider-default sampling (Section IV, Protocol).")


def sha(path):
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def wilson(k, n, z=1.959963984540054):
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return c - h, c + h


def body_rows(tex):
    out = {}
    for line in tex.splitlines():
        cells = [c.strip() for c in line.rstrip("\\ ").split("&")]
        if len(cells) > 1 and cells[0] in KEY:
            out[KEY[cells[0]]] = cells[1:]
    return out


def replace_caption(tex, new):
    i = tex.index(r"\caption{")
    depth, j = 0, i + len(r"\caption")
    while True:
        ch = tex[j]
        depth += ch == "{"
        depth -= ch == "}"
        j += 1
        if depth == 0:
            break
    return tex[:i] + r"\caption{" + new + "}" + tex[j:]


def dagger_names(tex):
    for k in LOCAL:
        tex = re.sub(r"(?m)^" + re.escape(LABEL[k]) + r"(?= &)", lambda m: LABEL[k] + DAG, tex)
    return tex


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--generated", required=True, help="paper/generated (frozen generators' output)")
    ap.add_argument("--acc-core", required=True)
    ap.add_argument("--ext-acc", required=True)
    ap.add_argument("--typhoon-ext", required=True, help="rev_numbers.py ext_typhoon_descriptive.csv")
    ap.add_argument("--gap", required=True, help="analyze_rc1 rc1_gap.csv")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"refuse: {a.out} exists")
    src = {t: os.path.join(a.generated, f"tab_{t}.tex") for t in ("headline", "tiers", "crosslingual", "stability")}
    tex = {t: open(p, encoding="utf-8").read() for t, p in src.items()}
    diffs, outtex = [], {}

    # Table II
    core = {(r["model"], r["lang"]): (int(r["correct"]), int(r["n"])) for r in rows(a.acc_core) if r["scope"] == "all"}
    ext = {(r["model"], r["lang"]): int(r["correct"]) for r in rows(a.ext_acc)}
    short_runs = set()
    for r in rows(a.typhoon_ext):
        ext[(r["model"], r["lang"])] = int(r["correct_items"])
        if r["cells_lt5_runs"].strip():
            short_runs.add(r["model"])
    old = body_rows(tex["headline"])
    lines = []
    for k, lab in LABEL.items():
        cells = []
        for lang in ("en", "th"):
            c, n = core[(k, lang)]
            lo, hi = wilson(c, n)
            cells += [str(c), f"{100 * c / n:.1f} [{round(100 * lo)},{round(100 * hi)}]"]
        for i, (o, nw) in enumerate(zip(old[k], cells)):
            if o != nw:
                diffs.append(f"Table II {lab} col{i + 1}: {o} -> {nw}")
        cell_ext = f"{ext[(k, 'en')]}/{ext[(k, 'th')]}" + (r"\textsuperscript{\ddag}" if k in short_runs else "")
        lines.append(f"{lab}{DAG if k in LOCAL else ''} & " + " & ".join(cells) + f" & {cell_ext} \\\\")
    t2 = replace_caption(tex["headline"], CAP_II)
    t2 = t2.replace(r"\begin{tabular}{lcccc}", r"\begin{tabular}{lccccc}")
    t2 = t2.replace(r" & \multicolumn{2}{c}{English} & \multicolumn{2}{c}{Thai} \\", r" & \multicolumn{2}{c}{English} & \multicolumn{2}{c}{Thai} & Ext. \\")
    t2 = t2.replace(r"Model & $n$ & \% [CI] & $n$ & \% [CI] \\", r"Model & $n$ & \% [CI] & $n$ & \% [CI] & EN/TH \\")
    t2 = re.sub(r"(?s)\\midrule\n.*?\\bottomrule", lambda m: "\\midrule\n" + "\n".join(lines) + "\n\\bottomrule", t2)
    outtex["headline"] = t2

    # Table III
    if not CAP_III_OLD.search(tex["tiers"]):
        sys.exit("Table III caption text not found")
    outtex["tiers"] = dagger_names(CAP_III_OLD.sub(lambda m: CAP_III_NEW, tex["tiers"]))

    # Table IV
    gap = {r["model"]: int(r["gap_values_all"]) for r in rows(a.gap) if r["model"] in LABEL}
    n = core[("claude-sonnet", "th")][1]
    t4 = replace_caption(tex["crosslingual"], CAP_IV)
    t4 = t4.replace(r"\setlength{\tabcolsep}{3.5pt}", r"\setlength{\tabcolsep}{3pt}").replace(r"\begin{tabular}{lccccc}", r"\begin{tabular}{lcccccc}")
    t4 = t4.replace(r"& $p$ & $p_{\text{Holm}}$ \\", r"& $p$ & $p_{\text{Holm}}$ & $\Delta_V$ \\")
    for k, lab in LABEL.items():
        line = next(l for l in t4.splitlines() if l.startswith(lab + " &"))
        t4 = t4.replace(line, line[:-2].rstrip() + f" & {100 * gap[k] / n:+.1f} \\\\")
    outtex["crosslingual"] = dagger_names(t4)

    # Table V
    if not CAP_V_OLD.search(tex["stability"]):
        sys.exit("Table V caption text not found")
    outtex["stability"] = dagger_names(CAP_V_OLD.sub(lambda m: CAP_V_NEW, tex["stability"]))

    # acceptance: old printed numbers unchanged (Tables III-V exactly; Table II except listed Wilson bounds)
    for t in ("tiers", "crosslingual", "stability"):
        o, nw = body_rows(tex[t]), body_rows(outtex[t].replace(DAG, ""))
        for k in LABEL:
            if nw[k][:len(o[k])] != o[k]:
                sys.exit(f"acceptance failed: {t} {k}: {o[k]} -> {nw[k]}")
    allowed = [d for d in diffs if re.search(r"\[\d+,\d+\] -> .*\[\d+,\d+\]$", d) and d.split(": ")[1].split(" [")[0] == d.split("-> ")[1].split(" [")[0]]
    if len(allowed) != len(diffs):
        sys.exit("acceptance failed: Table II change beyond a Wilson bound: " + "; ".join(diffs))

    os.makedirs(a.out)
    for t, s in outtex.items():
        with open(os.path.join(a.out, f"tab_{t}_rev.tex"), "w", encoding="utf-8") as f:
            f.write(s)
    with open(os.path.join(a.out, "diff.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(diffs) + "\n" if diffs else "no number changed\n")
    meta = {"script": "harness/" + os.path.basename(__file__), "script_sha256": sha(__file__),
            "inputs": {**{f"tab_{t}": {"path": p, "sha256": sha(p)} for t, p in src.items()},
                       **{k: {"path": v, "sha256": sha(v)} for k, v in vars(a).items() if k not in ("out", "generated")}}}
    with open(os.path.join(a.out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("changed printed numbers:", diffs or "none")
    print(f"[out] {a.out}: tab_headline_rev.tex tab_tiers_rev.tex tab_crosslingual_rev.tex tab_stability_rev.tex diff.txt meta.json")


if __name__ == "__main__":
    main()
