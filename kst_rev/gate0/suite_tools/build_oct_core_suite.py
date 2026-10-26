#!/usr/bin/env python3
"""build_oct_core_suite.py -- builder of the October core suite (D11, author decision 14 Oct 2026).

D11: the October session (AMENDMENT-7, Gate 3) grades all 60 core items. Q27 is repaired in
place (new EN, new TH, new gold) and is primary in the October suite only. The August
re-grade (Gate 2) keeps suite/k3n_suite_v1.3n.tsv unchanged, with the original Q27 excluded
(D3, n=59); the August-October consistency comparison uses the 59 shared items.

Output: one new file, the October core suite (registered name k3n_suite_v1.3n_oct.tsv,
destined for suite/). It is the August v1.3n suite with the line of each repaired item
replaced; every other line is byte-identical to the August suite (same CRLF line ends, same
csv quoting, same column and row order). The repaired line keeps the August columns except:
  question_en, question_th, gold_sql_draft   the texts of the repair file
  v13_status                                  primary
  v13_rule                                    D11
  v13_rationale                               REPAIRED_RATIONALE below
  gold_sql_v12                                empty: answer key v1.2 has no gold for the
                                              repaired question (grade_v13n.py --legacy
                                              falls back to gold_sql_draft)
tier, schema, eff, notes, order_en, order_th, sort_keys, norm, alt_gold_en and alt_gold_th
stay as in the August suite (the author recorded no alternative reading for the new text).

Modes:
  (default)  build: write --out and the sidecar <out stem>.sha256 (sha256 of the output, of
             the two inputs under neutral labels and of this builder). An existing --out or
             sidecar is refused unless --overwrite.
  --check    rebuild in memory and compare with the existing --out byte for byte; writes
             nothing. Exit 0 when identical, 1 when not.
  --pg DSN   (either mode, optional) run the repaired gold and the original gold read-only on
             the database and print the row counts (TEST-ONLY unless run by the author).
Guards (one 'REFUSED: ...' line, exit 2, nothing written):
  * the August suite sha256 differs from AUG_SUITE_SHA256 (tests pass --aug-sha256);
  * the repair file has another header, an id twice, an id that is not a core item, an empty
    question or gold, a tab or line break in a value, a v13_status other than primary, an
    empty 'decided' cell or one that still carries PENDING;
  * the repair row does not describe the August row it replaces: original_en differs from
    the August question_en, original_gold does not start with the August gold, or the
    August row is not excluded;
  * the rebuilt suite fails its own checks (60 items in the August order, no excluded item,
    only the repaired lines differ from the August suite).

Usage (one command each; from harness/ on the author's machine, every path in double quotes):
  python3 -I -B "../kst_rev/gate0/suite_tools/build_oct_core_suite.py" --check --aug-suite "../suite/k3n_suite_v1.3n.tsv" --repair "../kst_rev/gate0/suite_tools/Q27_REPAIR_2026-10-14.tsv" --out "../suite/k3n_suite_v1.3n_oct.tsv"
  python3 -I -B "../kst_rev/gate0/suite_tools/build_oct_core_suite.py" --aug-suite "../suite/k3n_suite_v1.3n.tsv" --repair "../kst_rev/gate0/suite_tools/Q27_REPAIR_2026-10-14.tsv" --out "../kst_rev/gate0/suite_tools/out/k3n_suite_v1.3n_oct.tsv"
Exit: 0 PASS, 1 --check mismatch, 2 refused input.
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import csv  # noqa: E402
import hashlib  # noqa: E402
import io  # noqa: E402
import os  # noqa: E402

# August core suite v1.3n (copy of kst_rev/wf_null/core/k3n_suite_v1.3n_DRAFT.tsv; RUNBOOK 1a.21)
AUG_SUITE_SHA256 = "195839ec46f902901f03e90965c00bb1b78b4ef6bc970f4cabb0ed0272997366"
OCT_SUITE_NAME = "k3n_suite_v1.3n_oct.tsv"
CORE_N = 60
REPAIR_HEADER = ["id", "scope", "question_en", "question_th", "gold_sql", "v13_status",
                 "decided", "testonly_k3n", "original_en", "original_gold"]
REPAIRED_RULE = "D11"
REPAIRED_RATIONALE = ("D11 (author, 14 Oct 2026): question repaired for the October session "
                      "(same month instead of same date; each pair listed once); primary in the "
                      "October suite only; the August re-grade keeps the original item excluded "
                      "(D3, n=59) and the August-October comparison uses the 59 shared items")
PENDING_WORDS = ("PENDING", "TODO", "TBD")


class Refused(Exception):
    pass


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    with open(path, "rb") as f:
        return sha256_bytes(f.read())


def parse_tsv_bytes(raw):
    """rows (lists) of a csv-quoted TSV, read exactly as csv.DictReader reads the suite"""
    return list(csv.reader(io.StringIO(raw.decode("utf-8"), newline=""), delimiter="\t"))


def serialize_row(row):
    buf = io.StringIO(newline="")
    csv.writer(buf, delimiter="\t", lineterminator="\r\n").writerow(row)
    return buf.getvalue().encode("utf-8")


def read_repair(path):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.reader(f, delimiter="\t"))
    if not rows or rows[0] != REPAIR_HEADER:
        raise Refused(f"repair file {os.path.basename(path)}: header must be "
                      f"{' '.join(REPAIR_HEADER)}")
    out = {}
    for n, r in enumerate(rows[1:], 2):
        if not any(x.strip() for x in r):
            continue
        if len(r) != len(REPAIR_HEADER):
            raise Refused(f"repair file line {n}: {len(r)} fields, expected {len(REPAIR_HEADER)}")
        d = dict(zip(REPAIR_HEADER, r))
        qid = d["id"].strip()
        if not qid or qid in out:
            raise Refused(f"repair file line {n}: empty or duplicate id {qid!r}")
        for k in ("question_en", "question_th", "gold_sql", "original_en", "original_gold"):
            if not d[k].strip():
                raise Refused(f"repair file {qid}: {k} is empty")
        for k in ("question_en", "question_th", "gold_sql"):
            if any(c in d[k] for c in "\t\r\n"):
                raise Refused(f"repair file {qid}: {k} holds a tab or a line break")
            if d[k] != d[k].strip():
                raise Refused(f"repair file {qid}: {k} has leading or trailing white space")
        if d["v13_status"].strip() != "primary":
            raise Refused(f"repair file {qid}: v13_status must be primary (found {d['v13_status']!r})")
        dec = d["decided"].strip()
        if not dec or any(w in dec.upper() for w in PENDING_WORDS):
            raise Refused(f"repair file {qid}: the 'decided' cell is empty or still pending")
        out[qid] = d
    if not out:
        raise Refused(f"repair file {os.path.basename(path)}: no repaired item")
    return out


def build(aug_raw, repair):
    """-> (bytes of the October suite, list of repaired ids). Only the lines of the repaired
    items are re-serialised; every other line is copied from the August bytes."""
    lines = aug_raw.split(b"\r\n")
    if lines[-1] != b"" or any(b"\n" in x or b"\r" in x for x in lines[:-1]):
        raise Refused("August suite: every line must end with CRLF and hold no other line break")
    rows = parse_tsv_bytes(aug_raw)
    if len(rows) != len(lines) - 1:
        raise Refused("August suite: a quoted field spans lines (not the v1.3n layout)")
    header = rows[0]
    for c in ("id", "question_en", "question_th", "gold_sql_draft", "gold_sql_v12", "v13_status",
              "v13_rule", "v13_rationale"):
        if c not in header:
            raise Refused(f"August suite: column {c} missing")
    ix = {c: header.index(c) for c in header}
    ids = [r[ix["id"]] for r in rows[1:]]
    if len(ids) != CORE_N or len(set(ids)) != CORE_N:
        raise Refused(f"August suite: {len(ids)} rows, {len(set(ids))} distinct ids "
                      f"(a core suite has {CORE_N})")
    excluded = [r[ix["id"]] for r in rows[1:] if r[ix["v13_status"]].strip() == "excluded"]
    if sorted(excluded) != sorted(repair):
        raise Refused(f"August suite: excluded items {excluded} differ from the repaired items "
                      f"{sorted(repair)} (the October suite must have no excluded item)")
    out_lines = list(lines)
    for qid, d in repair.items():
        if qid not in ids:
            raise Refused(f"repair item {qid} is not a core item")
        i = ids.index(qid) + 1
        row = list(rows[i])
        if row[ix["question_en"]] != d["original_en"]:
            raise Refused(f"{qid}: original_en of the repair file differs from the August question_en")
        if not d["original_gold"].startswith(row[ix["gold_sql_draft"]].strip()):
            raise Refused(f"{qid}: original_gold of the repair file does not start with the August gold")
        row[ix["question_en"]] = d["question_en"]
        row[ix["question_th"]] = d["question_th"]
        row[ix["gold_sql_draft"]] = d["gold_sql"]
        row[ix["gold_sql_v12"]] = ""
        row[ix["v13_status"]] = "primary"
        row[ix["v13_rule"]] = REPAIRED_RULE
        row[ix["v13_rationale"]] = REPAIRED_RATIONALE
        new = serialize_row(row)
        if not new.endswith(b"\r\n") or b"\n" in new[:-2] or b"\r" in new[:-2]:
            raise Refused(f"{qid}: the repaired line would span lines")
        out_lines[i] = new[:-2]
    oct_raw = b"\r\n".join(out_lines)
    # self-checks of the result
    got = parse_tsv_bytes(oct_raw)
    if got[0] != header or [r[ix["id"]] for r in got[1:]] != ids:
        raise Refused("rebuilt suite: header or item order changed")
    if any(r[ix["v13_status"]].strip() != "primary" for r in got[1:]):
        raise Refused("rebuilt suite: an item is not primary")
    new_lines = oct_raw.split(b"\r\n")
    changed = [ids[k - 1] for k in range(1, len(lines) - 1) if new_lines[k] != lines[k]]
    if sorted(changed) != sorted(repair) or new_lines[0] != lines[0]:
        raise Refused(f"rebuilt suite: changed lines {changed} differ from the repaired items")
    for qid, d in repair.items():
        r = dict(zip(header, got[ids.index(qid) + 1]))
        if (r["question_en"], r["question_th"], r["gold_sql_draft"]) != \
                (d["question_en"], d["question_th"], d["gold_sql"]):
            raise Refused(f"rebuilt suite: {qid} does not read back as the repair texts")
    return oct_raw, sorted(repair)


def gold_counts(dsn, aug_raw, oct_raw, repaired):
    import psycopg2
    conn = psycopg2.connect(dsn)
    conn.set_session(readonly=True, autocommit=False)
    out = []
    try:
        for label, raw in (("October", oct_raw), ("August", aug_raw)):
            rows = parse_tsv_bytes(raw)
            ix = {c: rows[0].index(c) for c in rows[0]}
            for r in rows[1:]:
                if r[ix["id"]] in repaired:
                    with conn.cursor() as cur:
                        cur.execute("SET LOCAL statement_timeout = '20s'")
                        cur.execute(r[ix["gold_sql_draft"]].strip().rstrip(";"))
                        out.append((label, r[ix["id"]], len(cur.fetchall())))
                    conn.rollback()
    finally:
        conn.close()
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--aug-suite", required=True, help="August core suite v1.3n (suite/k3n_suite_v1.3n.tsv)")
    ap.add_argument("--repair", required=True, help="Q27_REPAIR_2026-10-14.tsv")
    ap.add_argument("--out", required=True, help=f"October core suite ({OCT_SUITE_NAME})")
    ap.add_argument("--check", action="store_true", help="compare with the existing --out; write nothing")
    ap.add_argument("--overwrite", action="store_true", help="build mode: replace an existing --out")
    ap.add_argument("--aug-sha256", default=AUG_SUITE_SHA256,
                    help="expected sha256 of --aug-suite (default: the registered August suite)")
    ap.add_argument("--pg", default=None, help="libpq DSN: print the gold row counts (read only)")
    a = ap.parse_args()
    try:
        if os.path.basename(a.out) != OCT_SUITE_NAME:
            print(f"note: --out is not named {OCT_SUITE_NAME} (registered name of the October suite)")
        if "DRAFT" in os.path.basename(a.out).upper():
            raise Refused("--out name holds DRAFT (the runner and the grader would treat the suite as a draft)")
        aug_raw = open(a.aug_suite, "rb").read()
        aug_sha = sha256_bytes(aug_raw)
        if aug_sha != a.aug_sha256.strip().lower():
            raise Refused(f"--aug-suite sha256 {aug_sha[:12]}... differs from the expected "
                          f"{a.aug_sha256.strip()[:12]}... (registered August suite v1.3n)")
        repair = read_repair(a.repair)
        oct_raw, repaired = build(aug_raw, repair)
    except (Refused, OSError, UnicodeDecodeError, csv.Error) as e:
        print(f"REFUSED: {e}")
        sys.exit(2)
    oct_sha = sha256_bytes(oct_raw)
    rep_sha = sha256_file(a.repair)
    me_sha = sha256_file(os.path.abspath(__file__))
    print(f"August suite: sha256 {aug_sha} ({CORE_N} items; excluded {repaired})")
    print(f"repair file: sha256 {rep_sha} (items {repaired})")
    print(f"October suite: {CORE_N} items, every item primary; lines replaced {repaired}; "
          f"the other {CORE_N - len(repaired)} item lines and the header byte-identical to the August suite")
    print(f"October suite sha256 {oct_sha}")
    if a.pg:
        try:
            for label, qid, n in gold_counts(a.pg, aug_raw, oct_raw, repaired):
                print(f"gold rows ({label} {qid}) on the --pg database: {n}")
        except Exception as e:  # noqa: BLE001 -- the database error type only
            print(f"REFUSED: --pg query failed ({type(e).__name__})")
            sys.exit(2)
    if a.check:
        if not os.path.isfile(a.out):
            print(f"CHECK: FAIL ({os.path.basename(a.out)} not found)")
            sys.exit(1)
        have = open(a.out, "rb").read()
        if have != oct_raw:
            print(f"CHECK: FAIL ({os.path.basename(a.out)} sha256 {sha256_bytes(have)} differs from the rebuilt suite)")
            sys.exit(1)
        print(f"CHECK: PASS ({os.path.basename(a.out)} equals the rebuilt suite byte for byte)")
        sys.exit(0)
    stem = os.path.splitext(a.out)[0]
    side = stem + ".sha256"
    for p in (a.out, side):
        if os.path.exists(p) and not a.overwrite:
            print(f"REFUSED: {os.path.basename(p)} exists (pass --overwrite to replace it)")
            sys.exit(2)
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    tmp = a.out + ".tmp"
    with open(tmp, "wb") as f:
        f.write(oct_raw)
    os.replace(tmp, a.out)
    with open(side + ".tmp", "w", encoding="utf-8", newline="\n") as f:
        f.write(f"{oct_sha}  {os.path.basename(a.out)}\n")
        f.write(f"{aug_sha}  aug_suite_v1.3n\n")
        f.write(f"{rep_sha}  q27_repair\n")
        f.write(f"{me_sha}  builder/build_oct_core_suite.py\n")
    os.replace(side + ".tmp", side)
    print(f"written: {os.path.basename(a.out)} and {os.path.basename(side)}")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
