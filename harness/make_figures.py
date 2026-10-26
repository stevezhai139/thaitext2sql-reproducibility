"""
make_figures.py — figure ของ paper จาก <results-dir>/tables/accuracy.csv (reproducible)
fig_tiers.pdf: small multiples 2x3 — ช่องละโมเดล, EN ทึบ / TH ประ (สไตล์ NEJM: สะอาด 2 เส้น/ช่อง)
fig_slope.pdf: slopegraph EN -> TH (เขียนพ่วง; --no-slope หยุดเขียนหลัง Gate 4 ตัด Fig. 2; OQ32)

Gate 0 (KST 2027 revision; GATE0 design 2.6, D10):
  * --arm บังคับ และตรวจ <results-dir>/tables/meta.json ก่อน import matplotlib:
    ไม่มี meta หรือ arm ต่างจาก --arm → exit 2 (ตารางหลักมาจากแขน base ของรอบ ต.ค.)
  * D10: ทุก producer ของตารางต้องอ่าน graded ไฟล์เดียวกัน; --out ใต้โฟลเดอร์ชื่อ paper
    รับเฉพาะตารางของแขน base จาก graded สองแขน (log หลักของรอบ ต.ค.; analyze.paper_guard)
    และ (D11) เฉพาะตารางบน suite core ของรอบ ต.ค. (Q27 ฉบับซ่อม, n=60)
  * --results-dir และ --out บังคับ (ไม่มีค่า default ที่ชี้ไป paper/generated)
  * รันด้วย python3 -B -E -P (matplotlib อยู่ใน user site; RUNBOOK 1a.10b, 3.47, 4.3);
    ถ้า import matplotlib ไม่ได้ จะหยุดด้วย exit 2 และข้อความบอกวิธี (ไม่เขียนไฟล์ใด)
  * รูปแบบรูปไม่เปลี่ยน; matplotlib ตั้ง pdf.fonttype = 42 (ไม่มี Type 3)
  * โมเดลที่ไม่มีในตาราง (ตัดด้วย --exclude-models ของ analyze.py) แสดงเป็นช่องว่างที่มีป้าย

Usage: python3 -B -E -P make_figures.py --results-dir ../results/rc1/base60 \
         --out ../paper/generated/fig_tiers.pdf --arm base
"""
import argparse
import csv
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402

PANELS = [  # (key, label) — แถวบน frontier, แถวล่าง open-weight
    ("claude-sonnet", "claude-sonnet-5"),
    ("gpt-mini", "gpt-5.4-mini"),
    ("gemini-flash", "gemini-3.6-flash"),
    ("qwen25-coder-7b", "qwen2.5-coder 7B"),
    ("llama31-8b", "llama3.1 8B"),
    ("typhoon2-8b", "typhoon2 8B (Thai)"),
]
EN_C, TH_C = "#0072B2", "#D55E00"  # Okabe-Ito blue/vermillion (colorblind-safe; แยกด้วย solid/dash ในขาวดำ)


def load_accuracy(results_dir, arm, out):
    T = os.path.join(results_dir, "tables")
    meta = ac.read_meta(os.path.join(T, ac.META_NAME))
    ac.check_meta_arm(meta, arm, os.path.join(T, ac.META_NAME), required=True)
    g = ac.producers_graded(meta, os.path.join(T, ac.META_NAME))
    print(f"[D10] tables (every producer) from {ac.describe(g)}")
    ac.paper_guard(out, [g], False, meta.get("arm"), meta.get("suite_session"))
    A = {}
    for r in csv.DictReader(open(os.path.join(T, "accuracy.csv"), encoding="utf-8")):
        A[(r["model"], r["lang"], r["scope"])] = float(r["acc"]) * 100
    print(f"[meta] tables arm={meta.get('arm')} items={meta.get('n_items')}")
    return A


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results-dir", required=True)
    ap.add_argument("--out", required=True, help="fig_tiers.pdf path (fig_slope.pdf next to it)")
    ap.add_argument("--arm", required=True, help="arm the input tables must come from")
    ap.add_argument("--no-slope", action="store_true",
                    help="do not write fig_slope.pdf (after Gate 4 removes Fig. 2; OQ32)")
    a = ap.parse_args()
    A = load_accuracy(a.results_dir, a.arm, a.out)   # contract checked before matplotlib

    try:
        import matplotlib
    except ImportError:
        ac.die(2, "matplotlib is not importable by this python; install it in the user site "
                  "(RUNBOOK 1a.10b) and run make_figures.py with python3 -B -E -P; nothing written")
    matplotlib.use("Agg")
    # IEEE PDF eXpress compliance: embed TrueType (Type 42) instead of Type 3
    # glyph-procedure fonts (Type 3 trips the camera-ready checker).
    matplotlib.rcParams["pdf.fonttype"] = 42
    matplotlib.rcParams["ps.fonttype"] = 42
    import matplotlib.pyplot as plt

    tiers = [1, 2, 3, 4]
    fig, axes = plt.subplots(2, 3, figsize=(6.6, 3.6), sharex=True, sharey=True)
    for ax, (key, label) in zip(axes.flat, PANELS):
        if (key, "en", "tier1") not in A:
            ax.set_title(label + " (not in data)", fontsize=8.5, pad=3)
            ax.set_xticks(tiers)
            ax.set_xticklabels(["T1", "T2", "T3", "T4"], fontsize=7.5)
            ax.set_ylim(-4, 104)
            continue
        en = [A[(key, "en", f"tier{t}")] for t in tiers]
        th = [A[(key, "th", f"tier{t}")] for t in tiers]
        ax.plot(tiers, en, "-", color=EN_C, lw=2.0)
        ax.plot(tiers, th, "--", color=TH_C, lw=1.8)
        ax.set_title(label, fontsize=8.5, pad=3)
        ax.set_xticks(tiers)
        ax.set_xticklabels(["T1", "T2", "T3", "T4"], fontsize=7.5)
        ax.set_ylim(-4, 104)
        ax.tick_params(labelsize=7.5, length=2)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axes[0, 0].set_ylabel("Accuracy (%)", fontsize=8.5)
    axes[1, 0].set_ylabel("Accuracy (%)", fontsize=8.5)
    fig.legend([plt.Line2D([], [], color=EN_C, ls="-", lw=2.0),
                plt.Line2D([], [], color=TH_C, ls="--", lw=1.8)],
               ["English", "Thai"], ncol=2, fontsize=8.5,
               loc="upper center", bbox_to_anchor=(0.5, 1.02), frameon=False)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(a.out, bbox_inches="tight")
    print("wrote", a.out)
    if a.no_slope:
        print("fig_slope.pdf not written (--no-slope)")
        return
    make_slope(A, os.path.join(os.path.dirname(a.out), "fig_slope.pdf"))


def make_slope(A, out):
    """slopegraph EN -> TH: เส้นละโมเดล + pooled เส้นหนา (pooled = ค่าเฉลี่ยของโมเดลที่มีในข้อมูล)"""
    import matplotlib.pyplot as plt
    # Okabe-Ito palette + marker ต่างกันทุกเส้น -> ปลอดภัยทั้ง colorblind และขาวดำ
    order = [("claude-sonnet", "claude-sonnet-5", "#0072B2", 3, "o"),
             ("gpt-mini", "gpt-5.4-mini", "#009E73", 5, "s"),
             ("gemini-flash", "gemini-3.6-flash", "#E69F00", -5, "^"),
             ("qwen25-coder-7b", "qwen2.5-coder 7B", "#CC79A7", 3, "D"),
             ("llama31-8b", "llama3.1 8B", "#56B4E9", -3, "v"),
             ("typhoon2-8b", "typhoon2 8B (Thai)", "#D55E00", 0, "X")]
    order = [o for o in order if (o[0], "en", "all") in A]
    fig, ax = plt.subplots(figsize=(3.9, 3.4))
    tot_en = tot_th = 0
    for key, label, color, dy, mk in order:
        en = A[(key, "en", "all")] ; th = A[(key, "th", "all")]
        tot_en += en ; tot_th += th
        ax.plot([0, 1], [en, th], "-", marker=mk, color=color, lw=1.4, ms=3.6, alpha=0.9)
        ax.annotate(label, (0, en), textcoords="offset points",
                    xytext=(-7, dy), ha="right", va="center", fontsize=6.6,
                    color=color, clip_on=False, annotation_clip=False)
    n = len(order)
    pe, pt = tot_en / n, tot_th / n
    ax.plot([0, 1], [pe, pt], "-", color="#222222", lw=3.2, alpha=0.9)
    words = {6: "all six", 5: "all five", 4: "all four", 3: "all three"}
    ax.annotate(f"pooled ({words.get(n, str(n))})", (1, pt), textcoords="offset points",
                xytext=(6, -8), ha="left", va="center", fontsize=7.2,
                color="#222222", fontweight="bold")
    ax.set_xlim(-1.05, 1.5); ax.set_ylim(0, 102)
    ax.set_xticks([0, 1]); ax.set_xticklabels(["English", "Thai"], fontsize=9)
    ax.set_ylabel("Accuracy (%)", fontsize=9)
    ax.tick_params(labelsize=8, length=2)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, bbox_inches="tight")
    print("wrote", out)


if __name__ == "__main__":
    main()
