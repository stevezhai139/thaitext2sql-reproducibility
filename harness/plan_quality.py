"""
plan_quality.py — RQ3 (Amendment-5): วัดคุณภาพ query plan แทนการจับเวลา

หลักการ: EXPLAIN (FORMAT JSON) ไม่ execute จริง → ไม่มีประเด็น warm/cold cache,
deterministic ต่อ (PG version, ข้อมูล, ANALYZE, config) ที่ repo ตรึงไว้ทั้งหมด

สำหรับข้อ eff=yes ของ --suite: gold + SQL ตัวแทนของทุก model×lang ที่ majority-correct
(record แรกในไฟล์ที่ correct) → เขียนใหม่ให้ชี้ Ecommerce1M → EXPLAIN → ดึง
  - total_cost   : planner estimated cost (หน่วยภายใน PG — เทียบกันได้ใน config เดียว)
  - scan_types   : ชนิด node การอ่านตาราง (Seq Scan / Index Scan / Bitmap ...)
  - uses_index   : plan แตะ index หรือไม่
  - cost_ratio   : cost ของโมเดล / cost ของ gold ข้อเดียวกัน (>1 = plan ด้อยกว่า)

เรียกสองเฟส: --phase indexed (หลัง indexes.sql) และ --phase noindex (หลัง DROP INDEX)
เปรียบเทียบสองเฟส = index-responsiveness (plan ขยับตาม index ไหม)

Gate 0 (KST 2027 revision; GATE0 design 2.6, D10, OQ20):
  * --arm บังคับ (สัญญาของ analyze.py) กรองทั้งไฟล์ graded และ jsonl เพราะคีย์ของ
    graded_runs (l.54, 60, 66 ของฉบับเดิม) ไม่มี arm; record ที่ไม่มี field arm = base
  * --results ซ้ำได้ (results_rc1_api.jsonl + results_rc1_local.jsonl) อ่านตามลำดับ
  * อ่าน jsonl ด้วย hook ที่เก็บเฉพาะ model_key, arm, lang, qid, run, sql และแปลง
    error เป็น boolean (ไม่เก็บและไม่พิมพ์ค่าของ error)
  * reference cost = gold ของ --suite (RUNBOOK ส่ง suite v1.2: gold v1.2 คำนวณใหม่บน
    k3n ตาม brief 1.2) รันบนสำเนา k3n_rq3 เท่านั้น
  * เขียน <out>.meta.json; คอลัมน์ CSV เหมือนเดิม (make_tables อ่าน tab_plan ได้)
  * D10: meta เก็บ input record ของ graded พร้อม session fingerprint (analyze.graded_record)
    ให้ make_tables และ analyze_log_v13 B5 ตรวจว่า plan มาจากรอบเดียวกับตาราง
  * D11 (RQ3; analyze.D11_REPAIRED): reference cost ของข้อที่ซ่อมสำหรับรอบ ต.ค. ต้องมาจาก
    gold ฉบับซ่อมเมื่อ --graded เป็น log core ของรอบ ต.ค. (graded สองแขน) และคงเป็น gold
    เดิมเมื่อเป็น log ส.ค.; gold ของข้อที่ซ่อมมาจาก --suite เมื่อ --suite เป็น suite core
    ของรอบ ต.ค. หรือจาก --d11-gold-suite (suite core ของรอบ ต.ค.) เมื่อ --suite เป็น v1.2;
    ข้อที่ซ่อมซึ่งเป็นข้อ eff=yes บน log ของรอบ ต.ค. โดยไม่มี gold ฉบับซ่อม และ log ส.ค.
    คู่กับ suite core ของรอบ ต.ค. (gold ฉบับซ่อม) ทำให้หยุด (exit 2);
    ใน suite ทุกฉบับปัจจุบัน Q27 เป็น eff=no จึงไม่อยู่ใน RQ3 ทั้งสองรอบ และ reference gold
    ของ 11 ข้อ eff=yes ไม่เปลี่ยน (สคริปต์พิมพ์บรรทัด [D11] ยืนยันทุกครั้ง)

Usage:
  python3 -I -B plan_quality.py --graded ../results/rc1/graded_rc1.csv \
    --results ../results/rc1/results_rc1_api.jsonl --results ../results/rc1/results_rc1_local.jsonl \
    --suite ../suite/k3_suite_v1.2.tsv --pg "dbname=k3n_rq3" --arm base \
    --phase indexed --out ../results/rc1/base60/plan_indexed.csv
"""
import argparse
import csv
import json
import os
import re
import statistics
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402

_KEEP = ("model_key", "arm", "lang", "qid", "run", "sql")


def _hook(pairs):
    d = {}
    for k, v in pairs:
        if k == "error":
            d["error"] = v is not None     # tested for None only; value never kept
        elif k in _KEEP:
            d[k] = v
    return d


def iter_records(paths):
    for path in paths:
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    yield json.loads(line, object_pairs_hook=_hook)
                except json.JSONDecodeError:
                    ac.die(2, f"{os.path.basename(path)} line {n}: not JSON (incomplete write?)")


def rq3_gold(a, suite, eff_qids, grec):
    """D11 (RQ3): {qid: reference gold} of the eff items and the [D11] line to print. The
    October core log (two arms) takes the repaired gold of a D11 item; the August log keeps
    the gold of --suite (the original one)."""
    gold = {q: suite[q]["gold_sql_draft"] for q in eff_qids}
    d11_eff = [q for q in eff_qids if q in ac.D11_REPAIRED]
    october = set(ac.TWO_ARMS) <= set(grec.get("arms_in_file") or [])
    if a.d11_gold_suite:
        rows = ac.load_suite_rows(a.d11_gold_suite)
        ac.draft_guard(a.d11_gold_suite, rows, a.allow_draft_testonly, out_files=[a.out])
        if ac.suite_session(rows, os.path.basename(a.d11_gold_suite)) != ac.SESSION_OCT:
            ac.die(2, "[D11] --d11-gold-suite must be the October core suite (repaired items primary)")
    if not d11_eff:
        return gold, (f"[D11] RQ3: the repaired items {list(ac.D11_REPAIRED)} are not eff items of "
                      f"--suite (eff=no); reference gold of the {len(eff_qids)} eff items unchanged "
                      f"for both sessions")
    session = ac.suite_session(suite, os.path.basename(a.suite))
    if not october:
        if session == ac.SESSION_OCT:
            ac.die(2, f"[D11] RQ3: {d11_eff} are eff items and --suite is the October core suite "
                      f"(repaired gold); the August log answers the original question: use the "
                      f"August suite or suite v1.2")
        return gold, (f"[D11] RQ3: August log; {d11_eff} keep the original gold of --suite")
    if session == ac.SESSION_OCT:
        return gold, f"[D11] RQ3: October core log; {d11_eff} use the repaired gold of --suite"
    if not a.d11_gold_suite:
        ac.die(2, f"[D11] RQ3: {d11_eff} are eff items of --suite ({session}), whose gold is the "
                  f"original one; the October core log needs the repaired gold: pass "
                  f"--d11-gold-suite <October core suite>")
    for q in d11_eff:
        gold[q] = rows[q]["gold_sql_draft"]
    return gold, f"[D11] RQ3: October core log; {d11_eff} use the repaired gold of --d11-gold-suite"


def walk(node, acc):
    acc.append(node.get("Node Type", "?"))
    for child in node.get("Plans", []):
        walk(child, acc)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graded", required=True)
    ap.add_argument("--results", required=True, action="append",
                    help="results jsonl; repeat for api + local")
    ap.add_argument("--suite", required=True)
    ap.add_argument("--pg", required=True)
    ap.add_argument("--phase", choices=["indexed", "noindex"], required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--d11-gold-suite", help="October core suite: gold of the repaired items "
                                             "(D11) when one of them is an eff item of --suite")
    ac.add_arm_contract(ap)
    ac.add_draft_flag(ap)
    a = ap.parse_args()

    suite = {r["id"]: r for r in csv.DictReader(open(a.suite, encoding="utf-8"), delimiter="\t")}
    ac.draft_guard(a.suite, suite, a.allow_draft_testonly, out_files=[a.out])
    eff_qids = [qid for qid, r in suite.items() if r["eff"].strip() == "yes"]

    excluded = ac.split_list(a.exclude_models)
    rows_all = ac.read_csv_rows(a.graded)
    grec = ac.graded_record(a.graded, rows_all, a.arm)
    gold_of, d11_note = rq3_gold(a, suite, eff_qids, grec)
    print(d11_note)
    graded = ac.filter_arm(rows_all, a.arm, excluded)
    ac.require_complete_present(graded, a.runs)

    votes = {}
    for row in graded:
        if row["qid"] not in eff_qids:
            continue
        k = (row["model_key"], row["lang"], row["qid"])
        votes.setdefault(k, []).append(row["correct"] == "True")
    majority_ok = {k: (sum(v) > len(v) / 2) for k, v in votes.items()}

    graded_runs = {}
    for row in graded:
        graded_runs[(row["model_key"], row["lang"], row["qid"], row["run"])] = row["correct"] == "True"
    rep_sql = {}
    n_other_arm = 0
    for rec in iter_records(a.results):
        if rec.get("error"):
            continue
        if ac.row_arm(rec) != a.arm or rec.get("model_key") in excluded:
            n_other_arm += 1
            continue
        k3 = (rec["model_key"], rec["lang"], rec["qid"])
        if rec["qid"] in eff_qids and majority_ok.get(k3) and k3 not in rep_sql:
            if graded_runs.get((rec["model_key"], rec["lang"], rec["qid"], str(rec["run"]))):
                rep_sql[k3] = rec["sql"]
    print(f"[arm] results: {n_other_arm} non-error records of another arm or excluded model skipped")

    import psycopg2
    conn = psycopg2.connect(a.pg)
    conn.set_session(readonly=True, autocommit=True)

    def to_1m(sql):
        return re.sub(r"\bEcommerce\b", "Ecommerce1M", sql)

    def explain(sql):
        with conn.cursor() as cur:
            cur.execute("SET statement_timeout = '30s'")  # EXPLAIN เร็วมาก แต่กันเหนียว
            cur.execute("EXPLAIN (FORMAT JSON) " + sql)
            plan = cur.fetchone()[0][0]["Plan"]
        nodes = []
        walk(plan, nodes)
        scans = sorted({n for n in nodes if "Scan" in n})
        uses_index = any(("Index" in n) or ("Bitmap" in n) for n in nodes)
        return plan["Total Cost"], ";".join(scans), uses_index

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    fh = open(a.out, "w", newline="", encoding="utf-8")
    out = csv.writer(fh)
    out.writerow(["phase", "source", "lang", "qid", "total_cost",
                  "scan_types", "uses_index", "cost_ratio_vs_gold", "error"])
    gold_cost = {}
    for qid in eff_qids:
        g = to_1m(gold_of[qid].strip().rstrip(";"))
        try:
            cost, scans, ui = explain(g)
            gold_cost[qid] = cost
            out.writerow([a.phase, "gold", "-", qid, f"{cost:.1f}", scans, ui, "1.00", ""])
            print(f"gold {qid}: cost {cost:,.0f}  [{scans}] index={ui}")
        except Exception as e:
            out.writerow([a.phase, "gold", "-", qid, "", "", "", "", str(e)[:80]])
            print(f"gold {qid}: EXPLAIN ล้มเหลว — {str(e)[:60]}")

    ratios = {}
    for (mk, lang, qid), sql in sorted(rep_sql.items()):
        try:
            cost, scans, ui = explain(to_1m(sql))
            ratio = cost / gold_cost[qid] if gold_cost.get(qid) else None
            out.writerow([a.phase, mk, lang, qid, f"{cost:.1f}", scans, ui,
                          f"{ratio:.2f}" if ratio else "", ""])
            ratios.setdefault(mk, []).append(ratio)
        except Exception as e:
            out.writerow([a.phase, mk, lang, qid, "", "", "", "", str(e)[:80]])
    fh.close()

    print(f"\nสรุป cost ratio (median ต่อโมเดล, เฟส {a.phase}):")
    for mk, v in sorted(ratios.items()):
        v = [x for x in v if x]
        if v:
            print(f"  {mk:16s} median {statistics.median(v):.2f}  (n={len(v)})")
    n_skip = sum(1 for k, ok in majority_ok.items() if not ok)
    print(f"cells ที่ไม่มี SQL ถูกให้วัด: {n_skip}")
    detail = {"inputs": {"graded": grec,
                         "results": [ac.input_record(p) for p in a.results]},
              "phase": a.phase, "runs": a.runs, "excluded_models": sorted(excluded),
              "eff_items": eff_qids, "d11": d11_note,
              "d11_gold_suite": ac.input_record(a.d11_gold_suite) if a.d11_gold_suite else None}
    common = {"arm": a.arm, "suite_sha256": ac.sha256_file(a.suite), "n_items": len(eff_qids)}
    p = ac.write_file_meta(a.out, "plan_quality.py", common, detail)
    print(f"[meta] {os.path.basename(p)} (arm {a.arm})")


if __name__ == "__main__":
    main()
