"""
selftest_v13.py -- checks answer key v1.3 on the engine of record (read-only).

  1. question text, tier, schema, eff, notes byte-identical to v1.2
  2. gold_sql_v12 identical to v1.2 gold_sql_draft
  3. every primary item: primary gold non-empty; every gold (primary and
     alternatives, per language) executes, is deterministic over two runs,
     and grades correct against itself under R-v1.3 (grade_v13.match_v13)
  4. every alternative differs from the primary on the run DB (else it is
     redundant and is reported, not failed)
  5. ordered items: the gold's own rows satisfy its sort_keys (consistency)
Exit 1 on any failure.

Usage:
  python3 selftest_v13.py --suite ../suite/k3_suite_v1.3.tsv \
    --suite-v12 ../suite/k3_suite_v1.2.tsv --pg "dbname=k3"
"""
import argparse
import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from grade_v13 import (make_engine, match_v13, parse_keys, parse_norms)  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True)
    ap.add_argument("--suite-v12", required=True)
    ap.add_argument("--pg", required=True)
    a = ap.parse_args()
    q = make_engine(a.pg)
    s13 = list(csv.DictReader(open(a.suite, encoding="utf-8"), delimiter="\t"))
    s12 = list(csv.DictReader(open(a.suite_v12, encoding="utf-8"), delimiter="\t"))
    fails, notes = [], []

    if [r["id"] for r in s13] != [r["id"] for r in s12]:
        fails.append("item ids differ from v1.2")
    for x, y in zip(s12, s13):
        for f in ("tier", "schema", "eff", "question_en", "question_th", "notes"):
            if x[f] != y[f]:
                fails.append(f"{y['id']}: column {f} differs from v1.2")
        if x["gold_sql_draft"] != y["gold_sql_v12"]:
            fails.append(f"{y['id']}: gold_sql_v12 differs from v1.2 gold")

    n_primary = n_keys = 0
    for item in s13:
        qid = item["id"]
        primary = item["v13_status"].strip() == "primary"
        n_primary += primary
        sk = parse_keys(item["sort_keys"])
        norms = parse_norms(item["norm"])
        for lang in ("en", "th"):
            ordered = item[f"order_{lang}"].strip() == "yes"
            sqls = [("primary", item["gold_sql_draft"])]
            sqls += [(f"alt{i}", s) for i, s in
                     enumerate(json.loads(item[f"alt_gold_{lang}"] or "[]"), 1)]
            rows0 = None
            for label, sql in sqls:
                sql = sql.strip().rstrip(";")
                try:
                    r1, r2 = q(sql), q(sql)
                except Exception as e:
                    fails.append(f"{qid} {lang} {label}: exec error {str(e)[:80]}")
                    continue
                n_keys += 1
                if label == "primary":
                    rows0 = r1
                    if primary and not r1:
                        fails.append(f"{qid} {lang}: primary gold returns 0 rows")
                if not match_v13(r1, r2, ordered, sk, norms):
                    fails.append(f"{qid} {lang} {label}: not deterministic over two runs")
                if not match_v13(r1, r1, ordered, sk, norms):
                    fails.append(f"{qid} {lang} {label}: does not grade correct against itself")
                if label != "primary" and rows0 is not None and \
                        match_v13(r1, rows0, ordered, sk, norms):
                    notes.append(f"{qid} {lang} {label}: same result as primary on this DB "
                                 f"({len(r1)} rows; kept for other instances)")
                if label != "primary" and rows0 is not None and r1 and rows0 and \
                        len(r1[0]) != len(rows0[0]):
                    fails.append(f"{qid} {lang} {label}: column count differs from primary")
    print(f"items: {len(s13)} (primary {n_primary}); gold keys executed: {n_keys}")
    for n in notes:
        print("  note:", n)
    if fails:
        print("SELF-TEST v1.3 FAILED:")
        for f in fails:
            print("  ", f)
        sys.exit(1)
    print("self-test v1.3: PASS (question text identical to v1.2; every key executes, "
          "is deterministic and matches itself; no empty primary gold)")


if __name__ == "__main__":
    main()
