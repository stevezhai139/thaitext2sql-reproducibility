"""
selftest_v13n.py -- self-test of an answer key on the grading database (read-only):
the core suite v1.3n on k3n, or the extension suite (AMENDMENT-9) with its
kst-mi-2 manifest. It reads no model output and prints check results only.

  0  first line: build_status (DRAFT / FROZEN); a DRAFT suite is refused unless
     --allow-draft-testonly (tests only)
  1  header and values follow suite_columns.json (same strict loader as
     grade_v13n.py); ids are unique
  2  rows whose id is in v1.2 (--suite-v12): tier, schema, eff, question_en,
     question_th, notes byte-identical to v1.2 and gold_sql_v12 equal to the
     v1.2 gold; a core suite has exactly the v1.2 ids in the v1.2 order (a
     core suite without --suite-v12 fails); other rows need question_en and
     question_th. D11: an item of core_repaired (suite_columns.json) that is
     primary in a core suite (the October suite) carries the repaired
     question: tier, schema, eff and notes still equal v1.2, question_en and
     question_th must differ from v1.2 and gold_sql_v12 is empty (v1.2 has no
     gold for the repaired question); where it is excluded (the August
     suite) the full v1.2 identity above holds
  3  every gold key (primary and alternatives, per language) executes, is
     deterministic over two runs, grades correct against itself under R-v1.3,
     and an alternative has the column count of the primary; a primary item
     that is not multi-instance has a non-empty primary gold on the base
  4  col_roles: the items with a non-empty col_roles (column, or the core
     registry when the core suite has no column) are exactly the registry of
     suite_columns.json, and every index is below the column count of every
     key; a core suite prints core_directional (apply and the status text of
     suite_columns.json, OQ35); while that status still carries the
     PENDING_MARK (an author decision not yet recorded) the self-test FAILS
     unless --allow-draft-testonly (tests only), so an undecided OQ35 cannot
     pass an official step
  5  core suite: 60 items, every item of core_repaired present, and either
     exactly the core_repaired items excluded (August re-grade suite: 59
     primary of 60) or no excluded item (October suite, D11: 60 primary);
     the line 'core session: ...' names which; a columns file without
     core_repaired fails a core suite;
     extension suite: ext_item_count items (suite_columns.json), every item
     of mi_items present, primary (FK1 included) and with a non-empty
     mi_instances, every item of the directional registry present; a reserves
     file (--reserves) holds no multi-instance item
  6  multi-instance items (--mi-manifest): the grader's own manifest checks
     (format, recorded status unless --allow-draft-testonly, recorded
     fingerprints of base and instances, expected_gold, mi_instances, manifest
     gold_sql == suite gold after normalising whitespace and a trailing ';',
     no excluded MI item); every item of mi_items in the suite is a manifest
     item; every key runs on every instance, deterministic and self-matching;
     the gold is non-empty on at least one instance and is not the same on
     every instance unless the manifest says gold_varies: false
Exit 1 on any failure, 2 on a refused input.

Usage: RUNBOOK steps 1a.38 (core: the August suite k3n_suite_v1.3n.tsv, and the
October suite k3n_suite_v1.3n_oct.tsv of D11 in its own step) and 1a.62 (extension
with --mi-manifest), run from harness/, one line, every path in double quotes.
"""
import argparse
import csv
import importlib.util
import json
import os
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
# marker of an author decision not yet recorded (core_directional.status, OQ35)
PENDING_MARK = "PENDING-AUTHOR"
# number of core items (v1.2 ids); D11 keeps it at 60 in both core suites
CORE_N = 60


def load_grader(path):
    spec = importlib.util.spec_from_file_location("grade_v13n", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", required=True)
    ap.add_argument("--pg", required=True)
    ap.add_argument("--suite-v12", default=None)
    ap.add_argument("--mi-manifest", default=None)
    ap.add_argument("--columns", default=os.path.join(HERE, "suite_columns.json"))
    ap.add_argument("--grader", default=os.path.join(HERE, "grade_v13n.py"))
    ap.add_argument("--allow-draft-testonly", action="store_true")
    ap.add_argument("--reserves", action="store_true",
                    help="the suite is the extension reserves file (not the 40-item suite)")
    a = ap.parse_args()
    g = load_grader(a.grader)
    fails, notes = [], []

    # ---------------------------------------------------------------- 0, 1
    try:
        cols = g.load_columns(a.columns)
        suite, header, is_ext = g.load_suite_checked(a.suite, cols)
    except g.Refuse as e:
        print("build_status: unknown (suite not readable)")
        print(f"SELF-TEST v1.3n REFUSED: {e}")
        sys.exit(2)
    draft = g.suite_is_draft(a.suite, suite, header)
    how = "build_status column" if "build_status" in header else "file name (no build_status column)"
    print(f"build_status: {'DRAFT' if draft else 'FROZEN'} ({how}); "
          f"suite kind: {'extension' if is_ext else 'core'}")
    if draft and not a.allow_draft_testonly:
        print("SELF-TEST v1.3n REFUSED: DRAFT suite (official steps use the frozen suite; "
              "--allow-draft-testonly is for tests only)")
        sys.exit(2)
    if a.reserves and not is_ext:
        print("SELF-TEST v1.3n REFUSED: --reserves is for the extension reserves file")
        sys.exit(2)

    # ---------------------------------------------------------------- 2
    # D11: core items repaired for the October session (suite_columns.json core_repaired)
    repaired = list((cols.get("core_repaired") or {}).get("items") or [])
    if not is_ext and not a.suite_v12:
        fails.append("2: a core suite needs --suite-v12 (identity of the v1.2 rows is part "
                     "of the check)")
    if a.suite_v12:
        s12 = list(csv.DictReader(open(a.suite_v12, encoding="utf-8"), delimiter="\t"))
        v12 = {r["id"]: r for r in s12}
        if not is_ext and list(suite) != [r["id"] for r in s12]:
            fails.append("2: core item ids differ from v1.2 (set or order)")
        for qid, y in suite.items():
            x = v12.get(qid)
            if x is None:
                continue
            if not is_ext and qid in repaired and y["v13_status"].strip() == "primary":
                # October suite (D11): the repaired question replaces the v1.2 text
                for f in ("tier", "schema", "eff", "notes"):
                    if x[f] != y.get(f):
                        fails.append(f"2: {qid} column {f} differs from v1.2")
                for f in ("question_en", "question_th"):
                    if x[f] == y.get(f):
                        fails.append(f"2: {qid} is primary as a repaired item (D11) but {f} "
                                     "still equals v1.2 (the original question)")
                if (y.get("gold_sql_v12") or "").strip():
                    fails.append(f"2: {qid} is a repaired item (D11): gold_sql_v12 must be "
                                 "empty (v1.2 has no gold for the repaired question)")
                continue
            for f in ("tier", "schema", "eff", "question_en", "question_th", "notes"):
                if x[f] != y.get(f):
                    fails.append(f"2: {qid} column {f} differs from v1.2")
            if x["gold_sql_draft"] != y["gold_sql_v12"]:
                fails.append(f"2: {qid} gold_sql_v12 differs from the v1.2 gold")
    else:
        v12 = {}
    for qid, y in suite.items():
        if qid not in v12 and not ((y.get("question_en") or "").strip()
                                   and (y.get("question_th") or "").strip()):
            fails.append(f"2: {qid} needs question_en and question_th")

    # ---------------------------------------------------------------- 4 (registry)
    try:
        roles = g.roles_by_item(suite, header, cols, False)
    except g.Refuse as e:
        fails.append(f"4: {e}")
        roles = {}
    reg = g.directional_registry(cols)
    for qid in suite:
        if qid in roles and qid not in reg:
            fails.append(f"4: {qid} has col_roles but is not in the registry")
    core_items = cols["core_directional"].get("items") or {}
    if not is_ext:
        miss = [x for x in core_items if x not in suite]
        if miss:
            fails.append(f"4: core registry items not in the suite: {miss}")
    if is_ext and not a.reserves:
        miss = [x for x in cols["directional"] if x not in suite]
        if miss:
            fails.append(f"4: directional items of the registry missing from the suite: {miss}")
    core_status = str(cols["core_directional"].get("status") or "")
    if PENDING_MARK in core_status:
        if a.allow_draft_testonly:
            notes.append(f"core_directional status carries {PENDING_MARK} (OQ35 not recorded); "
                         "accepted only because of --allow-draft-testonly (tests)")
        else:
            fails.append(f"4: core_directional status in {os.path.basename(a.columns)} carries "
                         f"{PENDING_MARK}: record the OQ35 decision in suite_columns.json "
                         "(apply and status) before the official self-test")

    # ---------------------------------------------------------------- 5
    excluded = [qid for qid, r in suite.items() if r["v13_status"].strip() == "excluded"]
    n_primary = len(suite) - len(excluded)
    session = None
    if not is_ext:
        miss_rep = [x for x in repaired if x not in suite]
        if not repaired:
            fails.append(f"5: {os.path.basename(a.columns)} has no core_repaired items (D11): "
                         "a core suite cannot be classed as the August or the October suite")
        elif len(suite) != CORE_N or miss_rep:
            fails.append(f"5: core suite needs {CORE_N} items including the repaired items "
                         f"{repaired} (found {len(suite)} items; missing {miss_rep})")
        elif sorted(excluded) == sorted(repaired):
            session = (f"August re-grade suite ({', '.join(repaired)} excluded with the original "
                       f"text; {n_primary} primary)")
        elif not excluded:
            session = (f"October suite (D11: {', '.join(repaired)} repaired and primary; "
                       f"{n_primary} primary)")
        else:
            fails.append(f"5: core suite needs exactly the repaired items {repaired} excluded "
                         f"(August re-grade) or no excluded item (October suite, D11); found "
                         f"excluded {excluded}")
    elif a.reserves:
        mi_here = [x for x in cols["mi_items"] if x in suite] + \
            [qid for qid, r in suite.items() if g.parse_mi_instances(r)]
        if mi_here:
            fails.append(f"5: a reserves file holds no multi-instance item (found "
                         f"{sorted(set(mi_here))})")
    else:
        want_n = cols.get("ext_item_count")
        if want_n is None:
            notes.append("extension item count not checked (no ext_item_count in the columns file)")
        elif len(suite) != want_n:
            fails.append(f"5: extension suite needs {want_n} items (ext_item_count of the columns "
                         f"file), found {len(suite)}")
        if suite.get("FK1", {}).get("v13_status", "").strip() != "primary":
            fails.append("5: extension suite needs FK1 as a primary item")
        for x in cols["mi_items"]:
            if x not in suite:
                fails.append(f"5: multi-instance item {x} is missing from the extension suite")
                continue
            if suite[x]["v13_status"].strip() != "primary":
                fails.append(f"5: multi-instance item {x} must be primary")
            if not g.parse_mi_instances(suite[x]):
                fails.append(f"5: multi-instance item {x} has no mi_instances (it would be graded "
                             "on the base alone)")
        if excluded:
            notes.append(f"extension items marked excluded: {excluded}")

    # ---------------------------------------------------------------- 6 (manifest)
    q = g.make_engine(a.pg)
    mi = None
    mi_items_in_suite = [qid for qid, r in suite.items() if g.parse_mi_instances(r)]
    if a.mi_manifest:
        try:
            mi = g.mi_setup(a.mi_manifest, a.pg, q, suite, header, a.allow_draft_testonly)
        except g.Refuse as e:
            fails.append(f"6: {e}")
        if mi:
            ungraded = [x for x in cols["mi_items"] if x in suite and x not in mi["items"]]
            if ungraded:
                fails.append(f"6: multi-instance items {ungraded} (mi_items) are not items of the "
                             "manifest")
    elif mi_items_in_suite:
        fails.append(f"6: suite lists mi_instances for {mi_items_in_suite}: pass --mi-manifest")
    man = json.load(open(a.mi_manifest, encoding="utf-8")) if (a.mi_manifest and mi) else {}

    # ---------------------------------------------------------------- 3 (+6 per instance)
    def check_keys(eng, where, item, qid, primary_must_rows):
        """run every key of the item on one database; returns (#keys run, rows of
        the primary per language, column count or None)"""
        sk, norms = g.parse_keys(item["sort_keys"]), g.parse_norms(item["norm"])
        n, prim, ncol = 0, {}, None
        for lang in g.LANGS:
            ordered = item[f"order_{lang}"].strip() == "yes"
            sqls = [("primary", item["gold_sql_draft"])]
            sqls += [(f"alt{i}", s) for i, s in
                     enumerate(json.loads(item[f"alt_gold_{lang}"] or "[]"), 1)]
            rows0 = None
            for label, sql in sqls:
                sql = sql.strip().rstrip(";")
                try:
                    r1, r2 = eng(sql), eng(sql)
                except Exception as e:
                    fails.append(f"3: {qid} {lang} {label} on {where}: exec error "
                                 f"{str(e).splitlines()[0][:80]}")
                    continue
                n += 1
                if r1 and ncol is None:
                    ncol = len(r1[0])
                if label == "primary":
                    rows0 = r1
                    prim[lang] = r1
                    if primary_must_rows and not r1:
                        fails.append(f"3: {qid} {lang}: primary gold returns 0 rows on {where}")
                if not g.match_v13(r1, r2, ordered, sk, norms):
                    fails.append(f"3: {qid} {lang} {label} on {where}: not deterministic")
                if not g.match_v13(r1, r1, ordered, sk, norms):
                    fails.append(f"3: {qid} {lang} {label} on {where}: does not match itself")
                if label != "primary" and rows0 is not None and r1 and rows0 and \
                        len(r1[0]) != len(rows0[0]):
                    fails.append(f"3: {qid} {lang} {label} on {where}: column count differs "
                                 "from the primary")
                if label != "primary" and rows0 is not None and where == "base" and \
                        g.match_v13(r1, rows0, ordered, sk, norms):
                    notes.append(f"{qid} {lang} {label}: same result as primary on the base "
                                 f"({len(r1)} rows; kept for other readings or instances)")
        return n, prim, ncol

    n_keys = n_inst_keys = 0
    mi_names = mi["items"] if mi else {}
    for qid, item in suite.items():
        primary = item["v13_status"].strip() == "primary"
        is_mi = qid in mi_names
        n, prim, ncol = check_keys(q, "base", item, qid,
                                   primary and not is_mi and qid not in mi_items_in_suite)
        n_keys += n
        golds = {"base": prim.get("en")}
        if is_mi:
            for name in mi_names[qid][1:]:
                k, p2, c2 = check_keys(mi["engines"][name], name, item, qid, False)
                n_inst_keys += k
                golds[name] = p2.get("en")
                ncol = ncol or c2
            canon = [None if v is None else sorted(tuple(g.cv13(x) for x in r) for r in v)
                     for v in golds.values()]
            if all(not c for c in canon):
                fails.append(f"6: {qid}: gold is empty on every instance")
            varies = man.get("items", {}).get(qid, {}).get("gold_varies", True)
            if varies and len({json.dumps(c) for c in canon}) < 2:
                fails.append(f"6: {qid}: gold is the same on every instance "
                             "(a constant answer would pass; set gold_varies: false only "
                             "when intended)")

    # ---------------------------------------------------------------- 4 (width, every key)
    # the grader's own check over every key (primary, alternatives, both languages,
    # every instance); a core suite also checks its core registry items when
    # apply is false, because a --core-directional on sensitivity grades them
    try:
        width_roles = g.roles_by_item(suite, header, cols, False,
                                      None if "col_roles" in header else True)
    except g.Refuse:
        width_roles = roles
    if width_roles:
        wkeys = {(qid, lang): g.item_keys(q, suite[qid], lang)
                 for qid in width_roles for lang in g.LANGS}

        def describe(sql):
            if "d" not in lazy:
                lazy["d"] = g.make_describer(a.pg)
            return lazy["d"](sql)
        lazy = {}
        try:
            g.check_roles_width(width_roles, suite, wkeys, mi, describe)
        except g.Refuse as e:
            fails.append(f"4: {e}")

    print(f"items: {len(suite)} (primary {n_primary}); gold keys executed on the base: {n_keys}"
          + (f"; on the other instances: {n_inst_keys}" if mi else ""))
    oct_rep = [x for x in repaired if not is_ext and x in suite
               and suite[x]["v13_status"].strip() == "primary"]
    if session:
        print(f"core session: {session}")
    print(f"col_roles items: {sorted(roles) if roles else 'none'}"
          + (" (from the core registry)" if roles and "col_roles" not in header else ""))
    if not is_ext and "col_roles" not in header:
        core = cols["core_directional"]
        print(f"core_directional ({os.path.basename(a.columns)}): apply "
              f"{str(g.core_apply(cols)).lower()}; items {sorted(core.get('items') or {})}; "
              f"status: {core.get('status') or '(none)'}")
    if mi:
        print(f"multi-instance items: { {k: v for k, v in mi_names.items()} }")
    for n in notes:
        print("  note:", n)
    if fails:
        print("SELF-TEST v1.3n FAILED:")
        for f in fails:
            print("  ", f)
        sys.exit(1)
    print("self-test v1.3n: PASS (header and values follow suite_columns.json; every key "
          "executes, is deterministic and matches itself"
          + ("; v1.2 identity holds" if a.suite_v12 else "")
          + (f" except the repaired question of {', '.join(oct_rep)} (D11)" if a.suite_v12 and oct_rep
             else "")
          + ("; multi-instance gold verified on every instance" if mi else "") + ")")


if __name__ == "__main__":
    main()
