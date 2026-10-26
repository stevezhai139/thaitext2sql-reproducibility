"""
parity_grader.py -- proves that grade_v13n.py (candidate) changes no grade outside
the multi-instance and directional items, without copying results.jsonl
(AMENDMENT-7 Part C). Prints IDENTICAL / DIFFERENT and sha256 prefixes only --
never an accuracy -- and deletes the graded CSVs in --work after the
comparison unless --keep.

Two runs in Gate 1a:
  first run (RUNBOOK step 1a.40, before the manifest is recorded and the
    extension suite is frozen): every P1 mode without the manifest, P2 and the
    two-arm part of P3; it prints two SKIPPED lines, 'P1 modes + manifest' and
    'P3 extension golds', and these are expected there
  final run (after 1a.62; same command plus --mi-manifest
    "db/mi_manifest_k3n.json" --ext-suite "../suite/k3n_ext_suite_v1.0.tsv"
    --final): everything, with nothing skipped; --final refuses (exit 2) when
    --mi-manifest or --ext-suite is missing, so the final run cannot pass with
    a SKIPPED part. Expected: IDENTICAL on every P1 line (including the three
    '+ manifest' lines), P2 IDENTICAL, P3 PASS, 'P3 extension golds' PASS with
    rows 80/80 (40 items x 2 languages)

  P1  reference grade_v13.py (aed86b26...) vs candidate on --pg (k3n) with --suite
      (v1.3n), byte comparison of CSV and stdout:
        default, --keep-excluded, --colperm off            (candidate as is)
        default with an explicit col_roles column filled from the registry of
          suite_columns.json (empty for every other item)
        candidate --no-col-roles vs reference default       (pure G1 on both
          sides: must be IDENTICAL, no tolerance)
        candidate --core-directional on vs reference default (OQ35 option (c)
          sensitivity path)
        with --mi-manifest: the three modes again with the manifest
      --colperm off and --no-col-roles must be IDENTICAL. In the other modes a
      difference confined to directional items of the registry in force for
      that mode is reported 'DIFFERENT (directional items only: <qid> <rows>,
      ...)' and does not fail (the August log under the recorded OQ35 choice;
      TEST-ONLY it is IDENTICAL everywhere, so such a line must be reported in
      AMENDMENT-7 if it appears); any other difference fails.
      The reference reads results.jsonl through a parse hook (REF_SHIM) that
      keeps only the grader's fields and replaces the text of 'error' with a
      fixed marker, so neither grader holds the error text; the reference code
      itself is not changed and its bytes are those of grade_v13.py.
  P2  candidate --legacy on --legacy-pg (k3) vs --record (results/graded.csv):
      exec_ok, correct, fail_reason equal on every (model, lang, qid, run) and the
      same key set; and candidate --legacy vs reference --legacy byte-identical
  P3  a synthetic two-arm log built from the suite golds only (no model output):
      every gold answer in arms base and values, plus a parse failure, a
      non-SELECT and an execution error per item; the candidate keeps the arm on
      every row, grades base and values identically, prints a separate stdout
      line for the values arm, and refuses an arm outside --arms.
      With --ext-suite and --mi-manifest the extension golds are added (arm base;
      every gold correct, one row per item and language).
Exit 1 if any check fails, 2 on a refused command.

Usage: RUNBOOK step 1a.40 (first run) and the final run described above, run
from harness/, one line, every path in double quotes.
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


def sha(b):
    return hashlib.sha256(b).hexdigest()


def run(script, args, columns=None):
    cmd = [sys.executable, "-I", "-B", script] + list(args)
    if columns:
        cmd += ["--columns", columns]
    return subprocess.run(cmd, capture_output=True)


# The reference grade_v13.py does json.loads(line) on every record and only tests
# rec.get("error") is not None. REF_SHIM loads it unchanged and gives it a json
# whose loads() keeps only the grader's fields of a record and turns the text of
# 'error' into a fixed marker (None stays None), so the reference skips exactly
# the same records and writes the same bytes without holding the error text.
REF_SHIM = r'''
import importlib.util, json, sys
sys.dont_write_bytecode = True
FIELDS = set(json.loads(sys.argv[1]))
REF = sys.argv[2]


def _hook(pairs):
    out = {}
    for k, v in pairs:
        if k == "error":
            out[k] = None if v is None else "<error>"
        elif k in FIELDS:
            out[k] = v
    return out


class _Json:
    def __getattr__(self, name):
        return getattr(json, name)

    @staticmethod
    def loads(s, *args, **kw):
        kw.setdefault("object_pairs_hook", _hook)
        return json.loads(s, *args, **kw)


spec = importlib.util.spec_from_file_location("grade_v13_reference", REF)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
mod.json = _Json()
sys.argv = [REF] + sys.argv[3:]
mod.main()
'''


def reference_cmd(reference, args, fields):
    """command that runs the unchanged reference grader through REF_SHIM"""
    return [sys.executable, "-I", "-B", "-c", REF_SHIM, json.dumps(list(fields)),
            reference] + list(args)


def run_reference(reference, args, fields):
    return subprocess.run(reference_cmd(reference, args, fields), capture_output=True)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


class Ctx:
    def __init__(self, a):
        self.a = a
        self.fails = []
        self.made = []

    def path(self, name):
        """a file of this script in --work; a file of the same name left by an
        earlier run (--keep) is removed first, so the grader never meets an
        existing output"""
        p = os.path.join(self.a.work, name)
        if os.path.isfile(p):
            os.remove(p)
        self.made.append(p)
        return p

    def line(self, tag, status, extra=""):
        print(f"{tag:50s} {status}{('  ' + extra) if extra else ''}")
        if status.startswith("FAIL") or status == "DIFFERENT" or status.startswith("ERROR"):
            self.fails.append(tag)


def csv_rows(path):
    return list(csv.DictReader(open(path, encoding="utf-8")))


def diff_items(p_ref, p_new):
    """{qid: number of differing rows} between two graded CSVs of the same input
    (None when the row counts differ)"""
    A, B = csv_rows(p_ref), csv_rows(p_new)
    if len(A) != len(B):
        return None
    out = {}
    for x, y in zip(A, B):
        if x != y:
            out[x["qid"]] = out.get(x["qid"], 0) + 1
    return out


STRICT_MODES = ("--colperm off", "--no-col-roles")


def classify(diff, tolerated, strict):
    """verdict of a P1 mode whose bytes differ from the reference:
    'DIRECTIONAL' when the differing rows are confined to the tolerated
    (directional) items and the mode is not strict, else 'DIFFERENT'.
    diff: diff_items() result (None = row counts differ)."""
    if strict or not diff:
        return "DIFFERENT"
    return "DIRECTIONAL" if set(diff) <= set(tolerated) else "DIFFERENT"


def p1(ctx, g, reg):
    a = ctx.a
    ref_base = ["--results", a.results, "--suite", a.suite, "--pg", a.pg]
    new_base = ref_base + ["--db-fingerprint", a.db_fingerprint]
    modes = [("default", []), ("--keep-excluded", ["--keep-excluded"]),
             ("--colperm off", ["--colperm", "off"])]
    reg_on = g.directional_registry(g.load_columns(a.columns), True)
    refs = {}
    for name, extra in modes:
        o = ctx.path(f"p1_ref_{len(refs)}.csv")
        r = run_reference(a.reference, ref_base + ["--out", o] + extra, g.RECORD_FIELDS)
        if r.returncode != 0:
            ctx.line(f"P1 reference {name}", "ERROR (reference grader failed)")
            continue
        refs[name] = (o, r.stdout)

    def compare(tag, name, extra, suite=None, columns=None, tolerated=None, strict=None):
        """candidate (extra flags) vs the reference of mode 'name'; strict modes
        (--colperm off on both sides, candidate --no-col-roles) tolerate nothing"""
        tolerated = reg if tolerated is None else tolerated
        strict = (name in STRICT_MODES or "--no-col-roles" in extra) if strict is None else strict
        if name not in refs:
            return
        o = ctx.path(f"p1_new_{len(ctx.made)}.csv")
        args = list(new_base) + ["--out", o] + extra
        if suite:
            args[args.index("--suite") + 1] = suite
        r = run(a.candidate, args, columns or a.columns)
        if r.returncode != 0:
            ctx.line(tag, "ERROR (candidate refused or failed)",
                     (r.stderr.decode(errors="replace").strip().splitlines() or [""])[-1][:100])
            return
        ro, rs = refs[name]
        c_ref, c_new = open(ro, "rb").read(), open(o, "rb").read()
        if c_ref == c_new and rs == r.stdout:
            ctx.line(tag, "IDENTICAL", f"csv {sha(c_new)[:8]} stdout {sha(r.stdout)[:8]}")
            return
        qs = diff_items(ro, o)
        if classify(qs, tolerated, strict) == "DIRECTIONAL":
            items = ", ".join(f"{q} {n}" for q, n in sorted(qs.items()))
            print(f"{tag:50s} DIFFERENT (directional items only: {items} rows)  "
                  f"csv {sha(c_new)[:8]}")
            return
        ctx.line(tag, "DIFFERENT", f"csv {sha(c_ref)[:8]}/{sha(c_new)[:8]} "
                                   f"stdout {sha(rs)[:8]}/{sha(r.stdout)[:8]}"
                                   + (" (strict mode)" if strict else ""))

    for name, extra in modes:
        compare(f"P1 {name}", name, extra)
    # explicit col_roles column = registry values
    suite_cr = ctx.path("p1_suite_with_col_roles.tsv")
    with open(a.suite, encoding="utf-8", newline="") as f:
        rd = csv.DictReader(f, delimiter="\t")
        hdr = list(rd.fieldnames) + ["col_roles"]
        rows = list(rd)
    with open(suite_cr, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=hdr, delimiter="\t", lineterminator="\r\n")
        w.writeheader()
        for r in rows:
            r["col_roles"] = reg.get(r["id"], "")
            w.writerow(r)
    compare("P1 default, col_roles column from registry", "default", [], suite=suite_cr)
    compare("P1 --no-col-roles vs reference default", "default", ["--no-col-roles"])
    compare("P1 --core-directional on vs reference default", "default",
            ["--core-directional", "on"], tolerated=reg_on)
    if a.mi_manifest:
        test = ["--allow-draft-testonly"] if a.allow_draft_testonly else []
        for name, extra in modes:
            compare(f"P1 {name} + manifest", name,
                    extra + ["--mi-manifest", a.mi_manifest] + test)
    else:
        print(f"{'P1 modes + manifest':50s} SKIPPED (no --mi-manifest; expected in the first "
              "run, covered by the final run with --final)")


def p2(ctx, g):
    a = ctx.a
    base = ["--results", a.results, "--suite", a.suite, "--pg", a.legacy_pg, "--legacy"]
    o_new, o_ref = ctx.path("p2_new_legacy.csv"), ctx.path("p2_ref_legacy.csv")
    r_new = run(a.candidate, base + ["--db-fingerprint", a.legacy_fingerprint, "--out", o_new],
                a.columns)
    r_ref = run_reference(a.reference, base + ["--out", o_ref], g.RECORD_FIELDS)
    if r_new.returncode != 0 or r_ref.returncode != 0:
        ctx.line("P2 --legacy on the legacy database", "ERROR (a grader failed)",
                 (r_new.stderr.decode(errors="replace").strip().splitlines() or [""])[-1][:100])
        return
    key = lambda r: (r["model_key"], r["lang"], r["qid"], r["run"])  # noqa: E731
    A = {key(r): r for r in csv_rows(a.record)}
    B = {key(r): r for r in csv_rows(o_new)}
    cols = ("exec_ok", "correct", "fail_reason")
    bad = sum(1 for k in A if k not in B or any(A[k][c] != B[k][c] for c in cols))
    same_keys = set(A) == set(B) and len(B) == len(csv_rows(o_new))
    ctx.line("P2 --legacy vs record (exec_ok, correct, reason)",
             "IDENTICAL" if (bad == 0 and same_keys) else "DIFFERENT",
             f"{len(A) - bad}/{len(A)} keys")
    same = open(o_new, "rb").read() == open(o_ref, "rb").read() and r_new.stdout == r_ref.stdout
    ctx.line("P2 --legacy candidate vs reference (bytes)", "IDENTICAL" if same else "DIFFERENT",
             f"csv {sha(open(o_new, 'rb').read())[:8]}")


def p3(ctx, g):
    a = ctx.a
    cols = g.load_columns(a.columns)
    suite, header, _ = g.load_suite_checked(a.suite, cols)
    res = ctx.path("p3_synthetic_two_arm.jsonl")
    n = 0
    with open(res, "w", encoding="utf-8") as f:
        for qid, it in suite.items():
            if it["v13_status"].strip() != "primary":
                continue
            for lang in g.LANGS:
                variants = [("gold", True, it["gold_sql_draft"]), ("parse", False, ""),
                            ("nonselect", True, "UPDATE party SET partyname = partyname"),
                            ("execerr", True, "SELECT 1/0")]
                for run_no, (tag, ok, sql) in enumerate(variants, 1):
                    for arm in ("base", "values"):
                        f.write(json.dumps({"model_key": f"syn-{tag}", "lang": lang,
                                            "qid": qid, "tier": it["tier"],
                                            "schema": it["schema"], "run": run_no,
                                            "parse_ok": ok, "sql": sql, "latency_s": 0.0,
                                            "error": None, "arm": arm}) + "\n")
                        n += 1
    o = ctx.path("p3_graded.csv")
    r = run(a.candidate, ["--results", res, "--suite", a.suite, "--pg", a.pg,
                          "--db-fingerprint", a.db_fingerprint, "--out", o], a.columns)
    if r.returncode != 0:
        ctx.line("P3 synthetic two-arm log", "ERROR (candidate failed)")
        return
    rows = csv_rows(o)
    by = {}
    for x in rows:
        by.setdefault((x["model_key"], x["lang"], x["qid"], x["run"]), {})[x["arm"]] = x
    keep_arm = len(rows) == n and all(set(v) == {"base", "values"} for v in by.values())
    fields = [c for c in g.OUT_HEADER if c != "arm"]
    same = all(v["base"][c] == v["values"][c] for v in by.values() for c in fields)
    golds_ok = all(v["base"]["correct"] == "True" for k, v in by.items() if k[0] == "syn-gold")
    others_wrong = all(v["base"]["correct"] == "False" for k, v in by.items()
                       if k[0] != "syn-gold")
    out = r.stdout.decode()
    lines_ok = "[values]" in out and all(
        ln.split(":")[0].strip().endswith("[values]") or "[" not in ln
        for ln in out.splitlines()[1:])
    ok = keep_arm and same and golds_ok and others_wrong and lines_ok
    ctx.line("P3 synthetic two-arm log (arm kept, arms equal)", "PASS" if ok else "FAIL",
             f"rows {len(rows)}/{n}")
    o2 = ctx.path("p3_refused.csv")
    r2 = run(a.candidate, ["--results", res, "--suite", a.suite, "--pg", a.pg,
                           "--db-fingerprint", a.db_fingerprint, "--out", o2, "--arms", "base"],
             a.columns)
    ctx.line("P3 arm outside --arms refused", "PASS" if (r2.returncode != 0 and
                                                          not os.path.exists(o2)) else "FAIL")
    if a.ext_suite and a.mi_manifest:
        esuite, eh, _ = g.load_suite_checked(a.ext_suite, cols)
        res_e = ctx.path("p3_ext_golds.jsonl")
        with open(res_e, "w", encoding="utf-8") as f:
            for qid, it in esuite.items():
                for lang in g.LANGS:
                    f.write(json.dumps({"model_key": "syn-gold", "lang": lang, "qid": qid,
                                        "tier": it["tier"], "schema": it["schema"], "run": 1,
                                        "parse_ok": True, "sql": it["gold_sql_draft"],
                                        "latency_s": 0.0, "error": None, "arm": "base"}) + "\n")
        oe = ctx.path("p3_ext_graded.csv")
        extra = ["--allow-draft-testonly"] if a.allow_draft_testonly else []
        r3 = run(a.candidate, ["--results", res_e, "--suite", a.ext_suite, "--pg", a.pg,
                               "--db-fingerprint", a.db_fingerprint, "--out", oe,
                               "--mi-manifest", a.mi_manifest, "--arms", "base"] + extra,
                 a.columns)
        want = 2 * len(esuite)
        got = csv_rows(oe) if r3.returncode == 0 else []
        ok3 = r3.returncode == 0 and len(got) == want and \
            all(x["correct"] == "True" and x["arm"] == "base" for x in got)
        ctx.line("P3 extension golds (MI-1b, arm base)", "PASS" if ok3 else "FAIL",
                 f"rows {len(got)}/{want}" + ("" if r3.returncode == 0 else
                                              " " + (r3.stderr.decode(errors="replace").strip()
                                                     .splitlines() or [""])[-1][:100]))
    else:
        print(f"{'P3 extension golds':50s} SKIPPED (no --ext-suite / --mi-manifest; expected in "
              "the first run, covered by the final run with --final)")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pg", required=True)
    ap.add_argument("--legacy-pg", required=True)
    ap.add_argument("--reference", required=True, help="grade_v13.py (aed86b26...)")
    ap.add_argument("--candidate", required=True, help="grade_v13n.py")
    ap.add_argument("--suite", required=True)
    ap.add_argument("--results", required=True)
    ap.add_argument("--record", required=True, help="results/graded.csv of v1.2")
    ap.add_argument("--db-fingerprint", required=True)
    ap.add_argument("--legacy-fingerprint", required=True)
    ap.add_argument("--work", required=True)
    ap.add_argument("--keep", action="store_true", help="keep the graded CSVs in --work")
    ap.add_argument("--columns", default=os.path.join(HERE, "suite_columns.json"))
    ap.add_argument("--mi-manifest", default=None)
    ap.add_argument("--ext-suite", default=None)
    ap.add_argument("--allow-draft-testonly", action="store_true")
    ap.add_argument("--final", action="store_true",
                    help="final Gate 1a run: --mi-manifest and --ext-suite are required, so "
                         "nothing is skipped")
    a = ap.parse_args()
    if a.final and not (a.mi_manifest and a.ext_suite):
        print("PARITY: REFUSED: --final needs --mi-manifest and --ext-suite (the final run "
              "checks the manifest modes and the extension golds; nothing may be skipped)")
        sys.exit(2)
    os.makedirs(a.work, exist_ok=True)
    g = load_module(a.candidate, "grade_v13n_candidate")
    ctx = Ctx(a)
    reg = g.directional_registry(g.load_columns(a.columns))
    full = bool(a.mi_manifest and a.ext_suite)
    print("mode: " + ("final run (--final; manifest and extension golds included)" if a.final
                      else "run with manifest and extension golds" if full
                      else "first run (manifest and extension parts SKIPPED)"))
    print(f"reference {os.path.basename(a.reference)} sha256 "
          f"{sha(open(a.reference, 'rb').read())[:16]}...; candidate "
          f"{os.path.basename(a.candidate)} sha256 {sha(open(a.candidate, 'rb').read())[:16]}...")
    try:
        p1(ctx, g, reg)
        p2(ctx, g)
        p3(ctx, g)
    finally:
        if not a.keep:
            for p in ctx.made:
                if os.path.exists(p):
                    os.remove(p)
    if ctx.fails:
        print(f"PARITY: FAIL ({len(ctx.fails)} check(s): {', '.join(ctx.fails)})")
        sys.exit(1)
    print("PARITY: PASS (no grade changes outside the directional and multi-instance items"
          + ("" if full else "; manifest and extension parts not run: the final run follows")
          + ")")


if __name__ == "__main__":
    main()
