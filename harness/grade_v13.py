"""
grade_v13.py -- execute-and-compare grader for answer key v1.3 (D7).

Execution semantics are identical to grade.py (run-of-record grader):
  PostgreSQL via psycopg2, read-only session, SET LOCAL statement_timeout 20s
  + 20 s SIGALRM per candidate, rollback after every query, error records
  skipped, parse_ok False -> wrong ('parse'), non-SELECT/WITH -> wrong.

Comparison under rule R-v1.3 (answer key v1.3, dated amendment):
  general rules (every item, both languages)
    G1 column order is not graded: the answer matches if some permutation
       of its columns equals the key (column COUNT must still match, i.e.
       the projection frozen by AMENDMENT-2 stays exact)
    G2 numeric values compare by value regardless of SQL type or scale
       (int / NUMERIC / float), canonicalised to 6 decimal places
    G3 a date equals a timestamp/timestamptz at midnight of that date
       (time-zone suffix of the session is not graded)
    G4 row order is graded only where the question, in that language,
       asks for an order (suite columns order_en / order_th); rows tied on
       the requested sort keys (suite column sort_keys) may appear in any
       order
  item-scoped acceptance sets (suite columns, written from the question
  text before re-grading)
    norm         per-column value encoding left open by the question
                 (month2024 | round2 | abs | decade)
    alt_gold_en  JSON list of alternative gold SQL accepted in EN
    alt_gold_th  JSON list of alternative gold SQL accepted in TH
    v13_status   primary | excluded  (excluded = gold empty on run DB)

Modes
  default            v1.3 rules, excluded items skipped
  --keep-excluded    also grade excluded items (n=60 sensitivity)
  --colperm off      v1.3 rules but positional columns (sensitivity)
  --legacy           exact grade.py v1.2 comparison with gold_sql_v12
                     (parity check: must reproduce results/graded.csv)

Output columns: graded.csv columns + arm, n_rows, matched_gold,
                correct_positional, correct_v12

Usage:
  python3 grade_v13.py --results ../results/results.jsonl \
    --suite ../suite/k3_suite_v1.3.tsv --pg "dbname=k3" \
    --out ../results/v13/graded_v13.csv
"""
import argparse
import csv
import datetime as dt
import itertools
import json
import re
import signal
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

ORDER_RE = re.compile(r"order\s+by", re.I)
SIX_DP = Decimal("0.000001")
TWO_DP = Decimal("0.01")
MONTHS = {m: i for i, m in enumerate(
    ["january", "february", "march", "april", "may", "june", "july",
     "august", "september", "october", "november", "december"], 1)}
MONTHS.update({k[:3]: v for k, v in list(MONTHS.items())})


# ---------------------------------------------------------------- v1.2 (frozen)
def has_toplevel_order(sql):
    out, depth = [], 0
    for ch in sql:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth = max(0, depth - 1)
        elif depth == 0:
            out.append(ch)
    return bool(ORDER_RE.search("".join(out)))


def canon_v12(rows, ordered):
    def cv(v):
        if v is None:
            return "\\N"
        if isinstance(v, float):
            return f"{v:.6g}"
        return str(v)
    out = [tuple(cv(v) for v in r) for r in rows]
    return out if ordered else sorted(out)


# ---------------------------------------------------------------- v1.3 values
def _num(v):
    """int / Decimal / float -> Decimal, else None"""
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return Decimal(v)
    if isinstance(v, Decimal):
        return v if v.is_finite() else None
    if isinstance(v, float):
        if v != v or v in (float("inf"), float("-inf")):
            return None
        return Decimal(repr(v))
    return None


def _fmt(d):
    d = d.quantize(SIX_DP, rounding=ROUND_HALF_UP).normalize()
    s = format(d, "f")
    return "0" if s in ("-0", "0", "-0.0") else s


def _num_from_str(s):
    try:
        return Decimal(s.strip())
    except (InvalidOperation, AttributeError):
        return None


def apply_norm(v, norm):
    if v is None or not norm:
        return v
    if norm == "round2":
        d = _num(v)
        return d.quantize(TWO_DP, rounding=ROUND_HALF_UP) if d is not None else v
    if norm == "abs":
        d = _num(v)
        return abs(d) if d is not None else v
    if norm == "decade":
        d = _num(v)
        if d is None and isinstance(v, str):
            m = re.fullmatch(r"\s*(\d{3,4})\s*'?s?\s*", v)
            d = Decimal(m.group(1)) if m else None
        return d if d is not None else v
    if norm.startswith("month"):
        year = int(norm[5:])
        if isinstance(v, (dt.datetime, dt.date)):
            return f"{v.year:04d}-{v.month:02d}"
        d = _num(v)
        if d is None and isinstance(v, str):
            s = v.strip()
            m = re.match(r"^(\d{4})-(\d{2})", s)
            if m:
                return f"{m.group(1)}-{m.group(2)}"
            if s.lower() in MONTHS:
                return f"{year:04d}-{MONTHS[s.lower()]:02d}"
            d = _num_from_str(s)
        if d is not None and d == d.to_integral_value() and 1 <= d <= 12:
            return f"{year:04d}-{int(d):02d}"
        return v
    raise ValueError("unknown norm " + norm)


def cv13(v, norm=None):
    v = apply_norm(v, norm)
    if v is None:
        return "\\N"
    d = _num(v)
    if d is not None:
        return _fmt(d)
    if isinstance(v, dt.datetime):
        if (v.hour, v.minute, v.second, v.microsecond) == (0, 0, 0, 0):
            return v.date().isoformat()
        return str(v)
    if isinstance(v, dt.date):
        return v.isoformat()
    return str(v)


def parse_norms(spec):
    out = {}
    for part in (spec or "").split(";"):
        part = part.strip()
        if part:
            col, kind = part.split(":", 1)
            out[int(col)] = kind.strip()
    return out


def parse_keys(spec):
    spec = (spec or "").strip()
    return tuple(int(x) for x in spec.split(",")) if spec else None


def match_v13(ans, gold, ordered, sort_keys, norms, colperm=True):
    """ans, gold: lists of raw row tuples. Returns True iff equal under R-v1.3."""
    if len(ans) != len(gold):
        return False
    if not gold:
        return True
    k = len(gold[0])
    if len(ans[0]) != k:
        return False
    G = [tuple(cv13(r[j], norms.get(j)) for j in range(k)) for r in gold]
    gcol = [sorted(row[j] for row in G) for j in range(k)]
    cand = []
    for j in range(k):
        cj = []
        for c in (range(k) if colperm else [j]):
            if sorted(cv13(r[c], norms.get(j)) for r in ans) == gcol[j]:
                cj.append(c)
        if not cj:
            return False
        cand.append(cj)
    if ordered:
        bounds, start = [], 0
        if sort_keys:
            for i in range(1, len(G) + 1):
                if i == len(G) or tuple(G[i][x] for x in sort_keys) != \
                        tuple(G[start][x] for x in sort_keys):
                    bounds.append((start, i))
                    start = i
    gsorted = sorted(G)
    for perm in itertools.product(*cand):
        if len(set(perm)) != k:
            continue
        A = [tuple(cv13(r[perm[j]], norms.get(j)) for j in range(k)) for r in ans]
        if not ordered:
            if sorted(A) == gsorted:
                return True
        elif sort_keys is None:
            if A == G:
                return True
        elif all(sorted(A[s:e]) == sorted(G[s:e]) for s, e in bounds):
            return True
    return False


# ---------------------------------------------------------------- engine
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


def make_engine(dsn):
    import psycopg2
    conn = psycopg2.connect(dsn)
    conn.set_session(readonly=True, autocommit=False)

    def q(sql):
        try:
            with conn.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout = '20s'")
                cur.execute(sql)
                return cur.fetchall()
        finally:
            conn.rollback()
    return q


def load_suite(path):
    return {r["id"]: r for r in csv.DictReader(open(path, encoding="utf-8"), delimiter="\t")}


def item_keys(q, item, lang):
    """list of (label, raw gold rows) accepted for this item and language"""
    sql = item["gold_sql_draft"].strip().rstrip(";")
    keys = [("primary", q(sql))]
    alts = json.loads(item.get(f"alt_gold_{lang}") or "[]")
    for i, a in enumerate(alts, 1):
        keys.append((f"alt{i}", q(a.strip().rstrip(";"))))
    return keys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--pg", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--colperm", choices=["on", "off"], default="on")
    ap.add_argument("--keep-excluded", action="store_true")
    ap.add_argument("--legacy", action="store_true",
                    help="frozen v1.2 comparison with gold_sql_v12 only")
    a = ap.parse_args()

    q = make_engine(a.pg)
    suite = load_suite(a.suite)
    colperm = a.colperm == "on"

    v12 = {}
    for qid, item in suite.items():
        sql = (item.get("gold_sql_v12") or item["gold_sql_draft"]).strip().rstrip(";")
        o = has_toplevel_order(sql)
        v12[qid] = (canon_v12(q(sql), o), o)

    keys = {}
    if not a.legacy:
        for qid, item in suite.items():
            for lang in ("en", "th"):
                keys[(qid, lang)] = item_keys(q, item, lang)

    out = csv.writer(open(a.out, "w", newline="", encoding="utf-8"))
    out.writerow(["model_key", "lang", "qid", "tier", "schema", "run",
                  "parse_ok", "exec_ok", "correct", "latency_s", "fail_reason",
                  "arm", "n_rows", "matched_gold", "correct_positional", "correct_v12"])
    stats = {}
    for line in open(a.results, encoding="utf-8"):
        rec = json.loads(line)
        if rec.get("error") is not None:
            continue
        qid, lang = rec["qid"], rec["lang"]
        item = suite[qid]
        excluded = (item.get("v13_status") or "primary").strip() == "excluded"
        if excluded and not (a.keep_excluded or a.legacy):
            continue
        parse_ok = rec.get("parse_ok", False)
        exec_ok, correct, reason = False, False, ""
        n_rows, matched, c_pos, c12 = "", "", False, False
        if not parse_ok:
            reason = "parse"
        else:
            sql = rec["sql"]
            if not sql.lower().lstrip().startswith(("select", "with")):
                reason = "non-select"
            else:
                try:
                    rows = run_with_timeout(lambda: q(sql))
                    exec_ok = True
                    n_rows = len(rows)
                    g12, o12 = v12[qid]
                    c12 = canon_v12(rows, o12) == g12
                    if a.legacy:
                        correct = c12
                    else:
                        ordered = (item.get(f"order_{lang}") or "no").strip() == "yes"
                        sk = parse_keys(item.get("sort_keys"))
                        norms = parse_norms(item.get("norm"))
                        for label, grows in keys[(qid, lang)]:
                            if match_v13(rows, grows, ordered, sk, norms, colperm):
                                correct, matched = True, label
                                break
                        for label, grows in keys[(qid, lang)]:
                            if match_v13(rows, grows, ordered, sk, norms, False):
                                c_pos = True
                                break
                    if not correct:
                        reason = "wrong-result"
                except Timeout:
                    reason = "timeout"
                except Exception as e:
                    reason = "exec-error: " + str(e).split("\n")[0][:120]
        out.writerow([rec["model_key"], lang, qid, rec["tier"], rec["schema"],
                      rec["run"], parse_ok, exec_ok, correct, rec.get("latency_s"),
                      reason, rec.get("arm", "base"), n_rows, matched, c_pos, c12])
        s = stats.setdefault((rec["model_key"], lang), [0, 0])
        s[1] += 1
        s[0] += 1 if correct else 0
    print("run-level accuracy (raw, before majority):")
    for (mk, lang), (c, t) in sorted(stats.items()):
        print(f"  {mk:22s} {lang}: {c}/{t} = {c/t:.3f}")


if __name__ == "__main__":
    main()
