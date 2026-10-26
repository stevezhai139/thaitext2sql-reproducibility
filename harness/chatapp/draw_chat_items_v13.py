#!/usr/bin/env python3
"""draw_chat_items_v13.py -- official non-VG item draw of the chat-app consistency
check (prereg AMENDMENT-8 sec.4), run once by the author on a frozen graded file.

Rule (AMENDMENT-8 sec.4; nothing here reads model text, only graded verdicts):
  pool  = primary items (v13_status = primary) not in VG_CHAT          (49 items)
  E     = pool items where >= 1 frontier proxy is majority-wrong in TH
  C     = pool items where all 3 frontier proxies are majority-correct in EN and TH
          (majority = strictly more than half of the 5 runs correct;
           majority-wrong = at most 2 of 5 correct)
  rng   = random.Random(20261012); shuffle sorted(E), then sorted(C), same rng
  take(order, k): pass 1 accepts an item when its tier has not been accepted
          yet in this call, until k; pass 2 fills from the rest in order
  e     = take(E, min(4, |E|));  c = take(C, min(8 - len(e), |C|))
  fill  = if len(e) + len(c) < 8: take(E minus e, 8 - len(e) - len(c))
  NONVG = e + c + fill;  items18 = VG_CHAT + NONVG
  items_sha256 = sha256(",".join(items18))

Input basis (OQ36, design 2.7): the graded file the author names with --graded,
filtered with --arm base under the --arm contract of design 2.6, implemented once in
harness/analyze.py (rows without an arm column count as base; rows of other arms are
dropped and only their counts are printed; every frontier cell must then hold exactly
5 runs). The draw basis label
(aug-k3n = August log re-graded on k3n, the OQ36 default; oct-base = October base
arm) is inferred from the file (any 'values' row => oct-base) and may be stated
with --draw-base, which must agree with the inference.

Guards (exit 2, nothing written): --out exists; sha256 of --graded differs from
--expect-graded-sha256; a DRAFT suite (file name or build_status, the rule of
grade_v13n.py) with --out under a folder named results; suite does not have 59 primary
items; VG set of the suite
(vg_rule.is_value_grounding) differs from VG_CHAT; graded file holds an excluded or
unknown qid; a value of correct, parse_ok or exec_ok other than True or False (any
other spelling, e.g. 1/0, would silently count as wrong); a frontier cell (model,
en|th, primary qid) does not hold exactly 5 runs; fewer than 8 items can be drawn.

Output (JSON, deterministic, no timestamp): input sha256, draw basis, |E|, |C|,
E and C (sorted and shuffled), e, c, fill, NONVG, items18, items_sha256.

Usage (from harness/, as in RUNBOOK_v2):
  python3 -I -B "chatapp/draw_chat_items_v13.py" --graded "<graded csv>"
      --suite "../suite/k3n_suite_v1.3n.tsv" --arm base
      --expect-graded-sha256 "<sha256>" --out "../results/chat/chat_items_v13.json"
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import csv  # noqa: E402
import hashlib  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import random  # noqa: E402
from collections import defaultdict  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- frozen constants of AMENDMENT-8 (single source for the chat kit) ----
SEED = 20261012
VG_CHAT = ["Q01", "Q07", "Q09", "Q13", "Q14", "Q15", "Q21", "Q30", "Q42", "Q48"]
FRONTIER = ["gpt-mini", "gemini-flash", "claude-sonnet"]
LANGS = ("en", "th")
RUNS = 5
N_PRIMARY = 59
N_NONVG = 8
E_MAX = 4
DRAW_BASES = ("aug-k3n", "oct-base")
DRAW_BASE_DEFAULT = "aug-k3n"  # OQ36 default (a); recorded in AMENDMENT-8


def die(msg, code=2):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def harness_dir(arg):
    """harness/ is the parent of chatapp/ in the repo; --harness-dir overrides."""
    return os.path.abspath(arg) if arg else os.path.dirname(HERE)


def load_suite(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    suite = {}
    for r in rows:
        if r["id"] in suite:
            die(f"duplicate id {r['id']} in suite")
        suite[r["id"]] = r
    return suite


def suite_is_draft(path, suite):
    """grade_v13n.py rule: the file name contains DRAFT, or a build_status cell contains DRAFT."""
    if "DRAFT" in os.path.basename(path).upper():
        return True
    return any("DRAFT" in (r.get("build_status") or "") for r in suite.values())


def under_results(path):
    """True when a folder of the absolute path is named results."""
    return "results" in os.path.abspath(path).split(os.sep)[:-1]


def refuse_draft_suite(suite_path, suite, outs):
    """exit 2 when a DRAFT suite would feed an output under results/ (official outputs
    use the frozen suite; tests write elsewhere)."""
    if suite_is_draft(suite_path, suite) and any(o and under_results(o) for o in outs):
        die(f"suite {os.path.basename(suite_path)} is a DRAFT (file name or build_status); "
            "outputs under results/ need the frozen suite")


def primary_ids(suite):
    return sorted(q for q, r in suite.items()
                  if (r.get("v13_status") or "primary").strip() == "primary")


def load_graded_arm(path, arm, suite, models, runs=RUNS, langs=LANGS, label="graded", d11_view=False):
    """--arm contract (design 2.6) for one graded CSV, through harness/analyze.py (the
    single implementation of the contract; the caller puts harness/ on sys.path).

    Rows without an arm are base; rows of other arms are dropped and only counted;
    the kept rows of `models` must cover every (model, en|th, primary qid) with exactly
    `runs` runs. Chat-specific guards: every model of `models` is present, no row (of
    any arm) has an excluded or unknown qid, and every correct/parse_ok/exec_ok value is
    True or False. Exits 2 otherwise.
    d11_view (D11, brief 1.0b; only for the proxy files of chat_report.py): rows of an item
    repaired for the October session (analyze.D11_REPAIRED) that `suite` (the August suite,
    the item excluded) marks excluded are left out and counted, which gives the 59-item view
    of the October core log that analyze.d11_check allows; the chat items never hold such an
    item (they are drawn from the August re-grade, where it is excluded).
    Returns ({(model, lang, qid): [bool, ...]}, {arm: dropped rows}, set of arms present).
    """
    import analyze  # noqa: E402  (harness/analyze.py)
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    bad_qid = defaultdict(int)
    d11_left = defaultdict(int)
    kept_rows = []
    for r in rows:
        q = r["qid"]
        if q not in suite:
            bad_qid["unknown"] += 1
        elif (suite[q].get("v13_status") or "primary").strip() != "primary":
            if d11_view and q in analyze.D11_REPAIRED:
                d11_left[q] += 1
                continue
            bad_qid["excluded:" + q] += 1
        kept_rows.append(r)
    rows = kept_rows
    if d11_left:
        n_prim = sum(1 for x in suite.values() if (x.get("v13_status") or "primary").strip() == "primary")
        print(f"[D11] {label}: {sum(d11_left.values())} rows of {sorted(d11_left)} left out (repaired for the "
              f"October session, excluded in the given suite): {n_prim}-item view")
    if bad_qid:
        die(f"{label}: rows with excluded or unknown qid: "
            + ", ".join(f"{k}={v}" for k, v in sorted(bad_qid.items())))
    check_bool_fields(rows, label)
    arms_seen = {analyze.row_arm(r) for r in rows}
    dropped = defaultdict(int)
    for r in rows:
        if analyze.row_arm(r) != arm:
            dropped[analyze.row_arm(r)] += 1
    kept = [r for r in analyze.filter_arm(rows, arm, label=label) if r["model_key"] in models]
    missing = [m for m in models if not any(r["model_key"] == m for r in kept)]
    if missing:
        die(f"{label}: no --arm {arm} rows for {missing}")
    analyze.require_complete(kept, runs, primary_ids(suite), label=label, langs=langs)
    cells = defaultdict(list)
    for r in kept:
        cells[(r["model_key"], r["lang"], r["qid"])].append(r["correct"] == "True")
    return dict(cells), dict(dropped), arms_seen


BOOL_FIELDS = ("correct", "parse_ok", "exec_ok")
BOOL_VALUES = ("True", "False")


def check_bool_fields(rows, label, fields=BOOL_FIELDS):
    """exit 2 when a present verdict column holds a value other than True or False (the
    grade_v13n.py spelling). Every chat reader compares with the string 'True', so any
    other spelling would silently count as wrong."""
    bad = defaultdict(int)
    for r in rows:
        for f in fields:
            if f in r and (r[f] or "").strip() not in BOOL_VALUES:
                bad[f"{f}={(r[f] or '')[:12]!r}"] += 1
    if bad:
        die(f"{label}: verdict values other than True/False: "
            + ", ".join(f"{k} x{v}" for k, v in sorted(bad.items())[:6]))


def majority_correct(runs_list):
    return sum(runs_list) * 2 > len(runs_list)


def take(order, k, tier):
    """AMENDMENT-8 sec.4 take(): one item per tier first, then fill in order."""
    picked, seen = [], set()
    for q in order:
        if len(picked) >= k:
            break
        if tier[q] not in seen:
            picked.append(q)
            seen.add(tier[q])
    for q in order:
        if len(picked) >= k:
            break
        if q not in picked:
            picked.append(q)
    return picked


def draw(suite, cells):
    """Pure draw on the filtered cells; returns the result dict (no I/O)."""
    prim = primary_ids(suite)
    tier = {q: suite[q]["tier"].strip() for q in prim}
    pool = [q for q in prim if q not in VG_CHAT]
    maj = {k: majority_correct(v) for k, v in cells.items()}
    E = sorted(q for q in pool if any(not maj[(m, "th", q)] for m in FRONTIER))
    C = sorted(q for q in pool if all(maj[(m, l, q)] for m in FRONTIER for l in LANGS))
    rng = random.Random(SEED)
    Es, Cs = list(E), list(C)
    rng.shuffle(Es)
    rng.shuffle(Cs)
    e = take(Es, min(E_MAX, len(Es)), tier)
    c = take(Cs, min(N_NONVG - len(e), len(Cs)), tier)
    need = N_NONVG - len(e) - len(c)
    fill = take([q for q in Es if q not in e], need, tier) if need > 0 else []
    nonvg = e + c + fill
    if len(nonvg) != N_NONVG:
        die(f"only {len(nonvg)} non-VG items can be drawn (|E|={len(E)}, |C|={len(C)}); need {N_NONVG}")
    items18 = VG_CHAT + nonvg
    return {
        "pool_size": len(pool),
        "E_size": len(E), "C_size": len(C),
        "E": E, "C": C, "E_shuffled": Es, "C_shuffled": Cs,
        "e": e, "c": c, "fill_from_E": fill,
        "nonvg": nonvg, "nonvg_tiers": {q: tier[q] for q in nonvg},
        "items18": items18,
        "items_sha256": hashlib.sha256(",".join(items18).encode("utf-8")).hexdigest(),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--graded", required=True, help="graded CSV (16 columns of grade_v13n)")
    ap.add_argument("--suite", required=True, help="suite/k3n_suite_v1.3n.tsv")
    ap.add_argument("--arm", required=True, choices=["base"], help="arm contract; the draw uses base")
    ap.add_argument("--expect-graded-sha256", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--draw-base", choices=DRAW_BASES,
                    help="optional statement of the draw basis; must agree with the file")
    ap.add_argument("--harness-dir", help="folder with vg_rule.py and analyze.py (default: parent of chatapp/)")
    a = ap.parse_args()

    if os.path.exists(a.out):
        die(f"--out exists, refusing to overwrite: {os.path.basename(a.out)}")
    got = sha256_file(a.graded)
    if got != a.expect_graded_sha256.strip().lower():
        die(f"sha256 of --graded is {got}, expected {a.expect_graded_sha256}")

    sys.path.insert(0, harness_dir(a.harness_dir))
    from vg_rule import is_value_grounding  # noqa: E402

    suite = load_suite(a.suite)
    refuse_draft_suite(a.suite, suite, [a.out])
    prim = primary_ids(suite)
    if len(prim) != N_PRIMARY:
        die(f"suite has {len(prim)} primary items, expected {N_PRIMARY}")
    vg = [q for q in prim if is_value_grounding(suite[q]["gold_sql_draft"], suite[q]["question_th"])]
    if vg != VG_CHAT:
        die(f"VG set of the suite {vg} != VG_CHAT {VG_CHAT}")

    cells, dropped, arms_seen = load_graded_arm(a.graded, a.arm, suite, FRONTIER)
    inferred = "oct-base" if "values" in arms_seen else "aug-k3n"
    if a.draw_base and a.draw_base != inferred:
        die(f"--draw-base {a.draw_base} disagrees with the graded file (looks like {inferred})")
    base_label = a.draw_base or inferred

    res = draw(suite, cells)
    out = {
        "tool": "draw_chat_items_v13.py",
        "tool_sha256": sha256_file(os.path.abspath(__file__)),
        "rule": "AMENDMENT-8 sec.4",
        "seed": SEED,
        "draw_base": base_label,
        "draw_base_default_oq36": DRAW_BASE_DEFAULT,
        "arm": a.arm,
        "runs": RUNS,
        "graded_file": os.path.basename(a.graded),
        "graded_sha256": got,
        "suite_file": os.path.basename(a.suite),
        "suite_sha256": sha256_file(a.suite),
        "dropped_rows_by_arm": dict(sorted(dropped.items())),
        "frontier": FRONTIER,
        "vg_chat": VG_CHAT,
    }
    out.update(res)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(out, ensure_ascii=False, indent=1) + "\n")

    print(f"draw basis: {base_label} (graded sha256 {got})")
    print(f"pool={res['pool_size']} |E|={res['E_size']} |C|={res['C_size']}")
    print(f"e={res['e']} c={res['c']} fill_from_E={res['fill_from_E']}")
    print(f"NONVG={res['nonvg']}")
    print(f"items_sha256={res['items_sha256']}")
    print(f"[out] {os.path.basename(a.out)} sha256={sha256_file(a.out)}")


if __name__ == "__main__":
    main()
