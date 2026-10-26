"""
analyze.py — สถิติตาม prereg (FROZEN 6 ส.ค.):
majority-vote ต่อข้อ (5 runs) → item-level accuracy + Wilson 95% CI
(ต่อ model×lang บนข้อ primary ของ suite: n=60 บน suite core ของรอบ ต.ค. (D11; ผลหลัก),
n=59 บน suite v1.3/v1.3n ของ ส.ค., n=60 เมื่อ --keep-excluded บน suite ของ ส.ค. หรือ
suite v1.2; ราย tier เชิงพรรณนา), McNemar TH-vs-EN ต่อ
โมเดล + Holm ข้ามโมเดล + Δaccuracy พร้อม Newcombe interval (ไม่แก้ pairing;
AMENDMENT-7 D-1), unanimity/flip rate, parse rate + CI, value_translated effect
(derive อัตโนมัติ: literal ใน gold ที่ไม่ปรากฏ verbatim ใน question_th หรือรายการ
จาก --vg-set)

Gate 0 (KST 2027 revision): สัญญา --arm (GATE0 design 2.6; D10)
  * --arm บังคับ ไม่มีค่า default: graded_rc1.csv ของรอบ ต.ค. มีทั้งแขน base และ
    values และคีย์ (model_key, lang, qid) ของฉบับก่อนจะรวม 10 run ของสองแขนเป็น
    cell เดียว; แถวที่ไม่มีคอลัมน์ arm (results/graded.csv ของ v1.2) ถือเป็น base
  * หลังกรอง ทุก cell (model, lang, qid) ของข้อที่วิเคราะห์ต้องมี run เท่ากับ
    --runs (default 5) ไม่เช่นนั้น exit 2; --exclude-models ตัดโมเดลที่เก็บไม่ครบ
    (AM-7 A5.6) และบันทึกลง meta.json
  * เขียน meta.json ในโฟลเดอร์ผล (arm, sha256 ของ input และ suite, จำนวนข้อ,
    keep_excluded); โฟลเดอร์ที่มี meta ของ arm อื่นอยู่แล้วถูกปฏิเสธ
  * D10 (ผลหลักทั้งหมดมาจากรอบ ต.ค.): input record ของไฟล์ graded เก็บ arm ที่มีในไฟล์
    และ session fingerprint (sha256 ต่อข้อของ model|lang|run|latency_s ของแขนที่วิเคราะห์;
    latency มาจาก record จึงระบุรอบของการเก็บข้อมูลโดยไม่ขึ้นกับการ grade); โฟลเดอร์ผล
    ปฏิเสธ producer ที่อ่าน graded คนละไฟล์ (sha256) กับ producer ที่บันทึกไว้แล้ว;
    same_session() ใช้ตรวจ plan csv กับตาราง และ consistency_aug_oct ใช้ปฏิเสธ input ที่มา
    จากรอบเดียวกัน; paper_guard() ปฏิเสธการเขียนลงโฟลเดอร์ชื่อ paper เมื่อ graded ไม่ใช่
    ไฟล์สองแขน (log หลักของรอบ ต.ค. เป็นไฟล์เดียวที่มีทั้งแขน base และ values) หรือเมื่อ
    ตารางไม่ได้มาจากแขน PAPER_ARM = base (ตารางหลักของเล่มมาจากแขน base ของรอบ ต.ค.)
  * D11 (Q27 ซ่อมสำหรับรอบ ต.ค. เท่านั้น; D11_REPAIRED อ่านจาก core_repaired.items ของ
    suite_columns.json ที่อยู่ข้างไฟล์นี้ ซึ่งเป็นรายการเดียวกับที่ selftest_v13n อ่าน;
    --keep-excluded บน suite ของ ส.ค. รับเฉพาะไฟล์ graded_v13n_withQ27.csv ของขั้น 2.2
    = AUG_KEEP_EXCLUDED_GRADED): suite_session() อ่าน
    สถานะของข้อที่ซ่อมใน suite: excluded = suite ของ ส.ค. (n=59; --keep-excluded = n=60
    ของ ส.ค.), primary = suite core ของรอบ ต.ค. (n=60 เป็นผลหลัก), ไม่มีคอลัมน์
    v13_status = suite v1.2; d11_check() ของทุกสคริปต์ที่อ่าน core: suite ของรอบ ต.ค.
    รับเฉพาะ graded สองแขน (log core ของรอบ ต.ค.), suite v1.2 และ --keep-excluded บน suite
    ของ ส.ค. ไม่รับ log ของรอบ ต.ค. (Q27 ของรอบ ต.ค. เป็นโจทย์ฉบับซ่อม); log ของรอบ ต.ค.
    บน suite ของ ส.ค. (ไม่มี --keep-excluded) ให้มุมมอง 59 ข้อ ซึ่งไม่ใช่ผลหลัก; common_meta
    บันทึก suite_session และ paper_guard() รับเฉพาะตารางที่คำนวณบน suite core ของรอบ ต.ค.;
    การเทียบสองรอบ (consistency_aug_oct, drift ของ analyze_rc1) ใช้ข้อที่มีร่วมกัน 59 ข้อ
  * draft_guard(): suite ที่ชื่อไฟล์หรือ build_status มีคำว่า DRAFT ถูกปฏิเสธ เว้นแต่ส่ง
    --allow-draft-testonly และ output ทุกตัวอยู่นอกโฟลเดอร์ results/ (กฎเดียวกับ grade_v13n)
  * b1_class(): คลาส B1 ของ run ที่ผิด (loud / silent_empty / silent_nonempty) ที่เดียว;
    n_rows ว่างบน run ที่ execute ได้ทำให้หยุด (exit 2) ทุกสคริปต์; regex ของ B6
    (column / function does not exist) อยู่ที่นี่ที่เดียว
  * ผลบน v1.2 (results/graded.csv + suite v1.2, --arm base) เหมือนฉบับที่ส่งทุก byte
  ไฟล์นี้เป็น implementation เดียวของสัญญา --arm; สคริปต์ตารางอื่น import จากที่นี่

Usage: python3 -I -B analyze.py --graded ../results/rc1/graded_rc1.csv \
         --suite ../suite/k3n_suite_v1.3n_oct.tsv --arm base --out ../results/rc1/base60/tables
"""
import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)


# ===================================================================== --arm contract
# (shared implementation; imported by analyze_typhoon, phi_tableiv, empty_split_v13,
#  analyze_log_v13, plan_quality, paper_numbers_v13n, transitions_v13n, analyze_ext,
#  consistency_aug_oct, make_tables and make_figures)
LANGS = ("en", "th")
META_NAME = "meta.json"
META_CONSISTENT = ("arm", "keep_excluded", "suite_sha256")
TWO_ARMS = ("base", "values")   # only the October core log holds both arms (D10)
PAPER_ARM = "base"              # the paper's main tables come from the October base arm (D10)
# AM-7 B6 'schema-shaped' loud runs: the PostgreSQL message says a column or a function
# does not exist (one definition for analyze_typhoon.py --b6 and analyze_log_v13.py B6);
# an operator error is a type mismatch and is reported apart, outside schema_shaped
B6_BAD_COLUMN = re.compile(r"column .* does not exist", re.I)
B6_BAD_FUNCTION = re.compile(r"function .* does not exist", re.I)
B6_BAD_OPERATOR = re.compile(r"operator does not exist", re.I)
B6_BAD_RELATION = re.compile(r"relation .* does not exist", re.I)


def die(code, msg):
    print(msg)
    sys.exit(code)


# ===================================================================== B1 / B6 (shared)
def b1_class(row):
    """AM-7 B1 class of ONE wrong run from its graded row: loud (did not execute) /
    silent_empty (executed, 0 rows) / silent_nonempty (executed, >= 1 row). A blank or
    non-integer n_rows on an executed run stops every script the same way (exit 2)."""
    if row.get("exec_ok") != "True":
        return "loud"
    n = (row.get("n_rows") or "").strip()
    if not n.isdigit():
        die(2, f"[B1] executed wrong run without an integer n_rows ({row.get('model_key')}, "
               f"{row.get('lang')}, {row.get('qid')}, run {row.get('run')}): B1 needs the n_rows "
               f"column of grade_v13n.py")
    return "silent_empty" if int(n) == 0 else "silent_nonempty"


def b6_flags(fail_reason):
    """(bad_column, bad_function, bad_operator, bad_relation) of one graded fail_reason;
    only PostgreSQL execution errors count (never an API message)."""
    fr = fail_reason or ""
    if not fr.startswith("exec-error"):
        return False, False, False, False
    return (bool(B6_BAD_COLUMN.search(fr)), bool(B6_BAD_FUNCTION.search(fr)),
            bool(B6_BAD_OPERATOR.search(fr)), bool(B6_BAD_RELATION.search(fr)))


# ===================================================================== DRAFT guard
def add_draft_flag(ap):
    ap.add_argument("--allow-draft-testonly", action="store_true",
                    help="tests only: accept a DRAFT suite when every output is outside results/")


def path_parts(path, is_dir):
    """folder names of the resolved path (symlinks followed); a file's own name excluded."""
    parts = os.path.realpath(os.path.abspath(path)).split(os.sep)
    return parts if is_dir else parts[:-1]


def under_results(path, is_dir=False):
    """True when a folder of the resolved path is named results (any letter case: the
    project disk is case-insensitive)."""
    return any(p.casefold() == "results" for p in path_parts(path, is_dir))


def suite_is_draft(suite_path, suite_rows):
    if "DRAFT" in os.path.basename(suite_path).upper():
        return True
    return any("DRAFT" in (r.get("build_status") or "").upper() for r in suite_rows.values())


def draft_guard(suite_path, suite_rows, allow, out_files=(), out_dirs=()):
    """refuse a DRAFT suite (file name or build_status) unless --allow-draft-testonly and
    every output lies outside results/; --allow-draft-testonly with an output under
    results/ is refused too (same rule as grade_v13n.draft_guard). Returns draft."""
    draft = suite_is_draft(suite_path, suite_rows)
    if allow and (any(o and under_results(o) for o in out_files)
                  or any(o and under_results(o, True) for o in out_dirs)):
        die(2, "--allow-draft-testonly is for tests only (DRAFT suites): every output must be "
               "outside results/")
    if draft and not allow:
        die(2, f"suite {os.path.basename(suite_path)} is a DRAFT (file name or build_status); "
               f"official steps use the frozen suite")
    if draft:
        print(f"[suite] DRAFT suite {os.path.basename(suite_path)} accepted for a TEST-ONLY run")
    return draft


def row_arm(row):
    """arm of a graded row or a results record; a missing/empty arm is 'base'."""
    a = row.get("arm")
    if a is None:
        return "base"
    a = str(a).strip()
    return a or "base"


def add_arm_contract(ap, runs=True, exclude=True):
    ap.add_argument("--arm", required=True,
                    help="arm to analyse (no default); rows/records without an arm are 'base'")
    if runs:
        ap.add_argument("--runs", type=int, default=5,
                        help="runs every (model, lang, qid) cell must have after the filter")
    if exclude:
        ap.add_argument("--exclude-models", default="",
                        help="comma list of models left out (AM-7 A5.6); recorded in meta")


def split_list(spec):
    return [x.strip() for x in (spec or "").split(",") if x.strip()]


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_csv_rows(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def load_suite_rows(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return {r["id"]: r for r in csv.DictReader(fh, delimiter="\t")}


def primary_suite(suite, keep_excluded):
    if keep_excluded:
        return dict(suite)
    return {k: v for k, v in suite.items()
            if (v.get("v13_status") or "primary").strip() != "excluded"}


def read_vg_set(path, universe=None):
    """VG set file: one qid per line ('#' comments and blank lines ignored)."""
    out = []
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            s = line.split("#", 1)[0].strip()
            if not s:
                continue
            if not re.fullmatch(r"[A-Za-z0-9_\-]+", s):
                die(2, f"[vg-set] {os.path.basename(path)}: bad line {s[:20]!r}")
            out.append(s)
    if len(set(out)) != len(out):
        die(2, f"[vg-set] {os.path.basename(path)}: duplicate qid")
    if universe is not None:
        bad = [q for q in out if q not in universe]
        if bad:
            die(2, f"[vg-set] {os.path.basename(path)}: qids not among the analysed items: {bad}")
    return out


def filter_arm(rows, arm, excluded_models=(), label="graded"):
    """keep rows of --arm; drop listed models; print counts only."""
    kept, dropped, n_excl = [], Counter(), 0
    excluded_models = set(excluded_models)
    for r in rows:
        a = row_arm(r)
        if a != arm:
            dropped[a] += 1
            continue
        if r.get("model_key") in excluded_models:
            n_excl += 1
            continue
        kept.append(r)
    msg = (f"[arm] {label}: --arm {arm}: kept {len(kept)} rows; dropped by arm: "
           f"{dict(sorted(dropped.items())) if dropped else 0}")
    if excluded_models:
        msg += f"; --exclude-models {sorted(excluded_models)}: {n_excl} rows dropped"
    print(msg)
    if not kept:
        die(2, f"[arm] {label}: no rows left for --arm {arm}")
    return kept


def require_complete(rows, runs, qids, label="graded", langs=LANGS):
    """every (model, lang, qid) of the analysed items must have exactly `runs` rows."""
    cnt = Counter((r["model_key"], r["lang"], r["qid"]) for r in rows)
    models = sorted({r["model_key"] for r in rows})
    bad = [(m, lg, q, cnt.get((m, lg, q), 0)) for m in models for lg in langs
           for q in qids if cnt.get((m, lg, q), 0) != runs]
    if bad:
        die(2, f"[arm] {label}: {len(bad)} cells do not have exactly {runs} runs after the "
               f"arm filter (first: {bad[:6]}); a renamed arm, a merged file or an "
               f"incomplete model? (use --exclude-models for AM-7 A5.6)")
    return models


def require_complete_present(rows, runs, label="graded"):
    """every cell present in the rows must have exactly `runs` rows."""
    cnt = Counter((r["model_key"], r["lang"], r["qid"]) for r in rows)
    bad = [(k, n) for k, n in sorted(cnt.items()) if n != runs]
    if bad:
        die(2, f"[arm] {label}: {len(bad)} cells do not have exactly {runs} runs after the "
               f"arm filter (first: {bad[:6]})")


def _write_json(path, obj):
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=1, sort_keys=True)
        fh.write("\n")


def read_meta(path):
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def input_record(path):
    return {"basename": os.path.basename(path), "sha256": sha256_file(path)}


# ===================================================================== D10 session identity
def session_fingerprint(rows, arm):
    """{qid: sha256[:16]} over the sorted 'model|lang|run|latency_s' lines of the rows of
    one arm. latency_s is copied from the results record by the grader, so two gradings
    of the same log (n=59 / n=60 / positional) agree on every shared item, while two
    sessions (August log, October session) differ on every item."""
    lines = defaultdict(list)
    for r in rows:
        if row_arm(r) == arm:
            lines[r.get("qid", "")].append("|".join(str(r.get(k) or "") for k in
                                                    ("model_key", "lang", "run", "latency_s")))
    return {q: hashlib.sha256("\n".join(sorted(v)).encode("utf-8")).hexdigest()[:16]
            for q, v in sorted(lines.items())}


def graded_record(path, rows_all, arm):
    """input record of a graded file: basename, sha256, the arms present in the file and
    the session fingerprint of --arm (D10 checks of make_tables, make_figures,
    analyze_log_v13 B5 and consistency_aug_oct)."""
    rec = input_record(path)
    rec["arms_in_file"] = sorted({row_arm(r) for r in rows_all})
    rec["session_fp"] = session_fingerprint(rows_all, arm)
    return rec


def same_session(rec_a, rec_b):
    """(bool, why): two graded input records come from the same session when the files
    are identical, or when their session fingerprints agree on every shared item."""
    if not rec_a or not rec_b:
        return False, "an input record is missing"
    if rec_a.get("sha256") and rec_a.get("sha256") == rec_b.get("sha256"):
        return True, "same file"
    fa, fb = rec_a.get("session_fp"), rec_b.get("session_fp")
    if not fa or not fb:
        return False, "no session fingerprint (meta written before the D10 checks)"
    shared = sorted(set(fa) & set(fb))
    if not shared:
        return False, "no shared item"
    diff = [q for q in shared if fa[q] != fb[q]]
    if diff:
        return False, f"{len(diff)} of {len(shared)} shared items differ (first {diff[:3]})"
    return True, f"same session on {len(shared)} shared items"


def describe(rec):
    return (f"{rec.get('basename')} (sha256 {str(rec.get('sha256'))[:12]}..., arms in file: "
            f"{', '.join(rec.get('arms_in_file') or ['?'])})")


# ===================================================================== D11 (one place)
# D11 (author, 14 Oct 2026; brief 1.0b): the repaired items are repaired in place for the
# October session only. The October core suite carries each as v13_status primary with the
# new question and gold (n=60: the primary analyses of the October session); the August
# suite keeps the original item excluded (D3; n=59, and n=60 with --keep-excluded as the
# August sensitivity); the August-October comparison (consistency_aug_oct) and the drift of
# analyze_rc1 use the items shared by the two suites (59). The list is NOT declared here: it
# is read from the registry suite_columns.json next to this file (core_repaired.items, the
# list selftest_v13n reads), so the analysis and the suite checks share one declaration;
# every analysis script reads D11_REPAIRED from this module. The prompt-byte exception of
# check_prompts_rc1 (D11_PROMPT_EXCEPTION) must name the same items (RN-D11).
SUITE_COLUMNS_NAME = "suite_columns.json"


def load_d11_repaired(path=None):
    """tuple of the repaired core items: core_repaired.items of suite_columns.json (next to
    this file unless `path` is given). A missing file or list stops (exit 2)."""
    path = path or os.path.join(HERE, SUITE_COLUMNS_NAME)
    try:
        with open(path, encoding="utf-8") as fh:
            items = (json.load(fh).get("core_repaired") or {}).get("items")
    except (OSError, ValueError) as e:
        die(2, f"[D11] cannot read core_repaired.items from {os.path.basename(path)} next to "
               f"analyze.py ({type(e).__name__}); copy suite_columns.json into the same folder")
    if not isinstance(items, list) or not items or not all(isinstance(x, str) and x for x in items):
        die(2, f"[D11] {os.path.basename(path)}: core_repaired.items must be a non-empty list of item ids")
    return tuple(items)


D11_REPAIRED = load_d11_repaired()
# --keep-excluded (n=60 August sensitivity) is defined only for the August re-grade made with
# --keep-excluded at RUNBOOK step 2.2; a graded file with another name is refused with the
# August suite and --keep-excluded (d11_check), so a base-only copy of the October log, whose
# repaired rows answer the new question, cannot pass as that sensitivity.
AUG_KEEP_EXCLUDED_GRADED = "graded_v13n_withQ27.csv"
SESSION_OCT, SESSION_AUG, SESSION_V12, SESSION_NONE = "october", "august", "v1.2", "none"


def suite_session(suite_rows, where="suite"):
    """D11 session of a suite, from the status of the repaired items: 'october' (every D11
    item primary: the October core suite), 'august' (every D11 item excluded: the August
    suite v1.3/v1.3n), 'v1.2' (no v13_status column: the submitted key, D11 items primary
    with the original gold), 'none' (no D11 item: extension or synthetic suites). A suite
    that holds only some D11 items or mixes their status stops (exit 2)."""
    present = [q for q in D11_REPAIRED if q in suite_rows]
    if not present:
        return SESSION_NONE
    if len(present) != len(D11_REPAIRED):
        die(2, f"[D11] {where}: holds {present} but not every repaired item {list(D11_REPAIRED)}")
    if not any("v13_status" in r for r in suite_rows.values()):
        return SESSION_V12
    st = {(suite_rows[q].get("v13_status") or "primary").strip() for q in present}
    if st == {"excluded"}:
        return SESSION_AUG
    if st == {"primary"}:
        return SESSION_OCT
    die(2, f"[D11] {where}: status of the repaired items {sorted(st)}; expected all 'excluded' "
           f"(August suite) or all 'primary' (October core suite)")


def d11_shared(qids, session):
    """items of `qids` that ask the same question in both sessions: on the October core
    suite the D11 items are left out (repaired for the October session only)."""
    if session == SESSION_OCT:
        return [q for q in qids if q not in D11_REPAIRED]
    return list(qids)


def d11_check(suite_rows, keep_excluded, grec, where="suite"):
    """D11 contract between a core suite and the graded file (input record of
    graded_record; None when the script reads no graded file). Returns the session of the
    suite (suite_session) and prints one [D11] line.
      october: the graded file must be the two-arm October core log (the August re-grade
               and the submitted grading never answered the repaired question);
      august:  --keep-excluded on the October core log is refused (its D11 rows answer the
               repaired question, not the original one), and so is --keep-excluded on any
               graded file other than AUG_KEEP_EXCLUDED_GRADED (the August re-grade of step
               2.2; this also stops a base-only copy of the October log); without it the
               October log gives a 59-item view, never the primary October analysis
               (paper_guard refuses it);
      v1.2:    the October core log is refused (the D11 items keep the original gold);
      none:    no D11 item in the suite, nothing to check."""
    session = suite_session(suite_rows, where)
    two_arm = set(TWO_ARMS) <= set((grec or {}).get("arms_in_file") or [])
    items = ", ".join(D11_REPAIRED)
    if session == SESSION_OCT:
        if grec is not None and not two_arm:
            die(2, f"[D11] the October core suite ({items} repaired, primary) is for the two-arm "
                   f"October core log only; {describe(grec)} is not it (the August re-grade keeps "
                   f"the original {items} excluded: use the August suite)")
        print(f"[D11] October core suite: {items} repaired and primary (n=60, primary analyses "
              f"of the October session)")
    elif session == SESSION_AUG:
        if two_arm and keep_excluded:
            die(2, f"[D11] --keep-excluded with the August suite on the October core log refused: "
                   f"{items} of the October session answers the repaired question; use the "
                   f"October core suite")
        if keep_excluded and grec is not None and grec.get("basename") != AUG_KEEP_EXCLUDED_GRADED:
            die(2, f"[D11] --keep-excluded with the August suite refused for {describe(grec)}: the n=60 "
                   f"August sensitivity is defined only for {AUG_KEEP_EXCLUDED_GRADED} (the August "
                   f"re-grade with --keep-excluded, RUNBOOK step 2.2); a base-only copy of the October "
                   f"log would pass its repaired {items} rows as answers to the original question")
        if two_arm:
            print(f"[D11] October core log on the August suite: {items} left out (59 items); not "
                  f"the primary October analysis (n=60 on the October core suite)")
        else:
            print(f"[D11] August suite: {items} " + ("kept (--keep-excluded: n=60 sensitivity of "
                                                     "the August log)" if keep_excluded
                                                     else "excluded (n=59)"))
    elif session == SESSION_V12 and two_arm:
        die(2, f"[D11] suite v1.2 on the October core log refused: {items} keeps the original "
               f"gold there; use the October core suite")
    return session


def producers_graded(meta, where):
    """the single graded input record shared by every producer of a tables folder."""
    recs = {}
    for prod, det in (meta or {}).get("producers", {}).items():
        g = (det.get("inputs") or {}).get("graded")
        if not g:
            die(2, f"[meta] {where}: producer {prod} records no graded input")
        recs[prod] = g
    if not recs:
        die(2, f"[meta] {where}: no producer")
    shas = {g.get("sha256") for g in recs.values()}
    if len(shas) != 1:
        die(2, f"[meta] {where}: producers read different graded files "
               f"{ {p: g.get('basename') for p, g in recs.items()} } (D10: one session per folder)")
    return next(iter(recs.values()))


def paper_guard(out_path, graded_recs, is_dir, arm, session):
    """D10: the paper's folder (any folder named 'paper' on the resolved output path)
    takes tables of the October core log only, i.e. a graded file holding both arms
    base and values (the August log and the extension hold the base arm only), and only
    tables of the base arm (PAPER_ARM; values-arm tables go to results/ and the artifact).
    `arm` is the arm of the input tables (their meta, already equal to --arm).
    D11: and only tables computed on the October core suite (`session`, the suite_session
    recorded in the tables meta, must be 'october': n=60 with the repaired items)."""
    if not any(p.casefold() == "paper" for p in path_parts(out_path, is_dir)):
        return False
    if arm != PAPER_ARM:
        die(2, f"[D10] output under paper/ refused: the tables are of arm {arm!r}; the paper's "
               f"main tables come from the {PAPER_ARM} arm of the October session")
    for g in graded_recs:
        if not set(TWO_ARMS) <= set((g or {}).get("arms_in_file") or []):
            die(2, f"[D10] output under paper/ refused: the input {describe(g or {})} is not the "
                   f"two-arm October core log (all primary numbers come from the October session)")
    if session != SESSION_OCT:
        die(2, f"[D11] output under paper/ refused: the tables were computed on a suite of session "
               f"{session!r}; the paper's tables come from the October core suite "
               f"({', '.join(D11_REPAIRED)} repaired, n=60 primary)")
    print(f"[D10] output under paper/: every graded input is the two-arm October core log, "
          f"arm {arm}; [D11] October core suite (n=60)")
    return True


def guard_dir_meta(out_dir, common, graded=None):
    """refuse, BEFORE any output is written, a folder whose meta.json belongs to another
    arm, keep_excluded setting or suite, or (D10) whose producers read another graded
    file than `graded` (input record of this run)."""
    p = os.path.join(out_dir, META_NAME)
    meta = read_meta(p) or {}
    for k in META_CONSISTENT:
        if k in meta and k in common and meta[k] != common[k]:
            die(2, f"[meta] {p}: existing {k}={meta[k]!r} differs from this run "
                   f"({common[k]!r}); write to a fresh output folder")
    if graded:
        for prod, det in meta.get("producers", {}).items():
            g = (det.get("inputs") or {}).get("graded")
            if g and g.get("sha256") != graded.get("sha256"):
                die(2, f"[meta] {p}: {prod} read {g.get('basename')} (sha256 "
                       f"{str(g.get('sha256'))[:12]}...), this run reads {graded.get('basename')} "
                       f"(sha256 {str(graded.get('sha256'))[:12]}...); one graded file per output "
                       f"folder (D10); write to a fresh output folder")
    return meta


def update_dir_meta(out_dir, producer, common, detail):
    """merge this producer into <out_dir>/meta.json (guarded as guard_dir_meta)."""
    p = os.path.join(out_dir, META_NAME)
    graded = (detail.get("inputs") or {}).get("graded")
    meta = guard_dir_meta(out_dir, common, graded) or {"producers": {}}
    meta.update(common)
    meta.setdefault("producers", {})[producer] = detail
    _write_json(p, meta)
    return p


def write_file_meta(out_path, producer, common, detail):
    p = out_path + ".meta.json"
    obj = dict(common)
    obj["producer"] = producer
    obj.update(detail)
    _write_json(p, obj)
    return p


def check_meta_arm(meta, arm, where, required=True):
    if meta is None:
        if required:
            die(2, f"[meta] {where}: no meta.json; the input was not produced under the "
                   f"--arm contract")
        return False
    if meta.get("arm") != arm:
        die(2, f"[meta] {where}: arm {meta.get('arm')!r} differs from --arm {arm}")
    return True


def common_meta(arm, suite_path, keep_excluded, n_items):
    """meta shared by every producer of a folder; suite_session (D11) tells the October core
    suite (n=60) from the August suite (n=59) for paper_guard."""
    return {"arm": arm, "keep_excluded": bool(keep_excluded),
            "suite_sha256": sha256_file(suite_path), "n_items": n_items,
            "suite_session": suite_session(load_suite_rows(suite_path),
                                           os.path.basename(suite_path))}


# ===================================================================== statistics
def wilson(k, n, z=1.96):
    if n == 0:
        return (0, 0, 0)
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, max(0, c - h), min(1, c + h)


def mcnemar_p(b, c):
    """exact binomial two-sided บน discordant pairs"""
    n = b + c
    if n == 0:
        return 1.0
    from math import comb
    k = min(b, c)
    p = sum(comb(n, i) for i in range(0, k + 1)) / 2 ** n * 2
    return min(1.0, p)


def newcombe_paired(k1, k0, b, c, n, z=1.96):
    """Newcombe (1998) hybrid-score interval of p1-p2 WITHOUT the paired correlation
    correction (phi = 0; AMENDMENT-7 D-1, kept as computed in the submitted version)"""
    p1, l1, u1 = wilson(k1, n)
    p2, l2, u2 = wilson(k0, n)
    d = p1 - p2
    lo = d - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2)
    hi = d + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2)
    return d, lo, hi


def holm(pvals):
    idx = sorted(range(len(pvals)), key=lambda i: pvals[i])
    m = len(pvals)
    adj = [0.0] * m
    prev = 0.0
    for rank, i in enumerate(idx):
        v = min(1.0, (m - rank) * pvals[i])
        prev = max(prev, v)
        adj[i] = prev
    return adj


# ===================================================================== main
def main():
    ap = argparse.ArgumentParser(description="item-level tables (prereg) under the --arm contract")
    ap.add_argument("--graded", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--out", required=True, help="output folder (no default: D10)")
    ap.add_argument("--keep-excluded", action="store_true",
                    help="v1.3: keep items with v13_status=excluded (n=60 sensitivity of the "
                         "August log; only for the August re-grade graded_v13n_withQ27.csv of step "
                         "2.2; the October core suite has no excluded item, D11)")
    ap.add_argument("--vg-set", help="VG list file (one qid per line) for value_translated; "
                                     "default: vg_rule.is_value_grounding (unchanged)")
    add_arm_contract(ap)
    add_draft_flag(ap)
    a = ap.parse_args()
    suite_rows = load_suite_rows(a.suite)
    draft_guard(a.suite, suite_rows, a.allow_draft_testonly, out_dirs=[a.out])
    rows_all = read_csv_rows(a.graded)
    grec = graded_record(a.graded, rows_all, a.arm)
    d11_check(suite_rows, a.keep_excluded, grec, os.path.basename(a.suite))
    os.makedirs(a.out, exist_ok=True)

    suite = primary_suite(suite_rows, a.keep_excluded)
    # value_translated: literal ใน gold ไม่โผล่ verbatim ใน TH (หรือรายการจาก --vg-set)
    if a.vg_set:
        vgs = set(read_vg_set(a.vg_set, universe=suite))
        val_tr = {qid: qid in vgs for qid in suite}
    else:
        from vg_rule import is_value_grounding
        val_tr = {qid: is_value_grounding(r["gold_sql_draft"], r["question_th"])
                  for qid, r in suite.items()}

    common = common_meta(a.arm, a.suite, a.keep_excluded, len(suite))
    guard_dir_meta(a.out, common, grec)    # before any output is written
    excluded_models = split_list(a.exclude_models)
    graded = filter_arm(rows_all, a.arm, excluded_models)
    require_complete(graded, a.runs, sorted(suite))

    runs = defaultdict(list)   # (model, lang, qid) -> [correct...]
    parse = defaultdict(list)
    for row in graded:
        k = (row["model_key"], row["lang"], row["qid"])
        runs[k].append(row["correct"] == "True")
        parse[k].append(row["parse_ok"] == "True")

    models = sorted({k[0] for k in runs})
    item = {k: (sum(v) > len(v) / 2) for k, v in runs.items()}
    unanim = {k: (len(set(v)) == 1) for k, v in runs.items()}

    # ---- ตารางหลัก: accuracy + CI ----
    with open(f"{a.out}/accuracy.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "lang", "scope", "correct", "n", "acc", "ci_lo", "ci_hi"])
        for m in models:
            for lang in ("en", "th"):
                ks = [q for q in suite if (m, lang, q) in item]
                c = sum(item[(m, lang, q)] for q in ks)
                p, lo, hi = wilson(c, len(ks))
                w.writerow([m, lang, "all", c, len(ks), f"{p:.3f}", f"{lo:.3f}", f"{hi:.3f}"])
                for tier in ("1", "2", "3", "4"):
                    kt = [q for q in ks if suite[q]["tier"] == tier]
                    ct = sum(item[(m, lang, q)] for q in kt)
                    p2, l2, h2 = wilson(ct, len(kt))
                    w.writerow([m, lang, f"tier{tier}", ct, len(kt), f"{p2:.3f}", f"{l2:.3f}", f"{h2:.3f}"])

    # ---- McNemar TH vs EN + Holm + Δ CI ----
    pvals, rows = [], []
    for m in models:
        b = sum(1 for q in suite if item.get((m, "en", q)) and not item.get((m, "th", q)))
        c = sum(1 for q in suite if item.get((m, "th", q)) and not item.get((m, "en", q)))
        k_en = sum(1 for q in suite if item.get((m, "en", q)))
        k_th = sum(1 for q in suite if item.get((m, "th", q)))
        n = len(suite)
        p = mcnemar_p(b, c)
        d, lo, hi = newcombe_paired(k_en, k_th, b, c, n)
        pvals.append(p)
        rows.append([m, k_en, k_th, b, c, f"{d:+.3f}", f"{lo:+.3f}", f"{hi:+.3f}", f"{p:.4f}"])
    adj = holm(pvals)
    with open(f"{a.out}/cross_lingual.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "correct_en", "correct_th", "en_only(b)", "th_only(c)",
                    "delta", "ci_lo", "ci_hi", "p_mcnemar", "p_holm"])
        for r, pa in zip(rows, adj):
            w.writerow(r + [f"{pa:.4f}"])

    # ---- stability / parse / value-translated ----
    with open(f"{a.out}/stability_parse.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "lang", "unanimity_rate", "parse_rate", "parse_ci_lo", "parse_ci_hi"])
        for m in models:
            for lang in ("en", "th"):
                ks = [q for q in suite if (m, lang, q) in unanim]
                u = sum(unanim[(m, lang, q)] for q in ks) / max(1, len(ks))
                pk = sum(sum(parse[(m, lang, q)]) for q in ks)
                pn = sum(len(parse[(m, lang, q)]) for q in ks)
                p, lo, hi = wilson(pk, pn)
                w.writerow([m, lang, f"{u:.3f}", f"{p:.3f}", f"{lo:.3f}", f"{hi:.3f}"])

    with open(f"{a.out}/value_translated.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["model", "group", "n_items", "acc_th"])
        for m in models:
            for flag, name in ((True, "value_translated"), (False, "value_kept_or_none")):
                ks = [q for q in suite if val_tr[q] == flag and (m, "th", q) in item]
                if not ks:
                    continue
                acc = sum(item[(m, "th", q)] for q in ks) / len(ks)
                w.writerow([m, name, len(ks), f"{acc:.3f}"])

    print(f"tables written to {a.out}/: accuracy, cross_lingual, stability_parse, value_translated")
    print("value_translated items:", sorted(q for q, v in val_tr.items() if v))
    detail = {"inputs": {"graded": grec}, "runs": a.runs,
              "excluded_models": sorted(excluded_models), "models": models,
              "vg_set": input_record(a.vg_set) if a.vg_set else "vg_rule.is_value_grounding",
              "files": ["accuracy.csv", "cross_lingual.csv", "stability_parse.csv",
                        "value_translated.csv"]}
    p = update_dir_meta(a.out, "analyze.py", common, detail)
    print(f"[meta] {p} (arm {a.arm}, items {len(suite)})")


if __name__ == "__main__":
    main()
