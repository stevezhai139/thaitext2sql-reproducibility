#!/usr/bin/env python3
"""analyze_log_v13.py -- AMENDMENT-7 Part B (pre-specified descriptive; B6 exploratory).

Primary input (D10, AM-7 Part 0): the base arm of the October session
(results/rc1/graded_rc1.csv with --arm base and results_rc1_*.jsonl) on the October core
suite (D11: Q27 repaired and primary, n=60).
Secondary input: the August log re-graded on k3n (results/v13n/graded_v13n.csv and
results/results.jsonl) on the August suite (Q27 excluded, n=59). Same script, same flags;
--arm contract of analyze.py; analyze.d11_check pairs the suite with the graded file.

  B1  loud / silent-empty / silent-non-empty of wrong runs from exec_ok and n_rows of
      the graded file (run level: frontier pooled, per model x language, VG / non-VG;
      local models labelled exploratory; item level: the class of strictly more than
      half of the failing runs of a majority-wrong cell, otherwise 'mixed'; flag
      most_nonempty = silent-non-empty > 50% of frontier error runs, strictly)
  B3  English-Thai gap outside VG10 (the primary items without a VG literal by vg_rule:
      50 on the October core suite, where the repaired Q27 has no VG literal, and 49 on
      the August suite; AM-7 l.511 '50 or 49'): items, points, discordant b/c, exact
      McNemar (exploratory, no Holm)
  B4  SQL text variability per model x language (records without error; normalise:
      strip, collapse whitespace, drop a final ';'; parse_ok False -> <NO_SQL>):
      (a) text-unanimous cells, (b) distinct-SQL count distribution, (c) grade-unanimous
      cells, (d) byte-exact unanimous cells; wording flags
  B5  Q51 from plan_indexed.csv / plan_noindex.csv in --plan-dir (their .meta.json must
      carry the same arm, and their graded input must come from the same session as
      --graded: same file, or the same session fingerprint on every shared item; D10)
  B6  typhoon2-8b vs llama3.1:8b: B1 counts per language, loud runs whose PostgreSQL
      message says a column or function does not exist (analyze.B6_BAD_COLUMN /
      B6_BAD_FUNCTION, shared with analyze_typhoon.py --b6; 'operator does not exist'
      is reported apart), TH VG items wrong; a pair model that is absent is skipped
B1 classes come from analyze.b1_class (a blank n_rows on an executed run stops).
MI items (suite column mi_instances not empty) stay out of B1 (OQ23).
results*.jsonl is read through a hook that keeps model_key, arm, lang, qid, run, sql
and parse_ok and turns 'error' into a boolean.

Usage (Gate 3 step 44):
  python3 -I -B analyze_log_v13.py --graded ../results/rc1/graded_rc1.csv \
    --results ../results/rc1/results_rc1_api.jsonl --results ../results/rc1/results_rc1_local.jsonl \
    --suite ../suite/k3n_suite_v1.3n_oct.tsv --arm base --vg-set ../suite/vg_set_v13n.txt \
    --plan-dir ../results/rc1/base60 --out ../results/rc1/base60/partB
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

FRONTIER = ("claude-sonnet", "gpt-mini", "gemini-flash")
LOCAL = ("qwen25-coder-7b", "llama31-8b", "typhoon2-8b")
PAIR = ("typhoon2-8b", "llama31-8b")
B5_QID = "Q51"
NO_SQL = "<NO_SQL>"
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


def exact_mcnemar(b, c):
    n = b + c
    if n == 0:
        return 1.0
    return min(1.0, 2 * sum(comb(n, k) for k in range(0, min(b, c) + 1)) / 2 ** n)


b1_class = ac.b1_class   # the single B1 implementation (analyze.py)


def item_class(classes):
    cnt = Counter(classes)
    if not cnt:
        return None
    top, n = cnt.most_common(1)[0]
    return top if n > len(classes) / 2 else "mixed"


def most_nonempty(n_nonempty, n_wrong):
    """B1 wording flag: strictly more than 50% of error runs are silent-non-empty."""
    return n_wrong > 0 and n_nonempty * 2 > n_wrong


def normalise_sql(sql, parse_ok):
    if not parse_ok or sql is None:
        return NO_SQL
    s = re.sub(r"\s+", " ", sql.strip())
    return s[:-1].rstrip() if s.endswith(";") else s


def pct(x, n):
    return f"{100 * x / n:.1f}" if n else "n/a"


def main():
    ap = argparse.ArgumentParser(description="AM-7 Part B (B1, B3, B4, B5, B6)")
    ap.add_argument("--graded", required=True)
    ap.add_argument("--results", required=True, action="append")
    ap.add_argument("--suite", required=True)
    ap.add_argument("--vg-set", required=True)
    ap.add_argument("--plan-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--keep-excluded", action="store_true")
    ac.add_arm_contract(ap)
    ac.add_draft_flag(ap)
    a = ap.parse_args()
    suite_rows = ac.load_suite_rows(a.suite)
    ac.draft_guard(a.suite, suite_rows, a.allow_draft_testonly, out_dirs=[a.out])
    rows_all = ac.read_csv_rows(a.graded)
    grec = ac.graded_record(a.graded, rows_all, a.arm)
    ac.d11_check(suite_rows, a.keep_excluded, grec, os.path.basename(a.suite))
    os.makedirs(a.out, exist_ok=True)
    lines = []

    def P(s=""):
        print(s)
        lines.append(s)

    full = ac.primary_suite(suite_rows, a.keep_excluded)
    mi = sorted(k for k, v in full.items() if json.loads((v.get("mi_instances") or "[]") or "[]"))
    suite = {k: v for k, v in full.items() if k not in mi}
    qids = sorted(suite)
    vgs = set(ac.read_vg_set(a.vg_set, universe=full))
    from vg_rule import is_value_grounding
    vg10 = {q for q in qids if is_value_grounding(suite[q]["gold_sql_draft"], suite[q]["question_th"])}
    nonvg10 = [q for q in qids if q not in vg10]

    common = ac.common_meta(a.arm, a.suite, a.keep_excluded, len(qids))
    ac.guard_dir_meta(a.out, common, grec)  # before any output is written
    excluded = ac.split_list(a.exclude_models)
    graded = ac.filter_arm(rows_all, a.arm, excluded)
    models = ac.require_complete(graded, a.runs, sorted(full))
    graded = [r for r in graded if r["qid"] in suite]
    P(f"Part B on arm {a.arm}: {len(qids)} items, models {models}" +
      (f"; MI items out of B1 (OQ23): {mi}" if mi else ""))
    P(f"VG set ({len(vgs)}): {' '.join(sorted(vgs))}; non-VG10 for B3: {len(nonvg10)} items")

    cells = defaultdict(list)
    for r in graded:
        cells[(r["model_key"], r["lang"], r["qid"])].append(r)
    maj = {k: sum(x["correct"] == "True" for x in v) > len(v) / 2 for k, v in cells.items()}

    # ---------------------------------------------------------------- B1
    scopes = {"frontier": [m for m in FRONTIER if m in models],
              "local": [m for m in LOCAL if m in models]}
    for m in models:
        scopes["model:" + m] = [m]
    subsets = {"all": lambda q: True, "vg": lambda q: q in vgs, "nonvg": lambda q: q not in vgs}
    run_rows, item_rows = [], []
    for sname, ms in scopes.items():
        expl = "yes" if sname == "local" or (sname.startswith("model:") and sname[6:] in LOCAL) else "no"
        for lang in ("all", "en", "th"):
            for subn, pred in subsets.items():
                wrong = [r for r in graded if r["model_key"] in ms and r["correct"] != "True"
                         and (lang == "all" or r["lang"] == lang) and pred(r["qid"])]
                c = Counter(b1_class(r) for r in wrong)
                run_rows.append({"scope": sname, "lang": lang, "subset": subn,
                                 "exploratory": expl, "n_wrong_runs": len(wrong),
                                 "loud": c["loud"], "silent_empty": c["silent_empty"],
                                 "silent_nonempty": c["silent_nonempty"],
                                 "silent_total": c["silent_empty"] + c["silent_nonempty"],
                                 "silent_nonempty_pct": pct(c["silent_nonempty"], len(wrong)),
                                 "most_nonempty": most_nonempty(c["silent_nonempty"], len(wrong))})
                ic = Counter()
                for (m, lg, q), rs in cells.items():
                    if m in ms and (lang == "all" or lg == lang) and pred(q) and not maj[(m, lg, q)]:
                        ic[item_class([b1_class(r) for r in rs if r["correct"] != "True"])] += 1
                item_rows.append({"scope": sname, "lang": lang, "subset": subn,
                                  "exploratory": expl, "majority_wrong_cells": sum(ic.values()),
                                  "loud": ic["loud"], "silent_empty": ic["silent_empty"],
                                  "silent_nonempty": ic["silent_nonempty"], "mixed": ic["mixed"]})
    write_csv(os.path.join(a.out, "b1_runs.csv"), run_rows)
    write_csv(os.path.join(a.out, "b1_items.csv"), item_rows)
    fr = next(r for r in run_rows if (r["scope"], r["lang"], r["subset"]) == ("frontier", "all", "all"))
    P(f"\nB1 frontier (run level): {fr['n_wrong_runs']} error runs = loud {fr['loud']} + "
      f"silent-empty {fr['silent_empty']} + silent-non-empty {fr['silent_nonempty']} "
      f"(silent {pct(fr['silent_total'], fr['n_wrong_runs'])}%, non-empty "
      f"{fr['silent_nonempty_pct']}%); wording flag most_nonempty (>50%): {fr['most_nonempty']}")

    # ---------------------------------------------------------------- B3
    b3 = []
    tot = {"en": 0, "th": 0, "b": 0, "c": 0, "n": 0}
    for m in scopes["frontier"]:
        en = sum(maj[(m, "en", q)] for q in nonvg10)
        th = sum(maj[(m, "th", q)] for q in nonvg10)
        b = sum(1 for q in nonvg10 if maj[(m, "en", q)] and not maj[(m, "th", q)])
        c = sum(1 for q in nonvg10 if maj[(m, "th", q)] and not maj[(m, "en", q)])
        n = len(nonvg10)
        b3.append({"model": m, "n_items": n, "en_correct": en, "th_correct": th,
                   "gap_items": en - th, "gap_points": f"{100 * (en - th) / n:+.1f}" if n else "n/a",
                   "b_en_only": b, "c_th_only": c, "p_exact_exploratory": f"{exact_mcnemar(b, c):.4f}"})
        for k, v in (("en", en), ("th", th), ("b", b), ("c", c), ("n", n)):
            tot[k] += v
    if b3:
        b3.append({"model": "frontier_pooled", "n_items": tot["n"], "en_correct": tot["en"],
                   "th_correct": tot["th"], "gap_items": tot["en"] - tot["th"],
                   "gap_points": f"{100 * (tot['en'] - tot['th']) / tot['n']:+.1f}" if tot["n"] else "n/a",
                   "b_en_only": tot["b"], "c_th_only": tot["c"], "p_exact_exploratory": ""})
    write_csv(os.path.join(a.out, "b3_gap_nonvg.csv"), b3)
    P("\nB3 English-Thai gap outside VG10: " +
      ", ".join(f"{r['model']} {r['gap_points']} pts" for r in b3))

    # ---------------------------------------------------------------- B4
    sql_of = {}
    for rec in iter_records(a.results):
        if rec.get("error") or ac.row_arm(rec) != a.arm or rec.get("model_key") in excluded:
            continue
        if rec["qid"] not in suite:
            continue
        k = (rec["model_key"], rec["lang"], rec["qid"], str(rec["run"]))
        if k in sql_of:
            ac.die(2, f"duplicate non-error record {k}")
        sql_of[k] = (rec.get("sql"), bool(rec.get("parse_ok", False)))
    b4, group = [], defaultdict(Counter)
    for m in models:
        for lang in ("en", "th"):
            text_u = byte_u = grade_u = 0
            dist = Counter()
            for q in qids:
                rs = cells[(m, lang, q)]
                texts, raw = [], []
                for r in rs:
                    k = (m, lang, q, str(r["run"]))
                    if k not in sql_of:
                        ac.die(2, f"graded run without a results record: {k}")
                    s, ok = sql_of[k]
                    texts.append(normalise_sql(s, ok))
                    raw.append(s if ok and s is not None else NO_SQL)
                nd = len(set(texts))
                dist[nd] += 1
                text_u += nd == 1
                byte_u += len(set(raw)) == 1
                grade_u += len({r["correct"] for r in rs}) == 1
            n = len(qids)
            row = {"model": m, "lang": lang, "cells": n, "text_unanimous": text_u,
                   "byte_unanimous": byte_u, "grade_unanimous": grade_u,
                   "text_unanimous_pct": pct(text_u, n), "byte_unanimous_pct": pct(byte_u, n),
                   "grade_unanimous_pct": pct(grade_u, n),
                   "exploratory": "yes" if m in LOCAL else "no"}
            for d in range(1, a.runs + 1):
                row[f"distinct_{d}"] = dist[d]
            b4.append(row)
            g = "api" if m in FRONTIER else "local"
            group[g].update({"cells": n, "byte_u": byte_u, "text_u": text_u, "grade_u": grade_u})
            group["model:" + m].update({"cells": n, "grade_u": grade_u})
    write_csv(os.path.join(a.out, "b4_text_variability.csv"), b4)
    diff_graded = [100 - 100 * group["model:" + m]["grade_u"] / group["model:" + m]["cells"]
                   for m in scopes["frontier"] if group["model:" + m]["cells"]]
    P("\nB4: " + "; ".join(f"{g}: byte-exact {v['byte_u']}/{v['cells']}, text {v['text_u']}/"
                         f"{v['cells']}, grade {v['grade_u']}/{v['cells']}"
                         for g, v in group.items() if not g.startswith("model:")))
    for g in ("api", "local"):
        if group[g]["cells"]:
            P(f"  wording: 'bit-stable' allowed for {g}: {group[g]['byte_u'] == group[g]['cells']}")
    if diff_graded:
        P(f"  'a differently graded answer in [x]% of API cells': x from {min(diff_graded):.1f} "
          f"to {max(diff_graded):.1f} across the frontier models")

    # ---------------------------------------------------------------- B5
    b5 = []
    for phase in ("indexed", "noindex"):
        p = os.path.join(a.plan_dir, f"plan_{phase}.csv")
        if not os.path.exists(p):
            P(f"\nB5 {phase}: {os.path.basename(p)} not found; skipped")
            continue
        pmeta = ac.read_meta(p + ".meta.json")
        ac.check_meta_arm(pmeta, a.arm, p + ".meta.json")
        same, why = ac.same_session((pmeta.get("inputs") or {}).get("graded"), grec)
        if not same:
            ac.die(2, f"[D10] {os.path.basename(p)} was computed from another graded input than "
                      f"--graded {os.path.basename(a.graded)} ({why}); B5 refused")
        P(f"\nB5 {phase}: plan csv and --graded from the same session ({why})")
        ratios = defaultdict(list)
        for r in ac.read_csv_rows(p):
            if r["qid"] == B5_QID and r["source"] != "gold" and r["cost_ratio_vs_gold"] \
                    and r["source"] not in excluded:
                ratios[r["source"]].append(float(r["cost_ratio_vs_gold"]))
        beat = sorted(m for m, v in ratios.items() if min(v) < 1.0)
        mn = min((min(v) for v in ratios.values()), default=None)
        b5.append({"phase": phase, "qid": B5_QID, "models_with_cell": len(ratios),
                   "models_beating_gold": len(beat), "which": " ".join(beat),
                   "min_ratio": f"{mn:.2f}" if mn is not None else "",
                   "beats_gold_by_pct": round((1 - mn) * 100) if mn is not None and mn < 1 else 0})
        P(f"\nB5 {phase}: {len(beat)} model(s) beat gold on {B5_QID} "
          f"(min ratio {b5[-1]['min_ratio'] or 'n/a'}, by {b5[-1]['beats_gold_by_pct']}%)")
    write_csv(os.path.join(a.out, "b5_q51.csv"), b5)

    # ---------------------------------------------------------------- B6
    b6 = []
    for m in PAIR:
        if m not in models:
            continue
        for lang in ("en", "th"):
            wrong = [r for r in graded if r["model_key"] == m and r["lang"] == lang
                     and r["correct"] != "True"]
            c = Counter(b1_class(r) for r in wrong)
            flags = [ac.b6_flags(r["fail_reason"]) for r in wrong]
            col = sum(f[0] for f in flags)
            fn = sum(f[1] for f in flags)
            op = sum(f[2] for f in flags)
            shaped = sum(1 for f in flags if f[0] or f[1])
            vg_wrong = sum(1 for q in qids if q in vgs and not maj[(m, lang, q)])
            b6.append({"model": m, "lang": lang, "wrong_runs": len(wrong), "loud": c["loud"],
                       "silent_empty": c["silent_empty"], "silent_nonempty": c["silent_nonempty"],
                       "loud_bad_column": col, "loud_bad_function": fn,
                       "loud_schema_shaped": shaped, "loud_bad_operator_apart": op,
                       "vg_items_wrong": vg_wrong, "vg_items": len(vgs & set(qids)),
                       "exploratory": "yes"})
    write_csv(os.path.join(a.out, "b6_typhoon_llama.csv"), b6)
    t = {r["lang"]: r for r in b6 if r["model"] == PAIR[0]}
    l_ = {r["lang"]: r for r in b6 if r["model"] == PAIR[1]}
    if "th" in t and "th" in l_:
        P(f"\nB6 (exploratory): TH VG items wrong typhoon {t['th']['vg_items_wrong']} vs llama "
          f"{l_['th']['vg_items_wrong']}; 'no harder than the base' allowed: "
          f"{t['th']['vg_items_wrong'] <= l_['th']['vg_items_wrong']}")

    with open(os.path.join(a.out, "partB_summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    detail = {"inputs": {"graded": grec,
                         "results": [ac.input_record(p) for p in a.results],
                         "vg_set": ac.input_record(a.vg_set)},
              "runs": a.runs, "excluded_models": sorted(excluded), "mi_items_out": mi,
              "files": ["b1_runs.csv", "b1_items.csv", "b3_gap_nonvg.csv",
                        "b4_text_variability.csv", "b5_q51.csv", "b6_typhoon_llama.csv",
                        "partB_summary.txt"]}
    ac.update_dir_meta(a.out, "analyze_log_v13.py", common, detail)
    print(f"[out] {a.out}/b1..b6 + partB_summary.txt + meta.json")


def write_csv(path, rows):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        if not rows:
            fh.write("")
            return
        keys = list(rows[0].keys())
        for r in rows[1:]:
            for k in r:
                if k not in keys:
                    keys.append(k)
        w = csv.DictWriter(fh, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
