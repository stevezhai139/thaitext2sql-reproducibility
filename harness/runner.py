"""
runner.py — K3 experiment runner (run-of-record + RC1 October session).

Original behaviour (frozen prereg 6 Aug 2026, kept): for each model x language x
question x run(1..5) ask the model for a single PostgreSQL query and log
EVERYTHING to an append-only, resumable JSONL file. Model identifiers are echoed
from the provider response and locked (any later mismatch aborts — no silent
model swaps).

Providers: openai | anthropic | google | ollama   (config in models.json)
Env keys : OPENAI_API_KEY / ANTHROPIC_API_KEY / GOOGLE_API_KEY (live mode only;
           read only for the providers that this invocation will call)

RC1 (October session; prereg AMENDMENT-7, database k3n, answer key v1.3n)
-----------------------------------------------------------------------
  arm 'base'   = DDL-only prompt, byte-identical to the August run-of-record
  arm 'values' = base system prompt + "\n\n" + frozen per-schema value block
                 (suite/value_hints_v1.json, built from k3n by make_value_hints.py)
  Core suite  : suite/k3n_suite_v1.3n_oct.tsv (the October core suite, D11: Q27
                repaired and primary; the August suite k3n_suite_v1.3n.tsv is the
                answer key of the Gate 2 re-grade only), --arms base,values, --runs 5
                (2 arms x 2 languages x 60 items x 5 runs = 1,200 records/model;
                the two arms of one item are asked back to back, the arm order
                alternates with the parity of (item index + run))
  Extension   : suite/k3n_ext_suite_v1.0.tsv, --arms base (40 items, 400/model)
  Output      : results/rc1/results_rc1_api.jsonl and results_rc1_local.jsonl
                (core), results/ext/results_ext_api.jsonl and _local.jsonl (ext)

Usage: the commands of record are the RUNBOOK_v2 steps (dry run: Gate 1a step 56,
extension 64; live: Gate 3 steps 6-11 and 14-19). Each example below is one
command, run from harness/, with every path in double quotes.

Dry run (no model call, no network; never reads the key variables OPENAI_API_KEY /
ANTHROPIC_API_KEY / GOOGLE_API_KEY, so secrets.env need not be sourced); it writes
one file: 1 meta line, 1 prompt line per (arm, lang, qid) with the full text, 1 call
line per planned call (prompt_sha256 + payload_sha256):
  python3 -I -B "runner.py" --suite "../suite/k3n_suite_v1.3n_oct.tsv" --models "models.json" --out "../results/rc1/prompts_rc1.jsonl" --runs 5 --arms base,values --hints "../suite/value_hints_v1.json" --hints-sha256 "<sha256 of value_hints_v1.json>" --dry-run

Live run (one model per command; the run-of-record log is read only):
  python3 -I -B "runner.py" --suite "../suite/k3n_suite_v1.3n_oct.tsv" --models "models.json" --out "../results/rc1/results_rc1_api.jsonl" --runs 5 --arms base,values --hints "../suite/value_hints_v1.json" --hints-sha256 "<sha256 of value_hints_v1.json>" --lock-from "../results/results.jsonl" --prompts "../results/rc1/prompts_rc1.jsonl" --only gpt-mini
A local model adds --ollama-digests "../results/rc1/provenance_gate1a.json".

Guards (live): --lock-from required; values arm needs --hints-sha256 and matching
block sha256; --prompts must match the whole planned schedule before the first
call; a DRAFT suite (DRAFT in the file name, or a build_status column with any
value other than FROZEN) or a draft dry-run is refused; one writer process per
--out (flock); the append is refused when the existing --out has another
suite_sha256, another hints file or another arm set. When --out lies under a
folder named results (any letter case) a live run also needs --prompts, an echo
for every selected model in --lock-from, and --ollama-digests for local models.
Exit codes: 1 unexpected error (exception name and redacted message only),
2 usage/guard, 3 circuit breaker (consecutive errors; a provider body that reads
as credit or billing exhaustion adds the fixed label "(credit/quota)" after the
error type), 4 writer lock held by another process, 5 Ollama digest lock,
6 MODEL SWAP (echo differs from the lock).
"""
import argparse
import csv
import datetime
import fcntl
import hashlib
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
import uuid

DDL_P = """CREATE TABLE President(PresidentName TEXT, YearBorn INT, StateBorn TEXT, PartyName TEXT);
CREATE TABLE Party(PartyName TEXT);
CREATE TABLE PresidentMarriage(PresidentName TEXT, SpouseName TEXT, SpouseBirthDay DATE, MarriageYear INT, MarriageStatus TEXT);
CREATE TABLE PresidentHolding(PresidentName TEXT, YearHolding INT, YearEnd INT, VicePresidentName TEXT, RunnerUp TEXT);"""

DDL_E = """CREATE TABLE Ecommerce(OrderID TEXT, CustomerID TEXT, OrderDate DATE, ProductSKU TEXT, ProductName TEXT, Category TEXT, Brand TEXT, BasePrice NUMERIC, DiscountPercent NUMERIC, FinalPrice NUMERIC, Quantity INT, Revenue NUMERIC, Currency TEXT, CustomerAge INT, CustomerGender TEXT, CustomerCity TEXT, CustomerCountry TEXT, Region TEXT, MembershipTier TEXT, MarketingChannel TEXT, WebsiteVisits INT, TimeOnSite NUMERIC, CartAbandonment TEXT, ProductRating NUMERIC, CustomerSatisfaction NUMERIC, ShippingCost NUMERIC, DeliveryDays INT, ReturnStatus TEXT, RepeatCustomer TEXT, PurchaseFrequency INT, IsHighValue TEXT, SeasonalFactor NUMERIC, InventoryLevel INT, ConversionRate NUMERIC, CustomerLTV NUMERIC, AcquisitionCost NUMERIC, IsWeekendOrder TEXT, PaymentMethod TEXT);"""

SYSTEM = ("You are a SQL assistant. Given the schema below, answer the user's "
          "question with a single PostgreSQL query only. Output only the SQL, "
          "no explanation, no markdown.\n\nSchema:\n{ddl}")

# ---------------------------------------------------------------------------
# constants of the October session (registered defaults; change only by amendment)
# ---------------------------------------------------------------------------
ARMS = ("base", "values")                 # canonical arm order
LANGS = ("en", "th")
SCHEMAS = ("P", "E")
REQUIRED_COLUMNS = ("id", "tier", "schema", "question_en", "question_th")
EXT_MARKER_COLUMNS = ("build_status", "family")   # extension suite = base arm only
DEFAULT_MAX_CONSECUTIVE_ERRORS = 5        # OQ15.1 default (AM-7 A5)
EXPECTED_HINTS_SOURCE_DB = "k3n"          # brief 1.1: hints are built from k3n
OLLAMA_BASE = "http://localhost:11434"    # same host as the generate URL below
ERROR_BODY_MAX = 250                      # chars of the redacted HTTP error body
# breaker summary: provider bodies that read as credit/billing exhaustion get one fixed label
# (the provider message itself is never printed). Anthropic sends credit exhaustion as a plain
# 400 invalid_request_error, so without the label it looks like a rejected payload.
QUOTA_LABEL = "(credit/quota)"
QUOTA_HINT_RE = re.compile(r"credit balance|purchase credits|insufficient_quota|exceeded your current quota|billing",
                           re.I)
FROZEN_STATUS = "FROZEN"                  # design 3.2/3.3: build_status in {FROZEN, DRAFT}
OFFICIAL_DIR = "results"                  # an --out under this folder name (any case) is official
EXIT_UNEXPECTED = 1                       # any exception not handled below (never a model swap)
EXIT_SWAP = 6                             # MODEL SWAP gets its own code (AM-7 A5.2: stop both terminals)
ICT = datetime.timezone(datetime.timedelta(hours=7))

_SECRET_VARS = ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GOOGLE_API_KEY")
_PROVIDER_KEY = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY",
                 "google": "GOOGLE_API_KEY"}
# dry-run และการคำนวณ payload_sha256 ใช้ key ปลอมคงที่ (payload ไม่มี key; key อยู่ใน header)
FAKE_KEYS = {"OPENAI_API_KEY": "dry-run-no-key-openai",
             "ANTHROPIC_API_KEY": "dry-run-no-key-anthropic",
             "GOOGLE_API_KEY": "dry-run-no-key-google"}

# ค่า key จริงที่ live mode อ่านมา (เฉพาะผู้ให้บริการที่จะเรียก) — ใช้ใน redact เท่านั้น
_ACTIVE_SECRETS = []

_KEY_PATTERNS = (
    # key ที่ผู้ให้บริการปิดบางส่วนแล้ว เช่น 'sk-proj-****wxyz' หรือ 'sk-abc12****wxyz' ในข้อความ 401
    # ของ OpenAI — ต้องมาก่อน pattern 'sk-' ปกติ เพื่อให้ตัดทั้ง token (รวมตัวท้ายหลัง *)
    (re.compile(r"(?<![A-Za-z0-9])(?:sk-|AIza)[0-9A-Za-z_\-]*(?:\*+|\.{3,}|\u2026)[0-9A-Za-z_\-*]*"),
     "<REDACTED>"),
    (re.compile(r"(key=)[^&\s'\"]+"), r"\1<REDACTED>"),
    (re.compile(r"(?<![A-Za-z0-9])AIza[0-9A-Za-z_\-]{6,}"), "<REDACTED>"),
    (re.compile(r"(?<![A-Za-z0-9])sk-ant-[0-9A-Za-z_\-]{4,}"), "<REDACTED>"),
    (re.compile(r"(?<![A-Za-z0-9])sk-[0-9A-Za-z_\-]{6,}"), "<REDACTED>"),
    (re.compile(r"(Bearer\s+)[^\s'\",]+"), r"\1<REDACTED>"),
    (re.compile(r"((?:x-api-key|x-goog-api-key)['\"]?\s*[:=]\s*['\"]?)[^\s'\",}]+", re.I),
     r"\1<REDACTED>"),
)


def redact(text):
    """ตัด secret ออกจากข้อความก่อนเขียน log หรือพิมพ์ (กัน key รั่วแบบ results.jsonl 12 ส.ค. 69).
    ค่า key จริงมาจาก _ACTIVE_SECRETS (live mode) แล้วตามด้วย pattern ของรูปแบบ key;
    ไม่อ่าน os.environ ที่นี่ (dry-run จึงไม่อ่านตัวแปร key ใดเลย)"""
    if not text:
        return text
    text = str(text)
    for val in _ACTIVE_SECRETS:
        if val:
            text = text.replace(val, "<REDACTED>")
    for pat, rep in _KEY_PATTERNS:
        text = pat.sub(rep, text)
    return text


def say(msg):
    print(redact(msg), flush=True)


def die(code, msg):
    print(redact(msg), file=sys.stderr, flush=True)
    raise SystemExit(code)


# ---------------------------------------------------------------------------
# transport (tests replace http_json / http_get_json; nothing else opens sockets)
# ---------------------------------------------------------------------------
def http_json(url, payload, headers, timeout=120):
    req = urllib.request.Request(url, json.dumps(payload).encode(),
                                 {"Content-Type": "application/json", **headers})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def http_get_json(url, timeout=30):
    with urllib.request.urlopen(urllib.request.Request(url), timeout=timeout) as r:
        return json.loads(r.read())


# ---------------------------------------------------------------------------
# payload (dicts byte-identical to c698547 / 2f8db3d; only the Gemini key moved
# from the URL query to the x-goog-api-key header in c698547)
# ---------------------------------------------------------------------------
def build_payload(m, system, user, keys):
    """-> (url, payload, headers). keys = {ENV_NAME: value}; dry-run passes FAKE_KEYS."""
    p = m["provider"]
    if p == "openai":
        return ("https://api.openai.com/v1/chat/completions",
                {"model": m["model"], "temperature": 0,
                 "messages": [{"role": "system", "content": system},
                              {"role": "user", "content": user}]},
                {"Authorization": f"Bearer {keys['OPENAI_API_KEY']}"})
    if p == "anthropic":
        # หมายเหตุ prereg: claude-sonnet-5 ปฏิเสธ temperature (deprecated) —
        # จึงรันที่ค่า default ของผู้ให้บริการ; ผล 5 รอบใช้วัด stability ตามจริง
        return ("https://api.anthropic.com/v1/messages",
                {"model": m["model"], "max_tokens": 1024,
                 "system": system,
                 "messages": [{"role": "user", "content": user}]},
                {"x-api-key": keys["ANTHROPIC_API_KEY"],
                 "anthropic-version": "2023-06-01"})
    if p == "google":
        # key ส่งทาง header ไม่ใส่ใน URL — URL ติดไปกับข้อความ error ได้ (8 ต.ค. 69)
        # ไม่มี thinkingConfig (thinking ค่า default เหมือน ส.ค.)
        return (f"https://generativelanguage.googleapis.com/v1beta/models/{m['model']}:generateContent",
                {"systemInstruction": {"parts": [{"text": system}]},
                 "contents": [{"parts": [{"text": user}]}],
                 "generationConfig": {"temperature": 0}},
                {"x-goog-api-key": keys["GOOGLE_API_KEY"]})
    if p == "ollama":
        return (OLLAMA_BASE + "/api/chat",
                {"model": m["model"], "stream": False,
                 "options": {"temperature": 0, "seed": 42},
                 "messages": [{"role": "system", "content": system},
                              {"role": "user", "content": user}]}, {})
    raise ValueError(f"unknown provider {p}")


def payload_sha256(payload):
    """sha256 ของ body ที่ส่งจริง (json.dumps(payload).encode(); ไม่รวม URL และ header)"""
    return hashlib.sha256(json.dumps(payload).encode()).hexdigest()


def prompt_sha256(system, user):
    return hashlib.sha256((system + "\x00" + user).encode("utf-8")).hexdigest()


def _echo(r, field, m):
    v = r.get(field)
    return (v, "response") if v else (m["model"], "fallback")


def call_model(m, system, user, keys):
    """-> (text, echo, echo_source, usage{in,out,think})"""
    url, payload, headers = build_payload(m, system, user, keys)
    r = http_json(url, payload, headers)
    p = m["provider"]
    if p == "openai":
        u = r.get("usage") or {}
        echo, src = _echo(r, "model", m)
        return (r["choices"][0]["message"]["content"], echo, src,
                {"in": u.get("prompt_tokens"), "out": u.get("completion_tokens"), "think": None})
    if p == "anthropic":
        # content อาจมี block อื่นนำหน้า (เช่น thinking) — เอาเฉพาะ text blocks
        txt = "\n".join(b.get("text", "") for b in r["content"]
                        if b.get("type") == "text")
        if not txt:
            raise ValueError(f"no text block in response: {[b.get('type') for b in r['content']]}")
        u = r.get("usage") or {}
        echo, src = _echo(r, "model", m)
        return txt, echo, src, {"in": u.get("input_tokens"), "out": u.get("output_tokens"),
                                "think": None}
    if p == "google":
        u = r.get("usageMetadata") or {}
        echo, src = _echo(r, "modelVersion", m)
        # tok_out = candidatesTokenCount; tok_think = thoughtsTokenCount (คิดเงินเป็น output)
        return (r["candidates"][0]["content"]["parts"][0]["text"], echo, src,
                {"in": u.get("promptTokenCount"), "out": u.get("candidatesTokenCount"),
                 "think": u.get("thoughtsTokenCount")})
    if p == "ollama":
        echo, src = _echo(r, "model", m)
        # prompt_eval_count ใช้ตรวจว่า prompt ไม่ถูกตัดหัวเพราะเกิน num_ctx (check 5)
        return r["message"]["content"], echo, src, {
            "in": r.get("prompt_eval_count"), "out": r.get("eval_count"), "think": None}
    raise ValueError(f"unknown provider {p}")


def extract_sql(text):
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        # take first fenced block, strip optional 'sql' tag
        block = parts[1] if len(parts) > 1 else t
        t = block.split("\n", 1)[1] if block.lower().startswith("sql") else block
    t = t.strip().rstrip(";").strip()
    ok = t.lower().lstrip().startswith(("select", "with"))
    single = ";" not in t
    return t, (ok and single)


def build_prompt(q, lang, arm, hints):
    ddl = DDL_P if q["schema"] == "P" else DDL_E
    system = SYSTEM.format(ddl=ddl)          # arm 'base' = run-of-record bytes
    if arm == "values":
        system = system + "\n\n" + hints[q["schema"]]
    user = q["question_en"] if lang == "en" else q["question_th"]
    return system, user


def plan(models, suite, arms, runs):
    """ลำดับการเรียกที่ลงทะเบียน (AM-7 A4): run -> model -> lang -> ข้อ -> arm;
    สองแขนของข้อเดียวกันติดกัน ลำดับแขนสลับตาม parity ของ (index ของข้อ + run);
    --arms base ให้ลำดับเท่ากับ runner ของ ส.ค."""
    for run in range(1, runs + 1):
        for mkey, m in models.items():
            for lang in LANGS:
                for qi, q in enumerate(suite):
                    for arm in (arms if (qi + run) % 2 == 0 else arms[::-1]):
                        yield run, mkey, m, lang, q, arm


# ---------------------------------------------------------------------------
# safe readers and file helpers
# ---------------------------------------------------------------------------
def _safe_hook(pairs):
    """แปลงค่า field 'error' เป็น None/True ทันทีตอน decode — ข้อความ error ไม่ถูกเก็บหรือพิมพ์"""
    out = {}
    for k, v in pairs:
        out[k] = (None if v is None else True) if k == "error" else v
    return out


def read_jsonl_safe(path):
    """yield (line_no, record) — error field เป็น None/True; บรรทัดที่ไม่ใช่ JSON ทำให้หยุด"""
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            if not line.strip():
                continue
            try:
                rec = json.loads(line, object_pairs_hook=_safe_hook)
            except ValueError:
                die(2, f"{os.path.basename(path)} line {n} is not complete JSON (interrupted write?). "
                       f"Stop: do not delete records; report the line number before any resume.")
            if not line.endswith("\n"):
                die(2, f"{os.path.basename(path)} line {n} has no newline (interrupted write?). "
                       f"Stop: report the line number before any resume.")
            yield n, rec


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def under_results(path):
    """True เมื่อ path อยู่ใต้โฟลเดอร์ชื่อ results (ที่เก็บผลทางการ) โดยไม่สนตัวพิมพ์เล็กใหญ่
    (APFS ของ macOS ไม่แยกตัวพิมพ์: "../Results/x" คือโฟลเดอร์ results เดียวกัน); realpath
    ตาม symlink ของส่วนที่มีอยู่แล้ว"""
    parts = os.path.realpath(os.path.abspath(path)).split(os.sep)
    return any(p.casefold() == OFFICIAL_DIR for p in parts)


def root_relpath(path):
    """path สัมพัทธ์กับ ROOT (โฟลเดอร์แม่ของโฟลเดอร์ที่มี runner.py); นอก ROOT เก็บเพียง basename"""
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    rel = os.path.relpath(os.path.abspath(path), root)
    if rel.startswith(".."):
        return "<outside-root>/" + os.path.basename(path)
    return rel.replace(os.sep, "/")


def now_ict():
    return datetime.datetime.now(ICT).strftime("%Y-%m-%dT%H:%M:%S+07:00")


def append_record(fd, rec):
    """หนึ่ง record = os.write ครั้งเดียวบน fd แบบ O_APPEND"""
    data = (json.dumps(rec, ensure_ascii=False) + "\n").encode("utf-8")
    n = os.write(fd, data)
    if n != len(data):
        die(2, f"short write ({n} of {len(data)} bytes); stop and report before any resume")


def open_locked_append(path):
    fd = os.open(path, os.O_WRONLY | os.O_APPEND | os.O_CREAT, 0o644)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(fd)
        die(4, f"WRITER LOCK: another process is writing {os.path.basename(path)}; "
               f"one writer per file (wait for it to finish, then re-run the same command)")
    return fd


# ---------------------------------------------------------------------------
# inputs
# ---------------------------------------------------------------------------
def load_suite(path):
    with open(path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter="\t")
        cols = list(reader.fieldnames or [])
        suite = list(reader)
    missing = [c for c in REQUIRED_COLUMNS if c not in cols]
    if missing:
        die(2, f"suite {os.path.basename(path)}: missing column(s) {missing}")
    seen = set()
    for r in suite:
        if r["id"] in seen:
            die(2, f"suite {os.path.basename(path)}: duplicate id {r['id']}")
        seen.add(r["id"])
        if r["schema"] not in SCHEMAS:
            die(2, f"suite {os.path.basename(path)}: id {r['id']} has schema {r['schema']!r} (allowed {SCHEMAS})")
        if not (r.get("question_en") or "").strip() or not (r.get("question_th") or "").strip():
            die(2, f"suite {os.path.basename(path)}: id {r['id']} has an empty question")
    if not suite:
        die(2, f"suite {os.path.basename(path)} has no rows")
    return suite, cols


def suite_draft_reason(path, suite, cols):
    """None เมื่อ suite ตรึงแล้ว; มิฉะนั้นคืนเหตุผล. ค่าที่ถูกต้องของ build_status คือ {FROZEN, DRAFT}
    (design 3.2/3.3) — ค่าอื่นทุกค่า (ว่าง, 'PENDING', 'frozen') ถือเป็น draft"""
    if "DRAFT" in os.path.basename(path).upper():
        return "DRAFT in the file name"
    if "build_status" in cols:
        bad = sorted({r.get("build_status") or "" for r in suite} - {FROZEN_STATUS})
        if bad:
            return (f"build_status {', '.join(repr(x) for x in bad[:3])} "
                    f"(every row must be {FROZEN_STATUS!r})")
    return None


def suite_is_draft(path, suite, cols):
    return suite_draft_reason(path, suite, cols) is not None


def load_hints(path, expect_sha, require_sha):
    """โหลด value-hint blocks ที่ตรึงแล้ว; ตรวจ sha256 ของไฟล์ และ sha256 ของ block ต่อ schema"""
    if require_sha and not expect_sha:
        die(2, "arm 'values' needs --hints-sha256 (sha256 of the frozen hint file) in a live run")
    raw = open(path, "rb").read()
    got = hashlib.sha256(raw).hexdigest()
    if expect_sha and got != expect_sha.strip().lower():
        die(2, f"HINT FILE MISMATCH: sha256 {got} != expected {expect_sha} — aborting")
    try:
        d = json.loads(raw)
    except ValueError:
        die(2, f"HINT FILE {os.path.basename(path)} is not valid JSON — aborting")
    if d.get("source_db") != EXPECTED_HINTS_SOURCE_DB:
        die(2, f"HINT FILE: source_db {d.get('source_db')!r} != {EXPECTED_HINTS_SOURCE_DB!r} — aborting")
    top = d.get("block_sha256") or {}
    blocks, bsha = {}, {}
    for k in SCHEMAS:
        s = d["schemas"][k]
        h = hashlib.sha256(s["block"].encode("utf-8")).hexdigest()
        if h != s.get("sha256") or h != top.get(k):
            die(2, f"HINT BLOCK MISMATCH schema {k}: block sha256 {h} != recorded "
                   f"{s.get('sha256')} / {top.get(k)} — aborting")
        blocks[k], bsha[k] = s["block"], h
    return blocks, d.get("version"), got, bsha


def live_keys(models):
    """อ่าน os.environ เฉพาะ key ของผู้ให้บริการที่จะเรียก (live mode เท่านั้น)"""
    keys = {}
    for m in models.values():
        var = _PROVIDER_KEY.get(m["provider"])
        if var and var not in keys:
            val = os.environ.get(var)
            if not val:
                die(2, f"{var} is not set in the environment (source secrets.env in this terminal first)")
            keys[var] = val
            _ACTIVE_SECRETS.append(val)
    return keys


def _ollama_norm(name):
    last = name.split("/")[-1]
    return name if ":" in last else name + ":latest"


def _digest_hex(d):
    d = (d or "").strip().lower()
    return d.split(":", 1)[1] if d.startswith("sha256:") else d


def ollama_digest_lock(models, prov_path):
    """ก่อน local call แรก: digest จาก /api/tags ต้องเท่ากับ provenance (Gate 1a); payload ไม่เปลี่ยน"""
    try:
        prov = json.load(open(prov_path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        die(5, f"OLLAMA DIGEST LOCK: cannot read --ollama-digests ({type(e).__name__})")
    expected = (prov.get("ollama") or {}).get("models") or {}
    try:
        tags = http_get_json(OLLAMA_BASE + "/api/tags")
    except Exception as e:
        die(5, f"OLLAMA DIGEST LOCK: GET /api/tags failed ({type(e).__name__}); is Ollama running?")
    have = {}
    for t in (tags or {}).get("models") or []:
        for nm in (t.get("name"), t.get("model")):
            if nm:
                have[_ollama_norm(nm)] = t.get("digest")
    out = {}
    for mkey, m in models.items():
        if m["provider"] != "ollama":
            continue
        name = m["model"]
        ent = expected.get(name) or expected.get(_ollama_norm(name)) or {}
        exp = _digest_hex(ent.get("digest"))
        got = _digest_hex(have.get(_ollama_norm(name)))
        if not exp:
            die(5, f"OLLAMA DIGEST LOCK: {mkey} ({name}) has no digest in {os.path.basename(prov_path)}")
        if not got:
            die(5, f"OLLAMA DIGEST LOCK: {mkey} ({name}) is not listed by /api/tags")
        if exp != got:
            die(5, f"OLLAMA DIGEST MISMATCH {mkey} ({name}): provenance {exp[:12]} != installed {got[:12]} "
                   f"— no generate call made")
        out[mkey] = got
    return out


def verify_prompts(path, schedule, expect):
    """ตรวจไฟล์ dry-run กับตารางเวลาของ invocation นี้ทั้งหมดก่อน call แรก"""
    metas, calls = [], []
    with open(path, encoding="utf-8") as fh:
        for n, line in enumerate(fh, 1):
            try:
                d = json.loads(line)
            except ValueError:
                die(2, f"--prompts line {n} is not JSON")
            if not isinstance(d, dict):
                die(2, f"--prompts line {n} is not a JSON object")
            t = d.get("type")
            if t == "meta":
                metas.append(d)
            elif t == "call":
                calls.append(d)
    if len(metas) != 1:
        # check_prompts_rc1 ต้องการ meta เพียงหนึ่งบรรทัดเช่นกัน; ไม่ยอมให้บรรทัดหลังทับบรรทัดแรกเงียบๆ
        die(2, f"--prompts has {len(metas)} meta lines (exactly 1 expected); use the dry-run file as written")
    meta = metas[0]
    if meta.get("draft") is not False:
        die(2, "--prompts was made from a DRAFT suite (meta draft != false); a live run needs the frozen dry-run")
    for k, v in expect.items():
        if meta.get(k) != v:
            die(2, f"--prompts meta {k} does not match this invocation ({str(meta.get(k))[:16]} != {str(v)[:16]})")
    keys = {s[0] for s in schedule}
    mine = [(c.get("model_key"), c.get("run"), c.get("arm"), c.get("lang"), c.get("qid"),
             c.get("prompt_sha256"), c.get("payload_sha256")) for c in calls if c.get("model_key") in keys]
    if len(mine) != len(schedule):
        die(2, f"--prompts schedule has {len(mine)} calls for the selected model(s); this run plans {len(schedule)}")
    bad = sum(1 for a, b in zip(mine, schedule) if a != b)
    if bad:
        die(2, f"--prompts mismatch: {bad} of {len(schedule)} planned calls differ "
               f"(order, prompt_sha256 or payload_sha256)")
    return len(schedule)


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def _http_error_parts(e):
    try:
        body = e.read().decode(errors="replace")
    except Exception:
        body = ""
    etype = None
    try:
        d = json.loads(body)
        if isinstance(d, list) and d:
            d = d[0]
        err = d.get("error") if isinstance(d, dict) else None
        if isinstance(err, dict):
            etype = err.get("type") or err.get("status") or err.get("code")
    except Exception:
        etype = None
    if not (isinstance(etype, (str, int)) and re.fullmatch(r"[A-Za-z0-9_.\-]{1,64}", str(etype))):
        etype = "HTTPError"
    # token ที่มีรูปแบบ key (หรือเท่ากับ key จริง) ไม่ใช่ชนิด error: ใช้ชื่อกลางแทน
    if redact(str(etype)) != str(etype):
        etype = "HTTPError"
    return str(etype), body


def _quota_label(body):
    """ป้ายคงที่ QUOTA_LABEL เมื่อ body ของผู้ให้บริการบอกว่าเครดิตหรือโควตาหมด; ไม่คืนข้อความใดจาก body"""
    return " " + QUOTA_LABEL if body and QUOTA_HINT_RE.search(body) else ""


def main():
    """exit 1 สงวนไว้สำหรับ error ที่ไม่คาดไว้เท่านั้น (MODEL SWAP ใช้ exit 6); พิมพ์เฉพาะชื่อ exception
    และข้อความที่ redact แล้ว — SystemExit และ KeyboardInterrupt ไม่ถูกจับ"""
    try:
        _main()
    except Exception as e:
        # redact ก่อนตัด (design 2.5 ข้อ 8): key ที่คร่อมจุดตัดจะไม่เหลือ prefix
        die(EXIT_UNEXPECTED, f"UNEXPECTED ERROR (not a model swap) {type(e).__name__}: "
                             + redact(str(e))[:200])


def _main():
    ap = argparse.ArgumentParser(description="K3 runner (run-of-record + RC1)")
    ap.add_argument("--suite", required=True)
    ap.add_argument("--suite-sha256", help="expected sha256 of --suite (optional)")
    ap.add_argument("--models", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--runs", type=int, default=5)
    ap.add_argument("--only", help="one model_key from models.json")
    ap.add_argument("--arms", default="base", help="comma list from base,values")
    ap.add_argument("--hints", help="frozen value-hint JSON (required for arm 'values')")
    ap.add_argument("--hints-sha256", help="expected sha256 of --hints (required for arm 'values' in a live run)")
    ap.add_argument("--lock-from", help="run-of-record jsonl: pre-load model-echo locks (read only; required live)")
    ap.add_argument("--lock-from-sha256", help="expected sha256 of --lock-from (optional; pins the August log)")
    ap.add_argument("--prompts", help="dry-run file: the whole planned schedule must match before the first call "
                                      "(required for a live run under results/)")
    ap.add_argument("--dry-run", action="store_true", help="write the prompt/call plan without calling any model")
    ap.add_argument("--max-consecutive-errors", type=int, default=DEFAULT_MAX_CONSECUTIVE_ERRORS)
    ap.add_argument("--ollama-digests", help="provenance JSON: /api/tags digests must match before the first local call")
    a = ap.parse_args()

    # ---- arguments that do not depend on files
    if a.runs < 1:
        die(2, "--runs must be >= 1")
    if a.max_consecutive_errors < 1:
        die(2, "--max-consecutive-errors must be >= 1")
    req = [x.strip() for x in a.arms.split(",") if x.strip()]
    if not req or any(x not in ARMS for x in req) or len(set(req)) != len(req):
        die(2, f"--arms must be a comma list from {ARMS}")
    arms = [x for x in ARMS if x in req]          # canonical order base, values
    if "values" in arms and "base" not in arms:
        die(2, "arm 'values' runs only together with arm 'base' (concurrent control): use --arms base,values")
    inputs = [("--suite", a.suite), ("--models", a.models)]
    if "values" in arms:
        inputs.append(("--hints", a.hints))
    if not a.dry_run:
        inputs.append(("--prompts", a.prompts))      # --ollama-digests: exit 5 in the digest lock
    for flag, path in inputs:
        if path and not os.path.isfile(path):
            die(2, f"{flag} {os.path.basename(path)} not found")

    try:
        models_all = json.load(open(a.models, encoding="utf-8"))
    except ValueError:
        die(2, f"--models {os.path.basename(a.models)} is not valid JSON")
    if not isinstance(models_all, dict) or not all(isinstance(v, dict) for v in models_all.values()):
        die(2, f"--models {os.path.basename(a.models)}: expected an object of model_key -> settings")
    if a.only is not None:
        if a.only not in models_all:
            die(2, f"--only {a.only!r} is not a model_key in {os.path.basename(a.models)} "
                   f"(known: {', '.join(models_all)})")
        models = {a.only: models_all[a.only]}
    else:
        models = dict(models_all)
    for mkey, m in models.items():
        if m.get("provider") not in ("openai", "anthropic", "google", "ollama"):
            die(2, f"model {mkey}: unknown provider {m.get('provider')!r}")

    suite, cols = load_suite(a.suite)
    suite_sha = sha256_file(a.suite)
    if a.suite_sha256 and suite_sha != a.suite_sha256.strip().lower():
        die(2, f"SUITE MISMATCH: sha256 {suite_sha} != expected {a.suite_sha256}")
    is_ext = any(c in cols for c in EXT_MARKER_COLUMNS)
    if is_ext and "values" in arms:
        die(2, "the extension suite runs the base arm only (--arms base)")
    draft_reason = suite_draft_reason(a.suite, suite, cols)
    draft = draft_reason is not None
    official = under_results(a.out)

    hints, hints_ver, hints_sha, block_sha = {}, None, None, None
    if "values" in arms:
        if not a.hints:
            die(2, "arm 'values' needs --hints")
        hints, hints_ver, hints_sha, block_sha = load_hints(a.hints, a.hints_sha256,
                                                             require_sha=not a.dry_run)
    elif a.hints:
        say("NOTE: --hints ignored (arm 'values' not requested)")

    if a.lock_from and os.path.realpath(a.lock_from) == os.path.realpath(a.out):
        die(2, "--out must not be the run-of-record file")

    models_sha = sha256_file(a.models)
    runner_sha = sha256_file(os.path.abspath(__file__))

    # ---- dry run: one new file, no network, never reads the key variables (FAKE_KEYS only)
    if a.dry_run:
        if draft and official:
            die(2, f"DRAFT suite ({draft_reason}): a dry-run under results/ is refused; "
                   f"write it outside results/ (TEST-ONLY)")
        try:
            fd = os.open(a.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        except FileExistsError:
            die(2, f"--dry-run writes a fresh plan; {os.path.basename(a.out)} exists (give a new --out)")
        meta = {"type": "meta", "suite_path": root_relpath(a.suite), "suite_sha256": suite_sha,
                "draft": draft, "models_sha256": models_sha, "runner_sha256": runner_sha,
                "hints_sha256": hints_sha, "block_sha256": block_sha, "arms": arms, "runs": a.runs,
                "created_at_ict": now_ict()}
        n_prompt = n_call = 0
        with os.fdopen(fd, "w", encoding="utf-8") as out:
            out.write(json.dumps(meta, ensure_ascii=False) + "\n")
            for arm in arms:
                for lang in LANGS:
                    for q in suite:
                        system, user = build_prompt(q, lang, arm, hints)
                        out.write(json.dumps({"type": "prompt", "arm": arm, "lang": lang, "qid": q["id"],
                                              "schema": q["schema"], "system": system, "user": user,
                                              "prompt_sha256": prompt_sha256(system, user)},
                                             ensure_ascii=False) + "\n")
                        n_prompt += 1
            for seq, (run, mkey, m, lang, q, arm) in enumerate(plan(models, suite, arms, a.runs), 1):
                system, user = build_prompt(q, lang, arm, hints)
                _, payload, _ = build_payload(m, system, user, FAKE_KEYS)
                out.write(json.dumps({"type": "call", "seq": seq, "model_key": mkey, "run": run, "arm": arm,
                                      "lang": lang, "qid": q["id"],
                                      "prompt_sha256": prompt_sha256(system, user),
                                      "payload_sha256": payload_sha256(payload)},
                                     ensure_ascii=False) + "\n")
                n_call += 1
        say(f"DRY RUN (no model called): {n_prompt} prompts, {n_call} calls, draft={str(draft).lower()}, "
            f"suite sha256 {suite_sha[:12]}, hints sha256 {(hints_sha or '-')[:12]} -> {os.path.basename(a.out)}")
        return

    # ---- live run guards (before opening --out)
    if draft:
        die(2, f"DRAFT suite ({draft_reason}): a live run is refused; use the frozen suite")
    if not a.lock_from:
        die(2, "a live run needs --lock-from (run-of-record log for the echo lock)")
    if not os.path.isfile(a.lock_from):
        die(2, f"--lock-from {os.path.basename(a.lock_from)} not found")
    if os.path.exists(a.out) and os.path.samefile(a.lock_from, a.out):
        die(2, "--out must not be the run-of-record file")
    has_local = any(m["provider"] == "ollama" for m in models.values())
    if has_local and not a.ollama_digests and official:
        die(2, "local model(s) in a live run under results/ need --ollama-digests (provenance_gate1a.json)")
    if official and not a.prompts:
        die(2, "a live run under results/ needs --prompts (the frozen dry-run): the whole schedule "
               "is checked against it before the first call")
    lock_sha = sha256_file(a.lock_from)
    if a.lock_from_sha256 and lock_sha != a.lock_from_sha256.strip().lower():
        die(2, f"LOCK FILE MISMATCH: --lock-from sha256 {lock_sha[:12]} != expected "
               f"{a.lock_from_sha256.strip()[:12]} — aborting")

    schedule = []
    for run, mkey, m, lang, q, arm in plan(models, suite, arms, a.runs):
        system, user = build_prompt(q, lang, arm, hints)
        _, payload, _ = build_payload(m, system, user, FAKE_KEYS)
        schedule.append((mkey, run, arm, lang, q["id"], prompt_sha256(system, user), payload_sha256(payload)))
    if a.prompts:
        n = verify_prompts(a.prompts, schedule, {"suite_sha256": suite_sha, "arms": arms, "runs": a.runs,
                                                 "hints_sha256": hints_sha, "models_sha256": models_sha,
                                                 "runner_sha256": runner_sha})
        say(f"prompts check: {n}/{n} planned calls match the dry-run")
    else:
        say("NOTE (TEST-ONLY location): no --prompts given; the schedule is not checked against a dry-run")

    locked = {}
    for _, rec in read_jsonl_safe(a.lock_from):   # echo lock ตาม run-of-record ส.ค. (read only)
        if rec.get("model_echo") and rec.get("model_key") in models:
            locked.setdefault(rec["model_key"], rec["model_echo"])
    no_echo = [mkey for mkey in models if mkey not in locked]
    if no_echo and official:
        die(2, f"--lock-from {os.path.basename(a.lock_from)} has no echo for {', '.join(no_echo)}: under results/ "
               f"the echo lock must come from the run-of-record log (results.jsonl of August has an echo for "
               f"all six models)")
    for mkey in no_echo:
        say(f"WARNING (TEST-ONLY location): no echo for {mkey} in --lock-from; the first response sets the lock")
    say(f"echo lock from {os.path.basename(a.lock_from)} (sha256 {lock_sha[:12]}): "
        + ", ".join(f"{k} {v}" for k, v in sorted(locked.items())))

    keys = live_keys(models)

    digests = {}
    if has_local:
        if a.ollama_digests:
            digests = ollama_digest_lock(models, a.ollama_digests)
            say("ollama digest lock: " + ", ".join(f"{k} {v[:12]}" for k, v in digests.items()))
        else:
            say("WARNING (TEST-ONLY location): local model(s) without --ollama-digests; model_digest = None")

    # ---- one writer per file; read the existing log only after the lock is held
    fd = open_locked_append(a.out)
    try:
        done, max_seq, file_arms = set(), 0, set()
        for _, rec in read_jsonl_safe(a.out):
            if rec.get("suite_sha256") != suite_sha:
                die(2, f"{os.path.basename(a.out)} holds records of another suite "
                       f"(suite_sha256 {str(rec.get('suite_sha256'))[:12]}); refusing to append")
            if rec.get("arm") not in arms:
                die(2, f"{os.path.basename(a.out)} holds arm {rec.get('arm')!r} outside --arms {arms}; refusing to append")
            if rec.get("arm") == "values" and rec.get("hints_sha256") != hints_sha:
                die(2, f"{os.path.basename(a.out)} holds values records made with another hint file; refusing to append")
            file_arms.add(rec.get("arm"))
            if isinstance(rec.get("seq"), int):
                max_seq = max(max_seq, rec["seq"])
            if "raw" in rec and rec.get("error") is None:   # error records = ลองใหม่ได้ตอน resume
                done.add((rec["model_key"], rec.get("arm"), rec["lang"], rec["qid"], rec["run"]))
            if rec.get("model_echo") and rec.get("model_key") in models:
                locked.setdefault(rec["model_key"], rec["model_echo"])
        # ชุด arm ของไฟล์ต้องเท่ากับ --arms ทั้งสองทิศ (design 2.5 ข้อ 7): ไฟล์ base อย่างเดียวรับแขน values
        # ไม่ได้ เพราะทุกคู่ B/V จะถูกถามคนละโปรเซส; ข้อยกเว้นเดียวคือไฟล์ของ base,values ที่หยุดก่อน
        # record base แรก (record แรกของแผนคือ values เสมอ: run 1 ข้อแรก parity คี่) จึงมีแต่ values
        if file_arms and file_arms != set(arms) and not (file_arms == {"values"} and set(arms) == set(ARMS)):
            die(2, f"{os.path.basename(a.out)} holds arm set {sorted(file_arms)} but --arms is {arms}; "
                   f"one file holds one arm set (B/V pairs must come from the same process); refusing to append")

        run_id = uuid.uuid4().hex[:12]
        seq = max_seq
        say(f"run_id {run_id} | suite {os.path.basename(a.suite)} sha256 {suite_sha[:12]} | arms {','.join(arms)} "
            f"| runs {a.runs} | models {','.join(models)} | done {len(done)} | next seq {seq + 1}")

        per_round = len(models) * len(LANGS) * len(suite) * len(arms)
        total = per_round * a.runs
        consecutive, i, last_run = 0, 0, None
        for run, mkey, m, lang, q, arm in plan(models, suite, arms, a.runs):
            if run != last_run:
                i, last_run = 0, run
            i += 1
            key = (mkey, arm, lang, q["id"], run)
            if key in done:
                continue
            system, user = build_prompt(q, lang, arm, hints)
            psha = prompt_sha256(system, user)
            _, payload, _ = build_payload(m, system, user, FAKE_KEYS)
            paysha = payload_sha256(payload)
            t0 = time.time()
            usage, echo_source, err_summary = {}, None, None
            try:
                raw, echo, echo_source, usage = call_model(m, system, user, keys)
                sql, parse_ok = extract_sql(raw)
                err = None
            except urllib.error.HTTPError as e:
                etype, body = _http_error_parts(e)
                raw, echo, sql, parse_ok = None, None, None, False
                # redact ก่อนตัด (เดิมตัดก่อน redact จึงเหลือ prefix ของ key); แล้ว redact ทั้งบรรทัดอีกชั้น
                # เพื่อให้ทุกสตริงที่เข้า log ผ่าน redact (รวม status และชนิด error)
                err = redact(f"HTTP {e.code} {etype}: " + redact(body or str(e.reason or ""))[:ERROR_BODY_MAX])
                err_summary = redact(f"HTTP {e.code} {etype}") + _quota_label(body)
            except Exception as e:
                raw, echo, sql, parse_ok = None, None, None, False
                err = redact(f"{type(e).__name__}: " + redact(str(e))[:ERROR_BODY_MAX])
                err_summary = type(e).__name__
            if echo and mkey in locked and locked[mkey] != echo:
                die(EXIT_SWAP, f"MODEL SWAP DETECTED {mkey}: {locked[mkey]} -> {echo} — aborting per prereg "
                               f"(exit {EXIT_SWAP}; no record written for this call)")
            if echo:
                locked.setdefault(mkey, echo)
            now = time.time()
            seq += 1
            rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S", time.localtime(now)), "model_key": mkey,
                   "model_echo": echo, "lang": lang, "qid": q["id"],
                   "tier": q["tier"], "schema": q["schema"], "run": run,
                   "latency_s": round(now - t0, 3), "raw": raw,
                   "sql": sql, "parse_ok": parse_ok, "error": err,
                   "arm": arm,
                   "hints_version": hints_ver if arm == "values" else None,
                   "hints_sha256": hints_sha if arm == "values" else None,
                   "block_sha256": block_sha[q["schema"]] if arm == "values" else None,
                   "prompt_sha256": psha, "payload_sha256": paysha, "suite_sha256": suite_sha,
                   "run_id": run_id, "seq": seq, "t_epoch": round(now, 3),
                   "tok_in": usage.get("in"), "tok_out": usage.get("out"), "tok_think": usage.get("think"),
                   "echo_source": echo_source,
                   "model_digest": digests.get(mkey) if m["provider"] == "ollama" else None}
            append_record(fd, rec)
            if i % 25 == 0 or i == per_round:
                tail = "  ── จบ global loop {}".format(run) if i == per_round else ""
                say(f"{lang}-{run}-{i}/{per_round}  [{mkey} {arm} {q['id']}]{tail}")
            if err is None:
                consecutive = 0
            else:
                consecutive += 1
                if consecutive >= a.max_consecutive_errors:
                    die(3, f"CIRCUIT BREAKER: {consecutive} consecutive errors ({mkey}); last: {err_summary}. "
                           f"Error records are retried on resume: fix the cause, then re-run the same command.")
            time.sleep(m.get("sleep", 0.3))
    finally:
        os.close(fd)  # releases the writer lock on every exit path

    # นับสถานะจริงจากไฟล์ — เฉพาะโมเดล + arm + จำนวนรอบของ invocation นี้
    goodk, errk = set(), 0
    for _, rec in read_jsonl_safe(a.out):
        if (rec.get("model_key") not in models or rec.get("run", 0) > a.runs
                or rec.get("arm") not in arms):
            continue
        if rec.get("error") is None:
            goodk.add((rec["model_key"], rec.get("arm"), rec["lang"], rec["qid"], rec["run"]))
        else:
            errk += 1
    say(f"SUCCESS cells: {len(goodk)}/{total} | error records ค้างรอ retry: "
        f"{total - len(goodk)} (log error lines สะสม {errk})")
    say("ถ้ายังไม่ครบ: รันคำสั่งเดิมซ้ำ — จะ retry เฉพาะที่ยังพัง")
    say("locked models: " + json.dumps(locked, indent=1))


if __name__ == "__main__":
    main()
