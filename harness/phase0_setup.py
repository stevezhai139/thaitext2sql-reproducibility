"""
phase0_setup.py — K3 Phase 0: เตรียม PostgreSQL run-of-record ครบวงจร (reproducible)

ทำอะไร:
  1) (--fresh) drop + create database
  2) รัน setup_db.sql (DDL ทุกตาราง รวม Ecommerce1M LIKE Ecommerce)
  3) โหลด CSV 5 ตารางจาก --president-dir ผ่าน psql \\copy
  4) สร้างข้อมูล 1,000,000 แถวด้วย scale_ecommerce.py (seed คงที่) แล้วโหลดเข้า Ecommerce1M
  5) ตรวจจำนวนแถวทุกตาราง
  6) gold self-test บน PG: gold ทุกข้อเป็นคำตอบตัวเอง ต้องได้ 60/60 — ไม่ผ่าน = exit 1

ใช้:
  python3 phase0_setup.py --president-dir "/path/to/PresidentsData" [--db k3] [--n 1000000] [--fresh]

ต้องมี: PostgreSQL client (createdb/psql) ใน PATH และ server รันอยู่
"""
import argparse
import csv
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SUITE = os.path.join(HERE, "..", "suite", "k3_suite_v1.2.tsv")

LOADS = [  # (ตาราง, ไฟล์ csv)
    ("President", "President.csv"),
    ("Party", "Party.csv"),
    ("PresidentMarriage", "PresidentMarriage.csv"),
    ("PresidentHolding", "PresidentHolding.csv"),
    ("Ecommerce", "Ecommerce_Dataset.csv"),
]


def run(cmd, **kw):
    print(f"$ {' '.join(cmd)}")
    r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.exit(f"FAILED ({r.returncode}): {' '.join(cmd)}")
    return r


def psql(db, sql, capture=False):
    cmd = ["psql", "-d", db, "-v", "ON_ERROR_STOP=1", "-tA", "-c", sql]
    if capture:
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode != 0:
            sys.exit(f"FAILED psql: {sql}\n{r.stderr}")
        return r.stdout.strip()
    run(cmd)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--president-dir", required=True)
    ap.add_argument("--db", default="k3")
    ap.add_argument("--n", type=int, default=1_000_000)
    ap.add_argument("--scale-out", default="/tmp/ecommerce_1m.csv")
    ap.add_argument("--fresh", action="store_true",
                    help="drop database เดิมก่อน (เริ่มสะอาด)")
    a = ap.parse_args()

    # 1) database
    if a.fresh:
        run(["dropdb", "--if-exists", a.db])
    exists = subprocess.run(["psql", "-d", a.db, "-c", "SELECT 1"],
                            capture_output=True).returncode == 0
    if not exists:
        run(["createdb", a.db])
    else:
        print(f"database '{a.db}' มีอยู่แล้ว (ใช้ --fresh ถ้าต้องการเริ่มใหม่)")

    # 2) DDL
    run(["psql", "-d", a.db, "-v", "ON_ERROR_STOP=1",
         "-f", os.path.join(HERE, "setup_db.sql")])

    # 3) โหลด 5 ตาราง
    for table, fname in LOADS:
        path = os.path.join(a.president_dir, fname)
        if not os.path.exists(path):
            sys.exit(f"ไม่พบไฟล์ {path}")
        psql(a.db, f"TRUNCATE {table}")
        psql(a.db, f"\\copy {table} FROM '{path}' CSV HEADER")
        n = psql(a.db, f"SELECT COUNT(*) FROM {table}", capture=True)
        print(f"  {table}: {n} แถว")

    # 4) หนึ่งล้านแถว (deterministic: seed 42)
    if not os.path.exists(a.scale_out):
        run([sys.executable, os.path.join(HERE, "scale_ecommerce.py"),
             "--src", os.path.join(a.president_dir, "Ecommerce_Dataset.csv"),
             "--n", str(a.n), "--out", a.scale_out, "--seed", "42"])
    else:
        print(f"{a.scale_out} มีอยู่แล้ว — ใช้ไฟล์เดิม")
    psql(a.db, "TRUNCATE Ecommerce1M")
    psql(a.db, f"\\copy Ecommerce1M FROM '{a.scale_out}' CSV HEADER")
    n1m = psql(a.db, "SELECT COUNT(*) FROM Ecommerce1M", capture=True)
    print(f"  Ecommerce1M: {n1m} แถว")
    if int(n1m) != a.n:
        sys.exit(f"Ecommerce1M ได้ {n1m} แถว คาดหวัง {a.n}")

    # 5) gold self-test บน PG
    suite = list(csv.DictReader(open(SUITE, encoding="utf-8"), delimiter="\t"))
    selftest = "/tmp/k3_selftest.jsonl"
    with open(selftest, "w", encoding="utf-8") as f:
        for q in suite:
            f.write(json.dumps({
                "model_key": "selftest", "model_echo": "gold", "lang": "en",
                "qid": q["id"], "tier": q["tier"], "schema": q["schema"],
                "run": 1, "latency_s": 0, "raw": "",
                "sql": q["gold_sql_draft"].strip().rstrip(";"),
                "parse_ok": True, "error": None}, ensure_ascii=False) + "\n")
    r = subprocess.run([sys.executable, os.path.join(HERE, "grade.py"),
                        "--results", selftest, "--suite", SUITE,
                        "--engine", "pg", "--pg", f"dbname={a.db}",
                        "--out", "/tmp/k3_selftest_pg.csv"],
                       capture_output=True, text=True)
    print(r.stdout.strip())
    m = re.search(r"selftest\s+en:\s+(\d+)/(\d+)", r.stdout)
    if not m or m.group(1) != m.group(2) or m.group(2) != str(len(suite)):
        sys.exit(f"GOLD SELF-TEST ไม่ผ่าน — ห้ามไปต่อ Phase 3 (ดู /tmp/k3_selftest_pg.csv)\n{r.stderr[:500]}")
    print(f"\nPhase 0 สมบูรณ์: gold self-test {m.group(1)}/{m.group(2)} บน PostgreSQL ✔")


if __name__ == "__main__":
    main()
