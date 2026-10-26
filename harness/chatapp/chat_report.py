#!/usr/bin/env python3
"""chat_report.py -- mechanical report of the chat-app consistency check (prereg
AMENDMENT-8 sec.9-11). Descriptive counts only: no CI, no test.

Inputs (all graded files come from grade_v13n.py on k3n with suite v1.3n):
  --graded        graded_chat_k3n.csv (turn 1, arm chat; 84 cells)
  --graded-turn2  graded_chat_turn2_k3n.csv (optional; secondary result)
  --graded-tagsens graded_chat_tagsens_k3n.csv (optional; OQ33.1 Form A tag sensitivity):
                  the B2.3 codes, GF and levels are recomputed from these records
                  (--results-tagsens, default results_chat_tagsens.jsonl next to it) with
                  the same code as vg_outcome.py, and level changes are reported
  --vg-codes      vg_codes_chat.tsv (vg_outcome.py) with its <stem>_meta.json
  --silence       silence_final.tsv (chat_silence_sheet.py --agree)
  --rc1-graded    results/rc1/graded_rc1.csv, read under the --arm contract (design 2.6):
                  only --arm base rows are kept, dropped rows are counted, and every cell
                  (proxy, en|th, primary qid) must hold exactly 5 runs; D11: its rows of the
                  repaired Q27 (graded on the October core suite) are left out and counted,
                  because --suite is the August suite of the chat items (59-item view)
  --arm base      the comparator is the concurrent base arm (B) of AMENDMENT-7 Part A
  defaults        --log-index: log_index.tsv next to --graded; --raw-manifest:
                  raw_manifest.tsv next to the log index; --rc1-results:
                  results_rc1_api.jsonl next to --rc1-graded (SQL and parse_ok of the proxy
                  runs, for the proxy GF, and the B-arm dates); --suite and --hints: the
                  canonical ../suite files next to harness/
  --hints-sha256  optional: when given, the hint file must have it. Either way the hint
                  file must be the one vg_outcome.py used (sha256 in the vg_codes meta), and
                  vg_outcome.py (RUNBOOK C.6) checks it against the FREEZE STAMP
  --vocab-db k3   OQ33.7 sensitivity on k3 (vg_outcome.py --vocab-db k3; pass the k3 suite,
                  the k3 gradings and an explicit --rc1-results); default k3n
  window failure  an app whose chats fall outside +-7 days of its proxy's B arm is
                  labelled 'not concurrent'; its comparator follows the DEFAULT switch
                  FALLBACK_WINDOW_FAIL in make_chat_cells.py (A8-09): 'oct-base' keeps the
                  October base arm (default, brief 1.0 D10), 'aug-k3n' uses the fallback files
  fallback        --fallback-graded results/v13n/graded_v13n.csv and --fallback-results
                  results/results.jsonl (August log re-graded under key v1.3n on k3n): for a
                  proxy listed in --unusable-models (AMENDMENT-7 A5), and for a window
                  failure under 'aug-k3n'; such an app is labelled 'not concurrent'
Consistency guards (exit 2, nothing written): the vg_codes meta must name the same graded
file, hint file, suite and vocabulary database, and the vg_codes file must be unchanged
since vg_outcome.py wrote it; every cell's correct / exec_ok / n_rows in vg_codes must equal
the graded file, and its attempt must equal the done row of log_index.tsv; every row of
silence_final.tsv must carry the sha256 of this log_index.tsv and raw_manifest.tsv; every
correct/parse_ok/exec_ok value must be True or False.
Definitions (frozen in AMENDMENT-8; defaults of OQ33.9):
  k = 10 (VG10, Q48 counted within k)
  per app: reproduced = Form A has >= 1 GF cell; not reproduced = no GF cell in Form A
  or Form B and Form A has >= k - 1 clean cells; partially reproduced = otherwise
  cell GF (vg_outcome.py): a Form A or Form B reply whose SQL fails to parse is classified
  as a run without SQL (NO_PRED, never GF), the rule of analyze_rc1.py for the API runs;
  diagnostic only (not a rule): chat_rules.tsv counts the VG cells whose extracted SQL
  would be GF if it were classified despite the parse failure (class_extracted of
  vg_outcome.py) and gives the level that would follow
  proxy GF (B2.2): VG item, majority of 5 runs wrong, and more than half of the failing
  runs classified THAI_COPY or INVENTED by harness/vg_classifier.py; a failing run whose
  parse_ok is False is classified as a run without SQL (vg_outcome.classified_sql), so the
  proxy GF here equals the B2.2 GF of analyze_rc1.py
  silence (Form B, wrong or no-SQL cells): AMENDMENT-8 sec.6 codes a turn 1 without SQL
  as ASKED, so a no-SQL cell coded otherwise is set to ASKED and listed as an override;
  m = FLAGGED + ASKED; m >= n/2 -> "flagged or asked in m of n wrong replies"; otherwise
  "most wrong replies gave no warning (x of n)", x per the DEFAULT switch
  SILENCE_MOSTLY_SILENT_COUNT ('s' = SILENT = n - m, default; 'm' = the draft's literal m)
  turn 2: sent only when the app asked back (AMENDMENT-8 sec.6); a cell with turn 2 sent
  although turn 1 has SQL is listed as a deviation
  cell-major order (AMENDMENT-8 sec.5): cells started before the previous cell was done in
  all three apps are counted from log_index.tsv (make_chat_cells.cell_major_breaches, the
  rule chat_log_export.py prints) and listed as a deviation
  windows: all sent chats within 3 consecutive calendar days; every chat date of an app
  within [first B date - 7, last B date + 7] of its proxy's TH base-arm records
Outputs under --out (a new folder): chat_cells.tsv, chat_summary.tsv, chat_rules.tsv,
chat_report.txt, meta.json. --test labels every output TEST-ONLY. A DRAFT suite is
refused when --out lies under a folder named results.

Usage (from harness/):
  python3 -I -B "chatapp/chat_report.py" --graded "../results/chat/graded_chat_k3n.csv"
      --graded-turn2 "../results/chat/graded_chat_turn2_k3n.csv"
      --graded-tagsens "../results/chat/graded_chat_tagsens_k3n.csv" --vg-codes "../results/chat/vg_codes_chat.tsv"
      --silence "../results/chat/silence_final.tsv" --rc1-graded "../results/rc1/graded_rc1.csv"
      --arm base --out "../results/chat/report"
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import csv  # noqa: E402
import datetime as dt  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from collections import Counter, defaultdict  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draw_chat_items_v13 import (VG_CHAT, check_bool_fields, die, harness_dir,  # noqa: E402
                                 load_graded_arm, load_suite, majority_correct, primary_ids,
                                 refuse_draft_suite, sha256_file)
from make_chat_cells import (APP_LABEL, APP_PROXY, APPS, CELLS_PER_APP, CHAT_SPAN_MAX_DAYS,  # noqa: E402
                             CONCURRENT_DAYS, FALLBACK_WINDOW_FAIL, FORMS, LOG_COLUMNS,
                             SILENCE_MOSTLY_SILENT_COUNT, cell_major_breaches, check_switches, switches)
from vg_outcome import (GF_CLASSES, MODEL_KEY, VOCAB_DBS, classified_sql, code_cells,  # noqa: E402
                        load_chat_graded_runs, load_chat_results, load_classifier, load_vocab,
                        meta_path_of, read_jsonl, vg_setup)

K_VG = len(VG_CHAT)  # VG10 chosen (brief 1.2); Q48 counted within k
PID = re.compile(r"^\d{3}_(A|B)_(th|en)_(Q\d{2})$")
SILENCE_CODES = ("FLAGGED", "ASKED", "SILENT")
NOT_CONCURRENT = "not concurrent"
CONCURRENT = "concurrent B arm"


# ---------------------------------------------------------------- pure rules (unit-tested)
def app_level(gf_a, gf_b, clean_a, k=K_VG):
    if gf_a >= 1:
        return "reproduced"
    if gf_a == 0 and gf_b == 0 and clean_a >= k - 1:
        return "not reproduced"
    return "partially reproduced"


def silence_rule(codes, count=None):
    """codes of the Form B cells that are wrong or have no SQL (turn 1); the count shown in
    the 'mostly silent' sentence follows SILENCE_MOSTLY_SILENT_COUNT unless `count` is given."""
    count = count or SILENCE_MOSTLY_SILENT_COUNT
    n = len(codes)
    m = sum(1 for c in codes if c in ("FLAGGED", "ASKED"))
    if n == 0:
        return "none", "no wrong Form B replies", m, n
    if 2 * m >= n:
        return "flagged-or-asked", f"flagged or asked in {m} of {n} wrong replies", m, n
    shown = m if count == "m" else n - m
    return "mostly-silent", f"most wrong replies gave no warning ({shown} of {n})", m, n


def silence_with_rule(coded, form, sql_present):
    """(code used, source) for one cell: AMENDMENT-8 sec.6 codes a Form B turn 1 without
    SQL as ASKED; any other cell keeps the coded value."""
    if form == "B" and sql_present == "N" and coded != "ASKED":
        return "ASKED", "rule AM-8 sec.6 (no SQL in turn 1)"
    return coded, "coded"


def date_range(dates):
    if not dates:
        return "no dates"
    a, b = min(dates), max(dates)
    return a.isoformat() if a == b else f"{a.isoformat()} to {b.isoformat()}"


def chat_window_ok(dates):
    return bool(dates) and (max(dates) - min(dates)).days <= CHAT_SPAN_MAX_DAYS


def concurrent_ok(chat_dates, b_dates, days=CONCURRENT_DAYS):
    if not chat_dates or not b_dates:
        return False
    lo = min(b_dates) - dt.timedelta(days=days)
    hi = max(b_dates) + dt.timedelta(days=days)
    return all(lo <= d <= hi for d in chat_dates)


def app_statement(app, level, gf_a, gf_b, clean_a, proxy_gf_items, dates, k=K_VG):
    lab, when = APP_LABEL[app], date_range(dates)
    if level == "reproduced":
        return (f"the failure also appeared in the free {lab} ({gf_a} of {k} Form A cells; "
                f"entered {when}; single shot)")
    if level == "not reproduced":
        if proxy_gf_items:
            return f"not observed in {lab} on {when}, although its API proxy showed it (single shot)"
        return f"neither {lab} nor its API proxy showed this failure ({when}; single shot)"
    if gf_a == 0 and gf_b > 0:
        return (f"partially reproduced in {lab}: the failure appeared only in Form B "
                f"({gf_b} of {k}; {when}; single shot)")
    return (f"partially reproduced in {lab}: Form A replies were not clean enough to conclude "
            f"({clean_a} of {k} clean; {when}; single shot)")


def global_statements(levels):
    out = []
    if not any(v == "reproduced" for v in levels.values()):
        out.append("no app reproduced the failure: the value-grounding finding is confirmed at the "
                   "API-proxy level only; the Discussion advice on stored values is written at the proxy level")
        if all(v == "not reproduced" for v in levels.values()):
            out.append("the free apps did not show this failure on the test dates")
        else:
            out.append("do not write that the free apps do not show this failure; use the "
                       "'partially reproduced' wording for: "
                       + ", ".join(APP_LABEL[a] for a, v in levels.items() if v == "partially reproduced"))
    return out


# ---------------------------------------------------------------- loaders
def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as fh:
        return list(csv.DictReader((ln for ln in fh if not ln.startswith("#")), delimiter="\t"))


def load_chat_graded(path, label):
    cells = {}
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    check_bool_fields(rows, label)
    for r in rows:
        if (r.get("arm") or "") != "chat":
            die(f"{label}: row with arm other than 'chat'")
        m = MODEL_KEY.match(r["model_key"])
        if not m:
            die(f"{label}: unexpected model_key {r['model_key']}")
        k = (m.group(1), m.group(2), r["qid"])
        if k in cells:
            die(f"{label}: duplicate cell {k}")
        cells[k] = r
    return cells


def load_proxy(graded, results, suite, models, label, classifier, targets, vocab):
    """Majority verdicts (TH) and B2.2 GF of the paired proxies, plus TH base-arm dates."""
    import analyze  # noqa: E402  (harness/analyze.py: row_arm of the --arm contract)
    # D11: the October core log holds rows of the repaired Q27, which the August suite of the chat check
    # marks excluded; they are left out (59-item view), the chat items never include them
    cells, dropped, _ = load_graded_arm(graded, "base", suite, models, label=label, d11_view=True)
    run_ok = {}
    with open(graded, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            if analyze.row_arm(r) == "base" and r["model_key"] in models \
                    and r["lang"] == "th" and r["qid"] in VG_CHAT:
                run_ok[(r["model_key"], r["qid"], str(r["run"]))] = r["correct"] == "True"
    # (load_graded_arm above has already refused any verdict other than True/False)
    sqls, dates = {}, defaultdict(set)
    for p in results:
        for rec in read_jsonl(p, ("model_key", "arm", "lang", "qid", "run", "sql", "parse_ok", "ts")):
            if rec.get("error_is_set") or analyze.row_arm(rec) != "base":
                continue
            if rec.get("model_key") not in models or rec.get("lang") != "th":
                continue
            ts = rec.get("ts") or ""
            if re.match(r"^\d{4}-\d{2}-\d{2}", ts):
                dates[rec["model_key"]].add(dt.date.fromisoformat(ts[:10]))
            if rec["qid"] in VG_CHAT:
                k = (rec["model_key"], rec["qid"], str(rec["run"]))
                if k in sqls and k in run_ok and not run_ok[k]:
                    die(f"{label}: duplicate non-error record for a failing run {k}")
                sqls[k] = classified_sql(rec.get("sql"), rec.get("parse_ok"))
    maj = {(m, q): majority_correct(cells[(m, "th", q)]) for m in models for q in primary_ids(suite)}
    gf = {}
    for m in models:
        for q in VG_CHAT:
            if maj[(m, q)]:
                gf[(m, q)] = False
                continue
            fails = [k for k, ok in run_ok.items() if k[0] == m and k[1] == q and not ok]
            missing = [k for k in fails if k not in sqls]
            if missing:
                die(f"{label}: failing run without a result record ({missing[0][0]} {missing[0][1]} run "
                    f"{missing[0][2]})")
            classes = [classifier.classify_run(sqls[k], targets[q], vocab) for k in fails]
            if callable(getattr(classifier, "is_gf_cell", None)):
                gf[(m, q)] = bool(classifier.is_gf_cell(True, True, classes))
            elif callable(getattr(classifier, "gf_union_majority", None)):
                gf[(m, q)] = bool(classifier.gf_union_majority(classes))
            else:
                gf[(m, q)] = 2 * sum(1 for c in classes if c in GF_CLASSES) > len(classes)
    return {"maj": maj, "gf": gf, "dates": dates, "dropped": dropped}


def suite_matches_db(suite_path, vocab_db):
    """canonical names: k3n_suite_* with the k3n vocabulary, k3_suite_* with k3."""
    name = os.path.basename(suite_path)
    if vocab_db == "k3" and name.startswith("k3n"):
        die(f"--vocab-db k3 with the k3n suite {name}: pass the k3 suite (../suite/k3_suite_v1.3.tsv)")
    if vocab_db == "k3n" and name.startswith("k3_"):
        die(f"the k3 suite {name} needs --vocab-db k3 (OQ33.7 sensitivity)")


def parse_log_ts(v):
    return dt.datetime.strptime(v, "%Y-%m-%dT%H:%M:%S") if v else None


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--graded", required=True)
    ap.add_argument("--graded-turn2")
    ap.add_argument("--vg-codes", required=True)
    ap.add_argument("--silence", required=True)
    ap.add_argument("--rc1-graded", required=True)
    ap.add_argument("--arm", required=True, choices=["base"])
    ap.add_argument("--out", required=True)
    ap.add_argument("--test", action="store_true", help="label every output TEST-ONLY")
    ap.add_argument("--log-index")
    ap.add_argument("--raw-manifest", help="default: raw_manifest.tsv next to the log index")
    ap.add_argument("--rc1-results", action="append")
    ap.add_argument("--suite")
    ap.add_argument("--hints")
    ap.add_argument("--hints-sha256", help="optional: sha256 the hint file must have (FREEZE STAMP)")
    ap.add_argument("--vocab-db", choices=VOCAB_DBS, default="k3n", help="k3 for the OQ33.7 sensitivity")
    ap.add_argument("--fallback-graded")
    ap.add_argument("--fallback-results", action="append")
    ap.add_argument("--unusable-models", default="", help="comma list of proxies unusable under AMENDMENT-7 A5")
    ap.add_argument("--graded-tagsens", help="graded turn-1 file of the OQ33.1 Form A tag sensitivity")
    ap.add_argument("--results-tagsens", help="default: results_chat_tagsens.jsonl next to --graded-tagsens")
    ap.add_argument("--harness-dir")
    a = ap.parse_args()
    check_switches()
    if os.path.exists(a.out):
        die(f"--out exists, refusing to overwrite: {os.path.basename(os.path.abspath(a.out))}")
    hdir = harness_dir(a.harness_dir)
    suite_path = a.suite or os.path.join(os.path.dirname(hdir), "suite", "k3n_suite_v1.3n.tsv")
    hints_path = a.hints or os.path.join(os.path.dirname(hdir), "suite", "value_hints_v1.json")
    log_index = a.log_index or os.path.join(os.path.dirname(os.path.abspath(a.graded)), "log_index.tsv")
    raw_manifest = a.raw_manifest or os.path.join(os.path.dirname(os.path.abspath(log_index)), "raw_manifest.tsv")
    rc1_results = a.rc1_results or [os.path.join(os.path.dirname(os.path.abspath(a.rc1_graded)),
                                                 "results_rc1_api.jsonl")]
    results_tagsens = None
    if a.graded_tagsens:
        results_tagsens = a.results_tagsens or os.path.join(os.path.dirname(os.path.abspath(a.graded_tagsens)),
                                                            "results_chat_tagsens.jsonl")
    vmeta_path = meta_path_of(a.vg_codes)
    for p in [suite_path, hints_path, log_index, raw_manifest, vmeta_path] + rc1_results \
            + ([results_tagsens] if results_tagsens else []):
        if not os.path.isfile(p):
            die(f"input not found: {os.path.basename(p)} (pass it explicitly)")
    suite_matches_db(suite_path, a.vocab_db)
    unusable = {x.strip() for x in a.unusable_models.split(",") if x.strip()}
    if unusable - set(APP_PROXY.values()):
        die(f"--unusable-models names an unknown proxy: {sorted(unusable - set(APP_PROXY.values()))}")
    hs = sha256_file(hints_path)
    if a.hints_sha256 and hs != a.hints_sha256.strip().lower():
        die(f"sha256 of the hint file is {hs}, expected {a.hints_sha256}")

    # ---- the vg codes must come from these inputs (vg_outcome.py meta)
    with open(vmeta_path, encoding="utf-8") as fh:
        vmeta = json.load(fh)
    bad = []
    if vmeta.get("vg_codes_sha256") != sha256_file(a.vg_codes):
        bad.append("the vg_codes file changed after vg_outcome.py wrote it")
    if vmeta.get("graded_sha256") != sha256_file(a.graded):
        bad.append(f"vg_codes were built from another graded file ({vmeta.get('graded_file')})")
    if vmeta.get("hints_sha256") != hs:
        bad.append("vg_codes were built with another hint file")
    if vmeta.get("suite_sha256") != sha256_file(suite_path):
        bad.append(f"vg_codes were built with another suite ({vmeta.get('suite_file')})")
    if vmeta.get("vocab_db") != a.vocab_db:
        bad.append(f"vg_codes use the {vmeta.get('vocab_db')} vocabulary, this report {a.vocab_db}")
    if bad:
        die("vg_codes do not belong to these inputs: " + "; ".join(bad))

    vgc, vg_rule = load_classifier(hdir)
    suite = load_suite(suite_path)
    refuse_draft_suite(suite_path, suite, [os.path.join(os.path.abspath(a.out), "chat_report.txt")])
    lits, targets = vg_setup(suite, vgc, vg_rule)
    vocab, vocab_src = load_vocab(vgc, hints_path, targets, a.vocab_db)

    g1 = load_chat_graded(a.graded, "graded")
    if len(g1) != CELLS_PER_APP * len(APPS):
        die(f"graded holds {len(g1)} chat cells, expected {CELLS_PER_APP * len(APPS)}")
    g2 = load_chat_graded(a.graded_turn2, "graded-turn2") if a.graded_turn2 else {}
    codes = {(r["app"], r["form"], r["qid"]): r for r in read_tsv(a.vg_codes)}
    if set(codes) != set(g1):
        die("vg_codes and graded cover different cells")
    diff = [k for k in g1 if (codes[k]["correct"], codes[k]["exec_ok"], codes[k]["n_rows"])
            != ("Y" if g1[k]["correct"] == "True" else "N", "Y" if g1[k]["exec_ok"] == "True" else "N",
                g1[k]["n_rows"])]
    if diff:
        die(f"vg_codes disagree with the graded file on {len(diff)} cells (first {' '.join(diff[0])}): "
            "they were built from another grading")

    # ---- log index: dates, turn 2, attempts, cell-major order
    chat_dates = defaultdict(set)
    turn2_sent, done_attempt, log_rows = {}, {}, []
    for r in read_tsv(log_index):
        if list(r.keys()) != LOG_COLUMNS:
            die("log_index.tsv header differs")
        if r["ts_sent_ict"]:
            chat_dates[r["app"]].add(dt.date.fromisoformat(r["ts_sent_ict"][:10]))
        m = PID.match(r["prompt_id"])
        if r["status"] == "done" and m:
            turn2_sent[(r["app"], m.group(1), m.group(3))] = r["turn2_sent"] == "Y"
            done_attempt[(r["app"], m.group(1), m.group(3))] = r["attempt"]
        log_rows.append({"order": int(r["order"]), "status": r["status"],
                         "ts_sent": parse_log_ts(r["ts_sent_ict"]), "ts_done": parse_log_ts(r["ts_done_ict"])})
    bad_att = [k for k in g1 if str(codes[k]["attempt"]) != str(done_attempt.get(k))]
    if bad_att:
        die(f"vg_codes and log_index.tsv disagree on the attempt of {len(bad_att)} cells (first "
            f"{' '.join(bad_att[0])}): the chat results were converted from another log index")
    breach = cell_major_breaches(log_rows)
    all_dates = set().union(*chat_dates.values()) if chat_dates else set()
    window3 = chat_window_ok(all_dates)
    t2_deviation = [k for k in g1 if turn2_sent.get(k) and codes[k]["sql_present"] == "Y"]

    # ---- silence codes, tied to this log index and raw manifest
    srows = read_tsv(a.silence)
    li_sha, rm_sha = sha256_file(log_index), sha256_file(raw_manifest)
    if not srows or any(r.get("log_index_sha256") != li_sha or r.get("raw_manifest_sha256") != rm_sha
                        for r in srows):
        die("silence codes were not coded from this log_index.tsv and raw_manifest.tsv (sha256 columns of "
            "silence_final.tsv; rerun chat_silence_sheet.py --agree with the current kit if they are missing)")
    coded = {(r["app"], r["form"], r["qid"]): r["code_final"].strip().upper() for r in srows}
    for k in g1:
        if k[1] == "B" and coded.get(k) not in SILENCE_CODES:
            die(f"silence code missing for {k}")
    silence, silence_src, overrides = {}, {}, []
    for k in g1:
        if k[1] != "B":
            continue
        silence[k], silence_src[k] = silence_with_rule(coded[k], k[1], codes[k]["sql_present"])
        if silence_src[k] != "coded":
            overrides.append(f"{k[0]} B {k[2]} (coded {coded[k]})")

    # ---- OQ33.1 tag sensitivity: codes, GF and levels recomputed from its own records
    tcodes = {}
    if a.graded_tagsens:
        gsr = load_chat_graded_runs(a.graded_tagsens, "graded-tagsens")
        srecs = load_chat_results(results_tagsens, gsr, "results-tagsens")
        trows = code_cells(srecs, gsr, lits, targets, vocab, vgc)[0]
        tcodes = {(r["app"], r["form"], r["qid"]): r for r in trows}
        if set(tcodes) != set(g1):
            die("tag-sensitivity records cover other cells than the graded file")

    proxies = [APP_PROXY[x] for x in APPS]
    usable = [p for p in proxies if p not in unusable]
    rc1 = load_proxy(a.rc1_graded, rc1_results, suite, usable, "rc1-graded", vgc, targets, vocab) \
        if usable else {"maj": {}, "gf": {}, "dates": {}, "dropped": {}}
    comparator, src_name, window = {}, {}, {}
    for app in APPS:
        p = APP_PROXY[app]
        window[app] = p not in unusable and concurrent_ok(chat_dates[app], rc1["dates"].get(p, set()))
        comparator[app] = CONCURRENT if window[app] else NOT_CONCURRENT
        if p in unusable or (not window[app] and FALLBACK_WINDOW_FAIL == "aug-k3n"):
            src_name[app] = "fallback"
        else:
            src_name[app] = "rc1"
    fb = None
    if any(v == "fallback" for v in src_name.values()):
        if not (a.fallback_graded and a.fallback_results):
            die("an app needs the fallback comparator (August log re-graded on k3n): pass "
                "--fallback-graded and --fallback-results")
        need = [APP_PROXY[x] for x in APPS if src_name[x] == "fallback"]
        fb = load_proxy(a.fallback_graded, a.fallback_results, suite, need, "fallback-graded",
                        vgc, targets, vocab)
    src = {app: (rc1 if src_name[app] == "rc1" else fb) for app in APPS}
    src_label = {app: ("October base arm" if src_name[app] == "rc1" else "August log re-graded on k3n")
                 for app in APPS}

    # ---- per-cell table
    rows = []
    for (app, form, q) in sorted(g1, key=lambda k: (APPS.index(k[0]), k[1], k[2])):
        g, c, P = g1[(app, form, q)], codes[(app, form, q)], src[app]
        proxy = APP_PROXY[app]
        correct = g["correct"] == "True"
        pmaj = P["maj"][(proxy, q)]
        pgf = P["gf"].get((proxy, q)) if q in VG_CHAT else None
        t2 = g2.get((app, form, q))
        tc = tcodes.get((app, form, q))
        rows.append({
            "app": app, "form": form, "qid": q, "vg": "yes" if q in VG_CHAT else "no", "tier": g["tier"],
            "correct": "Y" if correct else "N", "exec_class": c["exec_class"], "n_rows": g["n_rows"],
            "fail_reason": g["fail_reason"], "sql_present": c["sql_present"], "vg_code": c["vg_code"],
            "gf": c["gf"], "clean": c["clean"], "lit_elsewhere": c["lit_elsewhere"],
            "class_extracted": c.get("class_extracted", ""),
            "silence_code": silence.get((app, form, q), "") if form == "B" else "",
            "silence_code_coded": coded.get((app, form, q), "") if form == "B" else "",
            "silence_source": silence_src.get((app, form, q), "") if form == "B" else "",
            "proxy": proxy, "comparator": comparator[app], "comparator_source": src_label[app],
            "proxy_majority_correct": "Y" if pmaj else "N",
            "proxy_gf": "" if pgf is None else ("Y" if pgf else "N"),
            "concord_exec": "Y" if pmaj == correct else "N",
            "concord_gf": "" if pgf is None else ("Y" if (c["gf"] == "Y") == pgf else "N"),
            "turn2_sent": "Y" if turn2_sent.get((app, form, q)) else "N",
            "turn2_deviation": "Y" if (app, form, q) in t2_deviation else "N",
            "turn2_correct": "" if t2 is None else ("Y" if t2["correct"] == "True" else "N"),
            "tagsens_correct": "" if tc is None else tc["correct"],
            "tagsens_vg_code": "" if tc is None else tc["vg_code"],
            "tagsens_gf": "" if tc is None else tc["gf"],
            "tagsens_clean": "" if tc is None else tc["clean"],
        })

    # ---- summaries
    summ = []
    for app in APPS:
        for form in FORMS:
            for subset in ("ALL", "VG", "NONVG"):
                rs = [r for r in rows if r["app"] == app and r["form"] == form and
                      (subset == "ALL" or (subset == "VG") == (r["vg"] == "yes"))]
                if not rs:
                    continue
                cnt = Counter(r["exec_class"] for r in rs)
                vgr = [r for r in rs if r["vg"] == "yes"]
                t2r = [r for r in rs if r["turn2_correct"]]
                summ.append({
                    "app": app, "form": form, "subset": subset, "n_cells": len(rs),
                    "correct": sum(r["correct"] == "Y" for r in rs),
                    "wrong": sum(r["correct"] == "N" for r in rs),
                    "no_sql": sum(r["sql_present"] == "N" for r in rs),
                    "loud": cnt["loud"], "silent_empty": cnt["silent-empty"],
                    "silent_non_empty": cnt["silent-non-empty"],
                    "gf": sum(r["gf"] == "Y" for r in vgr) if vgr else "",
                    "clean": sum(r["clean"] == "Y" for r in vgr) if vgr else "",
                    "concord_exec": f"{sum(r['concord_exec'] == 'Y' for r in rs)}/{len(rs)}",
                    "concord_gf": f"{sum(r['concord_gf'] == 'Y' for r in vgr)}/{len(vgr)}" if vgr else "",
                    "silence_flagged": sum(r["silence_code"] == "FLAGGED" and r["correct"] == "N" for r in rs)
                    if form == "B" else "",
                    "silence_asked": sum(r["silence_code"] == "ASKED" and r["correct"] == "N" for r in rs)
                    if form == "B" else "",
                    "silence_silent": sum(r["silence_code"] == "SILENT" and r["correct"] == "N" for r in rs)
                    if form == "B" else "",
                    "turn2_cells": len(t2r), "turn2_correct": sum(r["turn2_correct"] == "Y" for r in t2r),
                    "correct_turn2_substituted": sum((r["turn2_correct"] or r["correct"]) == "Y" for r in rs),
                    "tagsens_changed": sum(1 for r in rs if r["tagsens_correct"] and r["tagsens_correct"] != r["correct"])
                    if tcodes else "",
                    "tagsens_gf_changed": sum(1 for r in vgr if r["tagsens_gf"] != r["gf"])
                    if tcodes and vgr else "",
                })

    # ---- rules per app
    rules, levels, levels_ts = [], {}, {}
    for app in APPS:
        va = [r for r in rows if r["app"] == app and r["form"] == "A" and r["vg"] == "yes"]
        vb = [r for r in rows if r["app"] == app and r["form"] == "B" and r["vg"] == "yes"]
        gf_a, gf_b = sum(r["gf"] == "Y" for r in va), sum(r["gf"] == "Y" for r in vb)
        clean_a = sum(r["clean"] == "Y" for r in va)
        lvl = app_level(gf_a, gf_b, clean_a)
        levels[app] = lvl
        hid_a = sum(1 for r in va if r["gf"] != "Y" and r["class_extracted"] in GF_CLASSES)
        hid_b = sum(1 for r in vb if r["gf"] != "Y" and r["class_extracted"] in GF_CLASSES)
        ts = {}
        if tcodes:
            ts = {"gf_form_a": sum(r["tagsens_gf"] == "Y" for r in va),
                  "gf_form_b": sum(r["tagsens_gf"] == "Y" for r in vb),
                  "clean_form_a": sum(r["tagsens_clean"] == "Y" for r in va)}
            ts["level"] = app_level(ts["gf_form_a"], ts["gf_form_b"], ts["clean_form_a"])
            levels_ts[app] = ts["level"]
        P, proxy = src[app], APP_PROXY[app]
        pgf_items = [q for q in VG_CHAT if P["gf"].get((proxy, q))]
        wrong_b = [r["silence_code"] for r in rows if r["app"] == app and r["form"] == "B" and r["correct"] == "N"]
        s_kind, s_text, m, n = silence_rule(wrong_b)
        rules.append({
            "app": app, "proxy": proxy, "comparator": comparator[app],
            "comparator_source": src_label[app],
            "chat_dates": date_range(chat_dates[app]),
            "b_arm_dates": date_range(rc1["dates"].get(proxy, set())),
            "window_3day": "PASS" if window3 else "FAIL",
            "window_pm7": ("not checked (proxy unusable, AM-7 A5)" if proxy in unusable else
                           "PASS" if window[app] else f"FAIL ({src_label[app]}, not concurrent)"),
            "k": K_VG, "gf_form_a": gf_a, "gf_form_b": gf_b, "clean_form_a": clean_a, "level": lvl,
            "a_of_k": f"{gf_a} of {K_VG}", "proxy_gf_items": ",".join(pgf_items),
            "statement": app_statement(app, lvl, gf_a, gf_b, clean_a, pgf_items, chat_dates[app]),
            "silence_wrong_n": n, "silence_flagged_or_asked": m, "silence_rule": s_kind,
            "silence_statement": s_text,
            "silence_overrides_am8_sec6": sum(1 for r in rows if r["app"] == app and r["silence_source"]
                                              and r["silence_source"] != "coded"),
            "turn2_deviations": sum(1 for k in t2_deviation if k[0] == app),
            "cell_major_breaches_all_apps": len(breach),
            "level_tagsens": ts.get("level", ""),
            "gf_form_a_tagsens": ts.get("gf_form_a", ""),
            "clean_form_a_tagsens": ts.get("clean_form_a", ""),
            "level_changed_tagsens": ("" if not ts else "Y" if ts["level"] != lvl else "N"),
            "diag_gf_hidden_by_parse_failure_a": hid_a,
            "diag_gf_hidden_by_parse_failure_b": hid_b,
            "diag_level_if_parse_failures_classified": app_level(gf_a + hid_a, gf_b + hid_b, clean_a),
        })
    glob = global_statements(levels)

    # ---- write
    os.makedirs(a.out)
    tag = "# TEST-ONLY: synthetic or test data, not a result\n" if a.test else ""

    def write_tsv(name, data):
        with open(os.path.join(a.out, name), "x", encoding="utf-8", newline="") as fh:
            fh.write(tag)
            w = csv.writer(fh, delimiter="\t", lineterminator="\n")
            w.writerow(list(data[0].keys()))
            for d in data:
                w.writerow(list(d.values()))
    write_tsv("chat_cells.tsv", rows)
    write_tsv("chat_summary.tsv", summ)
    write_tsv("chat_rules.tsv", rules)
    db_note = "" if a.vocab_db == "k3n" else " (OQ33.7 sensitivity on k3; artifact only)"
    lines = (["TEST-ONLY: synthetic or test data, not a result", ""] if a.test else []) + [
        "chat-app consistency check (AMENDMENT-8): mechanical report" + db_note,
        f"k = {K_VG} (VG10; Q48 counted within k); comparator = TH base arm (B) of the paired proxy, "
        f"majority of 5 runs; single shot per cell",
        f"chat dates (all apps): {date_range(all_dates)}; 3-day window: {'PASS' if window3 else 'FAIL'}",
        f"classifier vocabulary: {vocab_src}; database {a.vocab_db}; hints sha256 {hs}",
        f"DEFAULT switches: SILENCE_MOSTLY_SILENT_COUNT={SILENCE_MOSTLY_SILENT_COUNT}, "
        f"FALLBACK_WINDOW_FAIL={FALLBACK_WINDOW_FAIL}",
        "AMENDMENT-8 sec.6 (turn 1 without SQL is coded ASKED): "
        + (f"{len(overrides)} coded values overridden: " + ", ".join(overrides) if overrides else "no override"),
        "AMENDMENT-8 sec.6 deviation (turn 2 sent although turn 1 has SQL): "
        + (", ".join(f"{k[0]} {k[1]} {k[2]}" for k in sorted(t2_deviation)) if t2_deviation else "none"),
        "AMENDMENT-8 sec.5 deviation (cell started before the previous cell was done in all three apps): "
        + (f"{len(breach)} (after orders {', '.join(str(o) for o in breach)})" if breach else "none"), ""]
    for r in rules:
        lines += [f"[{r['app']}] proxy {r['proxy']} ({r['comparator']}; {r['comparator_source']}); "
                  f"chat {r['chat_dates']}; B arm {r['b_arm_dates']}",
                  f"  level: {r['level']} (GF Form A {r['gf_form_a']} of {K_VG}, Form B {r['gf_form_b']} of {K_VG}; "
                  f"clean Form A {r['clean_form_a']} of {K_VG}); proxy GF items: {r['proxy_gf_items'] or 'none'}",
                  f"  statement: {r['statement']}",
                  f"  silence (Form B): {r['silence_statement']}"]
    lines += [""] + ([f"overall: {x}" for x in glob] or
                     ["overall: at least one app reproduced the failure; the per-app statements apply"])
    lines += ["", "summary per app x form x subset (ALL / VG / NONVG): see chat_summary.tsv; "
              "per-cell table: chat_cells.tsv; turn 2 is a secondary result"]
    hidden = [f"{APP_LABEL[r['app']]} {r['diag_gf_hidden_by_parse_failure_a']} Form A + "
              f"{r['diag_gf_hidden_by_parse_failure_b']} Form B (level would be "
              f"{r['diag_level_if_parse_failures_classified']})" for r in rules
              if r["diag_gf_hidden_by_parse_failure_a"] or r["diag_gf_hidden_by_parse_failure_b"]]
    lines.append("diagnostic (not a rule): VG cells whose SQL failed to parse but would be GF on the extracted "
                 "text: " + ("; ".join(hidden) if hidden else "none"))
    if tcodes:
        ch = sum(1 for r in rows if r["form"] == "A" and r["tagsens_correct"] != r["correct"])
        chg = sum(1 for r in rows if r["vg"] == "yes" and r["tagsens_gf"] != r["gf"])
        chv = sum(1 for r in rows if r["vg"] == "yes" and r["tagsens_vg_code"] != r["vg_code"])
        lc = [f"{APP_LABEL[x]} {levels[x]} -> {levels_ts[x]}" for x in APPS if levels_ts[x] != levels[x]]
        lines.append(f"OQ33.1 Form A tag sensitivity: {ch} Form A cells change verdict, {chv} VG cells change "
                     f"B2.3 code, {chg} change GF; levels: " + ("; ".join(lc) if lc else "no level changes"))
    with open(os.path.join(a.out, "chat_report.txt"), "x", encoding="utf-8", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    meta = {"test_only": bool(a.test), "arm": a.arm, "k": K_VG, "vg_set": "VG10", "vocab_db": a.vocab_db,
            "comparator": comparator, "comparator_source": src_label, "unusable_models": sorted(unusable),
            "switches": switches(), "hints_sha256": hs, "levels": levels,
            "levels_tagsens": levels_ts or None,
            "silence_overrides_am8_sec6": overrides,
            "turn2_deviations": [" ".join(k) for k in sorted(t2_deviation)],
            "cell_major_breaches": {"count": len(breach), "after_orders": breach},
            "rc1_dropped_rows_by_arm": rc1["dropped"],
            "inputs": {os.path.basename(p): sha256_file(p) for p in
                       [a.graded, a.vg_codes, vmeta_path, a.silence, a.rc1_graded, suite_path, hints_path,
                        log_index, raw_manifest]
                       + rc1_results + ([a.graded_turn2] if a.graded_turn2 else [])
                       + ([a.graded_tagsens, results_tagsens] if a.graded_tagsens else [])
                       + ([a.fallback_graded] if fb else []) + (list(a.fallback_results) if fb else [])}}
    with open(os.path.join(a.out, "meta.json"), "x", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(meta, ensure_ascii=False, indent=1, sort_keys=True) + "\n")
    print("\n".join(lines))
    print(f"[out] {os.path.basename(os.path.abspath(a.out))}/ chat_cells.tsv chat_summary.tsv chat_rules.tsv "
          f"chat_report.txt meta.json")


if __name__ == "__main__":
    main()
