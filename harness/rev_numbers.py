"""Revision numbers that were so far assistant counts (KST revision, checkpoint 1, 22 Oct 2026).

Read-only over existing graded files; writes a new output folder only.
(1) graded generations (core two arms + extension) — C17 '9,598'
(2) extension, free-tier proxies: failed runs on single-instance items split loud / silent-empty /
    silent-non-empty, loud runs truncated by the output cap, failed multi-instance runs — N19, I-4, II-1
(3) typhoon2-8b extension item majorities (runs present, Wilson 95%) — Table II Ext. cell, ADD-T2
(4) claude-sonnet extension cells truncated by the 1,024-token cap and items whose majority depends on them — ADD-K2, C53
(5) decomposition of headline counts: submitted key v1.2 (n=60) -> August regrade v1.3n (n=59) -> October (n=60) — A-1
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
from collections import defaultdict

FRONTIER = ("claude-sonnet", "gpt-mini", "gemini-flash")
MI_ITEMS = ("PK1", "FK1", "FK2")
CAP = 1024


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def rows(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def wilson(k, n, z=1.959963984540054):
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


def is_true(v):
    return str(v) == "True"


def write_csv(path, header, data):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(data)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graded-rc1", required=True)
    ap.add_argument("--graded-ext", required=True)
    ap.add_argument("--results-ext-api", required=True)
    ap.add_argument("--acc-v12", required=True)
    ap.add_argument("--acc-v13n", required=True)
    ap.add_argument("--acc-oct", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"refuse: {a.out} exists")
    os.makedirs(a.out)
    summary = []

    # (1) graded generations
    rc1 = rows(a.graded_rc1)
    ext = rows(a.graded_ext)
    by_arm = defaultdict(int)
    for r in rc1:
        by_arm[r["arm"]] += 1
    total = len(rc1) + len(ext)
    write_csv(os.path.join(a.out, "generations.csv"), ["source", "arm", "graded_rows"],
              [["rc1", k, v] for k, v in sorted(by_arm.items())] + [["ext", "base", len(ext)], ["total", "", total]])
    summary.append(f"(1) graded generations: rc1 {dict(sorted(by_arm.items()))} + ext {len(ext)} = {total}")

    # final API record per extension cell (re-asked cells keep the last record), for truncation
    last = {}
    with open(a.results_ext_api, encoding="utf-8") as f:
        for line in f:
            j = json.loads(line)
            key = (j["model_key"], j["lang"], j["qid"], int(j["run"]))
            order = (j.get("t_epoch") or 0, j.get("seq") or 0)
            if key not in last or order >= last[key][0]:
                last[key] = (order, j.get("tok_out"))
    truncated = {k for k, (_, t) in last.items() if t == CAP}

    # (2) extension silent split, free-tier proxies
    split = defaultdict(lambda: defaultdict(int))
    for r in ext:
        m = r["model_key"]
        if m not in FRONTIER or is_true(r["correct"]):
            continue
        key = (m, r["lang"], r["qid"], int(r["run"]))
        grp = (m, r["lang"])
        if r["qid"] in MI_ITEMS:
            split[grp]["failed_mi"] += 1
            continue
        split[grp]["failed_single"] += 1
        if not is_true(r["exec_ok"]):
            split[grp]["loud"] += 1
            if key in truncated:
                split[grp]["loud_truncated"] += 1
        elif int(r["n_rows"] or 0) == 0:
            split[grp]["silent_empty"] += 1
        else:
            split[grp]["silent_nonempty"] += 1
    cols = ["failed_single", "loud", "loud_truncated", "silent_empty", "silent_nonempty", "failed_mi"]
    data, pooled = [], defaultdict(int)
    for grp in sorted(split):
        data.append(list(grp) + [split[grp][c] for c in cols])
        for c in cols:
            pooled[c] += split[grp][c]
    data.append(["free-tier pooled", "both"] + [pooled[c] for c in cols])
    write_csv(os.path.join(a.out, "ext_frontier_silent.csv"), ["model", "lang"] + cols, data)
    silent = pooled["silent_empty"] + pooled["silent_nonempty"]
    summary.append(f"(2) extension, free-tier proxies, single-instance items: failed {pooled['failed_single']} = loud {pooled['loud']} "
                   f"(truncated {pooled['loud_truncated']}) + silent-empty {pooled['silent_empty']} + silent-non-empty {pooled['silent_nonempty']}; "
                   f"silent {silent}/{pooled['failed_single']} = {100 * silent / pooled['failed_single']:.1f}%; failed multi-instance runs {pooled['failed_mi']}")

    # (3) typhoon item majorities on the extension
    cells = defaultdict(list)
    for r in ext:
        cells[(r["model_key"], r["lang"], r["qid"])].append(r)
    data = []
    for lang in ("en", "th"):
        items = sorted(q for (m, l, q) in cells if m == "typhoon2-8b" and l == lang)
        correct = sum(1 for q in items if sum(is_true(x["correct"]) for x in cells[("typhoon2-8b", lang, q)]) * 2 > len(cells[("typhoon2-8b", lang, q)]))
        short = [f"{q}:{len(cells[('typhoon2-8b', lang, q)])}" for q in items if len(cells[("typhoon2-8b", lang, q)]) < 5]
        runs = sum(len(cells[("typhoon2-8b", lang, q)]) for q in items)
        lo, hi = wilson(correct, len(items))
        data.append(["typhoon2-8b", lang, correct, len(items), runs, f"{lo:.3f}", f"{hi:.3f}", " ".join(short)])
        summary.append(f"(3) typhoon2-8b extension {lang}: {correct}/{len(items)} items (runs {runs}; Wilson {100 * lo:.1f}–{100 * hi:.1f}%; cells < 5 runs: {' '.join(short) or 'none'})")
    write_csv(os.path.join(a.out, "ext_typhoon_descriptive.csv"),
              ["model", "lang", "correct_items", "n_items", "runs", "wilson_lo", "wilson_hi", "cells_lt5_runs"], data)

    # (4) claude truncation and majority dependence
    data = []
    for (m, lang, q), rs in sorted(cells.items()):
        if m != "claude-sonnet":
            continue
        tr = [int(x["run"]) for x in rs if (m, lang, q, int(x["run"])) in truncated]
        if not tr:
            continue
        maj_all = sum(is_true(x["correct"]) for x in rs) * 2 > len(rs)
        keep = [x for x in rs if int(x["run"]) not in tr]
        maj_keep = (sum(is_true(x["correct"]) for x in keep) * 2 > len(keep)) if keep else None
        data.append([m, lang, q, " ".join(map(str, sorted(tr))), len(rs), maj_all, maj_keep, maj_keep is not None and maj_keep != maj_all])
    write_csv(os.path.join(a.out, "ext_claude_truncation.csv"),
              ["model", "lang", "qid", "truncated_runs", "runs", "majority_all_runs", "majority_untruncated_runs", "majority_depends_on_truncation"], data)
    n_tr = sum(len(d[3].split()) for d in data)
    dep = [f"{d[1]} {d[2]}" for d in data if d[7]]
    summary.append(f"(4) claude-sonnet truncated graded runs (final record tok_out = {CAP}): {n_tr} in {len(data)} cells; majority depends on truncated runs: {', '.join(dep) or 'none'}")

    # (5) decomposition of headline counts
    def acc(path):
        return {(r["model"], r["lang"]): (int(r["correct"]), int(r["n"])) for r in rows(path) if r["scope"] == "all"}
    v12, v13, oct_ = acc(a.acc_v12), acc(a.acc_v13n), acc(a.acc_oct)
    data = []
    for k in sorted(oct_):
        data.append([k[0], k[1], *v12.get(k, ("", "")), *v13.get(k, ("", "")), *oct_[k]])
    write_csv(os.path.join(a.out, "decomposition.csv"),
              ["model", "lang", "submitted_v12_correct", "submitted_v12_n", "aug_v13n_correct", "aug_v13n_n", "oct_correct", "oct_n"], data)
    summary.append("(5) decomposition written (submitted v1.2 n=60 -> August regrade v1.3n n=59 -> October n=60)")

    with open(os.path.join(a.out, "summary.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(summary) + "\n")
    meta = {"script": "harness/" + os.path.basename(__file__), "script_sha256": sha(__file__),
            "inputs": {k: {"path": v, "sha256": sha(v)} for k, v in vars(a).items() if k != "out"}}
    with open(os.path.join(a.out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, ensure_ascii=False, indent=1)
    print("\n".join(summary))
    print(f"[out] {a.out}")


if __name__ == "__main__":
    main()
