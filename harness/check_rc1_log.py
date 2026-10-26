#!/usr/bin/env python3
"""check_rc1_log.py -- integrity gate for the October-session logs BEFORE grading
(AMENDMENT-7 A5.3 as revised; core: results_rc1_api/_local.jsonl; extension:
results_ext_api/_local.jsonl). Logs are never merged: --log repeats.

Checks 1-7 must PASS (exit 1 otherwise); check 8 only reports.
  1 record format: arm in --arms; every values record has hints_sha256 = --hints-sha256,
    every base record has hints_sha256 None; seq / run_id / t_epoch present
  2 the set of successful (model, arm, lang, qid, run) equals --suite ids (Q27 included)
    x --arms x {en, th} x runs 1..--runs x models of --models, with exactly one
    successful record each (a missing qid, run 6 or a duplicate fails); D11: a suite that
    holds the repaired items (analyze.D11_REPAIRED) must be the October core suite
    (analyze.suite_session 'october': Q27 repaired and primary), never the August suite
    (Q27 excluded, original question) or suite v1.2
  3 one model_echo per model, equal to the echo of the run-of-record (--lock-from)
  4 prompt_sha256 equals the frozen dry-run (--prompts, type 'prompt') per (arm, lang, qid)
    and payload_sha256 equals its 'call' line per (model, run, arm, lang, qid); the
    dry-run meta is not a draft and its suite_sha256 equals the --suite file
  5 local models (provider ollama): for every pair of successful records of one
    (model, lang, qid, run) with the same run_id and seq_values = seq_base + 1 (base
    asked first), tok_in(values) > tok_in(base) (no num_ctx truncation). Cells without
    such a pair are 'unchecked' (warning, not FAIL; OQ25.1) and listed as
    'truncation unverified'. Skipped when --arms has no values.
  6 the earliest ts over ALL records (errors included) is not before --not-before
    (format YYYY-MM-DDTHH:MM:SS, the runner ts; any other format -> exit 2)
  7 no API-key-shaped string (left-bounded patterns; exact live keys if exported) on
    any line; prints file names and line numbers only
  8 concurrent control (core; reported, never FAIL): for every (model, lang, qid, run)
    with a successful record in both arms, the pair is concurrent when run_id is the
    same, |seq_B - seq_V| = 1 and |t_epoch_B - t_epoch_V| <= --pair-max-seconds
    (registered 130 s). Non-concurrent pairs: count per model, and keys (no raw, no
    sql) written to --pairs-out for analyze_rc1.py --exclude-pairs. Skipped for a
    base-only log (extension).
The 'error' field is read as a boolean only (object_pairs_hook) and never printed.

Usage (Gate 3 step 21):
  python3 -I -B check_rc1_log.py --log ../results/rc1/results_rc1_api.jsonl \
    --log ../results/rc1/results_rc1_local.jsonl --local-log ../results/rc1/results_rc1_local.jsonl \
    --suite ../suite/k3n_suite_v1.3n_oct.tsv --models models.json --arms base,values --runs 5 \
    --hints-sha256 <sha256> --lock-from ../results/results.jsonl \
    --prompts ../results/rc1/prompts_rc1.jsonl --not-before 2026-10-20T09:00:00 \
    --pairs-out ../results/rc1/nonconcurrent_pairs.tsv
"""
import argparse
import csv
import hashlib
import json
import os
import re
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True
HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import analyze as ac  # noqa: E402  (D11: the one list of repaired items and suite_session)

KEY_PATTERNS = [re.compile(p) for p in (
    r"(?<![A-Za-z0-9_\-])AIza[0-9A-Za-z_\-]{30,}",            # Google
    r"(?<![A-Za-z0-9_\-])sk-ant-[0-9A-Za-z_\-]{20,}",          # Anthropic
    r"(?<![A-Za-z0-9_\-])sk-(?:proj-)?[0-9A-Za-z_\-]{20,}",    # OpenAI
    r"[?&]key=[^&\s'\"<]{10,}",                                # key in a URL query
)]
ENV_KEYS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")
NOT_BEFORE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
PAIR_MAX_SECONDS = 130.0
_KEEP = ("ts", "model_key", "model_echo", "arm", "lang", "qid", "run", "prompt_sha256",
         "payload_sha256", "suite_sha256", "hints_sha256", "hints_version", "run_id",
         "seq", "t_epoch", "tok_in", "parse_ok")
PAIR_COLS = ["model_key", "lang", "qid", "run", "run_id_base", "run_id_values",
             "seq_base", "seq_values", "dt_seconds"]


def _hook(pairs):
    d = {}
    for k, v in pairs:
        if k == "error":
            d["error"] = v is not None
        elif k in _KEEP or k == "type":
            d[k] = v
    return d


def _int(x):
    try:
        return int(x)
    except (TypeError, ValueError):
        return None


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def read_log(path, fails):
    recs = []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                r = json.loads(line, object_pairs_hook=_hook)
            except json.JSONDecodeError:
                fails.append(f"1 {os.path.basename(path)} line {n} is not JSON (incomplete write?)")
                continue
            r["_file"] = os.path.basename(path)
            r["_line"] = n
            recs.append(r)
    return recs


def secret_scan(paths):
    hits = defaultdict(list)
    live = [os.environ[v] for v in ENV_KEYS if os.environ.get(v)]
    for p in paths:
        with open(p, encoding="utf-8", errors="replace") as fh:
            for n, line in enumerate(fh, 1):
                if any(pt.search(line) for pt in KEY_PATTERNS) or any(k in line for k in live):
                    hits[os.path.basename(p)].append(n)
    return hits


def main():
    ap = argparse.ArgumentParser(description="integrity checks of an October-session log")
    ap.add_argument("--log", required=True, action="append")
    ap.add_argument("--local-log", action="append", default=[],
                    help="log(s) that must hold local (ollama) models only")
    ap.add_argument("--suite", required=True)
    ap.add_argument("--models", required=True)
    ap.add_argument("--arms", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--hints-sha256")
    ap.add_argument("--lock-from", required=True)
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--not-before", required=True)
    ap.add_argument("--pairs-out")
    ap.add_argument("--pair-max-seconds", type=float, default=PAIR_MAX_SECONDS)
    ap.add_argument("--exclude-models", default="",
                    help="models left out of checks 2-5 and 8 (AM-7 A5.6; printed); "
                         "their lines are still scanned by check 7")
    a = ap.parse_args()
    if not NOT_BEFORE_RE.match(a.not_before):
        print(f"--not-before must look like 2026-10-20T09:00:00 (runner ts, no zone)")
        sys.exit(2)
    arms = [x.strip() for x in a.arms.split(",") if x.strip()]
    if not arms or any(x not in ("base", "values") for x in arms):
        print("--arms must be base or base,values")
        sys.exit(2)
    if "values" in arms and not a.hints_sha256:
        print("--arms with values needs --hints-sha256")
        sys.exit(2)
    excluded = {x.strip() for x in a.exclude_models.split(",") if x.strip()}
    fails, warns = [], []

    logs = list(dict.fromkeys(list(a.log) + list(a.local_log)))
    # 7 secret scan on the raw text first (line numbers only)
    hits = secret_scan(logs)
    if hits:
        fails.append("7 key-shaped strings on lines " + "; ".join(
            f"{f}: {v[:10]}" + (" ..." if len(v) > 10 else "") for f, v in hits.items()) +
            " -- do not share these files")

    models_cfg = json.load(open(a.models, encoding="utf-8"))
    local_models = {m for m, c in models_cfg.items() if c.get("provider") == "ollama"}
    expected_models = [m for m in models_cfg if m not in excluded]
    with open(a.suite, encoding="utf-8", newline="") as fh:
        suite_rows = list(csv.DictReader(fh, delimiter="\t"))
    suite_ids = [r["id"] for r in suite_rows]
    if len(set(suite_ids)) != len(suite_ids):
        fails.append("2 the suite has duplicate ids")
    session = ac.suite_session({r["id"]: r for r in suite_rows}, os.path.basename(a.suite))
    if session not in (ac.SESSION_OCT, ac.SESSION_NONE):
        fails.append(f"2 D11: --suite {os.path.basename(a.suite)} is of session {session!r}; an "
                     f"October log is checked against the October core suite (repaired items "
                     f"{list(ac.D11_REPAIRED)} primary)")
    elif session == ac.SESSION_OCT:
        print(f"check 2: D11 October core suite ({', '.join(ac.D11_REPAIRED)} repaired, primary)")

    recs = []
    for p in logs:
        recs += read_log(p, fails)
    for p in a.local_log:
        bad = sorted({r.get("model_key") for r in recs
                      if r["_file"] == os.path.basename(p) and r.get("model_key") not in local_models})
        if bad:
            fails.append(f"5 {os.path.basename(p)} holds non-local models {bad}")
    all_recs = recs
    recs = [r for r in recs if r.get("model_key") not in excluded]
    ok = [r for r in recs if not r.get("error")]

    # 1 record format
    bad_arm = [r for r in recs if r.get("arm") not in arms]
    bad_hint_v = [r for r in recs if r.get("arm") == "values" and r.get("hints_sha256") != a.hints_sha256]
    bad_hint_b = [r for r in recs if r.get("arm") == "base" and r.get("hints_sha256") is not None]
    no_order = [r for r in recs if not isinstance(r.get("seq"), int) or not r.get("run_id")
                or not isinstance(r.get("t_epoch"), (int, float))]
    if bad_arm or bad_hint_v or bad_hint_b or no_order:
        fails.append(f"1 arm outside {arms}: {len(bad_arm)}; values with another hints_sha256: "
                     f"{len(bad_hint_v)}; base with hints_sha256: {len(bad_hint_b)}; records "
                     f"without seq/run_id/t_epoch: {len(no_order)}")
    seq_dup = Counter((r["_file"], r.get("seq")) for r in all_recs if isinstance(r.get("seq"), int))
    dups = [k for k, v in seq_dup.items() if v > 1]
    if dups:
        fails.append(f"1 seq repeated inside a file: {len(dups)} values (one writer per file)")

    # 2 completeness (set equality)
    expected = {(m, arm, lg, q, run) for m in expected_models for arm in arms
                for lg in ("en", "th") for q in suite_ids for run in range(1, a.runs + 1)}
    got = Counter()
    for r in ok:
        try:
            run = int(r.get("run"))
        except (TypeError, ValueError):
            run = r.get("run")
        got[(r.get("model_key"), r.get("arm"), r.get("lang"), r.get("qid"), run)] += 1
    extra = [k for k in got if k not in expected]
    missing = [k for k in expected if k not in got]
    dup = [k for k, v in got.items() if v > 1]
    if extra or missing or dup:
        fails.append(f"2 successful records: missing {len(missing)} (first {sorted(missing)[:3]}), "
                     f"unexpected {len(extra)} (first {sorted(extra, key=str)[:3]}), duplicated "
                     f"{len(dup)}; expected {len(expected)} = {len(expected_models)} models x "
                     f"{len(arms)} arms x 2 langs x {len(suite_ids)} items x {a.runs} runs")

    # 3 echo lock
    ror = {}
    with open(a.lock_from, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line, object_pairs_hook=_hook)
            if not r.get("error") and r.get("model_echo") and r.get("model_key") not in ror:
                ror[r["model_key"]] = r["model_echo"]
    echo = defaultdict(set)
    for r in ok:
        echo[r.get("model_key")].add(r.get("model_echo"))
    for m in sorted(echo, key=str):
        e = echo[m]
        if len(e) != 1 or ror.get(m) not in e:
            fails.append(f"3 echo of {m}: {sorted(map(str, e))} vs run-of-record {ror.get(m)}")

    # 4 prompt and payload hashes against the dry-run
    meta, frozen_p, frozen_c = None, {}, {}
    with open(a.prompts, encoding="utf-8") as fh:
        for line in fh:
            if not line.strip():
                continue
            r = json.loads(line)
            t = r.get("type")
            if t == "meta":
                meta = r
            elif t == "prompt":
                frozen_p[(r["arm"], r["lang"], r["qid"])] = r["prompt_sha256"]
            elif t == "call":
                frozen_c[(r["model_key"], int(r["run"]), r["arm"], r["lang"], r["qid"])] = \
                    r["payload_sha256"]
    suite_sha = sha256_file(a.suite)
    if meta is None:
        fails.append("4 the dry-run file has no meta line")
    else:
        if meta.get("draft"):
            fails.append("4 the dry-run meta says draft: a live log must use a FROZEN suite")
        if meta.get("suite_sha256") != suite_sha:
            fails.append("4 suite_sha256 of the dry-run meta differs from --suite")
        if "values" in arms and meta.get("hints_sha256") not in (None, a.hints_sha256):
            fails.append("4 hints_sha256 of the dry-run meta differs from --hints-sha256")
    bad_p = [r for r in ok if frozen_p.get((r.get("arm"), r.get("lang"), r.get("qid")))
             != r.get("prompt_sha256")]
    bad_c = [r for r in ok if r.get("payload_sha256") is not None and frozen_c.get(
        (r.get("model_key"), _int(r.get("run")), r.get("arm"), r.get("lang"), r.get("qid")))
        != r.get("payload_sha256")]
    no_c = [r for r in ok if r.get("payload_sha256") is None]
    bad_s = [r for r in ok if r.get("suite_sha256") != suite_sha]
    if bad_p or bad_c or no_c or bad_s:
        fails.append(f"4 prompt hash differs: {len(bad_p)}; payload hash differs: {len(bad_c)}; "
                     f"payload hash missing: {len(no_c)}; suite_sha256 differs: {len(bad_s)}")

    # index successful records by cell for checks 5 and 8
    by = {}
    for r in ok:
        try:
            k = (r["model_key"], r["arm"], r["lang"], r["qid"], int(r["run"]))
        except (KeyError, TypeError, ValueError):
            continue
        by.setdefault(k, r)
    pair_keys = sorted({(m, lg, q, run) for (m, arm, lg, q, run) in by
                        if (m, "base", lg, q, run) in by and (m, "values", lg, q, run) in by})

    def adjacent_b_first(b, v):
        return (b.get("run_id") == v.get("run_id") and isinstance(b.get("seq"), int)
                and isinstance(v.get("seq"), int) and v["seq"] == b["seq"] + 1)

    # 5 truncation (local models; base asked first in the same process, adjacent seq)
    unchecked = []
    if "values" in arms:
        n_checked, trunc = 0, []
        for (m, lg, q, run) in pair_keys:
            if m not in local_models:
                continue
            b, v = by[(m, "base", lg, q, run)], by[(m, "values", lg, q, run)]
            if adjacent_b_first(b, v) and b.get("tok_in") is not None and v.get("tok_in") is not None:
                n_checked += 1
                if not v["tok_in"] > b["tok_in"]:
                    trunc.append((m, lg, q, run))
        cells_checked = {(m, lg, q) for (m, lg, q, run) in pair_keys if m in local_models
                         and adjacent_b_first(by[(m, "base", lg, q, run)], by[(m, "values", lg, q, run)])}
        cells_all = {(m, lg, q) for (m, lg, q, run) in pair_keys if m in local_models}
        unchecked = sorted(cells_all - cells_checked)
        if trunc:
            fails.append(f"5 tok_in(values) <= tok_in(base) in {len(trunc)} adjacent B->V pairs of "
                         f"local models (truncation?); first {trunc[:3]}")
        print(f"check 5: local B->V adjacent pairs checked {n_checked}; local cells checked "
              f"{len(cells_checked)}/{len(cells_all)}")
        if unchecked:
            warns.append(f"5 unchecked local cells (no adjacent B->V pair; 'truncation "
                         f"unverified'): {len(unchecked)}; first {unchecked[:5]}")
    else:
        print("check 5: skipped (no values arm)")

    # 6 not before the Gate 1b commit (all records, errors included)
    ts = [r.get("ts") for r in all_recs if isinstance(r.get("ts"), str)]
    if not ts:
        fails.append("6 no record carries a ts")
    elif min(ts) < a.not_before:
        fails.append(f"6 earliest record {min(ts)} precedes --not-before {a.not_before}")

    # 8 concurrent control (report only)
    nonconc = []
    if "values" in arms:
        for (m, lg, q, run) in pair_keys:
            b, v = by[(m, "base", lg, q, run)], by[(m, "values", lg, q, run)]
            same_proc = b.get("run_id") == v.get("run_id")
            adj = isinstance(b.get("seq"), int) and isinstance(v.get("seq"), int) and \
                abs(b["seq"] - v["seq"]) == 1
            dt = (abs(float(b["t_epoch"]) - float(v["t_epoch"]))
                  if isinstance(b.get("t_epoch"), (int, float)) and isinstance(v.get("t_epoch"), (int, float))
                  else None)
            if not (same_proc and adj and dt is not None and dt <= a.pair_max_seconds):
                nonconc.append({"model_key": m, "lang": lg, "qid": q, "run": run,
                                "run_id_base": b.get("run_id"), "run_id_values": v.get("run_id"),
                                "seq_base": b.get("seq"), "seq_values": v.get("seq"),
                                "dt_seconds": "" if dt is None else f"{dt:.3f}"})
        per = Counter(x["model_key"] for x in nonconc)
        print(f"check 8 (report only): pairs {len(pair_keys)}; non-concurrent "
              f"{len(nonconc)} (> {a.pair_max_seconds:g} s, other process, or not adjacent): "
              + (", ".join(f"{m} {n}" for m, n in sorted(per.items())) or "none"))
        if a.pairs_out:
            os.makedirs(os.path.dirname(os.path.abspath(a.pairs_out)) or ".", exist_ok=True)
            with open(a.pairs_out, "w", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=PAIR_COLS, delimiter="\t")
                w.writeheader()
                w.writerows(nonconc)
            print(f"check 8: keys of non-concurrent pairs -> {a.pairs_out}")
    else:
        print("check 8: skipped (base-only log)")

    print(f"records {len(all_recs)} | successful {len(ok)} | models "
          f"{sorted({str(r.get('model_key')) for r in ok})}" +
          (f" | excluded {sorted(excluded)}" if excluded else ""))
    for wmsg in warns:
        print("WARN:", wmsg)
    if fails:
        print("FAIL:\n  " + "\n  ".join(fails))
        sys.exit(1)
    print("PASS: checks 1-7")


if __name__ == "__main__":
    main()
