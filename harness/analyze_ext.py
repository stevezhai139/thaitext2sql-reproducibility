#!/usr/bin/env python3
"""analyze_ext.py -- descriptive analysis of the 40-item extension (AMENDMENT-9; base arm
only; exploratory/descriptive and reported in every direction; not part of H1-H4).

Inputs: graded_ext.csv (grade_v13n.py with --mi-manifest), its MI sidecar (--mi-log),
the positional (--colperm off) and no-col-roles (--no-col-roles) gradings, and the frozen
extension suite. --arm base is required (any other arm is refused). Stops when a family
is blank or not one of F1-F10, when one of F1-F10 has no item (design 2.6: stop when a
family is empty), when the number of items is not 40 or a cell does not have --runs (5)
runs. Items
are excluded only through v13_status of the suite: an empty gold never drops an item
(FK1 stays). A suite marked DRAFT is refused unless --allow-draft-testonly and --out
lies outside results/ (tests only).

Outputs in --out
  ext_accuracy.csv      accuracy per model x language (item majority, Wilson 95%)
  ext_family.csv        correct items per family F1-F10 per model x language
  ext_mcnemar.csv       EN-TH discordant b/c and exact McNemar per model (no Holm)
  ext_silent.csv        B1 loud / silent-empty / silent-non-empty on non-MI items
                        (analyze.b1_class; a blank n_rows on an executed run stops); MI
                        items apart (OQ23: their n_rows is the base instance only)
  ext_mi_instances.csv  per MI item x model x language: failing runs per instance, runs
                        that fail ONLY at that instance, runs that did not execute, and
                        runs that fail although every instance has a matching key, split
                        into key mismatch (no single key matches on every instance) and
                        permutation mismatch (one key matches everywhere, but with no
                        common column permutation) (MI-1b)
                        The MI-1b verdict is recomputed from the sidecar (keys_matched and
                        perms_by_label of every instance) and must equal the graded
                        verdict of every run; keys_matched must agree with perms_by_label
                        on every instance row. Any disagreement stops (exit 2).
  ext_positional.csv    item-level correct counts under primary, positional and no-col-roles
  ext_directional.csv   the directional items (non-empty col_roles) under the three gradings
  ext_vg_classes.csv    (with --results and --hints) B2.3 classes of failing TH runs on the
                        VG items of the extension (descriptive; OQ29.3)
  ext_pooled100.csv     (with --core-graded/--core-suite; POOLED_100_STATUS) core 60 + 40
                        = 100 items (D11: the October core suite, Q27 repaired and primary;
                        --core-suite must be of analyze.suite_session 'october');
                        --core-graded must be the two-arm October core log (graded_rc1.csv:
                        both arms base and values in the file; D10: the August re-grade is
                        never pooled with October data), recorded in meta.json
  ext_summary.txt, meta.json

Usage (Gate 3 step 58):
  python3 -I -B analyze_ext.py --graded ../results/ext/graded_ext.csv \
    --mi-log ../results/ext/graded_ext_mi.csv --graded-positional ../results/ext/graded_ext_positional.csv \
    --graded-nocolroles ../results/ext/graded_ext_nocolroles.csv \
    --suite ../suite/k3n_ext_suite_v1.0.tsv --arm base --out ../results/ext/tables
"""
import argparse
import csv
import json
import os
import re
import sys
from collections import Counter, defaultdict
from math import comb

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402

EXPECTED_ITEMS = 40
FAMILIES = [f"F{i}" for i in range(1, 11)]
# OQ29.3 / OQ29.4: the VG items of the extension by vg_rule on the final Thai text
# (TEST-ONLY expectation from the extsuite inventory); --expect-vg overrides.
EXPECTED_EXT_VG = ["F7C-1", "F7C-2", "F7C-3", "X10", "X26", "X27"]
# ------------------------------------------------------------------------ DECIDED (OQ29.2)
# OQ29.2 (GENUINE; answered by the author on 14 Oct 2026, brief 1.0c): option (a). Status of
# the pooled result, 100 items under D11 (core 60 with the repaired Q27 + extension 40):
#   "sensitivity" -- option (a), DECIDED: pre-declared sensitivity, every direction,
#                    never used to raise a claim (accuracy x language + exact McNemar)
#   "secondary"   -- option (b): registered secondary analysis (adds Holm across models)
#   "off"         -- option (c): no pooling
POOLED_100_STATUS = "sensitivity"   # DECIDED (OQ29.2): option (a), author 14 Oct 2026
POOLED_100_STATUSES = ("sensitivity", "secondary", "off")
# record of the answer (not a switch): the switch is POOLED_100_STATUS above
POOLED_100_DECISION = "OQ29.2 answered by the author on 14 Oct 2026: option (a) = 'sensitivity'"
POOLED_ITEMS = 100   # D11: core 60 (October core suite) + extension 40
# ----------------------------------------------------------------------------------------
FRONTIER = ("claude-sonnet", "gpt-mini", "gemini-flash")
LOCAL = ("qwen25-coder-7b", "llama31-8b", "typhoon2-8b")
_KEEP = ("model_key", "arm", "lang", "qid", "run", "sql", "parse_ok")


def exact_mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n)


def parse_list(v):
    """keys_matched of the MI sidecar: JSON list or a ';'/','/'|' separated string."""
    v = (v or "").strip()
    if not v or v in ("[]", "{}", "None", "-"):
        return []
    if v.startswith("["):
        try:
            return [str(x) for x in json.loads(v) if str(x).strip()]
        except json.JSONDecodeError:
            pass
    return [x.strip() for x in re.split(r"[;,|]", v) if x.strip()]


def parse_perms(v, where):
    """perms_by_label of the MI sidecar -> {label: None ('any') or set of tuples}."""
    v = (v or "").strip()
    if not v:
        return {}
    try:
        d = json.loads(v)
    except json.JSONDecodeError:
        ac.die(2, f"MI sidecar: perms_by_label is not JSON at {where}")
    if not isinstance(d, dict):
        ac.die(2, f"MI sidecar: perms_by_label is not an object at {where}")
    out = {}
    for lb, p in d.items():
        if p == "any":
            out[str(lb)] = None
        elif isinstance(p, list):
            out[str(lb)] = {tuple(int(i) for i in t) for t in p}
        else:
            ac.die(2, f"MI sidecar: perms_by_label value of {lb!r} is neither 'any' nor a list at {where}")
    return out


def perms_ok(p):
    """same meaning as grade_v13n.perms_ok: None ('any') or a non-empty set matches."""
    return p is None or bool(p)


def mi_verdict(inst_rows, instances, where):
    """MI-1b recomputed from the sidecar rows of ONE run (grade_v13n.mi_intersection):
    returns (verdict, bad) with verdict in correct / not_executed / no_key_at_instance /
    key_mismatch / perm_mismatch and bad = instances without any matching key (or that
    did not run, or have no sidecar row)."""
    per, bad, ran_all = [], [], True
    for i in instances:
        r = inst_rows.get(i)
        if r is None or r.get("executed") != "True":
            bad.append(i)
            ran_all = False
            continue
        perms = parse_perms(r.get("perms_by_label"), f"{where} {i}")
        ok_labels = {lb for lb, x in perms.items() if perms_ok(x)}
        km = set(parse_list(r.get("keys_matched")))
        if km != ok_labels:
            ac.die(2, f"MI sidecar: keys_matched {sorted(km)} disagrees with perms_by_label "
                      f"{sorted(ok_labels)} at {where} {i}")
        if not ok_labels:
            bad.append(i)
        per.append(perms)
    if not ran_all:
        return "not_executed", bad
    if bad:
        return "no_key_at_instance", bad
    labels = sorted(set().union(*[set(p) for p in per])) if per else []
    common = [lb for lb in labels if all(perms_ok(p.get(lb, set())) for p in per)]
    if not common:
        return "key_mismatch", bad
    for lb in common:
        inter = None
        for p in per:
            x = p.get(lb)
            if x is None:
                continue
            inter = set(x) if inter is None else inter & x
        if inter is None or inter:
            return "correct", bad
    return "perm_mismatch", bad


def majority(rows):
    cells = defaultdict(list)
    for r in rows:
        cells[(r["model_key"], r["lang"], r["qid"])].append(r["correct"] == "True")
    return {k: sum(v) > len(v) / 2 for k, v in cells.items()}


def load_graded(path, arm, excluded, runs, qids, label):
    rows = ac.filter_arm(ac.read_csv_rows(path), arm, excluded, label)
    rows = [r for r in rows if r["qid"] in qids]
    models = ac.require_complete(rows, runs, sorted(qids), label)
    return rows, models


def write(path, rows):
    keys = []
    for r in rows:
        for k in r:
            if k not in keys:
                keys.append(k)
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=keys or ["empty"])
        w.writeheader()
        w.writerows(rows)


def _hook(pairs):
    d = {}
    for k, v in pairs:
        if k == "error":
            d["error"] = v is not None
        elif k in _KEEP:
            d[k] = v
    return d


def main():
    ap = argparse.ArgumentParser(description="extension analysis (AM-9, descriptive)")
    ap.add_argument("--graded", required=True)
    ap.add_argument("--mi-log", required=True)
    ap.add_argument("--graded-positional", required=True)
    ap.add_argument("--graded-nocolroles", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--arm", required=True, choices=["base"])
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--exclude-models", default="")
    ap.add_argument("--out", required=True)
    ap.add_argument("--expect-vg", help="comma list; default EXPECTED_EXT_VG")
    ap.add_argument("--core-graded", help="graded_rc1.csv (pooled 100, OQ29.2)")
    ap.add_argument("--core-suite", help="October core suite k3n_suite_v1.3n_oct.tsv (pooled 100, D11)")
    ap.add_argument("--results", action="append", default=[], help="ext jsonl (VG classes)")
    ap.add_argument("--hints", help="value_hints_v1.json (vocabulary of the VG classes)")
    ap.add_argument("--hints-sha256")
    ap.add_argument("--allow-draft-testonly", action="store_true")
    a = ap.parse_args()
    if POOLED_100_STATUS not in POOLED_100_STATUSES:
        ac.die(2, f"unknown POOLED_100_STATUS {POOLED_100_STATUS!r} (one of {POOLED_100_STATUSES})")
    lines = []

    def P(s=""):
        print(s)
        lines.append(str(s))

    suite = ac.load_suite_rows(a.suite)
    draft = ac.draft_guard(a.suite, suite, a.allow_draft_testonly, out_dirs=[a.out])
    if a.core_suite:
        core_rows = ac.load_suite_rows(a.core_suite)
        ac.draft_guard(a.core_suite, core_rows, a.allow_draft_testonly, out_dirs=[a.out])
        cs = ac.suite_session(core_rows, os.path.basename(a.core_suite))
        if cs != ac.SESSION_OCT:
            ac.die(2, f"[D11] --core-suite {os.path.basename(a.core_suite)} is of session {cs!r}; the "
                      f"pooled 100 uses the October core suite (repaired items "
                      f"{list(ac.D11_REPAIRED)} primary)")
    if draft:
        P("DRAFT suite accepted for a TEST-ONLY run")
    items = ac.primary_suite(suite, False)
    if len(items) != EXPECTED_ITEMS:
        ac.die(2, f"{len(items)} analysed items, expected {EXPECTED_ITEMS}")
    blank = [q for q, r in items.items() if not (r.get("family") or "").strip()]
    if blank:
        ac.die(2, f"items with a blank family: {blank}")
    fam_of = {q: r["family"].strip() for q, r in items.items()}
    unknown = sorted(q for q, f in fam_of.items() if f not in FAMILIES)
    if unknown:
        ac.die(2, f"items with a family outside {FAMILIES[0]}-{FAMILIES[-1]}: "
                  f"{[(q, fam_of[q]) for q in unknown]}")
    empty_fam = [f for f in FAMILIES if f not in set(fam_of.values())]
    if empty_fam:
        ac.die(2, f"families without any item: {empty_fam} (design 2.6: stop when a family is empty)")
    core_rec = None
    if a.core_graded:   # D10: the pooled core rows come from the two-arm October core log only
        core_all = ac.read_csv_rows(a.core_graded)
        core_rec = ac.graded_record(a.core_graded, core_all, a.arm)
        if not set(ac.TWO_ARMS) <= set(core_rec["arms_in_file"]):
            ac.die(2, f"[D10] --core-graded {ac.describe(core_rec)} is not the two-arm October core "
                      f"log; the August re-grade is never pooled with October data (pooled 100, OQ29.2)")
        print(f"[D10] --core-graded: {ac.describe(core_rec)}")
    pooled_core = None
    if a.core_graded and POOLED_100_STATUS != "off":   # pooled 100 inputs, checked before any output
        if not a.core_suite:
            ac.die(2, "--core-graded needs --core-suite")
        pooled_core = ac.primary_suite(core_rows, False)
        overlap = set(pooled_core) & set(items)
        if overlap:
            ac.die(2, f"core and extension ids overlap: {sorted(overlap)}")
        if len(pooled_core) + len(items) != POOLED_ITEMS:
            ac.die(2, f"[D11] pooled set of {len(pooled_core)} core + {len(items)} extension items; "
                      f"expected {POOLED_ITEMS} (core 60 on the October core suite + 40)")
        print(f"[D11] pooled {POOLED_ITEMS}: core {len(pooled_core)} (October core suite, "
              f"{', '.join(ac.D11_REPAIRED)} repaired and primary) + extension {len(items)}")
    qids = set(items)
    order = list(items)
    os.makedirs(a.out, exist_ok=True)
    common = ac.common_meta(a.arm, a.suite, False, len(order))
    grec = ac.graded_record(a.graded, ac.read_csv_rows(a.graded), a.arm)
    ac.guard_dir_meta(a.out, common, grec)  # before any output is written
    excluded = ac.split_list(a.exclude_models)

    graded, models = load_graded(a.graded, a.arm, excluded, a.runs, qids, "graded")
    pos, _ = load_graded(a.graded_positional, a.arm, excluded, a.runs, qids, "positional")
    ncr, _ = load_graded(a.graded_nocolroles, a.arm, excluded, a.runs, qids, "no-col-roles")
    item, item_pos, item_ncr = majority(graded), majority(pos), majority(ncr)
    models = [m for m in FRONTIER + LOCAL if m in models] + sorted(set(models) - set(FRONTIER + LOCAL))
    mi_items = [q for q in order if json.loads((items[q].get("mi_instances") or "[]") or "[]")]
    directional = [q for q in order if (items[q].get("col_roles") or "").strip()]
    P(f"extension: {len(order)} items, models {models}; MI {mi_items}; directional {directional}")

    exp_vg = sorted(ac.split_list(a.expect_vg)) if a.expect_vg else sorted(EXPECTED_EXT_VG)
    vg = sorted(q for q in order if (items[q].get("vg") or "").strip().lower() == "yes")
    if vg != exp_vg:
        ac.die(2, f"VG items of the suite {vg} differ from the expected {exp_vg} (OQ29.4)")

    # accuracy, family, McNemar
    acc, fam, mc = [], [], []
    for m in models:
        for lg in ac.LANGS:
            c = sum(item[(m, lg, q)] for q in order)
            p, lo, hi = ac.wilson(c, len(order))
            acc.append({"model": m, "lang": lg, "correct": c, "n": len(order), "acc": f"{p:.3f}",
                        "ci_lo": f"{lo:.3f}", "ci_hi": f"{hi:.3f}", "exploratory": True})
            for f in FAMILIES:
                fq = [q for q in order if items[q]["family"].strip() == f]
                fam.append({"model": m, "lang": lg, "family": f, "n_items": len(fq),
                            "correct": sum(item[(m, lg, q)] for q in fq)})
        b = sum(1 for q in order if item[(m, "en", q)] and not item[(m, "th", q)])
        c = sum(1 for q in order if item[(m, "th", q)] and not item[(m, "en", q)])
        mc.append({"model": m, "en_correct": sum(item[(m, "en", q)] for q in order),
                   "th_correct": sum(item[(m, "th", q)] for q in order), "b_en_only": b,
                   "c_th_only": c, "p_exact": f"{exact_mcnemar(b, c):.4f}",
                   "holm": "not applied (exploratory)"})
    fam_n = Counter(items[q]["family"].strip() for q in order)
    P("families: " + ", ".join(f"{f}={fam_n[f]}" for f in FAMILIES) + f" (sum {sum(fam_n.values())})")
    write(os.path.join(a.out, "ext_accuracy.csv"), acc)
    write(os.path.join(a.out, "ext_family.csv"), fam)
    write(os.path.join(a.out, "ext_mcnemar.csv"), mc)

    # B1 on non-MI items; MI items apart
    sil = []
    for m in models:
        for lg in ac.LANGS:
            cnt = Counter()
            mi_wrong = 0
            for r in graded:
                if r["model_key"] != m or r["lang"] != lg or r["correct"] == "True":
                    continue
                if r["qid"] in mi_items:
                    mi_wrong += 1
                    continue
                cnt[ac.b1_class(r)] += 1
            sil.append({"model": m, "lang": lg, "loud": cnt["loud"], "silent_empty": cnt["silent_empty"],
                        "silent_nonempty": cnt["silent_nonempty"], "mi_wrong_runs_apart": mi_wrong})
    write(os.path.join(a.out, "ext_silent.csv"), sil)

    # MI per instance
    side = [r for r in ac.read_csv_rows(a.mi_log)
            if ac.row_arm(r) == a.arm and r["model_key"] not in excluded]
    inst_of = {q: json.loads(items[q]["mi_instances"]) for q in mi_items}
    by_run = defaultdict(dict)
    for r in side:
        by_run[(r["model_key"], r["lang"], r["qid"], str(r["run"]))][r["instance"]] = r
    wrong_run = {(r["model_key"], r["lang"], r["qid"], str(r["run"])): r["correct"] != "True"
                 for r in graded if r["qid"] in mi_items}
    mir, disagree = [], []
    for q in mi_items:
        for m in models:
            for lg in ac.LANGS:
                ks = [k for k in wrong_run if k[:3] == (m, lg, q)]
                failed_at = Counter()
                only_at = Counter()
                verdicts = Counter()
                for k in ks:
                    inst = by_run.get(k, {})
                    unknown = set(inst) - set(inst_of[q])
                    if unknown:
                        ac.die(2, f"MI sidecar has instances outside the suite for {k}: {sorted(unknown)}")
                    # an instance without a sidecar row did not run (parse failure, or the
                    # base failed to execute: grade_v13n then logs the base row only)
                    verdict, bad = mi_verdict(inst, inst_of[q], k)
                    if (verdict == "correct") == wrong_run[k]:
                        disagree.append((k, "graded wrong" if wrong_run[k] else "graded correct",
                                         verdict))
                    for i in bad:
                        failed_at[i] += 1
                    if wrong_run[k]:
                        verdicts[verdict] += 1
                        if len(bad) == 1:
                            only_at[bad[0]] += 1
                for i in inst_of[q]:
                    mir.append({"qid": q, "model": m, "lang": lg, "instance": i, "runs": len(ks),
                                "runs_wrong": sum(wrong_run[k] for k in ks),
                                "runs_failed_at_instance": failed_at[i],
                                "runs_failing_only_here": only_at[i],
                                "runs_not_executed": verdicts["not_executed"],
                                "runs_wrong_by_key_mismatch": verdicts["key_mismatch"],
                                "runs_wrong_by_perm_mismatch": verdicts["perm_mismatch"]})
    if disagree:
        ac.die(2, f"MI-1b verdict recomputed from the sidecar differs from the graded verdict in "
                  f"{len(disagree)} runs (first {disagree[:3]}); sidecar and graded file of "
                  f"different gradings?")
    write(os.path.join(a.out, "ext_mi_instances.csv"), mir)
    P(f"MI-1b verdicts recomputed from the sidecar agree with the graded file "
      f"({sum(len([k for k in wrong_run if k[2] == q]) for q in mi_items)} MI runs)")

    # positional / no-col-roles sensitivity
    pr, dr = [], []
    for m in models:
        for lg in ac.LANGS:
            pr.append({"model": m, "lang": lg,
                       "primary": sum(item[(m, lg, q)] for q in order),
                       "positional": sum(item_pos[(m, lg, q)] for q in order),
                       "no_col_roles": sum(item_ncr[(m, lg, q)] for q in order), "n": len(order)})
            for q in directional:
                dr.append({"qid": q, "col_roles": items[q]["col_roles"], "model": m, "lang": lg,
                           "primary": item[(m, lg, q)], "positional": item_pos[(m, lg, q)],
                           "no_col_roles": item_ncr[(m, lg, q)]})
    write(os.path.join(a.out, "ext_positional.csv"), pr)
    write(os.path.join(a.out, "ext_directional.csv"), dr)

    # VG classes (descriptive; OQ29.3)
    if a.results and a.hints:
        import vg_classifier as vgc
        hints, _ = vgc.load_hints(a.hints, a.hints_sha256)
        targets = {q: vgc.item_targets(items[q]) for q in vg}
        vocab = vgc.build_vocab(hints, gold_targets=[t for q in vg for t in targets[q]])
        need = {(r["model_key"], r["lang"], r["qid"], str(r["run"])) for r in graded
                if r["qid"] in vg and r["lang"] == "th" and r["correct"] != "True"}
        sql_of = {}
        for p in a.results:
            with open(p, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    rec = json.loads(line, object_pairs_hook=_hook)
                    if rec.get("error") or ac.row_arm(rec) != a.arm:
                        continue
                    k = (rec.get("model_key"), rec.get("lang"), rec.get("qid"), str(rec.get("run")))
                    if k in need:
                        sql_of[k] = (rec.get("sql") or "") if rec.get("parse_ok") else ""
        lost = need - set(sql_of)
        if lost:
            ac.die(2, f"{len(lost)} failing VG runs have no results record")
        vr = []
        for m in models:
            for q in vg:
                fails = [r for r in graded if r["model_key"] == m and r["lang"] == "th"
                         and r["qid"] == q and r["correct"] != "True"]
                cls = [vgc.classify_run(sql_of[(m, "th", q, str(r["run"]))], targets[q], vocab) for r in fails]
                cc = Counter(cls)
                vr.append({"model": m, "qid": q, "majority_wrong": not item[(m, "th", q)],
                           "n_fail": len(fails), **{c: cc[c] for c in vgc.CLASSES},
                           "gf_descriptive": vgc.is_gf_cell(True, not item[(m, "th", q)], cls)})
        write(os.path.join(a.out, "ext_vg_classes.csv"), vr)
        P(f"VG classes written for {len(vg)} VG items (descriptive, OQ29.3)")
    else:
        P("VG classes skipped (give --results and --hints for OQ29.3)")

    # pooled 100 (OQ29.2; D11: core 60 with the repaired Q27 + extension 40)
    if pooled_core is not None:
        core = pooled_core
        crows, cmodels = load_graded(a.core_graded, a.arm, excluded, a.runs, set(core), "core")
        citem = majority(crows)
        allq = sorted(core) + order
        pooled, ps = [], []
        for m in [x for x in models if x in cmodels]:
            def ok(lg, q):
                return citem[(m, lg, q)] if q in core else item[(m, lg, q)]
            row = {"model": m, "n_items": len(allq), "status": POOLED_100_STATUS,
                   "decision": POOLED_100_DECISION}
            for lg in ac.LANGS:
                c = sum(ok(lg, q) for q in allq)
                p, lo, hi = ac.wilson(c, len(allq))
                row.update({f"{lg}_correct": c, f"{lg}_acc": f"{p:.3f}",
                            f"{lg}_ci_lo": f"{lo:.3f}", f"{lg}_ci_hi": f"{hi:.3f}"})
            b = sum(1 for q in allq if ok("en", q) and not ok("th", q))
            c = sum(1 for q in allq if ok("th", q) and not ok("en", q))
            row.update({"b_en_only": b, "c_th_only": c, "p_exact": f"{exact_mcnemar(b, c):.4f}"})
            ps.append(exact_mcnemar(b, c))
            pooled.append(row)
        if POOLED_100_STATUS == "secondary":
            for r, h in zip(pooled, ac.holm(ps)):
                r["p_holm"] = f"{h:.4f}"
        write(os.path.join(a.out, "ext_pooled100.csv"), pooled)
        P(f"pooled {len(allq)} items written as '{POOLED_100_STATUS}' ({POOLED_100_DECISION})")
    elif a.core_graded:
        P(f"pooled 100 not computed: POOLED_100_STATUS = off ({POOLED_100_DECISION})")

    with open(os.path.join(a.out, "ext_summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    detail = {"inputs": {"graded": grec, "mi_log": ac.input_record(a.mi_log),
                         "graded_positional": ac.input_record(a.graded_positional),
                         "graded_nocolroles": ac.input_record(a.graded_nocolroles)},
              "runs": a.runs, "excluded_models": sorted(excluded), "mi_items": mi_items,
              "directional": directional, "vg": vg, "pooled_100_status": POOLED_100_STATUS,
              "draft_suite": draft}
    if a.core_graded:
        detail["inputs"]["core_graded"] = core_rec
        detail["inputs"]["core_suite"] = ac.input_record(a.core_suite) if a.core_suite else None
    ac.update_dir_meta(a.out, "analyze_ext.py", common, detail)
    print(f"[out] {a.out}/ext_*.csv + ext_summary.txt + meta.json")


if __name__ == "__main__":
    main()
