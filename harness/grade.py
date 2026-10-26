"""
grade.py — execute-and-compare grader (execution accuracy).

Reads results.jsonl (from runner.py) + suite, executes each candidate SQL
and the gold on the SAME engine, compares result multisets:
 - unordered multiset compare (sorted canonical), unless the gold contains
   a top-level ORDER BY -> ordered compare
 - floats rounded to 6 dp; NULLs normalized; values stringified
 - SELECT/WITH only; per-query timeout; read-only

Engines: --engine duckdb (dev)  |  --engine pg (run-of-record, PostgreSQL)
Output : graded.csv (one row per model x lang x qid x run) + summary.

Usage (dev):
  python3 grade.py --results results.jsonl --suite ../suite/k3_suite_v1.tsv \
    --engine duckdb --president-dir <dir> --eco <csv> --out graded.csv
Usage (record):
  python3 grade.py --results results.jsonl --suite ... --engine pg \
    --pg "dbname=k3 user=... password=..." --out graded.csv
"""
import argparse
import csv
import json
import re
import signal

ORDER_RE = re.compile(r"order\s+by", re.I)


def has_toplevel_order(sql):
    """ORDER BY ระดับนอกสุดเท่านั้น — ตัดเนื้อในวงเล็บทุกชั้นทิ้งก่อน
    (กัน false positive จาก OVER(...), WITHIN GROUP(...), subquery, CTE)"""
    out, depth = [], 0
    for ch in sql:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return bool(ORDER_RE.search("".join(out)))


def canon(rows, ordered):
    def cv(v):
        if v is None:
            return "\\N"
        if isinstance(v, float):
            return f"{v:.6g}"  # 6 sig digits: ทน FP flutter ของ parallel agg
        return str(v)
    out = [tuple(cv(v) for v in r) for r in rows]
    return out if ordered else sorted(out)


class Timeout(Exception):
    pass


def run_with_timeout(fn, seconds=20):
    def handler(sig, frm):
        raise Timeout()
    old = signal.signal(signal.SIGALRM, handler)
    signal.alarm(seconds)
    try:
        return fn()
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old)


def make_engine(a):
    if a.engine == "duckdb":
        import duckdb
        con = duckdb.connect()
        P = a.president_dir
        con.execute(f"CREATE TABLE President AS SELECT * FROM read_csv_auto('{P}/President.csv', header=true)")
        con.execute(f"CREATE TABLE Party AS SELECT * FROM read_csv_auto('{P}/Party.csv', header=true)")
        con.execute(f"CREATE TABLE PresidentMarriage AS SELECT * FROM read_csv_auto('{P}/PresidentMarriage.csv', header=true)")
        con.execute(f"CREATE TABLE PresidentHolding AS SELECT * FROM read_csv_auto('{P}/PresidentHolding.csv', header=true)")
        con.execute(f"CREATE TABLE Ecommerce AS SELECT * FROM read_csv_auto('{a.eco}', header=true)")

        def q(sql):
            return con.execute(sql).fetchall()
        return q
    else:
        import psycopg2
        conn = psycopg2.connect(a.pg)
        conn.set_session(readonly=True, autocommit=False)

        def q(sql):
            try:
                with conn.cursor() as cur:
                    cur.execute("SET LOCAL statement_timeout = '20s'")
                    cur.execute(sql)
                    rows = cur.fetchall()
                return rows
            finally:
                # ต้อง rollback เสมอ (แม้ SQL พัง) — ไม่งั้น transaction ค้าง
                # สถานะ aborted แล้วคำสั่งถัดไปตายยกแถว
                conn.rollback()
        return q


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--engine", choices=["duckdb", "pg"], default="duckdb")
    ap.add_argument("--president-dir")
    ap.add_argument("--eco")
    ap.add_argument("--pg")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()

    q = make_engine(a)
    suite = {r["id"]: r for r in csv.DictReader(open(a.suite, encoding="utf-8"), delimiter="\t")}

    gold_cache = {}
    for qid, item in suite.items():
        sql = item["gold_sql_draft"].strip().rstrip(";")
        ordered = has_toplevel_order(sql)
        gold_cache[qid] = (canon(q(sql), ordered), ordered)

    out = csv.writer(open(a.out, "w", newline="", encoding="utf-8"))
    out.writerow(["model_key", "lang", "qid", "tier", "schema", "run",
                  "parse_ok", "exec_ok", "correct", "latency_s", "fail_reason"])
    stats = {}
    for line in open(a.results, encoding="utf-8"):
        rec = json.loads(line)
        if rec.get("error") is not None:
            continue  # error record = ยังไม่มีคำตอบจริง (จะถูก retry) — ไม่นับเป็นความพยายาม
        qid = rec["qid"]
        gold, ordered = gold_cache[qid]
        parse_ok = rec.get("parse_ok", False)
        exec_ok, correct, reason = False, False, ""
        if not parse_ok:
            reason = "parse"
        else:
            sql = rec["sql"]
            low = sql.lower().lstrip()
            if not low.startswith(("select", "with")):
                reason = "non-select"
            else:
                try:
                    rows = run_with_timeout(lambda: q(sql))
                    exec_ok = True
                    correct = canon(rows, ordered) == gold
                    if not correct:
                        reason = "wrong-result"
                except Timeout:
                    reason = "timeout"
                except Exception as e:
                    reason = "exec-error: " + str(e).split("\n")[0][:120]
        out.writerow([rec["model_key"], rec["lang"], qid, rec["tier"],
                      rec["schema"], rec["run"], parse_ok, exec_ok, correct,
                      rec.get("latency_s"), reason])
        k = (rec["model_key"], rec["lang"])
        s = stats.setdefault(k, [0, 0])
        s[1] += 1
        s[0] += 1 if correct else 0
    print("run-level accuracy (raw, ก่อน majority):")
    for (mk, lang), (c, t) in sorted(stats.items()):
        print(f"  {mk:22s} {lang}: {c}/{t} = {c/t:.3f}")


if __name__ == "__main__":
    main()
