"""
validate_gold.py — ตรวจว่า gold SQL ทั้ง 60 ข้อ execute ได้และคืนผลสมเหตุผล
Dev engine: DuckDB (dialect ใกล้ PostgreSQL); run-of-record จริง = PostgreSQL
หมายเหตุ dialect ที่รู้ล่วงหน้า: integer division (PG: int/int=int,
DuckDB: /=float) — ข้อที่พึ่งพฤติกรรมนี้ถูกธงไว้ ไม่ถือเป็น fail

Usage: python3 validate_gold.py --suite <k3_suite_v1.tsv> \
         --president-dir <PresidentsData/> --eco <ecommerce csv>
"""
import argparse
import csv
import sys

import duckdb


def load(con, president_dir, eco_csv):
    con.execute(f"CREATE TABLE President AS SELECT * FROM read_csv_auto('{president_dir}/President.csv', header=true)")
    con.execute(f"CREATE TABLE Party AS SELECT * FROM read_csv_auto('{president_dir}/Party.csv', header=true)")
    con.execute(f"CREATE TABLE PresidentMarriage AS SELECT * FROM read_csv_auto('{president_dir}/PresidentMarriage.csv', header=true)")
    con.execute(f"CREATE TABLE PresidentHolding AS SELECT * FROM read_csv_auto('{president_dir}/PresidentHolding.csv', header=true)")
    con.execute(f"CREATE TABLE Ecommerce AS SELECT * FROM read_csv_auto('{eco_csv}', header=true)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True)
    ap.add_argument("--president-dir", required=True)
    ap.add_argument("--eco", required=True)
    a = ap.parse_args()

    con = duckdb.connect()
    load(con, a.president_dir, a.eco)

    with open(a.suite, newline="", encoding="utf-8") as f:
        suite = list(csv.DictReader(f, delimiter="\t"))

    ok, warn, fail = [], [], []
    for q in suite:
        qid, sql = q["id"], q["gold_sql_draft"].strip().rstrip(";")
        try:
            rows = con.execute(sql).fetchall()
            n = len(rows)
            if n == 0:
                warn.append((qid, "0 rows — ตรวจว่าตั้งใจหรือ gold ผิด"))
            else:
                ok.append((qid, n))
        except Exception as e:
            fail.append((qid, str(e).split("\n")[0][:160]))

    print(f"PASS {len(ok)} | WARN(0-row) {len(warn)} | FAIL {len(fail)}\n")
    for qid, n in ok:
        print(f"  ok   {qid}: {n} rows")
    for qid, m in warn:
        print(f"  WARN {qid}: {m}")
    for qid, m in fail:
        print(f"  FAIL {qid}: {m}")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
