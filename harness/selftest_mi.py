"""
selftest_mi.py -- end-to-end self-test of multi-instance grading (rule MI-1b) on
the instances of the kst-mi-2 manifest built from k3n (AMENDMENT-9). The
official run uses the FROZEN extension suite (Gate 1a step 63); its PASS line
goes into the FREEZE STAMP of AMENDMENT-9.

  A  answers: sha256 of --answers (the frozen copy) must equal every registered
     value that applies: REGISTERED_ANSWERS_SHA256 below (by file name; the
     value of the FREEZE STAMP of AMENDMENT-9), the <answers stem>.sha256 file
     next to it, and --answers-sha256; a file with no registered value at all
     fails A (a PASS always proves the answers are the frozen ones). The RUNBOOK
     copies only the frozen answers into harness/, so the built-in value is the
     one that applies there. A re-freeze (OQ24) replaces the frozen copy, its
     .sha256 file and the entry below together (test_grader_units t14 checks
     that the three agree).
  B  manifest: format kst-mi-2, rule MI-1b, status printed (the grader refuses a
     manifest that is not recorded, unless --allow-draft-testonly); every item
     lists the base first and
     is in the suite; instances are derived from the base or from an earlier
     instance; every recorded diff_sha256 matches its diff file; the item list
     and the instance lists equal those of the answers file
  C  gold on every instance (read-only, through grade_v13n.mi_setup): recorded
     fingerprints, expected_gold, mi_instances of the suite, manifest gold_sql ==
     suite gold; the gold is deterministic on every instance, non-empty on at
     least one and not the same on all unless the manifest says gold_varies: false
  D  every answer of --answers, in EN and in TH, graded by grade_v13n.py with the
     manifest (sidecar per instance):
       gold / correct answers  -> correct in both languages
       every foil              -> wrong, and fails on >= 1 instance
       brief 1.3 foils (uniqueness-only, nullity-only, constant, catalog) ->
                                  present for PK1, wrong, fail on >= 1 instance
       EN and TH get the same grade (same SQL)
       observed result per instance vs the prediction frozen before the run
       (reported; a miss is not a failure)
  D2 synthetic items written into --work (two instances whose President count
     differs): a permutation-drift answer is correct under the retired MI-1 and
     wrong under MI-1b; an answer that matches the primary on one instance and
     the alternative on the other is wrong; the consistent controls are correct
  E  guards: the grader refuses (exit 2, no output) a changed instance
     fingerprint, a changed expected_gold, a wrong base database, --legacy with
     a manifest, an excluded MI item, an MI suite without manifest, a manifest
     gold_sql that differs from the suite, a kst-mi-1 manifest, an instance
     that points at the base database and (official run only; a test run
     accepts any status) a manifest whose status is not recorded
Writes into --work only (its own file names, replaced on a re-run); exit 1 on
any failure, 2 on a refused input.

Usage: RUNBOOK step 1a.63 (run from harness/, one line, every path in double
quotes).
"""
import argparse
import csv
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
BRIEF_CATEGORIES = ("uniqueness-only", "nullity-only", "constant", "catalog")
# registered sha256 of the frozen MI answers, by file name (check A); equals
# answers_mi_PREREG_v2_frozen.sha256 and the FREEZE STAMP of AMENDMENT-9
REGISTERED_ANSWERS_SHA256 = {
    "answers_mi_PREREG_v2_frozen.py":
        "d708cbd4a6c9c5049c76d2836347cf408a94b442886c47b310097a38da9160db",
}


def sha256(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pg", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--answers", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--grader", default=os.path.join(HERE, "grade_v13n.py"))
    ap.add_argument("--columns", default=os.path.join(HERE, "suite_columns.json"))
    ap.add_argument("--allow-draft-testonly", action="store_true")
    ap.add_argument("--answers-sha256", default=None,
                    help="registered sha256 of --answers (needed when the .sha256 file is not "
                         "next to the answers)")
    a = ap.parse_args()
    g = load_module(a.grader, "grade_v13n")
    from psycopg2.extensions import make_dsn
    fails, notes = [], []

    try:
        cols = g.load_columns(a.columns)
        suite, header, is_ext = g.load_suite_checked(a.suite, cols)
        draft = g.draft_guard(a.suite, suite, header, a.allow_draft_testonly,
                              [os.path.join(a.work, "x")])
    except g.Refuse as e:
        print(f"SELF-TEST MI-1b REFUSED: {e}")
        sys.exit(2)
    print(f"build_status: {'DRAFT' if draft else 'FROZEN'}")
    os.makedirs(a.work, exist_ok=True)
    W = lambda f: os.path.join(a.work, f)  # noqa: E731
    grader_flags = ["--allow-draft-testonly"] if a.allow_draft_testonly else []

    # ---------------------------------------------------------------- A
    line, bad = answers_hash_check(a.answers, a.answers_sha256)
    print(line)
    fails.extend(bad)
    am = load_module(a.answers, "answers_frozen")
    answers, ans_inst = am.ANSWERS, am.INSTANCES

    # ---------------------------------------------------------------- B
    man = json.load(open(a.manifest, encoding="utf-8"))
    if man.get("format") != g.MI_FORMAT or man.get("rule") != g.MI_RULE:
        fails.append(f"B: manifest format/rule must be {g.MI_FORMAT}/{g.MI_RULE}")
    base = man.get("base")
    seen = []
    mdir = os.path.dirname(os.path.abspath(a.manifest))
    for x in man.get("instances") or []:
        n = x.get("name") or x.get("dbname")
        if n != base and x.get("derived_from") not in seen:
            fails.append(f"B: instance {n} is not derived from the base or an earlier instance")
        if x.get("diff") and x.get("diff_sha256"):
            dp = os.path.join(mdir, x["diff"])
            if not os.path.exists(dp) or sha256(dp) != x["diff_sha256"]:
                fails.append(f"B: diff of {n} does not match its recorded sha256")
        seen.append(n)
    m_items = man.get("items") or {}
    for qid, spec in m_items.items():
        if (spec.get("instances") or [None])[0] != base:
            fails.append(f"B: {qid} does not list the base first")
        if qid not in suite:
            fails.append(f"B: manifest item {qid} is not in the suite")
    if set(ans_inst) != set(m_items):
        fails.append(f"B: answers cover {sorted(ans_inst)}, manifest has {sorted(m_items)}")
    for qid, names in ans_inst.items():
        if qid in m_items and list(m_items[qid].get("instances") or []) != list(names):
            fails.append(f"B: {qid} instances of the answers file {names} differ from the "
                         f"manifest {m_items[qid].get('instances')}")
    print(f"B  manifest sha256 {sha256(a.manifest)}; status {man.get('status')!r}; base {base}; "
          f"items {sorted(m_items)}")

    # ---------------------------------------------------------------- C
    q = g.make_engine(a.pg)
    try:
        mi = g.mi_setup(a.manifest, a.pg, q, suite, header, a.allow_draft_testonly)
    except g.Refuse as e:
        fails.append(f"C: {e}")
        report(fails, notes)
        return
    eng = dict(mi["engines"])
    for qid, names in mi["items"].items():
        gold = suite[qid]["gold_sql_draft"].strip().rstrip(";")
        canon = []
        for n in names:
            r1, r2 = eng[n](gold), eng[n](gold)
            c1 = sorted(tuple(g.cv13(v) for v in r) for r in r1)
            if c1 != sorted(tuple(g.cv13(v) for v in r) for r in r2):
                fails.append(f"C: {qid} gold on {n} is not deterministic")
            canon.append(c1)
            print(f"C  {qid} gold on {n:22s} -> {show(g, ('rows', r1))}")
        if not any(canon):
            fails.append(f"C: {qid} gold is empty on every instance")
        if m_items[qid].get("gold_varies", True) and len({json.dumps(c) for c in canon}) < 2:
            fails.append(f"C: {qid} gold is the same on every instance")

    # ---------------------------------------------------------------- D
    fp_file = W("base_fingerprint_from_manifest.tsv")
    write_fp_from_manifest(g, man, base, fp_file)
    res = W("mi_answers_results.jsonl")
    with open(res, "w", encoding="utf-8") as f:
        for x in answers:
            if x["item"] not in suite:
                continue
            it = suite[x["item"]]
            for lang in g.LANGS:
                f.write(json.dumps({"model_key": x["id"], "lang": lang, "qid": x["item"],
                                    "tier": it["tier"], "schema": it["schema"], "run": 1,
                                    "parse_ok": True, "sql": x["sql"], "latency_s": 0.0,
                                    "error": None, "arm": "base"}) + "\n")
    out, log = W("mi_answers_graded.csv"), W("mi_answers_sidecar.csv")
    r = run_grader(a, g, ["--results", res, "--suite", a.suite, "--pg", a.pg,
                          "--db-fingerprint", fp_file, "--out", out, "--mi-manifest",
                          a.manifest, "--mi-log", log, "--arms", "base"] + grader_flags)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        fails.append("D: grade_v13n.py failed on the frozen answers")
        report(fails, notes)
        return
    graded = {(x["model_key"], x["lang"]): x for x in csv.DictReader(open(out, encoding="utf-8"))}
    side = {}
    for x in csv.DictReader(open(log, encoding="utf-8")):
        side.setdefault((x["model_key"], x["lang"]), []).append(x)
    table, misses, cats = [], 0, {}
    for x in answers:
        if x["item"] not in mi["items"]:
            notes.append(f"{x['id']}: item {x['item']} not in this suite (not graded)")
            continue
        names = mi["items"][x["item"]]
        obs = [observe(g, eng[n], x["sql"]) for n in names]
        hits = [pred_hit(g, p, o) for p, o in zip(x["predict"], obs)]
        misses += 0 if all(hits) else 1
        want = x["kind"] in ("gold", "correct")
        if x["brief_category"]:
            cats.setdefault((x["item"], x["brief_category"]), []).append(x["id"])
        verdicts = {}
        for lang in g.LANGS:
            gr = graded[(x["id"], lang)]
            per = side.get((x["id"], lang), [])
            fail_inst = [n for n in names
                         if not any(p["instance"] == n and p["executed"] == "True"
                                    and p["keys_matched"] for p in per)]
            correct = gr["correct"] == "True"
            verdicts[lang] = correct
            if want and not correct:
                fails.append(f"D: {x['id']} {lang} ({x['kind']}) graded wrong; fails on "
                             f"{fail_inst} ({gr['fail_reason']})")
            if not want and correct:
                fails.append(f"D: foil {x['id']} {lang} graded correct")
            if not want and not fail_inst:
                fails.append(f"D: foil {x['id']} {lang} fails on no instance")
        if verdicts["en"] != verdicts["th"]:
            fails.append(f"D: {x['id']} EN and TH grades differ for the same SQL")
        table.append([x["item"], x["id"], x["kind"], x["origin"], x["brief_category"],
                      " | ".join(show(g, o) for o in obs),
                      "hit" if all(hits) else "MISS",
                      "correct" if verdicts["en"] else "wrong",
                      ",".join(fail_inst) or "-", x["label"]])
    if "PK1" in mi["items"]:
        for c in BRIEF_CATEGORIES:
            if ("PK1", c) not in cats:
                fails.append(f"D: no registered PK1 foil of brief category {c}")
    with open(W("answers_graded_selftest_mi.tsv"), "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(["# per-instance results in manifest order; EN shown (TH graded the same)"])
        w.writerow(["item", "answer", "kind", "origin", "brief_category", "observed",
                    "prediction", "MI-1b", "fails_on", "label"])
        w.writerows(table)
    for item in mi["items"]:
        rows = [t for t in table if t[0] == item]
        n_ok = sum(1 for t in rows if t[7] == "correct")
        print(f"D  {item}: {len(rows)} answers on {len(mi['items'][item])} instances; graded "
              f"correct {n_ok} (gold/correct answers: "
              f"{sum(1 for t in rows if t[2] in ('gold', 'correct'))})")
    print(f"D  prediction misses (answers whose observed result differs from the frozen "
          f"prediction on some instance): {misses}")

    # ---------------------------------------------------------------- D2
    synthetic(a, g, man, mi, suite, header, fp_file, grader_flags, fails, notes)

    # ---------------------------------------------------------------- E
    def refuses(tag, manifest_obj=None, suite_rows=None, extra=(), pg=None, no_manifest=False):
        mp, sp = a.manifest, a.suite
        if manifest_obj is not None:
            mp = W(f"guard_{tag}_manifest.json")
            json.dump(manifest_obj, open(mp, "w", encoding="utf-8"))
        if suite_rows is not None:
            sp = W(f"guard_{tag}_suite.tsv")
            write_suite(sp, header, suite_rows)
        o = W(f"guard_{tag}.csv")
        if os.path.exists(o):
            os.remove(o)
        args = ["--results", res, "--suite", sp, "--pg", pg or a.pg, "--db-fingerprint",
                fp_file, "--out", o, "--arms", "base"] + grader_flags + list(extra)
        if not no_manifest:
            args += ["--mi-manifest", mp]
        rr = run_grader(a, g, args)
        msg = (rr.stderr.strip().splitlines() or [""])[-1]
        print(f"E  {tag:24s} exit {rr.returncode}: {msg[:120]}")
        if rr.returncode == 0 or os.path.exists(o):
            fails.append(f"E: grader did not refuse ({tag})")
    first_item = next(iter(mi["items"]))
    other = mi["items"][first_item][1]
    m1 = json.loads(json.dumps(man))
    for x in m1["instances"]:
        if (x.get("name") or x["dbname"]) == other:
            t0 = sorted(x["fingerprint"])[0]
            fp = x["fingerprint"][t0]
            if isinstance(fp, dict):
                fp["md5"] = "0" * 32
            else:
                fp[1] = "0" * 32
    refuses("changed_fingerprint", m1)
    m2 = json.loads(json.dumps(man))
    m2["items"][first_item]["expected_gold"][other] = [["ZZZ-NOT-THE-GOLD"]]
    refuses("changed_expected_gold", m2)
    other_db = mi["instances"][other]["dbname"]
    refuses("wrong_base_database", pg=make_dsn(a.pg, dbname=other_db))
    refuses("legacy_with_manifest", extra=("--legacy",))
    rows_ex = [dict(r) for r in suite.values()]
    for r in rows_ex:
        if r["id"] == first_item:
            r["v13_status"] = "excluded"
    refuses("excluded_mi_item", suite_rows=rows_ex)
    refuses("mi_suite_without_manifest", no_manifest=True)
    m3 = json.loads(json.dumps(man))
    m3["items"][first_item]["gold_sql"] = m3["items"][first_item]["gold_sql"].replace(
        "SELECT", "SELECT DISTINCT", 1)
    refuses("gold_sql_differs", m3)
    m4 = json.loads(json.dumps(man))
    m4["format"] = "kst-mi-1"
    refuses("retired_format_kst_mi_1", m4)
    m5 = json.loads(json.dumps(man))
    bx = next(x for x in m5["instances"] if (x.get("name") or x["dbname"]) == base)
    for x in m5["instances"]:
        if (x.get("name") or x["dbname"]) == other:
            x["dbname"], x["fingerprint"] = bx["dbname"], bx.get("fingerprint")
    refuses("instance_is_the_base", m5)
    if a.allow_draft_testonly:
        print(f"E  {'manifest_not_recorded':24s} skipped (--allow-draft-testonly accepts any "
              "manifest status)")
    else:
        m6 = json.loads(json.dumps(man))
        m6["status"] = "DRAFT"
        refuses("manifest_not_recorded", m6)
    report(fails, notes)


def answers_hash_check(answers, expected=None, registered=None):
    """check A: the answers file against every registered sha256 that applies --
    the built-in REGISTERED_ANSWERS_SHA256 entry of its file name, the
    <answers stem>.sha256 file next to it and --answers-sha256. With none of
    them the check FAILS, so a PASS always means the answers are the frozen
    ones. Returns (line to print, list of failures)."""
    registered = REGISTERED_ANSWERS_SHA256 if registered is None else registered
    got = sha256(answers)
    regs = []
    builtin = registered.get(os.path.basename(answers))
    if builtin:
        regs.append(("built-in registration", builtin.strip().lower()))
    reg_path = os.path.splitext(answers)[0] + ".sha256"
    if os.path.exists(reg_path):
        words = open(reg_path, encoding="utf-8").read().split()
        regs.append(("registered file " + os.path.basename(reg_path), words[0] if words else ""))
    if expected:
        regs.append(("--answers-sha256", expected.strip().lower()))
    if not regs:
        return (f"A  answers sha256 {got} (NO registered sha256 for "
                f"{os.path.basename(answers)}: not a registered answers file name, no "
                f"{os.path.basename(reg_path)} next to it, no --answers-sha256)",
                ["A: no registered sha256 for the answers file (the frozen copy cannot be "
                 "verified)"])
    bad = [f"A: the answers file does not match the sha256 of the {src}"
           for src, h in regs if h != got]
    return (f"A  answers sha256 {got} ("
            + "; ".join(f"{src}: {'match' if h == got else 'MISMATCH'}" for src, h in regs) + ")",
            bad)


def report(fails, notes):
    print()
    for n in notes:
        print("  note:", n)
    if fails:
        print("SELF-TEST MI-1b FAILED:")
        for f in fails:
            print("  ", f)
        sys.exit(1)
    print("SELF-TEST MI-1b: PASS (gold and correct answers correct on every instance in EN "
          "and TH; every foil, the brief 1.3 classroom forms included, fails on at least one "
          "instance; permutation drift and mixed keys are wrong; guards refuse bad input)")


def run_grader(a, g, args):
    """the grader on files of --work only (its own names), so --overwrite lets a
    re-run of the self-test replace them"""
    return subprocess.run([sys.executable, "-I", "-B", a.grader, "--columns", a.columns,
                           "--overwrite"] + args, capture_output=True, text=True)


def write_fp_from_manifest(g, man, base, path):
    """db fingerprint TSV (section 3.5 layout, mi_md5 only) built from the
    fingerprint the manifest records for its base: the grader then checks the
    live --pg against the recorded manifest"""
    inst = {(x.get("name") or x["dbname"]): x for x in man["instances"]}
    fp = g.fp_map(inst[base].get("fingerprint")) or {}
    with open(path, "w", encoding="utf-8") as f:
        f.write("#meta\t" + json.dumps({"source": "manifest base fingerprint",
                                        "base": base}) + "\n")
        f.write("\t".join(["table", "rows", "columns", "md5_order_free", "mi_md5",
                           "rowhash_md5", "md5_physical_order", "md5_ctids",
                           "dml_counters"]) + "\n")
        for t, (n, h) in sorted(fp.items()):
            f.write("\t".join([t, str(n), "-", "-", h, "-", "-", "-", "-"]) + "\n")


def write_suite(path, header, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in header})


def observe(g, eng, sql):
    try:
        return ("rows", g.run_with_timeout(lambda: eng(sql)))
    except Exception:
        return ("error", None)


def show(g, obs):
    kind, rows = obs
    if kind == "error":
        return "<error>"
    if not rows:
        return "<0 rows>"
    if len(rows) == 1 and len(rows[0]) == 1:
        return g.cv13(rows[0][0])
    if len(rows) <= 2:
        return json.dumps([[g.cv13(v) for v in r] for r in rows], ensure_ascii=False)
    return f"<{len(rows)}x{len(rows[0])}>"


def pred_hit(g, pred, obs):
    kind, rows = obs
    if pred == "error":
        return kind == "error"
    if pred == "shape":
        return kind == "error" or not (len(rows) == 1 and len(rows[0]) == 1)
    if kind == "error":
        return False
    if isinstance(pred, dict):
        return len(rows) == pred["rows"]
    if isinstance(pred, list):
        canon = lambda rs: sorted(tuple(g.cv13(v) for v in r) for r in rs)  # noqa: E731
        return canon(rows) == canon(pred)
    return len(rows) == 1 and len(rows[0]) == 1 and g.cv13(rows[0][0]) == pred


def synthetic(a, g, man, mi, suite, header, fp_file, grader_flags, fails, notes):
    """D2: permutation drift and mixed keys on two instances whose President row
    count differs (synthetic items, written into --work only)"""
    base = mi["base"]
    eng = mi["engines"]
    cnt = {n: eng[n]("SELECT COUNT(*) FROM President")[0][0] for n in eng}
    other = next((n for n in eng if n != base and cnt[n] != cnt[base]), None)
    if other is None:
        fails.append("D2: no instance whose President row count differs from the base")
        return
    nb = cnt[base]
    drift_gold = "SELECT COUNT(*) AS n_presidents, COUNT(*) + 1 AS n_plus_one FROM President"
    mix_gold = "SELECT COUNT(*) AS n_presidents FROM President"
    mix_alt = "SELECT COUNT(*) - 1 AS n_presidents FROM President"
    answers = [
        ("syn_drift", "ZZ-DRIFT", False,
         f"SELECT CASE WHEN COUNT(*) = {nb} THEN COUNT(*) ELSE COUNT(*) + 1 END AS c1, "
         f"CASE WHEN COUNT(*) = {nb} THEN COUNT(*) + 1 ELSE COUNT(*) END AS c2 FROM President"),
        ("syn_swap_both", "ZZ-DRIFT", True,
         "SELECT COUNT(*) + 1 AS c1, COUNT(*) AS c2 FROM President"),
        ("syn_mixed_keys", "ZZ-MIX", False,
         f"SELECT CASE WHEN COUNT(*) = {nb} THEN COUNT(*) ELSE COUNT(*) - 1 END AS n "
         "FROM President"),
        ("syn_alt_both", "ZZ-MIX", True, "SELECT COUNT(*) - 1 AS n FROM President"),
    ]
    W = lambda f: os.path.join(a.work, f)  # noqa: E731
    names = [base, other]
    m = json.loads(json.dumps(man))
    tmpl = dict(next(iter(suite.values())))
    rows = []
    for qid, gold, alts in (("ZZ-DRIFT", drift_gold, []), ("ZZ-MIX", mix_gold, [mix_alt])):
        exp = {n: [list(map(lambda v: int(v) if isinstance(v, int) else str(v), r))
                   for r in eng[n](gold)] for n in names}
        m["items"][qid] = {"instances": names, "gold_sql": gold, "g1_shape": "synthetic",
                           "expected_gold": exp, "gold_varies": True,
                           "why": "synthetic item of selftest_mi D2 (not a benchmark item)"}
        r = dict(tmpl)
        r.update({"id": qid, "gold_sql_draft": gold, "gold_sql_v12": "", "notes": "",
                  "question_en": "synthetic", "question_th": "synthetic",
                  "v13_status": "primary", "order_en": "no", "order_th": "no",
                  "sort_keys": "", "norm": "", "alt_gold_en": json.dumps(alts),
                  "alt_gold_th": json.dumps(alts), "col_roles": "",
                  "mi_instances": json.dumps(names)})
        rows.append(r)
    mp, sp = W("synthetic_manifest.json"), W("synthetic_suite.tsv")
    json.dump(m, open(mp, "w", encoding="utf-8"))
    write_suite(sp, header, rows)
    res = W("synthetic_results.jsonl")
    with open(res, "w", encoding="utf-8") as f:
        for aid, qid, _, sql in answers:
            f.write(json.dumps({"model_key": aid, "lang": "en", "qid": qid, "tier": "4",
                                "schema": "P", "run": 1, "parse_ok": True, "sql": sql,
                                "latency_s": 0.0, "error": None, "arm": "base"}) + "\n")
    out, log = W("synthetic_graded.csv"), W("synthetic_sidecar.csv")
    r = run_grader(a, g, ["--results", res, "--suite", sp, "--pg", a.pg, "--db-fingerprint",
                          fp_file, "--out", out, "--mi-manifest", mp, "--mi-log", log,
                          "--arms", "base"] + grader_flags)
    if r.returncode != 0:
        print(r.stdout, r.stderr)
        fails.append("D2: grade_v13n.py failed on the synthetic items")
        return
    graded = {x["model_key"]: x for x in csv.DictReader(open(out, encoding="utf-8"))}
    side = {}
    for x in csv.DictReader(open(log, encoding="utf-8")):
        side.setdefault(x["model_key"], []).append(x)
    for aid, qid, want, _ in answers:
        mi1b = graded[aid]["correct"] == "True"
        per = side.get(aid, [])
        labels = ["primary"] + [f"alt{i}" for i in range(1, 3)]
        mi1 = any(all(lb in (p["keys_matched"] or "").split("|") for p in per)
                  and len(per) == len(names) for lb in labels)
        print(f"D2 {aid:16s} on {base}/{other}: MI-1 {'correct' if mi1 else 'wrong'}, "
              f"MI-1b {'correct' if mi1b else 'wrong'}; positional "
              f"{graded[aid]['correct_positional']}")
        if mi1b != want:
            fails.append(f"D2: {aid} graded {'correct' if mi1b else 'wrong'} under MI-1b")
        if aid == "syn_drift" and not mi1:
            fails.append("D2: the permutation-drift answer should be correct under MI-1")
        if aid == "syn_mixed_keys" and mi1:
            fails.append("D2: the mixed-key answer must be wrong under MI-1 as well")
        if aid == "syn_swap_both" and graded[aid]["correct_positional"] != "False":
            fails.append("D2: the swapped control must not be positional")


if __name__ == "__main__":
    main()
