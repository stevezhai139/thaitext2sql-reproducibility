#!/usr/bin/env python3
"""
empty_split_v13.py -- AMENDMENT-7 B1 (D3; R1-W4/R1-RC4): split wrong runs into
loud / silent-empty / silent-non-empty without changing any correctness label,
re-executing every candidate on the run DB (k3n) for the diagnostics that the graded
file does not keep (column count, shape match, NULL/0-only, order-only).

Origin: kst_rev/drafts/empty_split.py. Changes (GATE0 design 2.6):
  * the cross-check label is recomputed with the grader of record grade_v13n.py
    (every accepted key of the item and language, G1-G4, norm, and the directional
    items exactly as the grader resolves them: grade_v13n.roles_by_item on
    --columns suite_columns.json, i.e. the col_roles column or the registry, including
    the OQ35 core entry, DECIDED (a) by the author on 14 Oct 2026) instead of grade.canon
    (l.215-221);
  * key = (model, arm, lang, qid, run) (l.183-186), so a two-arm file has no key clash;
  * excluded items (v13_status) are skipped unless --keep-excluded (l.190-196); D11
    (analyze.d11_check): on the October core suite Q27 is repaired and primary (its gold
    is re-executed like every other item) and only the two-arm October core log is
    accepted; --keep-excluded with the August suite on the October log is refused;
  * item-level class (AM-7 B1: loud / silent-empty / silent-non-empty): the four loud
    sub-classes are mapped to 'loud' first, then the class of strictly more than half of
    the failing runs of a majority-wrong cell, otherwise 'mixed' (l.316-330); the item
    rows keep the loud sub-class (strict majority among the loud runs, else
    'loud_sub_mixed') in the sub-class columns, which therefore sum to loud_total;
  * the graded file must carry n_rows (grade_v13n.py); a blank n_rows on an executed
    wrong run stops (analyze.b1_class), as in every B1 script;
  * a DRAFT suite is refused unless --allow-draft-testonly with outputs outside results/
    (analyze.draft_guard; the grader's functions are imported, so its own guard does not run);
  * VG / non-VG subsets come from --vg-set;
  * --arm contract of analyze.py; --results may repeat (api + local);
  * MI items (suite column mi_instances not empty) stay out of the split and are
    listed (OQ23 default; their n_rows comes from the base instance only).
The graded file stays AUTHORITATIVE: classes come from its label; the recomputed label
is a check only. Any label mismatch is listed (keys only) and the exit status is 2.
results*.jsonl is read through a hook that keeps model_key, arm, lang, qid, run, sql
and parse_ok and turns 'error' into a boolean (never kept or printed).

Classes (one per record)
  correct | loud_parse | loud_nonselect | loud_exec | loud_timeout
  silent_empty (exec_ok, wrong, 0 rows) | silent_nonempty (exec_ok, wrong, >=1 row)
Diagnostics on silent_nonempty: nullzero, shape_match (rows x cols of the primary
gold), order_only (same multiset as an accepted key, wrong order where the question
asks for an order); on every record: thai_literal (some string literal outside comments
holds Thai script: vg_classifier.has_thai_literal, the one definition that the B2.3
THAI_COPY class also uses).

Usage (Gate 3 step 36):
  python3 -I -B empty_split_v13.py --results ../results/rc1/results_rc1_api.jsonl \
      --results ../results/rc1/results_rc1_local.jsonl --graded ../results/rc1/graded_rc1.csv \
      --suite ../suite/k3n_suite_v1.3n_oct.tsv --pg "dbname=k3n" --arm base \
      --vg-set ../suite/vg_set_v13n.txt --out-rows ../results/rc1/base60/partB/silent_split_rows.csv \
      --out-summary ../results/rc1/base60/partB/silent_split.csv
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import os
import sys
from collections import Counter, defaultdict
from decimal import Decimal

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402
import vg_classifier as vgc  # noqa: E402

FRONTIER = ("claude-sonnet", "gpt-mini", "gemini-flash")
LOCAL = ("qwen25-coder-7b", "llama31-8b", "typhoon2-8b")
LOUD = ("loud_parse", "loud_nonselect", "loud_exec", "loud_timeout")
_KEEP = ("model_key", "arm", "lang", "qid", "run", "sql", "parse_ok")


def load_grader(path):
    spec = importlib.util.spec_from_file_location("grade_v13n", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _hook(pairs):
    d = {}
    for k, v in pairs:
        if k == "error":
            d["error"] = v is not None
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
                    ac.die(2, f"{os.path.basename(path)} line {n}: not JSON")


def make_pg(dsn):
    """same session settings as grade_v13n.make_engine plus the column count."""
    import psycopg2
    conn = psycopg2.connect(dsn)
    conn.set_session(readonly=True, autocommit=False)

    def q(sql):
        try:
            with conn.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout = '20s'")
                cur.execute(sql)
                rows = cur.fetchall()
                ncols = len(cur.description) if cur.description else 0
            return rows, ncols
        finally:
            conn.rollback()

    with conn.cursor() as cur:
        cur.execute("SELECT version()")
        ver = cur.fetchone()[0]
    conn.rollback()
    return q, ver


def parse_roles(spec, k):
    """col_roles of the suite: '' -> (); '*' -> whole projection; 'i,j;k,l' -> groups."""
    spec = (spec or "").strip()
    if not spec:
        return ()
    if spec == "*":
        return (tuple(range(k)),)
    return tuple(tuple(int(x) for x in grp.split(",")) for grp in spec.split(";") if grp.strip())


class Matcher:
    """correctness under the grader of record for one (item, language)."""

    def __init__(self, grader, roles):
        self.g = grader
        self.has_perms = hasattr(grader, "match_perms")
        self.roles = roles            # {qid: parsed roles} as the grader resolves them

    def match(self, qid, rows, keyrows, ordered, sk, norms, use_roles=True):
        roles = self.roles.get(qid) if use_roles else None
        if roles:
            if not self.has_perms:
                return None   # cannot recompute; reported as label_check=skipped
            if isinstance(roles, str):   # fallback: raw col_roles text of the suite
                k = len(keyrows[0]) if keyrows else (len(rows[0]) if rows else 0)
                roles = parse_roles(roles, k)
            res = self.g.match_perms(rows, keyrows, ordered, sk, norms, True, roles)
            return res is None or bool(res)
        return self.g.match_v13(rows, keyrows, ordered, sk, norms, True)


def resolve_roles(grader, suite_path, suite, columns_path):
    """{qid: roles} of the directional items, the way grade_v13n does it (col_roles
    column of the suite, otherwise the registry of suite_columns.json incl. the
    OQ35 core entry). A grader without that API falls back to the suite column."""
    if hasattr(grader, "roles_by_item") and hasattr(grader, "load_columns"):
        if not os.path.exists(columns_path):
            ac.die(2, f"suite_columns.json not found ({os.path.basename(columns_path)}); give --columns")
        with open(suite_path, encoding="utf-8", newline="") as fh:
            header = list(csv.DictReader(fh, delimiter="\t").fieldnames or [])
        try:
            cols = grader.load_columns(columns_path)
            return grader.roles_by_item(suite, header, cols, False), "grade_v13n.roles_by_item"
        except Exception as e:   # grade_v13n.Refuse
            ac.die(2, f"roles of the suite refused by the grader: {e}")
    out = {q: (it.get("col_roles") or "").strip() for q, it in suite.items()
           if (it.get("col_roles") or "").strip()}
    return out, "suite col_roles column (grader without roles_by_item)"


def is_nullzero(rows):
    if not rows:
        return False
    for r in rows:
        for v in r:
            if v is None:
                continue
            if isinstance(v, bool):
                return False
            if isinstance(v, (int, float, Decimal)) and v == 0:
                continue
            return False
    return True


def classify(g):
    """class from the AUTHORITATIVE graded row (None = resolved by n_rows)"""
    if g["correct"] == "True":
        return "correct"
    fr = g["fail_reason"]
    if fr == "parse":
        return "loud_parse"
    if fr == "non-select":
        return "loud_nonselect"
    if fr == "timeout":
        return "loud_timeout"
    if fr.startswith("exec-error"):
        return "loud_exec"
    if fr == "wrong-result":
        return None
    raise SystemExit(f"unknown fail_reason category in the graded file: {fr[:20]!r}")


def reason_cat(fr):
    return "exec-error" if fr.startswith("exec-error") else fr


def item_class(wrong_classes):
    """strictly more than half of the failing runs, otherwise 'mixed' (AM-7 B1)."""
    cnt = Counter(wrong_classes)
    if not cnt:
        return None
    top, n = cnt.most_common(1)[0]
    return top if n > len(wrong_classes) / 2 else "mixed"


def item_b1(wrong_classes):
    """(item class, loud sub-class) of a majority-wrong cell from the run classes of its
    failing runs: the loud sub-classes count as 'loud' (AM-7 B1 three classes, strict
    majority, else 'mixed'); for a 'loud' item the sub-class of strictly more than half
    of its loud runs, else 'loud_sub_mixed'."""
    cls = item_class(["loud" if c in LOUD else c for c in wrong_classes])
    loud_sub = ""
    if cls == "loud":
        ls = item_class([c for c in wrong_classes if c in LOUD])
        loud_sub = ls if ls in LOUD else "loud_sub_mixed"
    return cls, loud_sub


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", required=True, action="append")
    ap.add_argument("--graded", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--pg", required=True)
    ap.add_argument("--vg-set", required=True)
    ap.add_argument("--out-rows", required=True)
    ap.add_argument("--out-summary", required=True)
    ap.add_argument("--keep-excluded", action="store_true")
    ap.add_argument("--grader", default=os.path.join(HERE, "grade_v13n.py"),
                    help="grader of record (default grade_v13n.py next to this script)")
    ap.add_argument("--columns", help="suite_columns.json of the grader (default: next to "
                                      "--grader); decides the directional items (OQ35)")
    ac.add_arm_contract(ap)
    ac.add_draft_flag(ap)
    a = ap.parse_args()

    suite_rows = ac.load_suite_rows(a.suite)
    ac.draft_guard(a.suite, suite_rows, a.allow_draft_testonly,
                   out_files=[a.out_rows, a.out_summary])
    rows_all = ac.read_csv_rows(a.graded)
    grec = ac.graded_record(a.graded, rows_all, a.arm)
    ac.d11_check(suite_rows, a.keep_excluded, grec, os.path.basename(a.suite))
    grader = load_grader(a.grader)
    q, ver = make_pg(a.pg)
    print(f"engine: {ver}")

    roles, roles_how = resolve_roles(grader, a.suite, suite_rows, a.columns or os.path.join(
        os.path.dirname(os.path.abspath(a.grader)), "suite_columns.json"))
    matcher = Matcher(grader, roles)
    print(f"directional items ({roles_how}): {sorted(roles) or 'none'}")
    full = ac.primary_suite(suite_rows, a.keep_excluded)
    mi_items = sorted(k for k, v in full.items()
                      if json.loads((v.get("mi_instances") or "[]").strip() or "[]"))
    suite = {k: v for k, v in full.items() if k not in mi_items}
    if mi_items:
        print(f"MI items kept out of the split (OQ23; reported per instance elsewhere): {mi_items}")
    vgs = set(ac.read_vg_set(a.vg_set, universe=full))
    print(f"VG set ({len(vgs)}): {' '.join(sorted(vgs))}")

    excluded = ac.split_list(a.exclude_models)
    if rows_all and "n_rows" not in rows_all[0]:
        ac.die(2, "the graded file has no n_rows column; empty_split_v13 needs the graded "
                  "file of grade_v13n.py")
    graded_rows = ac.filter_arm(rows_all, a.arm, excluded)
    ac.require_complete(graded_rows, a.runs, sorted(full))

    # ---- 1. accepted keys per item x language, primary gold shape ----
    keys, gshape = {}, {}
    for qid, it in suite.items():
        sql = it["gold_sql_draft"].strip().rstrip(";")
        rows, ncols = q(sql)
        gshape[qid] = (len(rows), ncols)
        for lang in ("en", "th"):
            ks = [("primary", rows)]
            for i, alt in enumerate(json.loads(it.get(f"alt_gold_{lang}") or "[]"), 1):
                ks.append((f"alt{i}", q(alt.strip().rstrip(";"))[0]))
            keys[(qid, lang)] = ks
    empty_gold = sorted(k for k, v in gshape.items() if v[0] == 0)
    print(f"gold executed: {len(gshape)} items; primary gold with 0 rows: {empty_gold or 'none'}")

    # ---- 2. graded rows (authoritative) ----
    graded = {}
    for g in graded_rows:
        if g["qid"] not in suite:
            continue
        k = (g["model_key"], ac.row_arm(g), g["lang"], g["qid"], str(g["run"]))
        if k in graded:
            ac.die(2, f"duplicate key in the graded file: {k}")
        if g["correct"] != "True":
            ac.b1_class(g)   # stops on a blank n_rows of an executed wrong run
        graded[k] = g

    # ---- 3. re-execute candidates ----
    out_rows, mismatches, skipped_check, seen = [], [], 0, set()
    for rec in iter_records(a.results):
        if rec.get("error"):
            continue
        if ac.row_arm(rec) != a.arm or rec.get("model_key") in excluded:
            continue
        if rec["qid"] not in suite:
            continue
        k = (rec["model_key"], ac.row_arm(rec), rec["lang"], rec["qid"], str(rec["run"]))
        if k not in graded:
            ac.die(2, f"record not in the graded file: {k}")
        if k in seen:
            ac.die(2, f"duplicate non-error record in results: {k}")
        seen.add(k)
        g = graded[k]
        it = suite[rec["qid"]]
        lang = rec["lang"]
        ordered = (it.get(f"order_{lang}") or "no").strip() == "yes"
        sk = grader.parse_keys(it.get("sort_keys"))
        norms = grader.parse_norms(it.get("norm"))

        parse_ok = bool(rec.get("parse_ok", False))
        exec_ok, correct, reason = False, False, ""
        n_rows = n_cols = ""
        nullzero = order_only = shape_match = False
        digest = ""
        check_possible = True
        if not parse_ok:
            reason = "parse"
        else:
            sql = rec.get("sql") or ""
            if not sql.lower().lstrip().startswith(("select", "with")):
                reason = "non-select"
            else:
                try:
                    rows, ncols = grader.run_with_timeout(lambda: q(sql))
                    exec_ok = True
                    hits = [matcher.match(rec["qid"], rows, grows, ordered, sk, norms)
                            for _, grows in keys[(rec["qid"], lang)]]
                    if any(h is None for h in hits):
                        check_possible = False
                    correct = any(h for h in hits)
                    if not correct:
                        reason = "wrong-result"
                    n_rows, n_cols = len(rows), ncols
                    nullzero = is_nullzero(rows)
                    shape_match = (n_rows, n_cols) == gshape[rec["qid"]]
                    order_only = bool(not correct and ordered and any(
                        matcher.match(rec["qid"], rows, grows, False, None, norms, use_roles=False)
                        for _, grows in keys[(rec["qid"], lang)]))
                    digest = hashlib.sha1(repr(sorted(
                        tuple(grader.cv13(v) for v in r) for r in rows)).encode("utf-8")).hexdigest()[:12]
                except grader.Timeout:
                    reason = "timeout"
                except Exception as e:
                    reason = "exec-error: " + str(e).split("\n")[0][:120]

        graded_n = (g.get("n_rows") or "").strip()
        same = (str(parse_ok) == g["parse_ok"] and str(exec_ok) == g["exec_ok"]
                and (not check_possible or str(correct) == g["correct"])
                and reason_cat(reason) == reason_cat(g["fail_reason"])
                and (not exec_ok or graded_n == str(n_rows)))
        if not check_possible:
            skipped_check += 1
        if not same:
            mismatches.append(k)

        cls = classify(g)
        if cls is None:
            if n_rows == "":
                cls = "silent_unresolved"
            else:
                cls = "silent_empty" if n_rows == 0 else "silent_nonempty"
        out_rows.append(dict(
            model_key=k[0], arm=k[1], lang=k[2], qid=k[3], run=k[4],
            tier=g["tier"], schema=g["schema"], vg=k[3] in vgs,
            correct=g["correct"], fail_cat=reason_cat(g["fail_reason"]),
            n_rows=n_rows, n_cols=n_cols,
            gold_rows=gshape[k[3]][0], gold_cols=gshape[k[3]][1],
            cls=cls,
            nullzero=cls == "silent_nonempty" and nullzero,
            shape_match=cls == "silent_nonempty" and shape_match,
            order_only=cls == "silent_nonempty" and order_only,
            thai_literal=bool(parse_ok and vgc.has_thai_literal(rec.get("sql") or "")),
            result_sha1=digest,
            label_check=("ok" if same else "MISMATCH") if check_possible else "skipped_col_roles"))

    missing = set(graded) - seen
    if missing:
        ac.die(2, f"{len(missing)} graded rows have no results record (first: {sorted(missing)[:3]})")
    if not out_rows:
        ac.die(2, "no records to split")

    os.makedirs(os.path.dirname(os.path.abspath(a.out_rows)), exist_ok=True)
    with open(a.out_rows, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(out_rows[0]))
        w.writeheader()
        w.writerows(out_rows)

    # ---- 4. summaries ----
    present = sorted({r["model_key"] for r in out_rows})
    scopes = {"all": set(present), "frontier": set(FRONTIER) & set(present),
              "local": set(LOCAL) & set(present)}
    for m in present:
        scopes["model:" + m] = {m}
    subsets = {"all": lambda r: True, "vg": lambda r: r["vg"],
               "nonvg": lambda r: not r["vg"]}
    cols = ["unit", "scope", "lang", "subset", "n", "n_wrong", "loud_total",
            "loud_parse", "loud_nonselect", "loud_exec", "loud_timeout", "loud_sub_mixed",
            "silent_total", "silent_empty", "silent_nonempty", "mixed",
            "silent_nonempty_nullzero", "silent_nonempty_shape_match",
            "silent_nonempty_order_only", "silent_unresolved",
            "silent_empty_thai_literal", "silent_nonempty_thai_literal"]
    summary = []

    def tally(rows, unit, scope, lang, subset):
        c = Counter(r["cls"] for r in rows)
        sn = [r for r in rows if r["cls"] == "silent_nonempty"]
        if unit == "run":
            sub = {x: c[x] for x in LOUD}
            sub["loud_sub_mixed"] = 0
        else:   # item rows: 'loud' items by their loud sub-class (strict majority)
            sub = Counter(r["loud_sub"] for r in rows if r["cls"] == "loud")
        summary.append(dict(
            unit=unit, scope=scope, lang=lang, subset=subset, n=len(rows),
            n_wrong=len(rows) - c["correct"],
            loud_total=c["loud"] + sum(c[x] for x in LOUD),
            loud_parse=sub["loud_parse"], loud_nonselect=sub["loud_nonselect"],
            loud_exec=sub["loud_exec"], loud_timeout=sub["loud_timeout"],
            loud_sub_mixed=sub["loud_sub_mixed"],
            silent_total=c["silent_empty"] + c["silent_nonempty"] + c["silent_unresolved"],
            silent_empty=c["silent_empty"], silent_nonempty=c["silent_nonempty"],
            mixed=c["mixed"],
            silent_nonempty_nullzero=sum(1 for r in sn if r["nullzero"]),
            silent_nonempty_shape_match=sum(1 for r in sn if r["shape_match"]),
            silent_nonempty_order_only=sum(1 for r in sn if r["order_only"]),
            silent_unresolved=c["silent_unresolved"],
            silent_empty_thai_literal=sum(1 for r in rows if r["cls"] == "silent_empty"
                                          and r["thai_literal"]),
            silent_nonempty_thai_literal=sum(1 for r in sn if r["thai_literal"])))

    for sname, ms in scopes.items():
        for lang in ("all", "en", "th"):
            for subname, pred in subsets.items():
                rows = [r for r in out_rows if r["model_key"] in ms
                        and (lang == "all" or r["lang"] == lang) and pred(r)]
                tally(rows, "run", sname, lang, subname)

    by_cell = defaultdict(list)
    for r in out_rows:
        by_cell[(r["model_key"], r["lang"], r["qid"])].append(r)
    items = []
    for (m, lang, qid), rs in sorted(by_cell.items()):
        if sum(r["correct"] == "True" for r in rs) > len(rs) / 2:
            continue
        wrong = [r for r in rs if r["correct"] != "True"]
        cls, loud_sub = item_b1([r["cls"] for r in wrong])
        rep = next((r for r in wrong if ("loud" if r["cls"] in LOUD else r["cls"]) == cls), wrong[0])
        items.append(dict(rep, cls=cls, loud_sub=loud_sub, lang=lang))
    for sname, ms in scopes.items():
        for lang in ("all", "en", "th"):
            for subname, pred in subsets.items():
                rows = [r for r in items if r["model_key"] in ms
                        and (lang == "all" or r["lang"] == lang) and pred(r)]
                tally(rows, "item_majority_wrong", sname, lang, subname)

    os.makedirs(os.path.dirname(os.path.abspath(a.out_summary)), exist_ok=True)
    with open(a.out_summary, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(summary)

    def pick(unit, scope, lang, subset):
        return next((s for s in summary if (s["unit"], s["scope"], s["lang"], s["subset"])
                     == (unit, scope, lang, subset)), None)

    def pct(x, n):
        return f"{100 * x / n:.1f}%" if n else "n/a"

    print(f"\nrecords re-executed: {len(out_rows)}; label check: "
          f"{len(out_rows) - len(mismatches) - skipped_check} ok, {len(mismatches)} MISMATCH, "
          f"{skipped_check} skipped (col_roles without grade_v13n.match_perms)")
    f_ = pick("run", "frontier", "all", "all")
    if f_ and f_["n_wrong"]:
        print("HEADLINE (frontier, run level): of "
              f"{f_['n_wrong']} error records, {f_['loud_total']} raise an error, "
              f"{f_['silent_empty']} execute and return an EMPTY result "
              f"({pct(f_['silent_empty'], f_['n_wrong'])}), and {f_['silent_nonempty']} "
              f"execute and return a wrong NON-EMPTY table "
              f"({pct(f_['silent_nonempty'], f_['n_wrong'])}); "
              f"most-non-empty flag (>50%): {f_['silent_nonempty'] / f_['n_wrong'] > 0.5}")
    common = ac.common_meta(a.arm, a.suite, a.keep_excluded, len(suite))
    detail = {"inputs": {"graded": grec,
                         "results": [ac.input_record(p) for p in a.results],
                         "vg_set": ac.input_record(a.vg_set),
                         "grader": ac.input_record(a.grader)},
              "runs": a.runs, "excluded_models": sorted(excluded), "mi_items_out": mi_items,
              "directional_items": sorted(roles), "roles_from": roles_how,
              "engine": ver.split(",")[0], "label_mismatches": len(mismatches),
              "rows_file": os.path.basename(a.out_rows)}
    ac.write_file_meta(a.out_summary, "empty_split_v13.py", common, detail)
    if mismatches:
        print("\nLABEL MISMATCHES (graded label vs re-execution; keys only):")
        for k in mismatches[:50]:
            print("  ", k)
        sys.exit(2)


if __name__ == "__main__":
    main()
