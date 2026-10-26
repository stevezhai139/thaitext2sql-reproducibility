#!/usr/bin/env python3
"""check_prompts_rc1.py — AMENDMENT-7 Gate 1a item 5 (offline; fake keys; no network).

Checks a runner dry-run file (prompts_rc1.jsonl or prompts_ext.jsonl) against the
run-of-record runner (git <--ror-commit>:harness/runner.py, read with `git show`,
read only) and against the RC1 runner next to this script:
  * meta: suite / models / runner / hint-file sha256 equal the given files;
  * counts: prompts = arms x 2 x items, calls = models x runs x arms x 2 x items,
    every prompt sha256 unique;
  * base prompts equal the run-of-record construction (SYSTEM.format(DDL) + question);
  * core suite (D11): base prompts and base request bodies equal the August run-of-record
    bytes, i.e. the 2f8db3d runner with the run-of-record suite (git <--ror-commit>:
    suite/k3_suite_v1.2.tsv, read with `git show`), for every item except the one declared
    exception D11_PROMPT_EXCEPTION (Q27, repaired for the October session): its base
    prompts carry the repaired question (sha256 of the text declared below, equal to the
    --suite text) and its base calls carry the body of that prompt, which differs from the
    August body. A plan built from the August suite (original Q27) therefore FAILs;
  * base request bodies equal the run-of-record call_model bodies for every
    model x language x item (payload_sha256 of every base call line), URL equal
    after the query string is cut (2f8db3d put the Gemini key in ?key=), header
    names differ only by x-goog-api-key for Gemini;
  * values prompts: system = base system + "\\n\\n" + block, same user text, block
    sha256 equal to the frozen hint file; V longer than B for every call pair;
  * every call: payload_sha256 recomputed with the RC1 runner, prompt reference,
    order equal to the registered plan, base/values of one item adjacent.
Safety: BEFORE any runner code is imported or executed, OPENAI_API_KEY,
ANTHROPIC_API_KEY and GOOGLE_API_KEY are overwritten with fixed fake values and
urllib.request.urlopen, http.client.HTTP(S)Connection.connect and
socket.create_connection are replaced by functions that raise. No URL or header
is printed or written; results.jsonl is not read. Output: PASS/FAIL counts only.

The plan must also match the registered design, not only its own meta: meta
draft = false and the suite is frozen (no DRAFT in the file name, build_status
FROZEN on every row); runs = --expect-runs (default 5); arms = --expect-arms
(default base,values for the core suite, base for the extension suite, which is
recognised by a build_status or family column). Counts are computed from these
expected values, so a --runs 4 plan or a base-only core plan FAILs.

Usage (RUNBOOK_v2 Gate 1a steps 57 and 64b; one command each, run from harness/; the core
dry-run is made from the October core suite k3n_suite_v1.3n_oct.tsv, D11):
  python3 -I -B "check_prompts_rc1.py" --prompts "../results/rc1/prompts_rc1.jsonl" --suite "../suite/k3n_suite_v1.3n_oct.tsv" --models "models.json" --hints "../suite/value_hints_v1.json" --ror-commit 2f8db3d
  python3 -I -B "check_prompts_rc1.py" --prompts "../results/ext/prompts_ext.jsonl" --suite "../suite/k3n_ext_suite_v1.0.tsv" --models "models.json" --ror-commit 2f8db3d
Exit: 0 all PASS, 1 any FAIL, 2 usage error.
"""
import sys

sys.dont_write_bytecode = True

import os  # noqa: E402

# ---- 1. fake keys and no network, before any runner code exists in this process
FAKE_KEYS = {"OPENAI_API_KEY": "sk-check-prompts-fake-openai-000000",
             "ANTHROPIC_API_KEY": "sk-ant-check-prompts-fake-000000",
             "GOOGLE_API_KEY": "AIza-check-prompts-fake-0000000000"}
for _k, _v in FAKE_KEYS.items():
    os.environ[_k] = _v

import http.client  # noqa: E402
import socket  # noqa: E402
import urllib.request  # noqa: E402

NET_ATTEMPTS = {"n": 0}


def _no_net(*a, **k):
    NET_ATTEMPTS["n"] += 1
    raise RuntimeError("network disabled in check_prompts_rc1")


urllib.request.urlopen = _no_net
http.client.HTTPConnection.connect = _no_net
http.client.HTTPSConnection.connect = _no_net
socket.create_connection = _no_net

import argparse  # noqa: E402
import collections  # noqa: E402
import csv  # noqa: E402
import hashlib  # noqa: E402
import importlib.util  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import subprocess  # noqa: E402
import types  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ("en", "th")
# run-of-record (August) core suite inside the run-of-record commit; the August prompts are
# rebuilt from it with the run-of-record runner (git show, read only)
ROR_SUITE_PATH = "suite/k3_suite_v1.2.tsv"
# D11 (author decision 14 Oct 2026, brief 1.0b): the ONE declared prompt-byte exception of the
# October core base arm. Q27 is repaired in place for the October session; its base prompts
# carry the repaired question, given here as the sha256 of the UTF-8 text per language
# (suite_tools/Q27_REPAIR_2026-10-14.tsv; October suite k3n_suite_v1.3n_oct.tsv). Every other
# base prompt and base request body must equal the August run-of-record bytes.
D11_PROMPT_EXCEPTION = {
    "Q27": {"en": "b4f5803d8258225195a86736c4a318ef75a98ab5be61366d7586dcdd5b69e71a",
            "th": "e68798bf23e2fb3b66460db895459c5efd78eb4df0d7ddcbe3d00c3c5964c830"},
}


def sha256_file(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def psha(system, user):
    return hashlib.sha256((system + "\x00" + user).encode("utf-8")).hexdigest()


def git_show(repo, spec):
    """read-only `git show <commit>:<path>`; --no-optional-locks and GIT_OPTIONAL_LOCKS=0 so that
    git never takes the index lock or refreshes the index of the repository it reads."""
    env = dict(os.environ, GIT_OPTIONAL_LOCKS="0")
    return subprocess.run(["git", "--no-optional-locks", "-C", repo, "show", spec],
                          capture_output=True, env=env)


def load_ror(repo, commit):
    r = git_show(repo, f"{commit}:harness/runner.py")
    if r.returncode != 0:
        print(f"usage: cannot read {commit}:harness/runner.py with git show (exit {r.returncode})")
        sys.exit(2)
    mod = types.ModuleType("runner_ror")
    mod.__file__ = f"<{commit}:harness/runner.py>"
    exec(compile(r.stdout.decode("utf-8"), mod.__file__, "exec"), mod.__dict__)
    return mod


def load_ror_suite(repo, commit):
    r = git_show(repo, f"{commit}:{ROR_SUITE_PATH}")
    if r.returncode != 0:
        print(f"usage: cannot read {commit}:{ROR_SUITE_PATH} with git show (exit {r.returncode})")
        sys.exit(2)
    rows = csv.DictReader(io.StringIO(r.stdout.decode("utf-8"), newline=""), delimiter="\t")
    return {x["id"]: x for x in rows}


def sha256_text(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def load_rc1(path):
    spec = importlib.util.spec_from_file_location("runner_rc1_checked", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def fake_response(url):
    if "openai" in url:
        return {"choices": [{"message": {"content": "SELECT 1"}}], "model": "m", "usage": {}}
    if "anthropic" in url:
        return {"content": [{"type": "text", "text": "SELECT 1"}], "model": "m", "usage": {}}
    if "googleapis" in url:
        return {"candidates": [{"content": {"parts": [{"text": "SELECT 1"}]}}], "modelVersion": "m"}
    return {"message": {"content": "SELECT 1"}, "model": "m"}


class Report:
    def __init__(self):
        self.fail = 0

    def item(self, name, ok, total, extra=""):
        status = "PASS" if (ok == total and total > 0) else "FAIL"
        if status == "FAIL":
            self.fail += 1
        print(f"{status}  {name}: {ok}/{total}{(' ' + extra) if extra else ''}")

    def flag(self, name, cond, extra=""):
        self.item(name, 1 if cond else 0, 1, extra)

    def na(self, name, why):
        print(f"N/A   {name}: {why}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompts", required=True)
    ap.add_argument("--suite", required=True)
    ap.add_argument("--models", required=True)
    ap.add_argument("--hints", help="frozen hint file (needed when the dry-run has the values arm)")
    ap.add_argument("--ror-commit", required=True, help="run-of-record commit, e.g. 2f8db3d")
    ap.add_argument("--runner", default=os.path.join(HERE, "runner.py"), help="RC1 runner (default: next to this script)")
    ap.add_argument("--repo", default=HERE, help="any folder inside the git repository (default: this folder)")
    ap.add_argument("--expect-runs", type=int, default=5, help="registered runs per cell (default 5)")
    ap.add_argument("--expect-arms", help="registered arms (default: base,values for the core suite, "
                                          "base for the extension suite)")
    a = ap.parse_args()
    if a.expect_runs < 1:
        print("usage: --expect-runs must be >= 1")
        sys.exit(2)

    rep = Report()
    ror = load_ror(a.repo, a.ror_commit)
    rc1 = load_rc1(a.runner)

    cap = []

    def ror_stub(url, payload, headers, timeout=120):
        cap.append((url.split("?", 1)[0], json.dumps(payload).encode(), tuple(sorted(headers))))
        return fake_response(url)

    ror.http_json = ror_stub

    def rc1_stub(*x, **k):
        raise RuntimeError("check_prompts_rc1 never sends with the RC1 runner")

    rc1.http_json = rc1_stub
    rc1.http_get_json = rc1_stub

    with open(a.suite, encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        cols = list(reader.fieldnames or [])
        suite = list(reader)
    models = json.load(open(a.models, encoding="utf-8"))
    lines = [json.loads(x) for x in open(a.prompts, encoding="utf-8") if x.strip()]
    metas = [d for d in lines if d.get("type") == "meta"]
    prompts = [d for d in lines if d.get("type") == "prompt"]
    calls = [d for d in lines if d.get("type") == "call"]
    if len(metas) != 1:
        print(f"FAIL  meta lines: {len(metas)}/1")
        sys.exit(1)
    meta = metas[0]
    is_ext = any(c in cols for c in rc1.EXT_MARKER_COLUMNS)
    req = [x.strip() for x in (a.expect_arms or ("base" if is_ext else "base,values")).split(",") if x.strip()]
    if not req or any(x not in rc1.ARMS for x in req) or len(set(req)) != len(req):
        print(f"usage: --expect-arms must be a comma list from {rc1.ARMS}")
        sys.exit(2)
    # จำนวนที่คาดคำนวณจากแบบที่ลงทะเบียน (ไม่ใช่จาก meta ของไฟล์ที่ถูกตรวจ)
    arms = [x for x in rc1.ARMS if x in req]
    runs = a.expect_runs
    n_items = len(suite)
    print(f"dry-run: draft={str(meta.get('draft')).lower()} arms={','.join(meta.get('arms') or [])} "
          f"runs={meta.get('runs')} items={n_items} models={len(models)} (TEST-ONLY counts unless run by the author)")
    print(f"expected ({'extension' if is_ext else 'core'} suite): draft=false arms={','.join(arms)} runs={runs} "
          f"prompts={len(arms) * len(LANGS) * n_items} calls={len(models) * runs * len(arms) * len(LANGS) * n_items}")

    # ---- registered design
    rep.flag("meta draft = false (plan made from a frozen suite)", meta.get("draft") is False)
    draft_reason = rc1.suite_draft_reason(a.suite, suite, cols)
    rep.flag("suite is frozen (no DRAFT in the file name; build_status FROZEN on every row)", draft_reason is None,
             f"({draft_reason})" if draft_reason else "")
    rep.flag(f"meta runs = expected {runs}", meta.get("runs") == runs)
    rep.flag(f"meta arms = expected {','.join(arms)}", list(meta.get("arms") or []) == arms)

    # ---- meta
    rep.flag("meta suite_sha256 = --suite", meta.get("suite_sha256") == sha256_file(a.suite))
    rep.flag("meta models_sha256 = --models", meta.get("models_sha256") == sha256_file(a.models))
    rep.flag("meta runner_sha256 = RC1 runner", meta.get("runner_sha256") == sha256_file(a.runner))
    hints_blocks = None
    if "values" in arms:
        if not a.hints:
            print("usage: the expected arms include values; give --hints (the frozen hint file)")
            sys.exit(2)
        hd = json.load(open(a.hints, encoding="utf-8"))
        hints_blocks = {k: hd["schemas"][k]["block"] for k in ("P", "E")}
        rep.flag("meta hints_sha256 = --hints", meta.get("hints_sha256") == sha256_file(a.hints))
        bsha = {k: hashlib.sha256(v.encode("utf-8")).hexdigest() for k, v in hints_blocks.items()}
        rep.item("block sha256 = frozen hint file (P, E)",
                 sum(1 for k in ("P", "E") if bsha[k] == (hd.get("block_sha256") or {}).get(k)
                     == (meta.get("block_sha256") or {}).get(k) == hd["schemas"][k].get("sha256")), 2)
    else:
        rep.flag("meta hints_sha256 is null (base arm only)", meta.get("hints_sha256") is None)

    # ---- counts
    exp_prompts = len(arms) * len(LANGS) * n_items
    exp_calls = len(models) * (runs or 0) * len(arms) * len(LANGS) * n_items
    rep.item("prompt lines", len(prompts), exp_prompts)
    rep.item("call lines", len(calls), exp_calls)
    rep.item("unique prompt_sha256", len({p.get("prompt_sha256") for p in prompts}), exp_prompts)
    per_model = collections.Counter(c.get("model_key") for c in calls)
    rep.item("models with the full call count", sum(1 for k in models if per_model.get(k) ==
                                                     (runs or 0) * len(arms) * len(LANGS) * n_items), len(models))

    P = {(p.get("arm"), p.get("lang"), p.get("qid")): p for p in prompts}
    rep.item("prompt text hashes to its prompt_sha256",
             sum(1 for p in prompts if psha(p.get("system", ""), p.get("user", "")) == p.get("prompt_sha256")),
             len(prompts))

    # ---- base prompts = run-of-record construction
    ok = 0
    ror_prompt = {}
    for q in suite:
        for lang in LANGS:
            ddl = ror.DDL_P if q["schema"] == "P" else ror.DDL_E
            system = ror.SYSTEM.format(ddl=ddl)
            user = q["question_en"] if lang == "en" else q["question_th"]
            ror_prompt[(lang, q["id"])] = (system, user)
            p = P.get(("base", lang, q["id"]))
            if p and p.get("system") == system and p.get("user") == user and p.get("prompt_sha256") == psha(system, user):
                ok += 1
    rep.item(f"base prompts = run-of-record {a.ror_commit} construction from --suite", ok, len(LANGS) * n_items)

    # ---- base bodies = run-of-record call_model bodies
    body_sha, url_ok, hdr_ok, nb = {}, 0, 0, 0
    for mkey, m in models.items():
        for (lang, qid), (system, user) in ror_prompt.items():
            cap.clear()
            ror.call_model(m, system, user)
            url_r, body_r, hdr_r = cap[0]
            body_sha[(mkey, lang, qid)] = hashlib.sha256(body_r).hexdigest()
            url_c, payload_c, hdr_c = rc1.build_payload(m, system, user, rc1.FAKE_KEYS)
            nb += 1
            if url_c.split("?", 1)[0] == url_r:
                url_ok += 1
            hc = tuple(sorted(hdr_c))
            if hc == hdr_r or (m["provider"] == "google" and set(hc) - set(hdr_r) == {"x-goog-api-key"}
                               and not set(hdr_r) - set(hc)):
                hdr_ok += 1
    ok = sum(1 for (mkey, lang, qid), s in body_sha.items()
             if s == rc1.payload_sha256(rc1.build_payload(models[mkey], *ror_prompt[(lang, qid)],
                                                          rc1.FAKE_KEYS)[1]))
    rep.item("base bodies RC1 runner = run-of-record (model x lang x item)", ok, nb)
    base_calls = [c for c in calls if c.get("arm") == "base"]
    ok = sum(1 for c in base_calls if body_sha.get((c.get("model_key"), c.get("lang"), c.get("qid")))
             == c.get("payload_sha256"))
    rep.item("base call lines: payload_sha256 = run-of-record body", ok, len(base_calls))
    rep.item("URL equal after cutting the query string", url_ok, nb)
    rep.item("header names equal (Gemini: + x-goog-api-key only)", hdr_ok, nb)

    # ---- D11: base prompts and bodies = August run-of-record bytes, except the declared exception
    if is_ext:
        rep.na("August run-of-record prompts (D11)", "extension suite: new items, no August prompt")
    else:
        aug = load_ror_suite(a.repo, a.ror_commit)
        exc = D11_PROMPT_EXCEPTION
        ids = [q["id"] for q in suite]
        print(f"D11 prompt-byte exception (declared once: D11_PROMPT_EXCEPTION): {', '.join(exc)} base calls; "
              f"August reference: {a.ror_commit}:{ROR_SUITE_PATH} ({len(aug)} items)")
        rep.flag("core --suite holds exactly the August run-of-record items",
                 sorted(ids) == sorted(aug) and len(ids) == len(aug),
                 f"({len(ids)} vs {len(aug)} items)")
        rep.flag("D11 exception items are items of --suite and of the August suite",
                 all(x in ids and x in aug for x in exc))
        ok = tot = eok = etot = 0
        aug_prompt = {}
        for q in suite:
            x = aug.get(q["id"])
            for lang in LANGS:
                p = P.get(("base", lang, q["id"]))
                if x is None:
                    tot += 1
                    continue
                system_a = ror.SYSTEM.format(ddl=ror.DDL_P if x["schema"] == "P" else ror.DDL_E)
                user_a = x["question_en"] if lang == "en" else x["question_th"]
                aug_prompt[(lang, q["id"])] = (system_a, user_a)
                if q["id"] in exc:
                    etot += 1
                    want = exc[q["id"]][lang]
                    user_s = q["question_en"] if lang == "en" else q["question_th"]
                    if p and p.get("system") == system_a and sha256_text(p.get("user")) == want \
                            and sha256_text(user_s) == want and p.get("user") != user_a:
                        eok += 1
                else:
                    tot += 1
                    if p and p.get("system") == system_a and p.get("user") == user_a:
                        ok += 1
        rep.item(f"base prompts = August run-of-record prompts ({a.ror_commit} runner + {ROR_SUITE_PATH}), "
                 "every item except the D11 exception", ok, tot)
        rep.item("D11 exception: base prompts carry the repaired question (declared sha256; differs from August)",
                 eok, etot)
        aug_body = {}
        for mkey, m in models.items():
            for key, (system_a, user_a) in aug_prompt.items():
                cap.clear()
                ror.call_model(m, system_a, user_a)
                aug_body[(mkey,) + key] = hashlib.sha256(cap[0][1]).hexdigest()
        keep = [c for c in base_calls if c.get("qid") not in exc]
        ok = sum(1 for c in keep if aug_body.get((c.get("model_key"), c.get("lang"), c.get("qid")))
                 == c.get("payload_sha256"))
        rep.item("base call lines = August run-of-record body (every item except the D11 exception)", ok, len(keep))
        exc_calls = [c for c in base_calls if c.get("qid") in exc]
        k = lambda c: (c.get("model_key"), c.get("lang"), c.get("qid"))  # noqa: E731
        ok = sum(1 for c in exc_calls if body_sha.get(k(c)) == c.get("payload_sha256")
                 and aug_body.get(k(c)) != c.get("payload_sha256"))
        rep.item("D11 exception calls: body of the repaired prompt (differs from the August body)", ok,
                 len(exc_calls))

    # ---- values prompts
    if hints_blocks is not None:
        ok = 0
        for q in suite:
            for lang in LANGS:
                b, v = P.get(("base", lang, q["id"])), P.get(("values", lang, q["id"]))
                if b and v and v.get("system") == b.get("system") + "\n\n" + hints_blocks[q["schema"]] \
                        and v.get("user") == b.get("user"):
                    ok += 1
        rep.item("values system = base system + \\n\\n + block, same user", ok, len(LANGS) * n_items)
        pairs = collections.defaultdict(dict)
        for c in calls:
            pairs[(c.get("model_key"), c.get("run"), c.get("lang"), c.get("qid"))][c.get("arm")] = c
        ok = 0
        for d in pairs.values():
            b = P.get(("base", d.get("base", {}).get("lang"), d.get("base", {}).get("qid")))
            v = P.get(("values", d.get("values", {}).get("lang"), d.get("values", {}).get("qid")))
            if b and v and len(v["system"]) + len(v["user"]) > len(b["system"]) + len(b["user"]):
                ok += 1
        rep.item("values prompt longer than base (call pairs)", ok, len(pairs))
    else:
        rep.na("values checks", "dry-run has the base arm only")

    # ---- every call: prompt reference, payload, order, adjacency
    ok_ref = ok_pay = 0
    for c in calls:
        p = P.get((c.get("arm"), c.get("lang"), c.get("qid")))
        if p and p.get("prompt_sha256") == c.get("prompt_sha256"):
            ok_ref += 1
            m = models.get(c.get("model_key"))
            if m is not None:
                payload = rc1.build_payload(m, p["system"], p["user"], rc1.FAKE_KEYS)[1]
                if rc1.payload_sha256(payload) == c.get("payload_sha256"):
                    ok_pay += 1
    rep.item("call lines reference a prompt line (arm, lang, qid, sha)", ok_ref, len(calls))
    rep.item("call lines: payload_sha256 recomputed with the RC1 runner", ok_pay, len(calls))
    planned = [(mkey, run, arm, lang, q["id"]) for run, mkey, m, lang, q, arm
               in rc1.plan(models, suite, arms, runs or 0)]
    got = [(c.get("model_key"), c.get("run"), c.get("arm"), c.get("lang"), c.get("qid")) for c in calls]
    rep.item("call order = registered plan (run, model, lang, item, alternating arms)",
             sum(1 for x, y in zip(planned, got) if x == y), len(planned))
    rep.flag("call seq = 1..N", [c.get("seq") for c in calls] == list(range(1, len(calls) + 1)))
    if len(arms) == 2:
        adj = sum(1 for x, y in zip(got[::2], got[1::2])
                  if x[0] == y[0] and x[1] == y[1] and x[3:] == y[3:] and {x[2], y[2]} == {"base", "values"})
        rep.item("base/values of one item adjacent", adj, len(got) // 2)

    # network: the guards installed at import raise on any connection; this line reports the count of blocked
    # attempts in words (not as a check fraction, so it cannot be read as "one network attempt")
    if NET_ATTEMPTS["n"] == 0:
        print("PASS  network: no connection attempted (every network call is blocked in this process)")
    else:
        rep.fail += 1
        print(f"FAIL  network: {NET_ATTEMPTS['n']} connection attempt(s) made and blocked (must be none)")
    print(f"RESULT: {'PASS' if rep.fail == 0 else 'FAIL'} ({rep.fail} check(s) failed)")
    sys.exit(0 if rep.fail == 0 else 1)


if __name__ == "__main__":
    main()
