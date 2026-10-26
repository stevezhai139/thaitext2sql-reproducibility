#!/usr/bin/env python3
"""make_vg_sets.py -- the two frozen VG lists of AMENDMENT-7 B2.1 (copied into harness/,
next to vg_rule.py). Reads the suite (gold SQL and Thai text) and the run DB only; it
takes no graded file and no model output (B2.1 'the tool must not read model results').

  VG10  primary items for which vg_rule.is_value_grounding(gold, question_th) holds
        (AMENDMENT-6 rule; the primary set under the 13 Oct decision)
  VG9   VG10 items with at least one VG literal whose replacement, at every occurrence
        in the gold at once, by 'zzqabsentvaluezzq' (no LIKE wildcard) changes the
        multiset of the gold result on --pg (relevance condition; sensitivity)
Writes one qid per line to --out (VG10) and --out-vg9 (VG9), never overwrites, and
exits non-zero (writing nothing) when a list differs from --expect-vg10 / --expect-vg9.
A DRAFT suite (file name or build_status) is refused unless --allow-draft-testonly with
both outputs outside results/ (analyze.draft_guard; analyze.py sits next to this script
in harness/).

Usage (Gate 1a step 46):
  python3 -I -B make_vg_sets.py --suite ../suite/k3n_suite_v1.3n.tsv --pg "dbname=k3n" \
    --out ../suite/vg_set_v13n.txt --out-vg9 ../suite/vg_set_v13n_VG9.txt \
    --expect-vg10 "Q01,Q07,Q09,Q13,Q14,Q15,Q21,Q30,Q42,Q48" \
    --expect-vg9 "Q01,Q07,Q09,Q13,Q14,Q15,Q21,Q30,Q42"
"""
import argparse
import collections
import csv
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
for _d in (HERE, os.path.join(HERE, "..", "harness")):   # harness/ layout, or Gate 0 layout
    if os.path.exists(os.path.join(_d, "analyze.py")) and _d not in sys.path:
        sys.path.insert(0, _d)
        break
if HERE not in sys.path:
    sys.path.insert(0, HERE)

REPLACEMENT = "'zzqabsentvaluezzq'"


def primary_items(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    return [r for r in rows if (r.get("v13_status") or "primary").strip() != "excluded"]


def gold_multiset(cur, sql):
    cur.execute(sql.strip().rstrip(";"))
    return collections.Counter(map(repr, cur.fetchall()))


def vg_sets(items, cur):
    from vg_rule import value_grounding_literals
    vg10, vg9, detail = [], [], []
    for r in items:
        lits = list(dict.fromkeys(value_grounding_literals(r["gold_sql_draft"], r["question_th"])))
        if not lits:
            continue
        vg10.append(r["id"])
        base = gold_multiset(cur, r["gold_sql_draft"])
        relevant = False
        for lit in lits:
            alt = r["gold_sql_draft"].replace("'" + lit + "'", REPLACEMENT)
            changed = gold_multiset(cur, alt) != base
            detail.append((r["id"], lit, changed))
            relevant = relevant or changed
        if relevant:
            vg9.append(r["id"])
    return vg10, vg9, detail


def parse_expect(s):
    return sorted(x.strip() for x in (s or "").split(",") if x.strip())


def main():
    ap = argparse.ArgumentParser(description="VG10 / VG9 lists (AM-7 B2.1)")
    ap.add_argument("--suite", required=True)
    ap.add_argument("--pg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--out-vg9", required=True)
    ap.add_argument("--expect-vg10", required=True)
    ap.add_argument("--expect-vg9", required=True)
    ap.add_argument("--allow-draft-testonly", action="store_true",
                    help="tests only: accept a DRAFT suite when both outputs are outside results/")
    a = ap.parse_args()
    import analyze as ac   # the single DRAFT guard
    with open(a.suite, encoding="utf-8", newline="") as fh:
        ac.draft_guard(a.suite, {r["id"]: r for r in csv.DictReader(fh, delimiter="\t")},
                       a.allow_draft_testonly, out_files=[a.out, a.out_vg9])
    for p in (a.out, a.out_vg9):
        if os.path.exists(p):
            sys.exit(f"{os.path.basename(p)} exists; the VG lists are written once")
    import psycopg2
    conn = psycopg2.connect(a.pg)
    conn.set_session(readonly=True, autocommit=True)
    with conn.cursor() as cur:
        items = primary_items(a.suite)
        vg10, vg9, detail = vg_sets(items, cur)
    conn.close()
    print(f"primary items {len(items)}")
    for qid, lit, changed in detail:
        print(f"  relevance {qid} '{lit}': gold result changes when replaced = {changed}")
    print(f"VG10 ({len(vg10)}): {','.join(vg10)}")
    print(f"VG9  ({len(vg9)}): {','.join(vg9)}")
    bad = []
    if sorted(vg10) != parse_expect(a.expect_vg10):
        bad.append("VG10")
    if sorted(vg9) != parse_expect(a.expect_vg9):
        bad.append("VG9")
    if bad:
        print(f"STOP: {' and '.join(bad)} differ from the expected list; nothing written (AM-7 B2.1)")
        sys.exit(1)
    for p, lst in ((a.out, vg10), (a.out_vg9, vg9)):
        with open(p, "w", encoding="utf-8") as fh:
            fh.write("".join(q + "\n" for q in lst))
    print(f"wrote {os.path.basename(a.out)} and {os.path.basename(a.out_vg9)}")


if __name__ == "__main__":
    main()
