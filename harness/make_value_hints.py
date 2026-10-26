#!/usr/bin/env python3
"""make_value_hints.py — RC1 (October session) value-hint block generator.

Builds, ONCE and before any RC1 model call, the per-schema block of stored text
values that the 'values' arm appends to the system prompt. The output file is
frozen (file sha256 and per-schema block sha256 recorded in the AMENDMENT-7
FREEZE STAMP) and runner.py reads it; runner.py never queries the database.

Rule (pre-registered, AMENDMENT-7 A2):
  * every TEXT column of the DDL the model sees (DDL_P / DDL_E in runner.py),
    in DDL order;
  * column with <= CAP distinct values  -> the full SELECT DISTINCT list,
    including NULL when present (NULL last);
  * column with  > CAP distinct values  -> "<N> distinct values, e.g." + the
    first EXAMPLES non-NULL values in code-point order;
  * values are rendered as SQL literals ('...' with '' escaping);
  * ordering is done in Python (code-point), not by the DB collation.
  * 'full_values' (columns with <= 100 distinct) is stored for the residual
    error classifier only (vg_classifier.py); it never enters a prompt.
CAP=25 / EXAMPLES=3.

Database: k3n (brief 1.1). --expect-db k3n checks, read-only, that the
database carries the k3n encoding: no text value 'None' in any TEXT column of
schema P and exactly 1 / 4 / 1 NULL in PresidentMarriage.SpouseName /
PresidentHolding.VicePresidentName / PresidentHolding.RunnerUp. The block text
is the same on k3 and k3n (TEST-ONLY), the column records (full_values) differ.

Output is deterministic: no timestamp, json.dumps(ensure_ascii=False, indent=1)
plus a final newline, so two builds on the same database give the same bytes.

Usage (RUNBOOK_v2 Gate 1a step 54; author's machine, read-only DB access; one
command, run from harness/):
  python3 -I -B "make_value_hints.py" --pg "dbname=k3n" --expect-db k3n --expect-block-sha "P=<64 hex>,E=<64 hex>" --out "../suite/value_hints_v1.json"
"""
import argparse
import hashlib
import importlib.util
import json
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))

CAP = 25
EXAMPLES = 3
FULL_DUMP_MAX = 100   # analysis-only vocabulary (never shown to a model)
# OQ14.1 default: version label 'v1' (source_db 'k3n'). This constant sets ONLY the JSON
# 'version' field (copied by runner.py into hints_version of each values record). The file
# name suite/value_hints_v1.json is fixed and does not follow this label: it is spelled out
# in the RUNBOOK, GATES_CHECKLIST, freeze_manifest_gate1b.tsv, gate1b_paths.txt, the runner,
# check_prompts_rc1, analysis/chat scripts and tests. Picking 'v1n' = change this constant
# only; renaming the file would be a separate edit of all those places.
HINTS_VERSION = "v1"
HEADER = ("Stored values of the text columns (SELECT DISTINCT; a column with "
          f"more than {CAP} distinct values shows {EXAMPLES} examples):")

# k3n guard (brief 1.1): the six cells 'None' -> NULL
K3N_NULLS = (("PresidentMarriage", "SpouseName", 1),
             ("PresidentHolding", "VicePresidentName", 4),
             ("PresidentHolding", "RunnerUp", 1))
SUPPORTED_DBS = ("k3n",)


def load_ddl(runner_path):
    """DDL_P / DDL_E จาก runner.py (แหล่งเดียวของข้อความ DDL); ไม่เขียน bytecode"""
    spec = importlib.util.spec_from_file_location("runner_for_hints", runner_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.DDL_P, mod.DDL_E


def text_columns(ddl):
    """[(table, column)] for TEXT columns, in DDL order."""
    out = []
    for m in re.finditer(r"CREATE TABLE (\w+)\((.*?)\);", ddl, re.S):
        table = m.group(1)
        for part in m.group(2).split(","):
            name, typ = part.strip().split()[:2]
            if typ.upper() == "TEXT":
                out.append((table, name))
    return out


def lit(v):
    return "NULL" if v is None else "'" + str(v).replace("'", "''") + "'"


def build(cur, ddl):
    lines, cols = [], []
    for table, col in text_columns(ddl):
        cur.execute(f"SELECT DISTINCT {col} FROM {table}")
        vals = [r[0] for r in cur.fetchall()]
        non_null = sorted(v for v in vals if v is not None)
        has_null = any(v is None for v in vals)
        n = len(non_null) + (1 if has_null else 0)
        if n <= CAP:
            shown = non_null + ([None] if has_null else [])
            line = f"{table}.{col}: " + ", ".join(lit(v) for v in shown)
            mode = "full"
        else:
            shown = non_null[:EXAMPLES]
            line = (f"{table}.{col}: {n} distinct values, e.g. "
                    + ", ".join(lit(v) for v in shown))
            mode = "examples"
        lines.append(line)
        cols.append({"table": table, "column": col, "n_distinct": n,
                     "mode": mode, "values": shown,
                     # ใช้ในตัวจำแนก residual error เท่านั้น — ไม่เข้า prompt
                     "full_values": non_null if n <= FULL_DUMP_MAX else None})
    block = HEADER + "\n" + "\n".join(lines)
    return block, cols


def check_k3n(cur, ddl_p):
    """read-only guard: ไม่มีสตริง 'None' ในคอลัมน์ TEXT ของ schema P และ NULL = 1/4/1"""
    problems, report = [], []
    n_none = 0
    for table, col in text_columns(ddl_p):
        cur.execute(f"SELECT count(*) FROM {table} WHERE {col} = 'None'")
        c = cur.fetchone()[0]
        n_none += c
        if c:
            problems.append(f"{table}.{col} has {c} value(s) 'None'")
    report.append(f"'None' strings in schema P text columns: {n_none}")
    for table, col, want in K3N_NULLS:
        cur.execute(f"SELECT count(*) - count({col}) FROM {table}")
        got = cur.fetchone()[0]
        report.append(f"NULL in {table}.{col}: {got} (expect {want})")
        if got != want:
            problems.append(f"{table}.{col} has {got} NULL (expect {want})")
    return problems, report


def parse_block_sha(s):
    out = {}
    for part in (s or "").split(","):
        if not part.strip():
            continue
        if "=" not in part:
            sys.exit(f"--expect-block-sha: bad item {part!r} (use P=<hex>,E=<hex>)")
        k, v = part.split("=", 1)
        out[k.strip()] = v.strip().lower()
    if set(out) != {"P", "E"}:
        sys.exit("--expect-block-sha needs both P and E")
    for k, v in out.items():
        if not re.fullmatch(r"[0-9a-f]{64}", v):
            sys.exit(f"--expect-block-sha {k}: give the full 64-hex sha256")
    return out


def render(out):
    return (json.dumps(out, ensure_ascii=False, indent=1) + "\n").encode("utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pg", required=True, help='libpq DSN, e.g. "dbname=k3n"')
    ap.add_argument("--expect-db", required=True, choices=SUPPORTED_DBS,
                    help="content guard of the database encoding (k3n)")
    ap.add_argument("--expect-block-sha", help='"P=<64 hex>,E=<64 hex>" from AMENDMENT-7 A2')
    ap.add_argument("--out", required=True)
    ap.add_argument("--runner", default=os.path.join(HERE, "runner.py"),
                    help="runner.py that holds DDL_P / DDL_E (default: next to this script)")
    a = ap.parse_args()
    if os.path.exists(a.out):
        sys.exit(f"{os.path.basename(a.out)} exists — the hint file is frozen; write a new version instead")
    expect = parse_block_sha(a.expect_block_sha) if a.expect_block_sha else None
    ddl_p, ddl_e = load_ddl(a.runner)

    import psycopg2
    conn = psycopg2.connect(a.pg)
    conn.set_session(readonly=True)
    cur = conn.cursor()
    cur.execute("SELECT current_database()")
    dbname = cur.fetchone()[0]
    problems, report = check_k3n(cur, ddl_p)
    print(f"database: {dbname} (guard --expect-db {a.expect_db})")
    for line in report:
        print("  " + line)
    if problems:
        conn.rollback()
        conn.close()
        sys.exit(f"REFUSED: database is not {a.expect_db}: " + "; ".join(problems))
    if dbname != a.expect_db:
        print(f"  note: database name {dbname!r} differs from {a.expect_db!r}; the content guard passed")

    out = {"version": HINTS_VERSION, "source_db": a.expect_db, "cap": CAP, "examples": EXAMPLES,
           "block_sha256": {}, "schemas": {}}
    for key, ddl in (("P", ddl_p), ("E", ddl_e)):
        block, cols = build(cur, ddl)
        sha = hashlib.sha256(block.encode("utf-8")).hexdigest()
        out["block_sha256"][key] = sha
        out["schemas"][key] = {"block": block, "columns": cols, "sha256": sha, "chars": len(block)}
    conn.rollback()
    conn.close()

    for key in ("P", "E"):
        s = out["schemas"][key]
        print(f"schema {key}: {s['chars']} chars, sha256 {s['sha256']}")
    if expect:
        bad = [k for k in ("P", "E") if out["block_sha256"][k] != expect[k]]
        if bad:
            sys.exit(f"REFUSED: block sha256 of {bad} differs from --expect-block-sha; file not written "
                     f"(record the actual values and the cause before any commit)")
        print("block sha256 P and E match --expect-block-sha")
    else:
        print("WARNING: no --expect-block-sha given; block sha256 not compared")

    data = render(out)
    fd = os.open(a.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    with os.fdopen(fd, "wb") as fh:
        fh.write(data)
    print(f"file sha256: {hashlib.sha256(data).hexdigest()}")


if __name__ == "__main__":
    main()
