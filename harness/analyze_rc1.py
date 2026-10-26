#!/usr/bin/env python3
"""analyze_rc1.py -- pre-registered analysis of the value-hint arm (AMENDMENT-7 Part A:
H1-H4, A6 measures, A9 slot values) and of the B2 counts (Part B2.2/B2.6, base-only
mode). Written and frozen before any October-session model call.

Unit: item-level majority of the runs of a (model, arm, language, item) cell, strictly
more than half correct. Primary contrast: arm 'values' (V) against the concurrent arm
'base' (B), same model, language and items. The August log is not the control.

Modes
  --mode rc1        both arms (results/rc1/graded_rc1.csv + results_rc1_*.jsonl)
  --mode base-only  base arm only (B2 'g of N', 'a of N' and contrast count per model
                    and pooled; e.g. the August log re-graded on k3n, secondary data)

Sets (on the primary items of --suite; D11: on the October core suite Q27 is repaired and
primary, n=60, the primary October analysis; on the August suite Q27 is excluded, n=59, and
--keep-excluded keeps it, n=60; analyze.d11_check pairs the suite with --graded)
  VG10     vg_rule (AMENDMENT-6) on the gold; PLACEBO = primary minus VG10 (50 items on the
           October core suite, where the repaired Q27 has no VG literal; 49 on the August suite)
  VG set   --vg-set FILE (default VG10); B2 counts (RQ2) use it
  VG_cov   VG10 items whose every target literal is visible in the frozen value block
           (computed from --hints; must equal --expect-vg-cov, the frozen 9 items)
GF(cell) = VG item and TH majority wrong and #(THAI_COPY u INVENTED) > failing runs / 2
(classifier: vg_classifier.py, the single B2.3 implementation; no manual tie rule).

Decision rules (AM-7 A7; computed from integers, no floating thresholds)
  H1  frontier pooled TH GF on VG_cov: GF_B < 4 -> S0; GF_V <= 0.25 GF_B -> S1 ('all'
      when GF_V = 0, else 'most'); GF_V >= 0.75 GF_B -> S3; otherwise S2. Fewer than two
      usable frontier models -> descriptive only (A5.2). GF max = 9 x frontier models.
  H2  share remaining = sum Gap_V / sum Gap_B (frontier pooled, all analysed items);
      sum Gap_B <= 2 -> G-d; share <= 0.60 -> G-a; share >= 0.90 -> G-c; else G-b.
      Item-cluster bootstrap 10,000 x, seed 20261012, percentile; a resample with
      sum Gap_B <= 0 keeps share = +inf and is counted; more than 250 such resamples
      -> the CI is [lo, unbounded) (OQ25.2 default).
  H3  placebo flips (PLACEBO items whose majority differs between B and V) <= 2 per
      frontier model per language; a failure sets M2 and H1/H2 are also reported
      without the failing model(s).
  H4  exact McNemar V vs B on TH, per frontier model, Holm across the frontier set;
      M1 = Holm-significant Thai accuracy GAIN.
--exclude-pairs <tsv> (check 8 output): both arms of each listed (model, lang, qid,
run) are dropped, the cell majority is taken over the remaining runs (strictly more than
half) and a cell with no run left is dropped from both arms; counts are reported
(sensitivity of AM-7 A4 as revised).

Outputs in --out: rc1_accuracy.csv (Wilson CI), rc1_gf.csv (H1 on VG_cov, RQ2 on the VG
set), rc1_gf_cells.csv, rc1_base_counts.csv (B2.6 a of N, g of N, contrast), rc1_gap.csv
(VG_cov / rest on the analysed items, pooled share and CI), rc1_mcnemar.csv,
rc1_placebo.csv, rc1_drift.csv (against --graded-ror: the August log re-graded on k3n,
which must come from another session than --graded (analyze.same_session, D10) and have
exactly --runs base runs in every cell of the items shared by the two sessions: D11 leaves
the repaired Q27 out of the drift on the October core suite, 59 items), rc1_silent.csv (B1 per arm),
rc1_decisions.json (bands, guards, modifiers, A9 slot values), rc1_audit_rows.csv (input
of make_audit_sheet_rc1.py), rc1_summary.txt and meta.json.
Audit rows (AM-7 A6 'every failing run on Thai VG items of both arms'): every analysed
model by default (AUDIT_SCOPE_DEFAULT = "all"; "frontier" is the narrower option).
A7-39 (OQ6): for each VG item whose gold literal is not a stored value of its column (on
k3n: Q48 'None'), the number of runs (every analysed model, arm and language, whatever the
grade) whose SQL uses that literal, and how many compare it with the target column; the
count of failing runs classed INVENTED only through that literal stays as a diagnostic.
B1 classes of rc1_silent.csv come from analyze.b1_class (a blank n_rows stops).
results*.jsonl is read through a hook that keeps model_key, arm, lang, qid, run, sql
and parse_ok and turns 'error' into a boolean (never kept or printed).

Usage (Gate 3 step 52):
  python3 -I -B analyze_rc1.py --mode rc1 --graded ../results/rc1/graded_rc1.csv \
    --results ../results/rc1/results_rc1_api.jsonl --results ../results/rc1/results_rc1_local.jsonl \
    --graded-ror ../results/v13n/graded_v13n.csv --suite ../suite/k3n_suite_v1.3n_oct.tsv \
    --hints ../suite/value_hints_v1.json --hints-sha256 <sha256> \
    --vg-set ../suite/vg_set_v13n.txt --expect-vg-cov Q01,Q07,Q09,Q13,Q14,Q15,Q21,Q30,Q42 \
    --out ../results/rc1/h1h4
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
from collections import Counter, defaultdict
from fractions import Fraction
from math import comb

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402
import vg_classifier as vgc  # noqa: E402
from vg_classifier import classify_run  # noqa: E402,F401  (same object as vg_classifier)

FRONTIER = ["claude-sonnet", "gpt-mini", "gemini-flash"]
LOCAL = ["qwen25-coder-7b", "llama31-8b", "typhoon2-8b"]
A9_ORDER = ["gpt-mini", "gemini-flash", "claude-sonnet"]   # order of the A9 RQ2 sentence
SEED = 20261012
N_BOOT = 10000
UNBOUNDED_LIMIT = 250      # OQ25.2: more resamples with sum Gap_B <= 0 -> unbounded CI
GF_B_MIN = 4               # H1: fewer baseline GF -> S0
PLACEBO_MAX_FLIPS = 2      # H3
HOLM_ALPHA = 0.05          # H4

# ------------------------------------------------------------------------ DECIDED (OQ18.1)
# OQ18.1 (GENUINE; answered by the author on 14 Oct 2026, brief 1.0c): option (b). Does the
# abstract carry the H2 gap clause?
#   "all_but_Gd" -- option (b), DECIDED: the clause is in the abstract in every scenario
#                   except G-d, and in RQ2 unless G-d
#   "rq2_only"   -- option (a), the AM-7 draft: RQ2 only, never in the abstract
ABSTRACT_H2_CLAUSE_RULE = "all_but_Gd"   # DECIDED (OQ18.1): option (b), author 14 Oct 2026
ABSTRACT_H2_CLAUSE_RULES = ("all_but_Gd", "rq2_only")
# record of the answer (not a switch): the switch is ABSTRACT_H2_CLAUSE_RULE above
ABSTRACT_H2_CLAUSE_STATUS = "OQ18.1 answered by the author on 14 Oct 2026: option (b) = 'all_but_Gd'"
# Audit scope of the blind B2.3 audit. AM-7 A6 as registered: "every failing run on Thai
# VG items of both arms" (no model restriction) -> "all" (default). "frontier" lists only
# the frontier cells (the counted cells of H1 and RQ2); choosing it needs an amendment
# entry before Gate 1b (author's decision). One switch; --audit-scope overrides per run.
# "all" is a disclosed assistant default (it is not one of the 58 triage defaults of brief
# 1.0c); the author approves it with the AMENDMENT_EDITS items at Gate 0 step 0.3.
AUDIT_SCOPE_DEFAULT = "all"   # assistant default (disclosed); author approval at Gate 0 step 0.3
AUDIT_SCOPES = ("all", "frontier")
# ----------------------------------------------------------------------------------------

_KEEP = ("model_key", "arm", "lang", "qid", "run", "sql", "parse_ok")


def _hook(pairs):
    d = {}
    for k, v in pairs:
        if k == "error":
            d["error"] = v is not None
        elif k in _KEEP:
            d[k] = v
    return d


def iter_records(paths):
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if line.strip():
                    try:
                        yield json.loads(line, object_pairs_hook=_hook)
                    except json.JSONDecodeError:
                        ac.die(2, f"{os.path.basename(path)} line {n}: not JSON")


# ---------------------------------------------------------------- statistics
def exact_mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n)


def holm(ps):
    idx = sorted(range(len(ps)), key=lambda i: ps[i])
    adj, prev = [0.0] * len(ps), 0.0
    for rank, i in enumerate(idx):
        prev = max(prev, min(1.0, (len(ps) - rank) * ps[i]))
        adj[i] = prev
    return adj


def h1_band(gf_b, gf_v):
    """(band, 'most'|'all'|None) of AM-7 A7 H1 (integer comparisons)."""
    if gf_b < GF_B_MIN:
        return "S0", None
    if 4 * gf_v <= gf_b:
        return "S1", ("all" if gf_v == 0 else "most")
    if 4 * gf_v >= 3 * gf_b:
        return "S3", None
    return "S2", None


def h2_band(gap_b, gap_v):
    """(band, share as Fraction or None) of AM-7 A7 H2."""
    if gap_b <= 2:
        return "G-d", (Fraction(gap_v, gap_b) if gap_b > 0 else None)
    s = Fraction(gap_v, gap_b)
    if s <= Fraction(60, 100):
        return "G-a", s
    if s >= Fraction(90, 100):
        return "G-c", s
    return "G-b", s


def cluster_bootstrap_share(qids, num_fn, den_fn, seed=SEED, n=N_BOOT):
    """item-cluster bootstrap of sum(num)/sum(den); all models, arms and languages of an
    item travel together. Resamples with den <= 0 keep share = +inf (OQ25.2).
    Returns (lo, hi or None for unbounded, n_den_le0)."""
    rnd = random.Random(seed)
    num = {q: num_fn(q) for q in qids}
    den = {q: den_fn(q) for q in qids}
    vals, n_bad = [], 0
    for _ in range(n):
        s = [rnd.choice(qids) for _ in qids]
        d = sum(den[q] for q in s)
        if d <= 0:
            n_bad += 1
            vals.append(float("inf"))
        else:
            vals.append(sum(num[q] for q in s) / d)
    vals.sort()
    lo, hi = vals[int(0.025 * n)], vals[int(0.975 * n) - 1]
    if n_bad > UNBOUNDED_LIMIT or hi == float("inf"):
        hi = None
    return lo, hi, n_bad


def wilson(k, n):
    return ac.wilson(k, n)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description="AM-7 Part A (H1-H4) and B2 counts")
    ap.add_argument("--mode", choices=["rc1", "base-only"], required=True)
    ap.add_argument("--graded", required=True)
    ap.add_argument("--results", required=True, action="append")
    ap.add_argument("--graded-ror", help="August log re-graded on k3n (drift, A6 item 7); another "
                                          "session than --graded, complete on the analysed items")
    ap.add_argument("--suite", required=True)
    ap.add_argument("--hints", required=True)
    ap.add_argument("--hints-sha256", required=True)
    ap.add_argument("--vg-set", help="VG list file; default VG10 from vg_rule")
    ap.add_argument("--expect-vg-cov", help="frozen VG_cov list (comma separated); "
                                            "required in --mode rc1")
    ap.add_argument("--keep-excluded", action="store_true",
                    help="n=60 sensitivity of the August log; only for the August re-grade "
                         "graded_v13n_withQ27.csv (analyze.d11_check, D11)")
    ap.add_argument("--exclude-models", default="")
    ap.add_argument("--exclude-pairs", help="nonconcurrent_pairs.tsv of check_rc1_log.py")
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--audit-scope", choices=list(AUDIT_SCOPES), default=AUDIT_SCOPE_DEFAULT)
    ap.add_argument("--out", required=True)
    ac.add_draft_flag(ap)
    a = ap.parse_args()
    if ABSTRACT_H2_CLAUSE_RULE not in ABSTRACT_H2_CLAUSE_RULES or AUDIT_SCOPE_DEFAULT not in AUDIT_SCOPES:
        ac.die(2, f"unknown switch value: ABSTRACT_H2_CLAUSE_RULE {ABSTRACT_H2_CLAUSE_RULE!r} "
                  f"(one of {ABSTRACT_H2_CLAUSE_RULES}), AUDIT_SCOPE_DEFAULT {AUDIT_SCOPE_DEFAULT!r} "
                  f"(one of {AUDIT_SCOPES})")
    suite_all = ac.load_suite_rows(a.suite)
    ac.draft_guard(a.suite, suite_all, a.allow_draft_testonly, out_dirs=[a.out])
    rows = ac.read_csv_rows(a.graded)
    grec = ac.graded_record(a.graded, rows, "base")
    session = ac.d11_check(suite_all, a.keep_excluded, grec, os.path.basename(a.suite))
    os.makedirs(a.out, exist_ok=True)
    lines = []

    def P(s=""):
        print(s)
        lines.append(str(s))

    rc1 = a.mode == "rc1"
    arms = ("base", "values") if rc1 else ("base",)
    n_items = len(ac.primary_suite(suite_all, a.keep_excluded))
    common = ac.common_meta("base,values" if rc1 else "base", a.suite, a.keep_excluded, n_items)
    ac.guard_dir_meta(a.out, common, grec)  # before any output is written

    # ---------------- suite, sets, hints
    suite = ac.primary_suite(suite_all, a.keep_excluded)
    qids = sorted(suite)
    targets = vgc.suite_vg_targets(suite)                  # VG10 (AMENDMENT-6 rule)
    vg10 = sorted(targets)
    vg_set = ac.read_vg_set(a.vg_set, universe=suite) if a.vg_set else list(vg10)
    missing_t = [q for q in vg_set if q not in targets]
    if missing_t:
        ac.die(2, f"VG set items without a VG literal in the gold: {missing_t}")
    hints, hsha = vgc.load_hints(a.hints, a.hints_sha256)
    gold_targets = [t for q in vg10 for t in targets[q]]
    vocab = vgc.build_vocab(hints, gold_targets=gold_targets)
    shown = vgc.shown_values(hints)
    vg_cov = [q for q in vg10 if vgc.covered(targets[q], shown)]
    placebo = [q for q in qids if q not in vg10]
    rest_cov = [q for q in qids if q not in vg_cov]
    nonvg_set = [q for q in qids if q not in vg_set]
    P(f"mode {a.mode}; items {len(qids)}; VG10 {vg10}; VG set {vg_set}")
    P(f"VG_cov (hint-covered) {vg_cov}; PLACEBO {len(placebo)} items; "
      f"hints sha256 {hsha[:12]}...; source_db {hints.get('source_db', '?')}; "
      f"Q48 vocabulary rule {vgc.Q48_VOCAB_RULE}")
    if a.expect_vg_cov is not None:
        exp = sorted(ac.split_list(a.expect_vg_cov))
        if exp != sorted(vg_cov):
            ac.die(2, f"VG_cov {vg_cov} differs from the frozen list {exp}; stop (AM-7 A6)")
        P("VG_cov equals the frozen list")
    elif rc1:
        ac.die(2, "--mode rc1 needs --expect-vg-cov (the frozen 9 items)")

    # ---------------- graded rows
    bad = Counter(ac.row_arm(r) for r in rows if ac.row_arm(r) not in ("base", "values"))
    if bad:
        ac.die(2, f"graded file has arms other than base/values: {dict(bad)}")
    excluded = set(ac.split_list(a.exclude_models))
    n_values_ignored = sum(1 for r in rows if ac.row_arm(r) == "values") if not rc1 else 0
    rows = [r for r in rows if ac.row_arm(r) in arms and r["model_key"] not in excluded
            and r["qid"] in suite]
    if n_values_ignored:
        P(f"base-only mode: {n_values_ignored} values-arm rows ignored")
    if excluded:
        P(f"--exclude-models: {sorted(excluded)}")
    models_present = sorted({r["model_key"] for r in rows})
    models = [m for m in FRONTIER + LOCAL if m in models_present] + \
        sorted(m for m in models_present if m not in FRONTIER + LOCAL)
    cnt = Counter((r["model_key"], ac.row_arm(r), r["lang"], r["qid"]) for r in rows)
    short = [(m, arm, lg, q, cnt.get((m, arm, lg, q), 0)) for m in models for arm in arms
             for lg in ac.LANGS for q in qids if cnt.get((m, arm, lg, q), 0) != a.runs]
    if short:
        ac.die(2, f"{len(short)} cells without exactly {a.runs} graded runs (first {short[:5]});"
                  f" finish the run or use --exclude-models (AM-7 A5.6)")
    frontier = [m for m in FRONTIER if m in models]
    P(f"models {models}; frontier for H1-H4 {frontier}")

    # ---------------- --graded-ror (drift against the August log): D10 session + completeness
    # D11: the drift compares the items shared by the two sessions (the repaired Q27 asks
    # another question in October; on the October core suite it is left out: 59 items)
    ror_rec, ror_rows = None, []
    drift_q = ac.d11_shared(qids, session)
    if a.graded_ror:
        ror_all = ac.read_csv_rows(a.graded_ror)
        ror_rec = ac.graded_record(a.graded_ror, ror_all, "base")
        same, why = ac.same_session(grec, ror_rec)
        if same:
            ac.die(2, f"[D10] --graded-ror {ac.describe(ror_rec)} comes from the same session as "
                      f"--graded ({why}); the drift needs the August log re-graded on k3n")
        ror_rows = [r for r in ac.filter_arm(ror_all, "base", excluded, "graded-ror")
                    if r["qid"] in drift_q]
        ac.require_complete(ror_rows, a.runs, drift_q, "graded-ror")
        P(f"--graded-ror: {ac.describe(ror_rec)}; another session than --graded ({why})")
        if len(drift_q) != len(qids):
            P(f"[D11] drift on the {len(drift_q)} items shared by the two sessions "
              f"({', '.join(q for q in qids if q not in drift_q)} repaired for October only, left out)")

    # ---------------- --exclude-pairs (sensitivity)
    dropped_pairs = 0
    if a.exclude_pairs:
        pairs = set()
        with open(a.exclude_pairs, encoding="utf-8", newline="") as fh:
            for r in csv.DictReader(fh, delimiter="\t"):
                pairs.add((r["model_key"], r["lang"], r["qid"], str(r["run"])))
        before = len(rows)
        rows = [r for r in rows
                if (r["model_key"], r["lang"], r["qid"], str(r["run"])) not in pairs]
        dropped_pairs = len({p for p in pairs if p[0] in models and p[2] in suite})
        P(f"--exclude-pairs: {len(pairs)} listed pairs, {dropped_pairs} in the analysed cells; "
          f"{before - len(rows)} graded rows dropped (both arms)")

    runs_of = defaultdict(list)
    for r in rows:
        runs_of[(r["model_key"], ac.row_arm(r), r["lang"], r["qid"])].append(r)
    item = {}
    dropped_cells = []
    for m in models:
        for lg in ac.LANGS:
            for q in qids:
                ks = [(m, arm, lg, q) for arm in arms]
                if any(not runs_of.get(k) for k in ks):
                    dropped_cells.append((m, lg, q))
                    continue
                for k in ks:
                    v = [x["correct"] == "True" for x in runs_of[k]]
                    item[k] = sum(v) > len(v) / 2
    if dropped_cells:
        P(f"cells with no run left, dropped from both arms: {len(dropped_cells)} {dropped_cells[:6]}")

    def ok(m, arm, lg, q):
        return item.get((m, arm, lg, q))

    def S(m, arm, lg, qs):
        return sum(1 for q in qs if ok(m, arm, lg, q))

    def N_def(m, arm, lg, qs):
        return sum(1 for q in qs if (m, arm, lg, q) in item)

    # ---------------- SQL of failing TH runs on VG10 items
    need = set()
    for (m, arm, lg, q), rs in runs_of.items():
        if lg == "th" and q in targets:
            for r in rs:
                if r["correct"] != "True":
                    need.add((m, arm, "th", q, str(r["run"])))
    # A7-39 (OQ6): VG gold literals that are not stored values of their column (k3n: Q48 'None')
    stored = vgc.build_vocab(hints, rule="keep")
    gold_ns = {q: [(c, lit) for c, lit in targets[q] if c is not None and c in stored
                   and lit not in stored[c]] for q in vg10}
    gold_ns = {q: v for q, v in gold_ns.items() if v}
    lit_use, lit_seen = Counter(), set()
    sql_of = {}
    for rec in iter_records(a.results):
        if rec.get("error"):
            continue
        k = (rec.get("model_key"), ac.row_arm(rec), rec.get("lang"), rec.get("qid"), str(rec.get("run")))
        if k in need:
            if k in sql_of:
                ac.die(2, f"duplicate non-error record {k}")
            sql_of[k] = rec.get("sql") or "" if rec.get("parse_ok", False) else ""
        if k[3] in gold_ns and k[1] in arms and k[0] in models and k not in lit_seen:
            lit_seen.add(k)
            s_ = (rec.get("sql") or "") if rec.get("parse_ok", False) else ""
            lits = vgc.string_literals(s_)
            for col, lit in gold_ns[k[3]]:
                for key in ((k[3], lit, col, "all", "all"), (k[3], lit, col, k[1], k[2])):
                    lit_use[key + ("runs",)] += 1
                    lit_use[key + ("uses",)] += lit in lits
                    lit_use[key + ("on_col",)] += any(x == lit for _, x in
                                                      vgc.predicates_on_column(s_, col))
    lost = sorted(need - set(sql_of))
    if lost:
        ac.die(2, f"{len(lost)} failing graded runs have no results record (first {lost[:3]})")
    a739 = []
    for q, pairs in sorted(gold_ns.items()):
        for col, lit in pairs:
            tot = {x: lit_use[(q, lit, col, "all", "all", x)] for x in ("runs", "uses", "on_col")}
            a739.append({"qid": q, "column": col, "literal": lit, **tot,
                         "by_arm_lang": {f"{arm}|{lg}": lit_use[(q, lit, col, arm, lg, "uses")]
                                         for arm in arms for lg in ac.LANGS}})
            P(f"A7-39 (OQ6): {q} runs whose SQL uses the literal '{lit}' (gold literal not stored "
              f"on k3n): {tot['uses']} of {tot['runs']} runs (every analysed model, arm and "
              f"language, any grade); compared with {col}: {tot['on_col']}; by arm|language "
              + ", ".join(f"{kk}={vv}" for kk, vv in a739[-1]["by_arm_lang"].items())
              + ("; report in the paper (non-zero)" if tot["uses"] else ""))
    if not gold_ns:
        P("A7-39 (OQ6): no VG gold literal outside the stored values")

    # ---------------- classes and GF per cell (TH, VG10 items)
    cell_rows, cls_of, gf = [], {}, {}
    gold_only_invented = Counter()
    for m in models:
        for arm in arms:
            for q in vg10:
                k = (m, arm, "th", q)
                if k not in item:
                    continue
                fails = [r for r in runs_of[k] if r["correct"] != "True"]
                classes = []
                for r in fails:
                    s = sql_of[(m, arm, "th", q, str(r["run"]))]
                    c = classify_run(s, targets[q], vocab)
                    classes.append(c)
                    cls_of[(m, arm, q, str(r["run"]))] = c
                    if c == "INVENTED":
                        inv = vgc.invented_literals(s, targets[q], vocab)
                        if inv and all(lit in {t[1] for t in targets[q]} for _, _, lit in inv):
                            gold_only_invented[q] += 1
                g = vgc.is_gf_cell(True, not item[k], classes)
                gf[k] = g
                cc = Counter(classes)
                cell_rows.append({"model": m, "arm": arm, "lang": "th", "qid": q,
                                  "in_vg_cov": q in vg_cov, "in_vg_set": q in vg_set,
                                  "n_runs": len(runs_of[k]), "n_fail": len(fails),
                                  "majority_wrong": not item[k],
                                  **{c: cc[c] for c in vgc.CLASSES}, "gf": g,
                                  "exploratory": m in LOCAL})
    write_csv(os.path.join(a.out, "rc1_gf_cells.csv"), cell_rows)
    if gold_only_invented:
        P(f"OQ6 diagnostic: failing TH runs classed INVENTED only because the gold literal is "
          f"not a stored value: {dict(sorted(gold_only_invented.items()))} (rule {vgc.Q48_VOCAB_RULE})")
    else:
        P("OQ6 diagnostic: no failing TH run is INVENTED only because of a non-stored gold literal")

    def GF(m, arm, qs):
        return sum(1 for q in qs if gf.get((m, arm, "th", q)))

    # ---------------- rc1_accuracy.csv
    acc = []
    subsets = [("all", qids), ("vg_cov", vg_cov), ("rest_cov", rest_cov), ("vg_set", vg_set),
               ("nonvg_set", nonvg_set), ("placebo", placebo)]
    for m in models:
        for arm in arms:
            for lg in ac.LANGS:
                for name, qs in subsets:
                    c, n = S(m, arm, lg, qs), N_def(m, arm, lg, qs)
                    p, lo, hi = wilson(c, n)
                    acc.append({"model": m, "arm": arm, "lang": lg, "subset": name, "correct": c,
                                "n": n, "acc": f"{p:.3f}", "ci_lo": f"{lo:.3f}", "ci_hi": f"{hi:.3f}",
                                "exploratory": m in LOCAL})
    write_csv(os.path.join(a.out, "rc1_accuracy.csv"), acc)

    # ---------------- rc1_gf.csv and rc1_base_counts.csv (B2.6)
    gfrows, bc = [], []
    for arm in arms:
        tot = Counter()
        for m in models:
            n_wrong_all = sum(1 for q in qids if (m, arm, "th", q) in item and not ok(m, arm, "th", q))
            for name, qs in (("vg_cov", vg_cov), ("vg_set", vg_set)):
                wrong_in = sum(1 for q in qs if (m, arm, "th", q) in item and not ok(m, arm, "th", q))
                gfrows.append({"model": m, "arm": arm, "subset": name, "n_items": len(qs),
                               "th_wrong_in_subset": wrong_in, "gf": GF(m, arm, qs),
                               "th_wrong_all": n_wrong_all, "exploratory": m in LOCAL})
            a_ = sum(1 for q in vg_set if (m, arm, "th", q) in item and not ok(m, arm, "th", q))
            contrast = sum(1 for q in vg_set if ok(m, arm, "en", q) and
                           (m, arm, "th", q) in item and not ok(m, arm, "th", q))
            g_ = GF(m, arm, vg_set)
            bc.append({"model": m, "arm": arm, "vg_set_n": len(vg_set), "a": a_,
                       "N": n_wrong_all, "g": g_, "contrast": contrast,
                       "exploratory": m in LOCAL})
            if m in frontier:
                tot.update({"a": a_, "N": n_wrong_all, "g": g_, "contrast": contrast})
        bc.append({"model": "frontier_total", "arm": arm, "vg_set_n": len(vg_set),
                   "a": tot["a"], "N": tot["N"], "g": tot["g"], "contrast": tot["contrast"],
                   "exploratory": False})
    write_csv(os.path.join(a.out, "rc1_gf.csv"), gfrows)
    write_csv(os.path.join(a.out, "rc1_base_counts.csv"), bc)
    P("\nB2 counts (TH, VG set; per model a of N, g of N, contrast):")
    for r in bc:
        P(f"  {r['model']:16} {r['arm']:6} a={r['a']} of N={r['N']}; g={r['g']} of N={r['N']}; "
          f"contrast={r['contrast']}")

    # ---------------- rc1_silent.csv (B1 per arm)
    sil = []
    for m in models:
        for arm in arms:
            for lg in ac.LANGS:
                c = Counter()
                for q in qids:
                    for r in runs_of.get((m, arm, lg, q), []):
                        if r["correct"] != "True":
                            c[ac.b1_class(r)] += 1
                sil.append({"model": m, "arm": arm, "lang": lg, "wrong_runs": sum(c.values()),
                            "loud": c["loud"], "silent_empty": c["silent_empty"],
                            "silent_nonempty": c["silent_nonempty"], "exploratory": m in LOCAL})
    write_csv(os.path.join(a.out, "rc1_silent.csv"), sil)

    # ---------------- rc1_drift.csv
    if a.graded_ror:
        rr = defaultdict(list)
        for r in ror_rows:
            rr[(r["model_key"], r["lang"], r["qid"])].append(r["correct"] == "True")
        ror = {k: sum(v) > len(v) / 2 for k, v in rr.items()}
        dr = []
        for m in models:
            for lg in ac.LANGS:
                both = [q for q in drift_q if (m, "base", lg, q) in item and (m, lg, q) in ror]
                d = sum(1 for q in both if ok(m, "base", lg, q) != ror[(m, lg, q)])
                dr.append({"model": m, "lang": lg, "items": len(both), "items_differ": d,
                           "ror_correct": sum(ror[(m, lg, q)] for q in both),
                           "base_now_correct": sum(1 for q in both if ok(m, "base", lg, q)),
                           "exploratory": m in LOCAL})
        write_csv(os.path.join(a.out, "rc1_drift.csv"), dr)
        P("\ndrift (items whose base-arm majority differs from the August log on k3n): " +
          ", ".join(f"{r['model']} {r['lang']} {r['items_differ']}/{r['items']}" for r in dr))

    # ---------------- audit rows
    audit_models = frontier if a.audit_scope == "frontier" else models
    au = []
    for m in audit_models:
        for arm in arms:
            for q in sorted(set(vg_set) | set(vg_cov)):
                k = (m, arm, "th", q)
                if k not in item:
                    continue
                fails = [r for r in runs_of[k] if r["correct"] != "True"]
                for r in sorted(fails, key=lambda x: int(x["run"])):
                    run = str(r["run"])
                    au.append({"row_key": f"{m}|{arm}|th|{q}|{run}", "model": m, "arm": arm,
                               "lang": "th", "qid": q, "run": run, "in_vg_cov": q in vg_cov,
                               "in_vg_set": q in vg_set, "cell_majority_wrong": not item[k],
                               "cell_n_fail": len(fails),
                               "question_th": suite[q]["question_th"],
                               "targets": "; ".join(f"{c} = '{lit}'" for c, lit in targets[q]),
                               "sql": sql_of[(m, arm, "th", q, run)],
                               "classifier_class": cls_of[(m, arm, q, run)]})
    write_csv(os.path.join(a.out, "rc1_audit_rows.csv"), au,
              header=["row_key", "model", "arm", "lang", "qid", "run", "in_vg_cov", "in_vg_set",
                      "cell_majority_wrong", "cell_n_fail", "question_th", "targets", "sql",
                      "classifier_class"])
    P(f"\naudit rows (failing TH runs on VG items, scope {a.audit_scope}): {len(au)}")

    decisions = None
    if rc1:
        decisions = rc1_section(a, P, models, frontier, qids, vg_cov, vg_set, placebo,
                                nonvg_set, item, ok, S, GF, bc)
    detail = {"mode": a.mode, "inputs": {"graded": grec,
                                         "results": [ac.input_record(p) for p in a.results],
                                         "hints": ac.input_record(a.hints)},
              "vg_set": vg_set, "vg_cov": vg_cov, "excluded_models": sorted(excluded),
              "exclude_pairs": ac.input_record(a.exclude_pairs) if a.exclude_pairs else None,
              "dropped_pairs": dropped_pairs, "dropped_cells": len(dropped_cells),
              "q48_vocab_rule": vgc.Q48_VOCAB_RULE, "audit_scope": a.audit_scope,
              "a7_39_gold_literal_not_stored": a739}
    if a.graded_ror:
        detail["inputs"]["graded_ror"] = ror_rec
    ac.update_dir_meta(a.out, "analyze_rc1.py", common, detail)
    with open(os.path.join(a.out, "rc1_summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print(f"\n[out] {a.out}/rc1_*.csv" + (" + rc1_decisions.json" if decisions else "") +
          " + rc1_summary.txt + meta.json")


def pooled(frontier, qids, item, S, GF, vg_cov, seed=SEED):
    """H1/H2 numbers on a frontier subset."""
    gf_b = sum(GF(m, "base", vg_cov) for m in frontier)
    gf_v = sum(GF(m, "values", vg_cov) for m in frontier)
    use = [(m, q) for m in frontier for q in qids
           if all((m, arm, lg, q) in item for arm in ("base", "values") for lg in ac.LANGS)]
    use_q = defaultdict(list)
    for m, q in use:
        use_q[q].append(m)

    def gap_item(q, arm):
        return sum(int(item[(m, arm, "en", q)]) - int(item[(m, arm, "th", q)]) for m in use_q.get(q, []))

    gap_b = sum(gap_item(q, "base") for q in qids)
    gap_v = sum(gap_item(q, "values") for q in qids)
    band1, most = h1_band(gf_b, gf_v)
    band2, share = h2_band(gap_b, gap_v)
    lo, hi, n_bad = cluster_bootstrap_share(qids, lambda q: gap_item(q, "values"),
                                            lambda q: gap_item(q, "base"), seed=seed)
    return {"frontier": list(frontier), "gf_b": gf_b, "gf_v": gf_v, "gf_max": 9 * len(frontier),
            "h1_band": band1, "h1_most_or_all": most, "sum_gap_b": gap_b, "sum_gap_v": gap_v,
            "share": float(share) if share is not None else None,
            "share_fraction": f"{share.numerator}/{share.denominator}" if share is not None else None,
            "h2_band": band2, "ci_lo": lo if lo != float("inf") else None,
            "ci_hi": hi, "ci_hi_unbounded": hi is None, "n_resample_den_le0": n_bad,
            "n_boot": N_BOOT, "seed": seed,
            "model_items_without_all_four_cells": len(frontier) * len(qids) - len(use)}


def rc1_section(a, P, models, frontier, qids, vg_cov, vg_set, placebo, nonvg_set,
                item, ok, S, GF, bc):
    descriptive_only = len(frontier) < 2
    main_res = pooled(frontier, qids, item, S, GF, vg_cov)

    # gap per model
    gaprows = []
    for m in models:
        row = {"model": m}
        for arm in ("base", "values"):
            for name, qs in (("all", qids), ("vg_cov", vg_cov),
                             ("rest", [q for q in qids if q not in vg_cov])):
                row[f"gap_{arm}_{name}"] = S(m, arm, "en", qs) - S(m, arm, "th", qs)
        row["exploratory"] = m in LOCAL
        gaprows.append(row)
    gaprows.append({"model": "frontier_pooled", "sum_gap_base": main_res["sum_gap_b"],
                    "sum_gap_values": main_res["sum_gap_v"],
                    "share_remaining": "" if main_res["share"] is None else f"{main_res['share']:.4f}",
                    "ci_lo": "" if main_res["ci_lo"] is None else f"{main_res['ci_lo']:.4f}",
                    "ci_hi": "unbounded" if main_res["ci_hi_unbounded"] else f"{main_res['ci_hi']:.4f}",
                    "n_boot": N_BOOT, "n_resample_den_le0": main_res["n_resample_den_le0"],
                    "h2_band": main_res["h2_band"]})
    write_csv(os.path.join(a.out, "rc1_gap.csv"), gaprows)

    # H3 placebo
    pl, h3_fail = [], []
    flips_frontier = 0
    for m in models:
        for lg in ac.LANGS:
            both = [q for q in placebo if (m, "base", lg, q) in item and (m, "values", lg, q) in item]
            f = sum(1 for q in both if ok(m, "base", lg, q) != ok(m, "values", lg, q))
            passed = f <= PLACEBO_MAX_FLIPS
            pl.append({"model": m, "lang": lg, "placebo_items": len(both), "flips": f,
                       "h3_pass": passed, "exploratory": m in LOCAL})
            if m in frontier:
                flips_frontier += f
                if not passed and m not in h3_fail:
                    h3_fail.append(m)
    write_csv(os.path.join(a.out, "rc1_placebo.csv"), pl)

    # H4 McNemar (TH; EN rows descriptive)
    mc, ps_fr = [], []
    for lg in ("th", "en"):
        for m in models:
            both = [q for q in qids if (m, "base", lg, q) in item and (m, "values", lg, q) in item]
            b = sum(1 for q in both if ok(m, "base", lg, q) and not ok(m, "values", lg, q))
            c = sum(1 for q in both if ok(m, "values", lg, q) and not ok(m, "base", lg, q))
            p = exact_mcnemar(b, c)
            mc.append({"lang": lg, "model": m, "items": len(both), "base_only": b, "values_only": c,
                       "p_exact": f"{p:.4f}", "p_holm_frontier_th": "",
                       "role": ("H4" if (lg == "th" and m in frontier) else "descriptive"),
                       "exploratory": m in LOCAL or lg == "en"})
            if lg == "th" and m in frontier:
                ps_fr.append((len(mc) - 1, p))
    adj = holm([p for _, p in ps_fr])
    m1_models, sig_loss = [], []
    for (i, _), h in zip(ps_fr, adj):
        mc[i]["p_holm_frontier_th"] = f"{h:.4f}"
        if h < HOLM_ALPHA:
            (m1_models if mc[i]["values_only"] > mc[i]["base_only"] else sig_loss).append(mc[i]["model"])
    write_csv(os.path.join(a.out, "rc1_mcnemar.csv"), mc)

    # exclusion variants for M2
    excl = {}
    if h3_fail:
        variants = [[m] for m in h3_fail] + ([h3_fail] if len(h3_fail) > 1 else [])
        for v in variants:
            fr2 = [m for m in frontier if m not in v]
            if fr2:
                excl["without_" + "+".join(v)] = pooled(fr2, qids, item, S, GF, vg_cov)

    # A9 slot values (base arm of this session; D10)
    bcm = {(r["model"], r["arm"]): r for r in bc}
    slots = {"GF_B": main_res["gf_b"], "GF_V": main_res["gf_v"],
             "most|all": main_res["h1_most_or_all"],
             "s": None if main_res["share"] is None else round(main_res["share"], 2),
             "lo": None if main_res["ci_lo"] is None else round(main_res["ci_lo"], 2),
             "hi": "unbounded" if main_res["ci_hi_unbounded"] else round(main_res["ci_hi"], 2),
             "a": bcm[("frontier_total", "base")]["a"], "N": bcm[("frontier_total", "base")]["N"],
             "VG_n": len(vg_set), "k": flips_frontier if h3_fail else None,
             "M1_models": m1_models}
    for i, m in enumerate(A9_ORDER, 1):
        if (m, "base") in bcm:
            slots[f"a{i}"] = bcm[(m, "base")]["a"]
            slots[f"N{i}"] = bcm[(m, "base")]["N"]
            slots[f"g{i}"] = bcm[(m, "base")]["g"]
            en, th = S(m, "base", "en", nonvg_set), S(m, "base", "th", nonvg_set)
            n = len(nonvg_set)
            slots[f"x{i}"] = round(100 * (en - th) / n, 1) if n else None
    band2 = main_res["h2_band"]
    if ABSTRACT_H2_CLAUSE_RULE == "all_but_Gd":
        abstract_clause = band2 != "G-d"
    elif ABSTRACT_H2_CLAUSE_RULE == "rq2_only":
        abstract_clause = False
    else:
        ac.die(2, f"unknown ABSTRACT_H2_CLAUSE_RULE {ABSTRACT_H2_CLAUSE_RULE!r}")
    decisions = {
        "frontier": frontier, "descriptive_only_fewer_than_two_frontier": descriptive_only,
        "h1": {k: main_res[k] for k in ("gf_b", "gf_v", "gf_max", "h1_band", "h1_most_or_all")},
        "h2": {k: main_res[k] for k in ("sum_gap_b", "sum_gap_v", "share", "share_fraction",
                                        "h2_band", "ci_lo", "ci_hi", "ci_hi_unbounded",
                                        "n_resample_den_le0", "n_boot", "seed")},
        "h3": {"max_flips": PLACEBO_MAX_FLIPS, "failing_frontier_models": h3_fail,
               "pass": not h3_fail,
               "flips": {f"{r['model']}|{r['lang']}": r["flips"] for r in pl}},
        "h4": {"holm_over": len(ps_fr), "alpha": HOLM_ALPHA,
               "rows": [r for r in mc if r["role"] == "H4"]},
        "m1": {"active": bool(m1_models), "models": m1_models,
               "significant_loss_models": sig_loss},
        "m2": {"active": bool(h3_fail), "k": flips_frontier if h3_fail else None},
        "h1_h2_without_failing_placebo_models": excl,
        "abstract_h2_clause": {"rule": ABSTRACT_H2_CLAUSE_RULE,
                               "status": ABSTRACT_H2_CLAUSE_STATUS,
                               "include_in_abstract": abstract_clause,
                               "include_in_rq2": band2 != "G-d"},
        "a9_slots": slots,
        "q48_vocab_rule": vgc.Q48_VOCAB_RULE,
    }
    with open(os.path.join(a.out, "rc1_decisions.json"), "w", encoding="utf-8") as fh:
        json.dump(decisions, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")
    P(f"\nH1 frontier pooled TH GF on VG_cov: B={main_res['gf_b']} V={main_res['gf_v']} "
      f"(max {main_res['gf_max']}) -> band {main_res['h1_band']}"
      + (f" ({main_res['h1_most_or_all']})" if main_res["h1_most_or_all"] else "")
      + (" [descriptive only: fewer than two frontier models]" if descriptive_only else ""))
    ci_hi = "unbounded" if main_res["ci_hi_unbounded"] else f"{main_res['ci_hi']:.2f}"
    ci_lo = "n/a" if main_res["ci_lo"] is None else f"{main_res['ci_lo']:.2f}"
    share = "n/a" if main_res["share"] is None else f"{main_res['share']:.2f}"
    P(f"H2 pooled gap B={main_res['sum_gap_b']:+d} V={main_res['sum_gap_v']:+d}; share remaining "
      f"{share} [bootstrap 95%: {ci_lo}, {ci_hi}]; resamples with sum Gap_B <= 0: "
      f"{main_res['n_resample_den_le0']} -> band {main_res['h2_band']}")
    P(f"H3 placebo flips per frontier model x language (<= {PLACEBO_MAX_FLIPS}): " +
      ", ".join(f"{r['model']}|{r['lang']}={r['flips']}" for r in pl if r["model"] in frontier)
      + (f" -> M2 active (failing {h3_fail})" if h3_fail else " -> pass"))
    P("H4 exact McNemar V vs B (TH), Holm over the frontier: " +
      ", ".join(f"{r['model']} b={r['base_only']} c={r['values_only']} p={r['p_exact']} "
                f"holm={r['p_holm_frontier_th']}" for r in mc if r["role"] == "H4")
      + (f" -> M1 for {m1_models}" if m1_models else " -> no M1"))
    P(f"abstract H2 clause ({ABSTRACT_H2_CLAUSE_STATUS}; rule {ABSTRACT_H2_CLAUSE_RULE}): "
      f"{abstract_clause}")
    return decisions


def write_csv(path, rows, header=None):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        if header is None:
            header = []
            for r in rows:
                for k in r:
                    if k not in header:
                        header.append(k)
        w = csv.DictWriter(fh, fieldnames=header)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
