#!/usr/bin/env python3
"""transitions_v13n.py -- the August log in three steps (secondary data under D10):
  k3/v1.2  (results/graded.csv, the submitted grading)
  -> k3n/v1.2  (grade_v13n.py --legacy on k3n: the data change alone)
  -> k3n/v1.3n (grade_v13n.py on k3n: the key change)
so that the change of data (None -> NULL) is separated from the change of key.
From kst_rev/wf_d7/tools/transitions_v13.py; changes: three files instead of one,
--arm base is required (the August log has one arm), the majority threshold comes from
the number of runs of each cell (no fixed '>= 3'), excluded items come from the suite
(no hard-coded Q27; they are reported apart and kept out of the item-level counts), and
the output must be under results/v13n/ (secondary data; a path component 'v13n').
D11: the three files are gradings of the August log, so --suite must be the August suite
(analyze.suite_session 'august': Q27 excluded, the original question); the October core
suite (Q27 repaired) is refused.

Outputs in --out: transitions_runs.csv (per model x language x step: runs wrong->correct
and correct->wrong, majority cells wrong->correct and correct->wrong), transitions_cells.csv
(every cell that changes in a step), transitions_summary.txt, meta.json.

Usage (Gate 2 step 23):
  python3 -I -B transitions_v13n.py --k3-v12 ../results/graded.csv \
    --k3n-v12 ../results/v13n/graded_v12_on_k3n.csv --k3n-v13n ../results/v13n/graded_v13n.csv \
    --suite ../suite/k3n_suite_v1.3n.tsv --arm base --out ../results/v13n/transitions
"""
import argparse
import csv
import os
import sys
from collections import defaultdict

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402

STEPS = (("data", "k3_v12", "k3n_v12"), ("key", "k3n_v12", "k3n_v13n"))


def load(path, arm, excluded, label):
    rows = ac.filter_arm(ac.read_csv_rows(path), arm, excluded, label)
    d = {}
    for r in rows:
        k = (r["model_key"], r["lang"], r["qid"], str(r["run"]))
        if k in d:
            ac.die(2, f"{label}: duplicate run {k}")
        d[k] = r["correct"] == "True"
    return d


def main():
    ap = argparse.ArgumentParser(description="three-step transitions of the August log")
    ap.add_argument("--k3-v12", required=True)
    ap.add_argument("--k3n-v12", required=True)
    ap.add_argument("--k3n-v13n", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--arm", required=True, choices=["base"])
    ap.add_argument("--exclude-models", default="")
    ap.add_argument("--out", required=True)
    ac.add_draft_flag(ap)
    a = ap.parse_args()
    parts = os.path.normpath(os.path.abspath(a.out)).split(os.sep)
    if "v13n" not in parts:
        ac.die(2, "--out must be under results/v13n/ (secondary data, D10)")
    suite = ac.load_suite_rows(a.suite)
    ac.draft_guard(a.suite, suite, a.allow_draft_testonly, out_dirs=[a.out])
    session = ac.suite_session(suite, os.path.basename(a.suite))
    if session != ac.SESSION_AUG:
        ac.die(2, f"[D11] transitions of the August log need the August suite (repaired items "
                  f"{list(ac.D11_REPAIRED)} excluded); {os.path.basename(a.suite)} is of session "
                  f"{session!r}")
    print(f"[D11] August suite: {', '.join(ac.D11_REPAIRED)} excluded (n=59)")
    os.makedirs(a.out, exist_ok=True)
    primary = set(ac.primary_suite(suite, False))
    excl_items = sorted(set(suite) - primary)
    excluded = ac.split_list(a.exclude_models)
    meta_common = ac.common_meta(a.arm, a.suite, False, len(primary))
    ac.guard_dir_meta(a.out, meta_common)  # before any output is written
    G = {"k3_v12": load(a.k3_v12, a.arm, excluded, "k3/v1.2"),
         "k3n_v12": load(a.k3n_v12, a.arm, excluded, "k3n/v1.2"),
         "k3n_v13n": load(a.k3n_v13n, a.arm, excluded, "k3n/v1.3n")}

    run_rows, cell_rows, lines = [], [], []
    for step, src, dst in STEPS:
        common = sorted(set(G[src]) & set(G[dst]))
        only = (len(G[src]) - len(common), len(G[dst]) - len(common))
        per = defaultdict(lambda: [0, 0])
        cells = defaultdict(lambda: ([], []))
        for k in common:
            m, lg, q, run = k
            x, y = G[src][k], G[dst][k]
            if y and not x:
                per[(m, lg)][0] += 1
            if x and not y:
                per[(m, lg)][1] += 1
            cells[(m, lg, q)][0].append(x)
            cells[(m, lg, q)][1].append(y)
        mw2c = defaultdict(int)
        mc2w = defaultdict(int)
        for (m, lg, q), (xs, ys) in sorted(cells.items()):
            if q not in primary:
                continue
            ma, mb = sum(xs) > len(xs) / 2, sum(ys) > len(ys) / 2
            if ma != mb or sum(xs) != sum(ys):
                cell_rows.append({"step": step, "model": m, "lang": lg, "qid": q,
                                  "runs": len(xs), f"correct_before": sum(xs),
                                  "correct_after": sum(ys),
                                  "majority": "W->C" if mb and not ma else ("C->W" if ma and not mb else "")})
            mw2c[(m, lg)] += mb and not ma
            mc2w[(m, lg)] += ma and not mb
        keys = sorted(set(per) | set(mw2c) | set(mc2w))
        for k in keys:
            run_rows.append({"step": step, "from": src, "to": dst, "model": k[0], "lang": k[1],
                             "runs_w2c": per[k][0], "runs_c2w": per[k][1],
                             "cells_w2c": mw2c[k], "cells_c2w": mc2w[k]})
        tot = [sum(v[0] for v in per.values()), sum(v[1] for v in per.values()),
               sum(mw2c.values()), sum(mc2w.values())]
        lines.append(f"step {step} ({src} -> {dst}): runs compared {len(common)} "
                     f"(only in {src} {only[0]}, only in {dst} {only[1]}); runs w->c {tot[0]}, "
                     f"c->w {tot[1]}; majority cells on primary items w->c {tot[2]}, c->w {tot[3]}")
    lines.append(f"excluded items (from the suite; not in the item-level counts): {excl_items or 'none'}")
    for p, rows in (("transitions_runs.csv", run_rows), ("transitions_cells.csv", cell_rows)):
        with open(os.path.join(a.out, p), "w", newline="", encoding="utf-8") as fh:
            keys = []
            for r in rows:
                for k in r:
                    if k not in keys:
                        keys.append(k)
            w = csv.DictWriter(fh, fieldnames=keys or ["step"])
            w.writeheader()
            w.writerows(rows)
    with open(os.path.join(a.out, "transitions_summary.txt"), "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    print("\n".join(lines))
    detail = {"inputs": {"k3_v12": ac.input_record(a.k3_v12), "k3n_v12": ac.input_record(a.k3n_v12),
                         "k3n_v13n": ac.input_record(a.k3n_v13n)},
              "excluded_items": excl_items, "excluded_models": sorted(excluded)}
    ac.update_dir_meta(a.out, "transitions_v13n.py", meta_common, detail)


if __name__ == "__main__":
    main()
