"""
make_tables.py — สร้างตาราง LaTeX ของ paper จาก results/*.csv โดยตรง
(กติกา: ตัวเลขใน paper ห้ามพิมพ์มือ — รันสคริปต์นี้ใหม่ทุกครั้งที่ results เปลี่ยน)

Gate 0 (KST 2027 revision; GATE0 design 2.6, D10):
  * --arm บังคับ: ตรวจ <results-dir>/tables/meta.json (เขียนโดย analyze.py) ว่า arm
    เท่ากับ --arm; --captions revised ต้องมี meta ของ tables, ของ plan_indexed.csv /
    plan_noindex.csv (<file>.meta.json จาก plan_quality.py) และของ --ci-label
    (phi_tableiv.csv.meta.json) และทุกตัวต้องเป็น arm เดียวกัน; meta ที่ไม่มีหรือ
    arm ต่างกันถูกปฏิเสธ (exit 2)
  * D10 (ผลหลักทั้งหมดมาจากรอบ ต.ค.): ทุก producer ใน tables/meta.json ต้องอ่าน graded
    ไฟล์เดียวกัน (sha256); phi_tableiv.csv ต้องมาจาก graded ไฟล์เดียวกับตาราง; plan csv
    ทั้งสองต้องมาจากรอบเดียวกับตาราง (ไฟล์เดียวกัน หรือ session fingerprint ตรงกันทุกข้อที่มี
    ร่วมกัน); --out-dir ใต้โฟลเดอร์ชื่อ paper รับเฉพาะตารางของแขน base จาก graded สองแขน
    (log หลักของรอบ ต.ค.; analyze.paper_guard) และเฉพาะ --captions revised
  * D11: --out-dir ใต้โฟลเดอร์ชื่อ paper รับเฉพาะตารางที่คำนวณบน suite core ของรอบ ต.ค.
    (suite_session = october ใน meta ของตาราง: Q27 ฉบับซ่อมเป็น primary, n=60); ตารางบน
    suite ของ ส.ค. (n=59) ถูกปฏิเสธ
  * --results-dir และ --out-dir บังคับ (ไม่มีค่า default ที่ชี้ไป ../results หรือ
    ../paper/generated)
  * --captions submitted (default) คง byte ของตารางฉบับที่ส่ง (v1.2) ทุกตัว; ใช้ทำซ้ำ
    เล่มที่ส่งเท่านั้น (plan csv ของ ส.ค. ไม่มี meta จึงไม่ตรวจ meta ของ plan)
  * --captions revised: caption ของ Table IV ใช้ label จาก --ci-label (AM-7 D-1, D8
    ทาง A); Table V 'Section IV-C' → 'Section IV, Protocol'; ประโยค n/±CI ของ caption
    tiers คำนวณจาก N_TIER; จำนวนโมเดลใน Holm มาจากข้อมูล; โมเดลที่ถูกตัดด้วย
    --exclude-models ของ analyze.py ไม่มีแถว (พิมพ์คำเตือน)
  * ตาราง EN–TH (McNemar + Holm ข้ามโมเดล) มาจาก cross_lingual.csv ของ analyze.py
    ของแขนที่ส่ง ไม่ใช่ rc1_mcnemar.csv ของ analyze_rc1.py

Usage:
  python3 -I -B make_tables.py --results-dir ../results/rc1/base60 --out-dir ../paper/generated \
      --arm base --captions revised --ci-label ../results/rc1/base60/tables/phi_tableiv.csv
"""
import argparse
import csv
import math
import os
import statistics
import sys
from collections import defaultdict

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402

MODEL_LABEL = {
    "claude-sonnet": "claude-sonnet-5",
    "gpt-mini": "gpt-5.4-mini",
    "gemini-flash": "gemini-3.6-flash",
    "qwen25-coder-7b": "qwen2.5-coder 7B",
    "llama31-8b": "llama3.1 8B",
    "typhoon2-8b": "typhoon2 8B (Thai)",
}
ORDER = ["claude-sonnet", "gpt-mini", "gemini-flash",
         "qwen25-coder-7b", "llama31-8b", "typhoon2-8b"]
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six"}


def read(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def w(path, s):
    open(path, "w", encoding="utf-8").write(s)
    print("wrote", path)


def wilson_halfwidth_max(n, z=1.96):
    """largest half-width (points) of a Wilson 95% interval at n (p = 0.5)."""
    p = 0.5
    return 100 * z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / (1 + z * z / n)


def check_inputs(a, T):
    """--arm contract (design 2.6) and the D10 session checks. Returns the phi table or None."""
    tmeta = ac.read_meta(os.path.join(T, ac.META_NAME))
    revised = a.captions == "revised"
    under_paper = any(p.casefold() == "paper" for p in ac.path_parts(a.out_dir, True))
    if under_paper and not revised:
        ac.die(2, "[D10] --out-dir under paper/ takes --captions revised only (the submitted "
                  "tables are kept in paper/generated_v12/)")
    ac.check_meta_arm(tmeta, a.arm, os.path.join(T, ac.META_NAME), required=revised)
    if tmeta is not None and "analyze.py" not in tmeta.get("producers", {}):
        ac.die(2, f"[meta] {T}: meta.json has no analyze.py entry")
    if not revised:
        if a.ci_label:
            ac.die(2, "--ci-label applies only to --captions revised")
        if tmeta is not None:
            g = ac.producers_graded(tmeta, T)
            print(f"[meta] tables from {ac.describe(g)}")
        print("[meta] captions submitted: tables meta " +
              ("checked" if tmeta else "absent (submitted reproduction)") +
              "; plan csv meta not checked")
        return None
    tg = ac.producers_graded(tmeta, T)
    print(f"[D10] tables (every producer) from {ac.describe(tg)}")
    for fn in ("plan_indexed.csv", "plan_noindex.csv"):
        p = os.path.join(a.results_dir, fn)
        plm = ac.read_meta(p + ".meta.json")
        ac.check_meta_arm(plm, a.arm, p + ".meta.json")
        same, why = ac.same_session((plm.get("inputs") or {}).get("graded"), tg)
        if not same:
            ac.die(2, f"[D10] {fn} comes from another session than the tables ({why}); refused")
        print(f"[D10] {fn}: same session as the tables ({why})")
    if not a.ci_label:
        ac.die(2, "--captions revised needs --ci-label <phi_tableiv.csv> (AM-7 D-1)")
    pmeta = ac.read_meta(a.ci_label + ".meta.json")
    ac.check_meta_arm(pmeta, a.arm, a.ci_label + ".meta.json")
    for k in ("keep_excluded", "suite_sha256"):
        if pmeta.get(k) != tmeta.get(k):
            ac.die(2, f"[meta] {k} of {os.path.basename(a.ci_label)} differs from the tables "
                      f"folder ({pmeta.get(k)!r} vs {tmeta.get(k)!r}); n=59 and n=60 mixed?")
    pg = (pmeta.get("inputs") or {}).get("graded") or {}
    if pg.get("sha256") != tg.get("sha256"):
        ac.die(2, f"[D10] {os.path.basename(a.ci_label)} was computed from {ac.describe(pg)}, the "
                  f"tables from {ac.describe(tg)}; Table IV label and tables must come from one file")
    ac.paper_guard(a.out_dir, [tg, pg], True, tmeta.get("arm"), tmeta.get("suite_session"))
    rows = read(a.ci_label)
    labels = {r["ci_label"] for r in rows}
    if len(labels) != 1:
        ac.die(2, f"[ci-label] {a.ci_label}: expected one label, found {len(labels)}")
    print(f"[meta] captions revised: tables, plan and phi meta all arm={a.arm}, one session")
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--arm", required=True, help="arm the input tables must come from")
    ap.add_argument("--captions", choices=["submitted", "revised"], default="submitted")
    ap.add_argument("--ci-label", help="phi_tableiv.csv (revised captions: Table IV label)")
    a = ap.parse_args()
    T = os.path.join(a.results_dir, "tables")
    phi_rows = check_inputs(a, T)
    revised = a.captions == "revised"
    os.makedirs(a.out_dir, exist_ok=True)

    acc = read(os.path.join(T, "accuracy.csv"))
    xl = read(os.path.join(T, "cross_lingual.csv"))
    st = read(os.path.join(T, "stability_parse.csv"))

    present = {r["model"] for r in acc}
    order = ORDER if not revised else [m for m in ORDER if m in present]
    if revised and len(order) != len(ORDER):
        print(f"WARNING: models absent from the tables (excluded): "
              f"{[m for m in ORDER if m not in present]}")

    # ---------- Table: headline accuracy (majority, all-60) ----------
    A = {(r["model"], r["lang"], r["scope"]): r for r in acc}
    # v1.3 (D7): item counts come from the data (60 under v1.2 and on the October core
    # suite of D11, 59 on the August suite v1.3/v1.3n)
    N_ALL = A[(order[0], "en", "all")]["n"]
    N_TIER = [A[(order[0], "en", f"tier{t}")]["n"] for t in (1, 2, 3, 4)]
    TIER_N = "15" if set(N_TIER) == {"15"} else \
        "15 (" + ", ".join(f"T{t}: {n}" for t, n in zip((1, 2, 3, 4), N_TIER) if n != "15") + ")"
    rows = []
    for m in order:
        en, th = A[(m, "en", "all")], A[(m, "th", "all")]
        rows.append(
            f"{MODEL_LABEL[m]} & {en['correct']} & "
            f"{float(en['acc'])*100:.1f} [{float(en['ci_lo'])*100:.0f},{float(en['ci_hi'])*100:.0f}] & "
            f"{th['correct']} & "
            f"{float(th['acc'])*100:.1f} [{float(th['ci_lo'])*100:.0f},{float(th['ci_hi'])*100:.0f}] \\\\")
    w(os.path.join(a.out_dir, "tab_headline.tex"), r"""\begin{table}[t]
\caption{Item-level accuracy (majority of 5 runs): correct items $n$
out of """ + N_ALL + r""" per language. Brackets: Wilson 95\% CI (\%). Engine of
record: PostgreSQL.}
\label{tab:headline}
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

    # ---------- Table: per-tier (counts /15) ----------
    rows = []
    for m in order:
        c = [f"{A[(m, lg, f'tier{t}')]['correct']}" for t in (1, 2, 3, 4) for lg in ("en", "th")]
        rows.append(f"{MODEL_LABEL[m]} & " + " & ".join(
            f"{c[i]}/{c[i+1]}" for i in range(0, 8, 2)) + r" \\")
    if revised:
        ns = sorted({int(n) for n in N_TIER})
        n_txt = f"{ns[0]}" if len(ns) == 1 else f"{ns[0]}$--${ns[-1]}"
        hw = wilson_halfwidth_max(ns[0])
        tiers_sentence = (f"At $n{{=}}{n_txt}$ per cell, a Wilson 95\\% interval spans up to\n"
                          f"$\\pm{hw:.0f}$ points;\ntier-level contrasts are indicative only.}}")
    else:
        tiers_sentence = r"""At $n{=}15$ per cell, Wilson intervals span roughly $\pm25$ points;
tier-level contrasts are indicative only.}"""
    w(os.path.join(a.out_dir, "tab_tiers.tex"), r"""\begin{table}[t]
\caption{Correct items per tier, shown as EN/TH out of """ + TIER_N + r""". T1
single-table, T2 joins, T3 aggregation, T4 windows/subqueries/CTE.
""" + tiers_sentence + r"""
\label{tab:tiers}
\centering\small
\begin{tabular}{lcccc}
\toprule
Model & T1 & T2 & T3 & T4 \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

    # ---------- Table: cross-lingual paired ----------
    X = {r["model"]: r for r in xl}
    rows = []
    for m in order:
        r = X[m]
        d = float(r["delta"]) * 100
        lo, hi = float(r["ci_lo"]) * 100, float(r["ci_hi"]) * 100
        ph = float(r["p_holm"])
        star = r"$^{*}$" if ph < 0.05 else ""
        rows.append(
            f"{MODEL_LABEL[m]} & {r['en_only(b)']} & {r['th_only(c)']} & "
            f"{d:+.1f} [{lo:+.1f},{hi:+.1f}] & {float(r['p_mcnemar']):.4f} & {ph:.4f}{star} \\\\")
    if revised:
        label = phi_rows[0]["ci_label"]
        zm = [MODEL_LABEL.get(r["model"], r["model"]) for r in phi_rows
              if r["zero_margin"] == "yes"]
        zm_txt = (f" For {', '.join(zm)}, $\\phi$ is undefined (zero margin) and set to 0."
                  if zm else "")
        nm = len(xl)
        xl_caption = (r"""\caption{Paired EN$-$TH contrast per model: discordant items (EN-only
correct $b$, TH-only correct $c$), accuracy difference in points with a
95\% """ + label + r""", exact McNemar $p$, and Holm-corrected $p$ across """
                      + WORDS.get(nm, str(nm)) + r"""
models ($^{*}$: significant at 0.05 after correction).""" + zm_txt + "}")
    else:
        xl_caption = r"""\caption{Paired EN$-$TH contrast per model: discordant items (EN-only
correct $b$, TH-only correct $c$), accuracy difference in points with
Newcombe 95\% CI, exact McNemar $p$, and Holm-corrected $p$ across six
models ($^{*}$: significant at 0.05 after correction).}"""
    w(os.path.join(a.out_dir, "tab_crosslingual.tex"), r"""\begin{table}[t]
""" + xl_caption + r"""
\label{tab:crosslingual}
\centering\footnotesize\setlength{\tabcolsep}{3.5pt}
\begin{tabular}{lccccc}
\toprule
Model & $b$ & $c$ & $\Delta$ pts [CI] & $p$ & $p_{\text{Holm}}$ \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

    # ---------- Table: stability + parse ----------
    S = {(r["model"], r["lang"]): r for r in st}
    rows = []
    for m in order:
        en, th = S[(m, "en")], S[(m, "th")]
        rows.append(
            f"{MODEL_LABEL[m]} & {float(en['unanimity_rate'])*100:.1f} & "
            f"{float(th['unanimity_rate'])*100:.1f} & "
            f"{float(en['parse_rate'])*100:.1f} & {float(th['parse_rate'])*100:.1f} \\\\")
    section = "Section IV, Protocol" if revised else "Section IV-C"
    w(os.path.join(a.out_dir, "tab_stability.tex"), r"""\begin{table}[t]
\caption{Five-run unanimity and parse rate (\%). Local models are run
at temperature 0 with fixed seed; API models at their pinned or
provider-default sampling (""" + section + r""").}
\label{tab:stability}
\centering\small
\begin{tabular}{lcccc}
\toprule
 & \multicolumn{2}{c}{Unanimity} & \multicolumn{2}{c}{Parse} \\
\cmidrule(lr){2-3}\cmidrule(lr){4-5}
Model & EN & TH & EN & TH \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")

    # ---------- Table: plan quality (สองเฟสรวม) ----------
    def plan_ratios(path):
        out = defaultdict(list)
        for r in read(path):
            if r["source"] != "gold" and r["cost_ratio_vs_gold"]:
                out[r["source"]].append(float(r["cost_ratio_vs_gold"]))
        return out

    pi = plan_ratios(os.path.join(a.results_dir, "plan_indexed.csv"))
    pn = plan_ratios(os.path.join(a.results_dir, "plan_noindex.csv"))
    rows = []
    for m in order:
        vi, vn = pi.get(m, []), pn.get(m, [])
        rows.append(
            f"{MODEL_LABEL[m]} & {len(vi)} & "
            f"{statistics.median(vi):.2f} & {max(vi):.2f} & "
            f"{statistics.median(vn):.2f} & {max(vn):.2f} \\\\"
            if vi and vn else f"{MODEL_LABEL[m]} & 0 & -- & -- & -- & -- \\\\")
    w(os.path.join(a.out_dir, "tab_plan.tex"), r"""\begin{table}[t]
\caption{Plan quality on the million-row table: planner-cost ratio of
each model's majority-correct SQL versus gold (1.00 = plan-equivalent;
$n$ = measurable cells). EXPLAIN only --- nothing is executed.}
\label{tab:plan}
\centering\small
\begin{tabular}{lccccc}
\toprule
 & & \multicolumn{2}{c}{Indexed} & \multicolumn{2}{c}{No index} \\
\cmidrule(lr){3-4}\cmidrule(lr){5-6}
Model & $n$ & med & max & med & max \\
\midrule
""" + "\n".join(rows) + r"""
\bottomrule
\end{tabular}
\end{table}
""")
    print("done — \\input{generated/tab_*.tex} ใน main.tex ได้เลย")


if __name__ == "__main__":
    main()
