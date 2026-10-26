#!/usr/bin/env python3
"""build_ext_suite.py -- the single builder of the extension suite (AMENDMENT-9).

Modes (exactly one):
  --check   list blank, unknown or conflicting decisions, missing literal EN texts and
            every other freeze blocker; writes nothing.
            Exit 2: at least one blocker.
            Exit 3: INCOMPLETE CHECK -- no blocker, but a check that --freeze runs was
                    skipped (--pg, --manifest or --columns not given, or a sweep pattern
                    source missing). Exit 3 never means "freeze will pass".
            Exit 0: no blocker and nothing skipped (only the typed approval hash of
                    --freeze is not checked).
  --draft   always write a DRAFT suite (file names end in _DRAFT, build_status DRAFT on
            every row); blank decisions are replaced by the proposals and reported.
  --freeze  write k3n_ext_suite_v1.0.tsv only when there is no blocker, every check
            passes, ext_decisions carries author_approved = true (with the approval time and
            master log reference) and the sha256 typed by the author
            (--approved-decisions-sha256) equals the decisions file read.
  Any refused input (missing label, pin mismatch, unreadable or non-JSON file, unreachable
  database, --out-dir naming a file) prints one 'REFUSED: ...' line and exits 2 with no
  file written.

Sources (every file is pinned by sha256 in ext_decisions.inputs under a neutral label;
paths are passed on the command line, never stored):
  --input selection_xlsx=...        selection workbook (sheets: item review, reserves, proposals)
  --input translation_fixes_xlsx=... decision record of the translation check (four sheets)
  --input typo_fixes=...            typo fixes applied before the decisions
  --input item_changes=...          ITEM_CHANGES of 13 Oct
  --input item_changes_add=...      ITEM_CHANGES_2026-10-14_ADD.tsv (missing audit rows)
  --input metadata_refresh=...      ext_metadata_refresh_2026-10-14.tsv
  --input items_json=...            items.json (cross-check only)
  --input sql_TESTONLY=<directory>  SQL files of acceptance readings and of the FK1 gold
                                    (each file used is pinned; the folder digest is recorded
                                    under the label sql_TESTONLY, as freeze_stamp.py records it)
  --decisions ext_decisions_2026-10-14.json, --manifest mi_manifest_k3n.json,
  --columns suite_columns.json, --pg "dbname=k3n"
  grade_v13.py and vg_rule.py are read from --lib-dir (default: this script's folder) and must
  equal the pins lib/grade_v13.py and lib/vg_rule.py of ext_decisions.inputs.

Order of application: workbook -> ITEM_CHANGES (checked against 'before') -> TYPO_FIXES ->
decisions recorded in TRANSLATION_FIXES (interpreted through ext_decisions). Membership,
order, reserves, reserve rule, directional items, MI rule, FK1 format, X33 EN and the
literal EN texts of FK2 and X19 come from ext_decisions only (never from the decision
cells of the selection workbook); the decision rows of FK2, X19 and X33 in the EN sheet
must agree with them (a blank or conflicting row is a blocker).

Anonymity sweep (all outputs and the git-bound inputs, before anything is written):
  built-in      e-mail form, the Thai word for 'student', absolute home paths;
  runtime       identity tokens of the running account (user, host, home folder; taken at
                run time and never written anywhere);
  CLAUDE.md     the first back-quoted pattern after the words 'sweep' + Thai 'with' in the
                CLAUDE.md two folders above the project root (the nearest folder above this
                script that holds both harness/ and suite/), read at run time;
                --anon-patterns-from FILE reads it from another file;
  --anon-extra  "A,B": literals with letter boundaries, e.g. the short name of the teaching
                institution typed by the author;
  --anon-patterns FILE: one regex per line.
  --freeze refuses when the CLAUDE.md pattern cannot be read. Without --anon-extra the short
  name is not swept here: --freeze is refused (REQUIRE_ANON_EXTRA_AT_FREEZE is True; with False
  it is a warning in the report and anon_sweep sweeps it at Gate 1a step 1a.73).

ITEM_CHANGES rows whose value is already in the workbook: the old value is no longer in any
pinned input, so the builder only checks that 'before' is filled and differs from 'after';
the 'before' values of the pinned files are checked once in Gate 0 (test EX-T7g) against the
draft of 13 Oct. Rows (ITEM_CHANGES, TYPO_FIXES) for an id outside the selection workbook are
blockers; rows of dropped items are skipped and listed in the report.
Manifest instances: the recorded data fingerprint and, when db_fingerprint.py sits next to
the manifest, the recorded schema_md5 are recomputed on each database (build_instances.py
checks schema_md5 too, at Gate 1a step 1a.45).

The xlsx reader uses the standard library only (zipfile + xml.etree) so that the script
runs under `python3 -I -B`. Output is deterministic (UTF-8 without BOM, LF, no time
stamps). Nothing is ever written outside --out-dir; a DRAFT is never written under a
results/ folder (checked on the real path, case-insensitive). Database sessions are
read-only. Messages on stdout are English; the build report (ext_build_report.md) is Thai.

Example (Gate 1a, run from harness/):
  python3 -I -B "build_ext_suite.py" --freeze --pg "dbname=k3n" --manifest "db/mi_manifest_k3n.json" \
    --decisions "../suite/ext_inputs/ext_decisions_2026-10-14.json" --columns "suite_columns.json" \
    --input "selection_xlsx=..." ... --out-dir "../results/ext/build" \
    --approved-decisions-sha256 "<sha256 typed by the author>" [--anon-extra "<short name typed by the author>"]
"""
import argparse
import csv
import getpass
import hashlib
import importlib.util
import io
import json
import os
import re
import socket
import sys
import zipfile
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path

sys.dont_write_bytecode = True

BUILDER_VERSION = "build_ext_suite 1.2 (Gate 0, 2026-10-14)"

# Single switch for the short name of the teaching institution in the anonymity sweep (--anon-extra).
# True:  --freeze without --anon-extra is a BLOCKER (in use since 14 Oct 2026: RUNBOOK step 1a.59 passes
#        --anon-extra "<short name>", so a freeze can never skip the short name).
# False: --freeze without --anon-extra is a WARNING recorded in the build report; the short name is then
#        swept by anon_sweep at Gate 1a step 1a.73 (freeze_manifest_gate1b lists every builder output that
#        enters git).
REQUIRE_ANON_EXTRA_AT_FREEZE = True
SUITE_BASENAME = "k3n_ext_suite_v1.0"
RESERVES_BASENAME = "k3n_ext_reserves_v1.0"
CHANGES_BASENAME = "ITEM_CHANGES_generated_2026-10-14"
REFRESH_BASENAME = "ext_metadata_refresh"
REPORT_BASENAME = "ext_build_report"
INPUTS_BASENAME = "ext_inputs"

CORE_COLUMNS = ["id", "tier", "schema", "eff", "question_en", "question_th", "gold_sql_draft",
                "notes", "gold_sql_v12", "v13_status", "order_en", "order_th", "sort_keys", "norm",
                "alt_gold_en", "alt_gold_th", "v13_rule", "v13_rationale"]
KNOWN_EXT_COLUMNS = {"family", "col_roles", "mi_instances", "vg", "vg_literals", "source",
                     "author_class", "ai_drafted", "fallback_rank", "build_status"}
REQUIRED_LABELS = ["selection_xlsx", "translation_fixes_xlsx", "typo_fixes", "item_changes",
                   "item_changes_add", "metadata_refresh", "items_json", "sql_TESTONLY"]
SQL_DIR_LABEL = "sql_TESTONLY"
LIB_FILES = {"lib/grade_v13.py": "grade_v13.py", "lib/vg_rule.py": "vg_rule.py"}

# sheet and header names of the two workbooks (data layout, not decisions)
SEL_ITEM_SHEETS = ["ตรวจและแปล", "ข้อสำรอง", "ข้อที่เสนอเพิ่ม"]
H_ID = "ID"
H_SOURCE = "ที่มา"
H_FAMILY = "ตระกูล"
H_TIER = "Tier"
H_RANK = "ลำดับสำรอง"
H_AUTHOR_A = "ผู้เขียนต้นฉบับ"
H_AUTHOR_B = "ผู้ร่าง"
H_EN = "ฉบับปรับ (EN) = question_en"
H_GOLD = "Gold SQL (ร่าง)"
H_TH = "[กรอก] ภาษาไทย"
H_SEL_DECISION = "[กรอก] การตัดสิน"
H_SEL_EN_EDIT = "[กรอก] แก้ถ้อยคำ EN"
TF_TH_SHEET = "แก้ TH"
TF_EN_SHEET = "ตัด EN"
TF_OTHER_SHEET = "ตัดสินอื่น"
TF_SET_SHEET = "ชุด 40 ข้อ"
TFH_TH_CUR = "TH ปัจจุบัน (แก้คำผิดแล้ว)"
TFH_TH_PROP = "TH ที่เสนอ"
TFH_TH_OWN = "[กรอก] TH ที่ใช้ (ถ้าใช้ถ้อยคำของฉัน)"
TFH_DECISION = "[กรอก] การตัดสิน"
TFH_EN_CUR = "EN ปัจจุบัน"
TFH_EN_PROP = "EN ที่เสนอ"
TFH_EN_OWN = "[กรอก] EN ที่ใช้ (ถ้าแก้เอง)"
TFH_OTHER_NO = "ข้อ"
TFH_OTHER_REC = "ผู้ช่วยแนะนำ"
TH_VOCAB = {"ใช้ตามเสนอ": "proposed", "ใช้ถ้อยคำของฉัน": "own", "คงเดิม": "keep"}
EN_VOCAB = {"อนุมัติ": "approve", "ไม่อนุมัติ": "reject", "แก้เอง": "own"}
EN_REJECT = "ไม่อนุมัติ"
TEXT_FIELDS = {"question_en", "question_th"}
GOLD_FIELD = "gold_sql_draft"

THAI_RE = re.compile("[฀-๿]")
NONE_RE = re.compile(r"(?<![A-Za-z])None(?![A-Za-z])")
QID_CORE_RE = re.compile(r"^Q\d{2}$")
OPTION_RE = re.compile(r"^\(([ก-ฮ])\)")
COL_ROLES_RE = re.compile(r"^(\*|\d+(,\d+)+(;\d+(,\d+)+)*)$")
FP_TABLE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
EMAIL_RE = r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"
SWEEP_LINE_RE = re.compile("sweep \u0e14\u0e49\u0e27\u0e22\\s*`([^`]+)`")   # 'sweep' + Thai 'with' + back-quoted pattern
LB_PRE, LB_POST = r"(?<![A-Za-z])", r"(?![A-Za-z])"
GENERIC_HOST_WORDS = {"macbook", "imac", "mac", "mini", "pro", "air", "studio", "local", "localhost",
                      "laptop", "desktop", "computer", "home", "users", "user", "admin", "root"}
KIND_TH = {"decision": "มติ", "input": "input", "check": "การตรวจ", "approval": "การอนุมัติ"}
# legal values of ext_decisions (design 2.8 and 3.2)
EFFECT_LIST_KEYS = ("require_th_rows", "forbid_th_keep", "forbid_th_change", "require_en_rows", "forbid_en_keep")
EFFECT_MAP_KEYS = ("add_alt_gold_th", "set_gold_from_sql")
AUTHOR_CLASSES = ("author", "assistant-drafted")
AI_DRAFTED_VALUES = ("yes", "no")
OVERRIDE_STATUSES = ("final", "reserve", "dropped")
CONFLICT_COPY_RE = re.compile(r"^(?P<stem>.+) (?P<n>[0-9]+)(?P<ext>\.[A-Za-z0-9]+)$")   # iCloud copy: 'name 2.tsv'

EXIT_OK, EXIT_REFUSED, EXIT_INCOMPLETE = 0, 2, 3


class Fatal(Exception):
    """input that makes any build meaningless (missing label, pin mismatch, bad layout)"""


# ======================================================================= xlsx (stdlib)
_NS_MAIN = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
_NS_REL = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
_NS_PKG = "http://schemas.openxmlformats.org/package/2006/relationships"


def _q(tag):
    return "{%s}%s" % (_NS_MAIN, tag)


def _si_text(node):
    """text of a <si> or <is> node: the direct <t> plus the <t> of every rich-text run
    (phonetic runs <rPh> are ignored), as openpyxl Text.content does"""
    parts = []
    t = node.find(_q("t"))
    if t is not None and t.text is not None:
        parts.append(t.text)
    for r in node.findall(_q("r")):
        rt = r.find(_q("t"))
        if rt is not None and rt.text is not None:
            parts.append(rt.text)
    return "".join(parts)


def _col_index(ref):
    letters = re.match(r"([A-Z]+)", ref).group(1)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def _cast_number(v):
    if "." in v or "E" in v or "e" in v:
        return float(v)
    return int(v)


def read_xlsx(path):
    """{sheet name: [row list]} with cached values (data_only semantics); rows are
    trimmed of trailing None and all-empty rows are dropped"""
    out = {}
    with zipfile.ZipFile(path) as z:
        names = set(z.namelist())
        shared = []
        if "xl/sharedStrings.xml" in names:
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall(_q("si")):
                shared.append(_si_text(si).replace("x005F_", ""))
        wb = ET.fromstring(z.read("xl/workbook.xml"))
        rels = ET.fromstring(z.read("xl/_rels/workbook.xml.rels"))
        target = {}
        for rel in rels.findall("{%s}Relationship" % _NS_PKG):
            tgt = rel.get("Target")
            tgt = tgt.lstrip("/") if tgt.startswith("/") else "xl/" + tgt
            target[rel.get("Id")] = tgt
        for sh in wb.find(_q("sheets")).findall(_q("sheet")):
            name = sh.get("name")
            part = target[sh.get("{%s}id" % _NS_REL)]
            root = ET.fromstring(z.read(part))
            rows = {}
            data = root.find(_q("sheetData"))
            row_counter = 0
            for row in (data.findall(_q("row")) if data is not None else []):
                r_attr = row.get("r")
                row_counter = int(r_attr) if r_attr else row_counter + 1
                cells = {}
                col_counter = -1
                for c in row.findall(_q("c")):
                    ref = c.get("r")
                    col_counter = _col_index(ref) if ref else col_counter + 1
                    t = c.get("t", "n")
                    if t == "inlineStr":
                        node = c.find(_q("is"))
                        val = _si_text(node) if node is not None else None
                    else:
                        val = c.findtext(_q("v"), None) or None
                        if val is not None:
                            if t == "n":
                                val = _cast_number(val)
                            elif t == "s":
                                val = shared[int(val)]
                            elif t == "b":
                                val = bool(int(val))
                    if val is not None:
                        cells[col_counter] = val
                if cells:
                    width = max(cells) + 1
                    rows[row_counter] = [cells.get(i) for i in range(width)]
            out[name] = [rows[k] for k in sorted(rows)]
    return out


def sheet_records(book, sheet, required_headers=()):
    """list of {header: value} for the data rows of a sheet whose first row is the header"""
    if sheet not in book:
        raise Fatal(f"workbook has no sheet '{sheet}'")
    rows = book[sheet]
    if not rows:
        return []
    hdr = [h if h is None else str(h) for h in rows[0]]
    for h in required_headers:
        if h not in hdr:
            raise Fatal(f"sheet '{sheet}' has no column '{h}'")
    recs = []
    for r in rows[1:]:
        d = {h: (r[i] if i < len(r) else None) for i, h in enumerate(hdr) if h is not None}
        recs.append(d)
    return recs


# ======================================================================= small helpers
def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree_digest(folder):
    """digest of a folder exactly as freeze_stamp.py records a folder row: sha256 of one
    'relative/path<TAB>sha256<LF>' line per file in sorted relative-path order, without
    __pycache__ and .DS_Store; a *.env file is refused"""
    folder = Path(folder)
    entries = []
    for f in sorted(folder.rglob("*"), key=lambda x: x.relative_to(folder).as_posix()):
        rel = f.relative_to(folder)
        if not f.is_file() or "__pycache__" in rel.parts or f.name == ".DS_Store":
            continue
        if rel.name == "secrets.env" or rel.name.endswith(".env"):
            raise Fatal(f"input '{SQL_DIR_LABEL}' holds a forbidden file")
        entries.append("%s\t%s\n" % (rel.as_posix(), sha256_file(f)))
    return sha256_bytes("".join(entries).encode("utf-8"))


def cell_str(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def is_blank(v):
    return v is None or not str(v).strip()


def norm_sql(sql):
    """drop SQL comments and collapse whitespace outside quoted strings/identifiers;
    strip the trailing ';' (used for comparisons and for the one-line gold)"""
    out, i, n = [], 0, len(sql)
    pending_space = False
    while i < n:
        ch = sql[i]
        if ch == "'" or ch == '"':
            q = ch
            j = i + 1
            while j < n:
                if sql[j] == q:
                    if j + 1 < n and sql[j + 1] == q:
                        j += 2
                        continue
                    break
                j += 1
            if pending_space and out:
                out.append(" ")
            pending_space = False
            out.append(sql[i:j + 1])
            i = j + 1
            continue
        if ch == "-" and i + 1 < n and sql[i + 1] == "-":
            j = sql.find("\n", i)
            i = n if j < 0 else j
            pending_space = True
            continue
        if ch == "/" and i + 1 < n and sql[i + 1] == "*":
            j = sql.find("*/", i + 2)
            i = n if j < 0 else j + 2
            pending_space = True
            continue
        if ch.isspace():
            pending_space = True
            i += 1
            continue
        if pending_space and out:
            out.append(" ")
        pending_space = False
        out.append(ch)
        i += 1
    s = "".join(out).strip()
    while s.endswith(";"):
        s = s[:-1].rstrip()
    return s


def one_line_gold(sql):
    return norm_sql(sql) + ";"


def parse_option(value):
    """'(ข) แก้ TH' -> 'ข'; 'อนุมัติ' -> 'อนุมัติ'; blank -> None"""
    if is_blank(value):
        return None
    s = str(value).strip()
    m = OPTION_RE.match(s)
    return m.group(1) if m else s


def family_of(raw):
    m = re.match(r"\s*(F\d+)", cell_str(raw))
    return m.group(1) if m else None


def tier_of(raw):
    m = re.match(r"\s*T(\d)", cell_str(raw))
    return int(m.group(1)) if m else None


def load_json_input(path, label):
    """a JSON object read from a file; a file that is not UTF-8 JSON is refused (exit 2, no traceback)"""
    try:
        obj = json.loads(Path(path).read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise Fatal(f"{label} is not a UTF-8 JSON file ({type(e).__name__}"
                    + (f" at line {e.lineno} column {e.colno}" if isinstance(e, json.JSONDecodeError) else "") + ")")
    if not isinstance(obj, dict):
        raise Fatal(f"{label} does not hold a JSON object")
    return obj


def read_tsv(path):
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def tsv_bytes(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_MINIMAL)
    w.writerow(header)
    for r in rows:
        w.writerow([r.get(h, "") for h in header])
    return buf.getvalue().encode("utf-8")


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, str(path))
    if spec is None or spec.loader is None:
        raise Fatal(f"cannot load {Path(path).name}")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def under_results(path):
    """True when the real path (symbolic links resolved) has a folder named results in any
    letter case (APFS is case-insensitive)"""
    real = Path(os.path.realpath(os.path.abspath(str(path))))
    return any(part.casefold() == "results" for part in real.parts)


def dsn_with_db(dsn, dbname):
    from psycopg2.extensions import make_dsn, parse_dsn
    d = parse_dsn(dsn)
    d["dbname"] = dbname
    return make_dsn(**d)


def dbname_of(dsn):
    from psycopg2.extensions import parse_dsn
    return parse_dsn(dsn).get("dbname")


class Engine:
    """read-only session; every statement runs in its own rolled-back transaction"""

    def __init__(self, dsn):
        import psycopg2
        self.conn = psycopg2.connect(dsn)
        self.conn.set_session(readonly=True, autocommit=False)

    def run(self, sql):
        try:
            with self.conn.cursor() as cur:
                cur.execute("SET LOCAL statement_timeout = '20s'")
                cur.execute(sql)
                cols = [d.name for d in cur.description] if cur.description else []
                rows = cur.fetchall() if cur.description else []
                return cols, rows
        finally:
            self.conn.rollback()

    def scalar(self, sql):
        return self.run(sql)[1][0][0]

    def close(self):
        try:
            self.conn.close()
        except Exception:
            pass


# ======================================================================= build context
class Build:
    def __init__(self, mode):
        self.mode = mode
        self.blockers = []        # (kind, item, message EN, message TH)
        self.warnings = []        # (item, message EN, message TH)
        self.notes = []           # Thai lines for the report
        self.changes = []         # generated ITEM_CHANGES rows
        self.blank_cells = {}     # sheet -> count
        self.used_inputs = {}     # label -> sha256
        self.read_sql = set()     # sql_TESTONLY file names actually read
        self.refresh_rows = []
        self.mi_results = []
        self.fp_results = []      # fingerprint of every manifest instance
        self.gold_results = {}
        self.sweep = {"files": 0, "hits": []}
        self.sweep_sources = {}
        self.flags_recheck = []
        self.incomplete = []      # --check only: checks of --freeze that were skipped
        self.skipped_rows = []    # ITEM_CHANGES / TYPO_FIXES rows of dropped items (not applied)
        self.n_before_unverified = 0
        self.schema_results = {}  # instance -> status of the schema digest check
        self.out_dir_copies = []  # conflict copies of output names found in --out-dir

    def block(self, kind, item, msg, th):
        self.blockers.append((kind, item or "-", msg, th))

    def warn(self, item, msg, th):
        self.warnings.append((item or "-", msg, th))

    def change(self, iid, field, before, after, source, rule, status):
        self.changes.append({"id": iid, "field": field, "before": before, "after": after,
                             "source": source, "rule": rule, "status": status})


# ======================================================================= inputs
def parse_inputs(pairs):
    out = {}
    for p in pairs or []:
        if "=" not in p:
            raise Fatal("--input expects <label>=<path>")
        label, path = p.split("=", 1)
        label = label.strip()
        if label in out:
            raise Fatal(f"--input label given twice: {label}")
        out[label] = path
    return out


def verify_lib(dec, lib_dir):
    """grade_v13.py and vg_rule.py must equal the pins lib/<file> of ext_decisions.inputs"""
    pins = dec.get("inputs") or {}
    out = {}
    for label, fname in LIB_FILES.items():
        p = lib_dir / fname
        if not p.is_file():
            raise Fatal(f"{fname} not found in the library directory")
        if label not in pins:
            raise Fatal(f"ext_decisions.inputs has no sha256 for '{label}'")
        got = sha256_file(p)
        if got != pins[label]:
            raise Fatal(f"sha256 of '{label}' differs from the pin in ext_decisions "
                        f"(pinned {pins[label][:16]}..., found {got[:16]}...)")
        out[label] = got
    return out


def verify_inputs(b, decisions, given):
    pins = decisions.get("inputs") or {}
    missing = [lab for lab in REQUIRED_LABELS if lab not in given]
    if missing:
        raise Fatal("required --input label(s) not given: " + ", ".join(missing))
    unknown = [lab for lab in given if lab not in REQUIRED_LABELS]
    if unknown:
        raise Fatal("unknown --input label(s): " + ", ".join(sorted(unknown)))
    for lab in REQUIRED_LABELS:
        path = Path(given[lab])
        if lab == SQL_DIR_LABEL:
            if not path.is_dir():
                raise Fatal(f"input '{lab}' is not a directory")
            b.used_inputs[lab] = tree_digest(path)
            continue
        if not path.is_file():
            raise Fatal(f"input '{lab}' does not exist")
        if lab not in pins:
            raise Fatal(f"ext_decisions.inputs has no sha256 for '{lab}'")
        got = sha256_file(path)
        if got != pins[lab]:
            raise Fatal(f"sha256 of input '{lab}' differs from the pin in ext_decisions "
                        f"(pinned {pins[lab][:16]}..., found {got[:16]}...)")
        b.used_inputs[lab] = got
    sql_dir = Path(given[SQL_DIR_LABEL])
    for key, pin in sorted(pins.items()):
        if not key.startswith(SQL_DIR_LABEL + "/"):
            continue
        fp = sql_dir / key.split("/", 1)[1]
        if not fp.is_file():
            raise Fatal(f"pinned input '{key}' not found in the {SQL_DIR_LABEL} directory")
        got = sha256_file(fp)
        if got != pin:
            raise Fatal(f"sha256 of input '{key}' differs from the pin "
                        f"(pinned {pin[:16]}..., found {got[:16]}...)")
    extra_pins = sorted(set(k for k in pins if not k.startswith(SQL_DIR_LABEL + "/"))
                        - set(REQUIRED_LABELS) - set(LIB_FILES) - {SQL_DIR_LABEL})
    if extra_pins:
        raise Fatal("ext_decisions.inputs has unknown label(s): " + ", ".join(extra_pins))
    if SQL_DIR_LABEL in pins:
        raise Fatal(f"ext_decisions.inputs pins the folder '{SQL_DIR_LABEL}'; pin each file as {SQL_DIR_LABEL}/<file>")


def read_pinned_sql(b, decisions, given, name):
    key = f"{SQL_DIR_LABEL}/{name}"
    pins = decisions.get("inputs") or {}
    if key not in pins:
        raise Fatal(f"decision refers to '{key}' which is not pinned in ext_decisions.inputs")
    text = (Path(given[SQL_DIR_LABEL]) / name).read_text(encoding="utf-8")
    b.read_sql.add(name)
    b.used_inputs[key] = pins[key]
    return text


def check_decisions_schema(dec):
    need = ["format", "inputs", "final40", "reserves", "dropped", "reserve_rule", "directional",
            "reserve_directional", "mi_rule", "mi_items", "single_instance_items", "fk1_format",
            "x33_en", "en_literal", "author_approved", "expected", "other_decisions",
            "conditional_alt_gold_th", "th_keep_blockers", "author_class_rule", "ai_drafted",
            "workbook_overrides"]
    miss = [k for k in need if k not in dec]
    if miss:
        raise Fatal("ext_decisions lacks field(s): " + ", ".join(miss))
    if dec["format"] != "kst-ext-decisions-1":
        raise Fatal("ext_decisions.format is not kst-ext-decisions-1")
    # layout (types the builder relies on); a wrong type makes any build meaningless
    shapes = {"final40": list, "reserves": list, "dropped": list, "directional": list, "reserve_directional": list,
              "mi_items": list, "single_instance_items": list, "en_literal": dict, "expected": dict,
              "other_decisions": dict, "conditional_alt_gold_th": list, "th_keep_blockers": dict,
              "author_class_rule": list, "ai_drafted": dict, "workbook_overrides": list, "inputs": dict}
    bad = [k for k, t in shapes.items() if not isinstance(dec[k], t)]
    if bad:
        raise Fatal("ext_decisions field(s) of the wrong type: " + ", ".join(bad))
    for k in ("family", "tier", "vg"):
        if not isinstance(dec["expected"].get(k), list if k == "vg" else dict):
            raise Fatal(f"ext_decisions.expected.{k} is missing or of the wrong type")
    for no, entry in dec["other_decisions"].items():
        if not isinstance(entry, dict) or not isinstance(entry.get("options"), dict) \
                or not all(isinstance(v, dict) for v in entry["options"].values()):
            raise Fatal(f"ext_decisions.other_decisions.{no} needs an 'options' table of effect objects")
    for k, rule in enumerate(dec["conditional_alt_gold_th"]):
        if not isinstance(rule, dict) or not all(isinstance(rule.get(f), str) and rule.get(f) for f in ("id", "sql")):
            raise Fatal(f"ext_decisions.conditional_alt_gold_th[{k}] needs 'id' and 'sql'")
    for k, rule in enumerate(dec["author_class_rule"]):
        if not isinstance(rule, dict) or not isinstance(rule.get("workbook_author_contains"), str):
            raise Fatal(f"ext_decisions.author_class_rule[{k}] needs 'workbook_author_contains' and 'class'")
    for k, o in enumerate(dec["workbook_overrides"]):
        if not isinstance(o, dict) or not isinstance(o.get("id"), str):
            raise Fatal(f"ext_decisions.workbook_overrides[{k}] needs 'id'")


def validate_decisions(b, dec):
    """values of ext_decisions (design 2.8 and 3.2); every problem is a blocker of the decisions"""
    final40, reserves = list(dec["final40"]), list(dec["reserves"])
    known = set(final40) | set(reserves)

    def bad(item, en, th):
        en, th = "ext_decisions: " + en, "ext_decisions: " + th
        b.block("decision", item, en, th)

    if dec.get("x33_en") != "keep":
        bad("X33", f"x33_en is '{dec.get('x33_en')}', the only legal value is 'keep' (design 2.8 rule 3)",
            f"x33_en มีค่า '{dec.get('x33_en')}' ค่าที่อนุญาตมีเพียง 'keep' (แบบงานหัวข้อ 2.8 ข้อ 3)")
    rule = dec.get("reserve_rule")
    if not isinstance(rule, str) or not rule.strip():
        bad("-", "reserve_rule is empty (AMENDMENT-9 quotes it verbatim)",
            "reserve_rule ว่าง (AMENDMENT-9 ต้องอ้างข้อความนี้ทุกตัวอักษร)")
    elif reserves and ", ".join(reserves) not in rule:
        bad("-", "the order of reserves (" + ", ".join(reserves) + ") is not the order written in reserve_rule "
            "(fallback_rank of the reserves file comes from that list)",
            "ลำดับใน reserves (" + ", ".join(reserves) + ") ไม่ตรงกับลำดับที่เขียนใน reserve_rule "
            "(fallback_rank ของไฟล์ข้อสำรองมาจากรายการนี้)")
    ai = dec["ai_drafted"].get("value")
    if ai not in AI_DRAFTED_VALUES:
        bad("-", f"ai_drafted.value '{ai}' is not one of {', '.join(AI_DRAFTED_VALUES)} (design 3.2)",
            f"ค่า ai_drafted.value '{ai}' ไม่อยู่ในค่าที่อนุญาต {', '.join(AI_DRAFTED_VALUES)} (แบบงานหัวข้อ 3.2)")
    for k, r in enumerate(dec["author_class_rule"]):
        if r.get("class") not in AUTHOR_CLASSES:
            bad("-", f"author_class_rule[{k}].class '{r.get('class')}' is not one of {', '.join(AUTHOR_CLASSES)}",
                f"author_class_rule[{k}].class '{r.get('class')}' ไม่อยู่ในค่าที่อนุญาต {', '.join(AUTHOR_CLASSES)}")
        if not r["workbook_author_contains"].strip():
            bad("-", f"author_class_rule[{k}].workbook_author_contains is empty (it would match every item)",
                f"author_class_rule[{k}].workbook_author_contains ว่าง (จะตรงกับทุกข้อ)")
    for iid in dec["en_literal"]:
        if iid not in known:
            bad(iid, "en_literal names an id outside final40/reserves", "en_literal อ้าง id ที่อยู่นอก final40/reserves")
    for no, entry in sorted(dec["other_decisions"].items()):
        for opt, eff in sorted(entry["options"].items()):
            where = f"other_decisions.{no}.options.{opt}"
            for key, val in sorted(eff.items()):
                if key in EFFECT_LIST_KEYS:
                    ids = val if isinstance(val, list) else None
                elif key in EFFECT_MAP_KEYS:
                    ids = list(val) if isinstance(val, dict) and all(isinstance(x, str) for x in val.values()) else None
                else:
                    bad(f"#{no}", f"{where}: unknown effect key '{key}' (known: "
                        + ", ".join(EFFECT_LIST_KEYS + EFFECT_MAP_KEYS) + ")",
                        f"{where}: ไม่รู้จัก effect '{key}' (ที่รู้จักได้แก่ " + ", ".join(EFFECT_LIST_KEYS + EFFECT_MAP_KEYS) + ")")
                    continue
                if ids is None:
                    bad(f"#{no}", f"{where}.{key} has the wrong type", f"{where}.{key} มีชนิดข้อมูลผิด")
                    continue
                outside = sorted(set(map(str, ids)) - known)
                if outside:
                    bad(f"#{no}", f"{where}.{key} names id(s) outside final40/reserves: " + ", ".join(outside),
                        f"{where}.{key} อ้าง id ที่อยู่นอก final40/reserves: " + ", ".join(outside))
    for rule_ in dec["conditional_alt_gold_th"]:
        if rule_["id"] not in known:
            bad(rule_["id"], "conditional_alt_gold_th names an id outside final40/reserves",
                "conditional_alt_gold_th อ้าง id ที่อยู่นอก final40/reserves")
        if rule_.get("when_th_decision") not in TH_VOCAB:
            bad(rule_["id"], f"conditional_alt_gold_th.when_th_decision '{rule_.get('when_th_decision')}' is not a "
                "decision value of the TH sheet",
                f"conditional_alt_gold_th.when_th_decision '{rule_.get('when_th_decision')}' ไม่ใช่ค่าการตัดสินของชีต TH")
    for iid in dec["th_keep_blockers"]:
        if iid not in known:
            bad(iid, "th_keep_blockers names an id outside final40/reserves", "th_keep_blockers อ้าง id ที่อยู่นอก final40/reserves")
    for key, pool, pool_name in (("directional", final40, "final40"), ("reserve_directional", reserves, "reserves"),
                                 ("mi_items", final40, "final40"), ("single_instance_items", final40, "final40")):
        outside = sorted(set(dec[key]) - set(pool))
        if outside:
            bad("-", f"{key} names id(s) outside {pool_name}: " + ", ".join(outside),
                f"{key} อ้าง id ที่อยู่นอก {pool_name}: " + ", ".join(outside))
    for o in dec["workbook_overrides"]:
        if o.get("status") not in OVERRIDE_STATUSES:
            bad(o["id"], f"workbook_overrides status '{o.get('status')}' is not one of {', '.join(OVERRIDE_STATUSES)}",
                f"สถานะ '{o.get('status')}' ใน workbook_overrides ไม่อยู่ในค่าที่อนุญาต {', '.join(OVERRIDE_STATUSES)}")
        if not str(o.get("ref") or "").strip():
            bad(o["id"], "workbook_overrides entry has no master log reference ('ref')",
                "รายการใน workbook_overrides ไม่มีการอ้างอิง master log ('ref')")
    if dec.get("author_approved") is True:
        appr = dec.get("approval") if isinstance(dec.get("approval"), dict) else {}
        missing = [k for k in ("approved_at_ict", "master_log_ref") if not str(appr.get(k) or "").strip()]
        if missing:
            b.block("approval", "-", "ext_decisions: author_approved is true but approval." + " and approval.".join(missing)
                    + " is empty (the assistant records the time and the master log reference with the approval)",
                    "ext_decisions: author_approved เป็น true แต่ approval." + " และ approval.".join(missing)
                    + " ว่าง (ผู้ช่วยต้องบันทึกวันเวลาและการอ้างอิง master log พร้อมการอนุมัติ)")


# ======================================================================= items
def load_workbook_items(b, sel_book):
    items = {}
    order = []
    for sheet in SEL_ITEM_SHEETS:
        recs = sheet_records(sel_book, sheet, [H_ID, H_FAMILY, H_TIER, H_EN, H_GOLD, H_TH,
                                               H_SEL_DECISION, H_SEL_EN_EDIT])
        for r in recs:
            iid = cell_str(r.get(H_ID)).strip()
            if not iid:
                continue
            if iid in items:
                raise Fatal(f"item {iid} appears twice in the selection workbook")
            author = cell_str(r.get(H_AUTHOR_A) if H_AUTHOR_A in r else r.get(H_AUTHOR_B))
            items[iid] = {
                "id": iid, "sheet": sheet,
                "family": family_of(r.get(H_FAMILY)), "tier": tier_of(r.get(H_TIER)),
                "source_raw": cell_str(r.get(H_SOURCE)).strip(),
                "rank_raw": cell_str(r.get(H_RANK)).strip(),
                "author_raw": author.strip(),
                "en": cell_str(r.get(H_EN)), "th": cell_str(r.get(H_TH)),
                "gold": cell_str(r.get(H_GOLD)),
                "wb_decision": cell_str(r.get(H_SEL_DECISION)).strip(),
                "en_edit": cell_str(r.get(H_SEL_EN_EDIT)).strip(),
            }
            order.append(iid)
    return items, order


def check_membership(b, dec, wb_items):
    final40, reserves, dropped = dec["final40"], dec["reserves"], dec["dropped"]
    if len(final40) != 40 or len(set(final40)) != 40:
        b.block("decision", "-", "ext_decisions.final40 must list 40 distinct ids",
                "ext_decisions.final40 ต้องมี id ที่ไม่ซ้ำกัน 40 รายการ")
    if len(set(reserves)) != len(reserves):
        b.block("decision", "-", "ext_decisions.reserves has duplicates", "ext_decisions.reserves มี id ซ้ำ")
    overlap = (set(final40) & set(reserves)) | (set(final40) & set(dropped)) | (set(reserves) & set(dropped))
    if overlap:
        b.block("decision", ",".join(sorted(overlap)), "id listed in more than one of final40/reserves/dropped",
                "id อยู่ในรายการ final40/reserves/dropped มากกว่าหนึ่งรายการ")
    for iid in final40 + reserves:
        if QID_CORE_RE.match(iid):
            b.block("decision", iid, "extension id collides with the core id space Q01-Q60",
                    "id ของชุดขยายชนกับช่วง id ของชุดหลัก Q01-Q60")
        if iid not in wb_items:
            b.block("decision", iid, "id not found in the selection workbook", "ไม่พบ id นี้ใน workbook การคัดเลือก")
    covered = set(final40) | set(reserves) | set(dropped)
    for iid in wb_items:
        if iid not in covered:
            b.block("decision", iid, "workbook item is neither in final40, reserves nor dropped",
                    "ข้อใน workbook ไม่อยู่ใน final40, reserves หรือ dropped")
    # workbook decision cells versus the recorded overrides (C12)
    status = {i: "final" for i in final40}
    status.update({i: "reserve" for i in reserves})
    status.update({i: "dropped" for i in dropped})
    ov = {o["id"]: o for o in dec.get("workbook_overrides", [])}
    for iid, it in wb_items.items():
        cell = it["wb_decision"]
        implied = {"อนุมัติ": "final", "ตัด": "dropped"}.get(cell, "undecided" if not cell else "other")
        if implied != status.get(iid):
            o = ov.get(iid)
            if o is None:
                b.block("decision", iid, f"workbook decision cell '{cell or '(blank)'}' differs from "
                        f"ext_decisions ({status.get(iid)}) and no override is recorded",
                        f"ช่องการตัดสินใน workbook ('{cell or '(ว่าง)'}') ไม่ตรงกับ ext_decisions ({status.get(iid)}) "
                        "และไม่มี override ที่บันทึกไว้")
            elif o.get("workbook_value", "") != cell:
                b.block("decision", iid, "recorded override does not match the workbook decision cell",
                        "override ที่บันทึกไม่ตรงกับช่องการตัดสินใน workbook")
            elif o.get("status") != status.get(iid):
                b.block("decision", iid, "recorded override status differs from final40/reserves/dropped",
                        "สถานะใน override ที่บันทึกไม่ตรงกับ final40/reserves/dropped")
    for iid, o in ov.items():
        if iid not in wb_items:
            b.block("decision", iid, "override for an id that is not in the workbook",
                    "มี override ของ id ที่ไม่อยู่ใน workbook")


def cross_check_items_json(b, items_json, wb_items, ids):
    for iid in ids:
        it, j = wb_items.get(iid), items_json.get(iid)
        if it is None:
            continue
        if j is None:
            b.block("input", iid, "items.json has no entry for this id", "items.json ไม่มีรายการของ id นี้")
            continue
        for wk, jk in (("en", "en"), ("th", "th"), ("gold", "gold")):
            if (it[wk] or "") != (j.get(jk) or ""):
                b.block("input", iid, f"items.json '{jk}' differs from the selection workbook",
                        f"ค่า '{jk}' ใน items.json ไม่ตรงกับ workbook การคัดเลือก")
        if family_of(j.get("family")) != it["family"] or tier_of(j.get("tier")) != it["tier"]:
            b.block("input", iid, "items.json family/tier differs from the selection workbook",
                    "family/tier ใน items.json ไม่ตรงกับ workbook การคัดเลือก")


def apply_item_changes(b, rows, cur, label, stage_filter, wb_items):
    """ITEM_CHANGES rows of the 'workbook' stage: value == after -> already in the workbook;
    value == before -> applied; otherwise blocker. A row whose id is not in the selection workbook is a
    blocker; a row of a dropped item is skipped. For a row already in the workbook the builder can only check
    that 'before' is filled and differs from 'after': the old value itself is gone from the workbook, so the
    'before' values of the pinned files are checked once against the 13 Oct draft in Gate 0 (test EX-T7g)."""
    pending = []
    for n, r in enumerate(rows, 2):
        iid, field = (r.get("id") or "").strip(), (r.get("field") or "").strip()
        stage = (r.get("applied_at") or "workbook").strip() or "workbook"
        src = f"{label}:row{n}"
        if iid not in wb_items:
            b.block("input", iid or "-", f"{src}: id '{iid}' is not in the selection workbook",
                    f"{src}: id '{iid}' ไม่อยู่ใน workbook การคัดเลือก")
            continue
        if stage not in ("workbook", "decision"):
            b.block("input", iid, f"{src}: unknown applied_at '{stage}'", f"{src}: ค่า applied_at '{stage}' ไม่รู้จัก")
            continue
        if stage != stage_filter:
            pending.append((n, r))
            continue
        if iid not in cur:
            b.skipped_rows.append(src)
            continue
        key = {"question_en": "en", "question_th": "th", GOLD_FIELD: "gold"}.get(field)
        if key is None:
            b.block("input", iid, f"{src}: unknown field '{field}'", f"{src}: field '{field}' ไม่รู้จัก")
            continue
        before, after = r.get("before") or "", r.get("after") or ""
        val = cur[iid][key]
        same = (lambda x, y: norm_sql(x) == norm_sql(y)) if key == "gold" else (lambda x, y: x.strip() == y.strip())
        if same(val, after):
            if not before.strip() or same(before, after):
                b.block("input", iid, f"{src}: 'before' of {field} is blank or equal to 'after' (the audit row records no change)",
                        f"{src}: ค่า 'before' ของ {field} ว่างหรือเท่ากับ 'after' (แถว audit ไม่ได้บันทึกการเปลี่ยนแปลง)")
            b.n_before_unverified += 1
            b.change(iid, field, before if key != "gold" else norm_sql(before), after if key != "gold" else norm_sql(after),
                     src, "ITEM_CHANGES (value already in the workbook)", "already_in_workbook")
        elif same(val, before):
            cur[iid][key] = after
            b.change(iid, field, before if key != "gold" else norm_sql(before), after if key != "gold" else norm_sql(after),
                     src, "ITEM_CHANGES applied", "applied")
        else:
            b.block("input", iid, f"{src}: workbook value of {field} equals neither 'before' nor 'after'",
                    f"{src}: ค่า {field} ใน workbook ไม่เท่ากับทั้ง 'before' และ 'after'")
    return pending


def apply_typo_fixes(b, rows, cur, wb_items):
    for n, r in enumerate(rows, 2):
        iid = (r.get("id") or "").strip()
        if iid not in wb_items:
            b.block("input", iid or "-", f"typo_fixes:row{n}: id '{iid}' is not in the selection workbook",
                    f"typo_fixes:row{n}: id '{iid}' ไม่อยู่ใน workbook การคัดเลือก")
            continue
        if iid not in cur:
            b.skipped_rows.append(f"typo_fixes:row{n}")
            continue
        before, after = r.get("th_before") or "", r.get("th_after") or ""
        val = cur[iid]["th"]
        if val == after:
            b.change(iid, "question_th", before, after, f"typo_fixes:row{n}", "TYPO_FIXES (already applied)", "already_in_workbook")
        elif val == before:
            cur[iid]["th"] = after
            b.change(iid, "question_th", before, after, f"typo_fixes:row{n}", "TYPO_FIXES applied before the decisions", "applied")
        else:
            b.block("input", iid, f"typo_fixes:row{n}: workbook TH equals neither th_before nor th_after",
                    f"typo_fixes:row{n}: TH ใน workbook ไม่เท่ากับทั้ง th_before และ th_after")


def _en_blank(b, iid):
    b.block("decision", iid, f"'{TF_EN_SHEET}': decision cell is blank", f"ชีต '{TF_EN_SHEET}': ช่องการตัดสินว่าง")


def _en_unknown(b, iid, raw):
    b.block("decision", iid, f"'{TF_EN_SHEET}': unknown decision value '{raw}'",
            f"ชีต '{TF_EN_SHEET}': ค่าการตัดสิน '{raw}' ไม่รู้จัก")


def _en_own_blank(b, iid):
    b.block("decision", iid, f"'{TF_EN_SHEET}': 'แก้เอง' but column 'EN ที่ใช้' is blank",
            f"ชีต '{TF_EN_SHEET}': เลือก 'แก้เอง' แต่คอลัมน์ 'EN ที่ใช้' ว่าง")


def apply_translation_fixes(b, dec, tf_book, cur, mode, given, decisions_obj):
    final40, reserves = dec["final40"], dec["reserves"]
    known = set(final40) | set(reserves)
    th_dec, en_dec = {}, {}
    # ------------------------------------------------ 'แก้ TH'
    recs = sheet_records(tf_book, TF_TH_SHEET, [H_ID, TFH_TH_CUR, TFH_TH_PROP, TFH_TH_OWN, TFH_DECISION])
    blanks = 0
    th_rows = {}
    for r in recs:
        iid = cell_str(r.get(H_ID)).strip()
        if not iid:
            continue
        if iid not in known:
            b.block("decision", iid, f"'{TF_TH_SHEET}' row for an id outside final40/reserves",
                    f"ชีต '{TF_TH_SHEET}' มีแถวของ id ที่อยู่นอก final40/reserves")
            continue
        if iid in th_rows:
            b.block("decision", iid, f"'{TF_TH_SHEET}' has two rows for this id", f"ชีต '{TF_TH_SHEET}' มีสองแถวของ id นี้")
            continue
        th_rows[iid] = r
        raw = cell_str(r.get(TFH_DECISION)).strip()
        if not raw:
            blanks += 1
        th_dec[iid] = raw
    b.blank_cells[TF_TH_SHEET] = blanks
    # ------------------------------------------------ 'ตัด EN'
    recs = sheet_records(tf_book, TF_EN_SHEET, [H_ID, TFH_EN_CUR, TFH_EN_PROP, TFH_EN_OWN, TFH_DECISION])
    blanks = 0
    en_rows = {}
    for r in recs:
        iid = cell_str(r.get(H_ID)).strip()
        if not iid:
            continue
        if iid not in known:
            b.block("decision", iid, f"'{TF_EN_SHEET}' row for an id outside final40/reserves",
                    f"ชีต '{TF_EN_SHEET}' มีแถวของ id ที่อยู่นอก final40/reserves")
            continue
        if iid in en_rows:
            b.block("decision", iid, f"'{TF_EN_SHEET}' has two rows for this id", f"ชีต '{TF_EN_SHEET}' มีสองแถวของ id นี้")
            continue
        en_rows[iid] = r
        raw = cell_str(r.get(TFH_DECISION)).strip()
        if not raw:
            blanks += 1
        en_dec[iid] = raw
    b.blank_cells[TF_EN_SHEET] = blanks
    # ------------------------------------------------ 'ตัดสินอื่น'
    recs = sheet_records(tf_book, TF_OTHER_SHEET, [TFH_OTHER_NO, TFH_DECISION, TFH_OTHER_REC])
    blanks = 0
    other = {}
    for r in recs:
        no = cell_str(r.get(TFH_OTHER_NO)).strip()
        if not no:
            continue
        if no in other:
            b.block("decision", f"#{no}", f"'{TF_OTHER_SHEET}' has two rows #{no}",
                    f"ชีต '{TF_OTHER_SHEET}' มีสองแถวของข้อ #{no} (มติขัดกันหรือซ้ำ)")
            continue
        val = parse_option(r.get(TFH_DECISION))
        if val is None:
            blanks += 1
            rec = parse_option(r.get(TFH_OTHER_REC))
            other[no] = {"value": None, "draft_value": rec}
        else:
            other[no] = {"value": val, "draft_value": val}
    b.blank_cells[TF_OTHER_SHEET] = blanks
    table = dec["other_decisions"]
    for no in sorted(set(table) | set(other), key=lambda x: int(x) if x.isdigit() else 99):
        if no not in other:
            b.block("decision", f"#{no}", f"'{TF_OTHER_SHEET}' has no row #{no}",
                    f"ชีต '{TF_OTHER_SHEET}' ไม่มีแถวของข้อ #{no}")
        elif no not in table:
            b.block("decision", f"#{no}", f"'{TF_OTHER_SHEET}' row #{no} has no entry in ext_decisions.other_decisions",
                    f"แถวข้อ #{no} ของชีต '{TF_OTHER_SHEET}' ไม่มีรายการใน ext_decisions.other_decisions")

    # effects of the other decisions
    effects = {"require_th_rows": set(), "forbid_th_keep": set(), "forbid_th_change": set(),
               "require_en_rows": set(), "forbid_en_keep": set(), "add_alt_gold_th": {},
               "set_gold_from_sql": {}}
    for no, d in sorted(other.items()):
        if no not in table:
            continue
        val = d["value"]
        if val is None:
            b.block("decision", f"#{no}", f"'{TF_OTHER_SHEET}' #{no}: decision cell is blank",
                    f"ชีต '{TF_OTHER_SHEET}' ข้อ #{no}: ช่องการตัดสินว่าง")
            val = d["draft_value"]
            if val is None or val not in table[no]["options"]:
                continue
            b.warn(f"#{no}", "DRAFT uses the recommended option of the sheet",
                   "ฉบับ DRAFT ใช้ทางเลือกที่ผู้ช่วยแนะนำในชีตแทนช่องที่ว่าง")
        opts = table[no]["options"]
        if val not in opts:
            b.block("decision", f"#{no}", f"'{TF_OTHER_SHEET}' #{no}: value '{val}' is not a known option",
                    f"ชีต '{TF_OTHER_SHEET}' ข้อ #{no}: ค่า '{val}' ไม่ใช่ทางเลือกที่รู้จัก")
            continue
        eff = opts[val]
        for k in ("require_th_rows", "forbid_th_keep", "forbid_th_change", "require_en_rows", "forbid_en_keep"):
            effects[k].update(eff.get(k, []))
        effects["add_alt_gold_th"].update(eff.get("add_alt_gold_th", {}))
        effects["set_gold_from_sql"].update(eff.get("set_gold_from_sql", {}))
        b.notes.append(f"ตัดสินอื่น #{no} = {val}")

    # ------------------------------------------------ TH decisions
    th_mode = {}
    for iid in final40 + reserves:
        r = th_rows.get(iid)
        if r is None:
            th_mode[iid] = "norow"
            continue
        cur_th = cell_str(r.get(TFH_TH_CUR))
        if cur_th != cur[iid]["th"]:
            b.block("decision", iid, f"'{TF_TH_SHEET}': '{TFH_TH_CUR}' differs from the workbook TH after TYPO_FIXES",
                    f"ชีต '{TF_TH_SHEET}': คอลัมน์ '{TFH_TH_CUR}' ไม่ตรงกับ TH ของ workbook หลังใช้ TYPO_FIXES")
        raw = th_dec[iid]
        kind = TH_VOCAB.get(raw)
        prop = cell_str(r.get(TFH_TH_PROP)).strip()
        own = cell_str(r.get(TFH_TH_OWN)).strip()
        src = f"translation_fixes_xlsx:{TF_TH_SHEET}:{iid}"
        if not raw:
            b.block("decision", iid, f"'{TF_TH_SHEET}': decision cell is blank", f"ชีต '{TF_TH_SHEET}': ช่องการตัดสินว่าง")
            kind = "proposed_draft"
        elif kind is None:
            b.block("decision", iid, f"'{TF_TH_SHEET}': unknown decision value '{raw}'",
                    f"ชีต '{TF_TH_SHEET}': ค่าการตัดสิน '{raw}' ไม่รู้จัก")
            th_mode[iid] = "unknown"
            continue
        before = cur[iid]["th"]
        if kind in ("proposed", "proposed_draft"):
            new = prop
        elif kind == "own":
            new = own
            if not own:
                b.block("decision", iid, f"'{TF_TH_SHEET}': 'ใช้ถ้อยคำของฉัน' but the own-wording cell is blank",
                        f"ชีต '{TF_TH_SHEET}': เลือก 'ใช้ถ้อยคำของฉัน' แต่ช่อง TH ที่ใช้ว่าง")
                new = prop
            else:
                b.flags_recheck.append(iid)
        else:
            new = before.strip()
        th_mode[iid] = kind
        if new != before:
            cur[iid]["th"] = new
            b.change(iid, "question_th", before, new, src,
                     {"proposed": "TH decision: use the proposal", "own": "TH decision: author's own wording",
                      "keep": "TH decision: keep (outer spaces trimmed)",
                      "proposed_draft": "DRAFT: blank decision replaced by the proposal"}[kind], "applied")
    for iid in sorted(effects["require_th_rows"]):
        if th_mode.get(iid) == "norow":
            b.block("decision", iid, f"a decision in '{TF_OTHER_SHEET}' requires a row in '{TF_TH_SHEET}'",
                    f"มติในชีต '{TF_OTHER_SHEET}' ต้องมีแถวของข้อนี้ในชีต '{TF_TH_SHEET}'")
    for iid in sorted(effects["forbid_th_keep"]):
        if th_mode.get(iid) in ("keep", "norow"):
            b.block("decision", iid, f"TH must change under the decisions in '{TF_OTHER_SHEET}', but it is kept",
                    f"มติในชีต '{TF_OTHER_SHEET}' กำหนดให้แก้ TH แต่ TH คงเดิม")
    for iid in sorted(effects["forbid_th_change"]):
        if th_mode.get(iid) not in ("keep", "norow"):
            b.block("decision", iid, f"TH must stay unchanged under the decisions in '{TF_OTHER_SHEET}'",
                    f"มติในชีต '{TF_OTHER_SHEET}' กำหนดให้คง TH แต่ TH ถูกแก้")
    for iid, why in sorted(dec["th_keep_blockers"].items()):
        if th_mode.get(iid) in ("keep", "norow"):
            b.block("decision", iid, "TH kept although it asks a different question: " + why,
                    "TH คงเดิมทั้งที่ถามคนละคำถามกับ gold: " + why)

    # ------------------------------------------------ EN decisions
    en_lit = dec.get("en_literal") or {}
    x33_keep = dec.get("x33_en") == "keep"
    for iid in final40 + reserves:
        r = en_rows.get(iid)
        src = f"translation_fixes_xlsx:{TF_EN_SHEET}:{iid}"
        before = cur[iid]["en"]
        raw = en_dec.get(iid, "")
        own = cell_str(r.get(TFH_EN_OWN)).strip() if r is not None else ""
        if r is not None and cell_str(r.get(TFH_EN_CUR)) != before:
            b.block("decision", iid, f"'{TF_EN_SHEET}': '{TFH_EN_CUR}' differs from the workbook EN after ITEM_CHANGES",
                    f"ชีต '{TF_EN_SHEET}': คอลัมน์ '{TFH_EN_CUR}' ไม่ตรงกับ EN ของ workbook หลังใช้ ITEM_CHANGES")
        if iid in en_lit:
            # the literal text is the approved trim of this row; the row must record an agreeing decision
            lit = "" if is_blank(en_lit.get(iid)) else str(en_lit.get(iid))
            if r is None:
                b.block("decision", iid, f"ext_decisions.en_literal.{iid} is set, but '{TF_EN_SHEET}' has no row for this "
                        "id (the literal text has no recorded decision)",
                        f"มีข้อความใน ext_decisions.en_literal.{iid} แต่ชีต '{TF_EN_SHEET}' ไม่มีแถวของข้อนี้ "
                        "(ข้อความตามตัวอักษรไม่มีมติที่บันทึก)")
            elif not raw:
                _en_blank(b, iid)
            elif EN_VOCAB.get(raw) is None:
                _en_unknown(b, iid, raw)
            elif EN_VOCAB[raw] == "reject":
                b.block("decision", iid, f"'{TF_EN_SHEET}': decision '{EN_REJECT}' keeps the old EN, but "
                        f"ext_decisions.en_literal.{iid} replaces it (conflicting decisions)",
                        f"ชีต '{TF_EN_SHEET}': การตัดสิน '{EN_REJECT}' ให้คง EN เดิม แต่ ext_decisions.en_literal.{iid} "
                        "แทน EN (มติขัดกัน)")
            elif EN_VOCAB[raw] == "own" and not own:
                _en_own_blank(b, iid)
            if own and lit and own != lit.strip():
                b.block("decision", iid, f"'{TF_EN_SHEET}': column 'EN ที่ใช้' differs from ext_decisions.en_literal.{iid} "
                        "(conflicting decisions)",
                        f"ชีต '{TF_EN_SHEET}': คอลัมน์ 'EN ที่ใช้' ไม่ตรงกับ ext_decisions.en_literal.{iid} (มติขัดกัน)")
            if not lit:
                b.block("decision", iid, f"ext_decisions.en_literal.{iid} has no approved text",
                        f"ext_decisions.en_literal.{iid} ยังไม่มีข้อความที่ผู้เขียนอนุมัติ")
                continue
            if lit != before:
                cur[iid]["en"] = lit
                b.change(iid, "question_en", before, lit, f"ext_decisions:en_literal.{iid}",
                         "literal EN approved by the author (OQ34)", "applied")
            continue
        if iid == "X33" and x33_keep:
            if r is not None:
                if not raw:
                    _en_blank(b, iid)
                elif raw != EN_REJECT:
                    b.block("decision", iid, f"X33 EN is kept by ext_decisions.x33_en, but the '{TF_EN_SHEET}' decision "
                            f"is '{raw}' (only '{EN_REJECT}' agrees)",
                            f"ext_decisions.x33_en กำหนดให้คง EN ของ X33 แต่การตัดสินในชีต '{TF_EN_SHEET}' เป็น "
                            f"'{raw}' (ค่าที่สอดคล้องมีเพียง '{EN_REJECT}')")
                if own and own != before.strip():
                    b.block("decision", iid, "X33 EN is kept by ext_decisions.x33_en, but column 'EN ที่ใช้' holds "
                            "another text", "ext_decisions.x33_en กำหนดให้คง EN ของ X33 แต่คอลัมน์ 'EN ที่ใช้' "
                            "มีข้อความอื่น")
            continue
        if r is None:
            if iid in effects["require_en_rows"]:
                b.block("decision", iid, f"a decision in '{TF_OTHER_SHEET}' requires a row in '{TF_EN_SHEET}'",
                        f"มติในชีต '{TF_OTHER_SHEET}' ต้องมีแถวของข้อนี้ในชีต '{TF_EN_SHEET}'")
            continue
        kind = EN_VOCAB.get(raw)
        prop = cell_str(r.get(TFH_EN_PROP)).strip()
        if not raw:
            _en_blank(b, iid)
            kind = "approve_draft"
        elif kind is None:
            _en_unknown(b, iid, raw)
            continue
        if own:
            new, rule = own, "EN: column 'EN ที่ใช้' is filled and always wins"
            if kind == "reject":
                b.warn(iid, f"'{TF_EN_SHEET}': decision '{EN_REJECT}' but column 'EN ที่ใช้' is filled; the filled text "
                       "is used (design 2.8 rule 5)",
                       f"ชีต '{TF_EN_SHEET}': การตัดสิน '{EN_REJECT}' แต่คอลัมน์ 'EN ที่ใช้' มีข้อความ "
                       "จึงใช้ข้อความนั้นตามกฎข้อ 5 ของแบบงานหัวข้อ 2.8 (โปรดยืนยัน)")
        elif kind in ("approve", "approve_draft"):
            if THAI_RE.search(prop):
                if kind == "approve":
                    b.block("decision", iid, f"'{TF_EN_SHEET}': the approved proposal is not an EN text (Thai characters)",
                            f"ชีต '{TF_EN_SHEET}': ข้อเสนอที่อนุมัติไม่ใช่ข้อความ EN (มีอักษรไทย)")
                new, rule = before, "EN kept (proposal not usable)"
            else:
                new = prop
                rule = "EN decision: approve the proposal" if kind == "approve" else "DRAFT: blank decision replaced by the proposal"
        elif kind == "own":
            _en_own_blank(b, iid)
            new, rule = before, "EN kept (own wording missing)"
        else:
            new, rule = before, "EN decision: keep"
        if kind == "reject" and not own and iid in effects["forbid_en_keep"]:
            b.block("decision", iid, f"EN must change under the decisions in '{TF_OTHER_SHEET}', but it is kept",
                    f"มติในชีต '{TF_OTHER_SHEET}' กำหนดให้แก้ EN แต่ EN คงเดิม")
        if new != before:
            cur[iid]["en"] = new
            b.change(iid, "question_en", before, new, src, rule, "applied")

    # ------------------------------------------------ a blank decision cell always blocks (brief 1.4)
    total = sum(b.blank_cells.values())
    if total:
        detail = ", ".join(f"{k} {v}" for k, v in sorted(b.blank_cells.items()) if v)
        b.block("decision", "-", f"TRANSLATION_FIXES has {total} blank decision cell(s) ({detail}); a frozen suite "
                "needs every decision",
                f"TRANSLATION_FIXES มีช่องการตัดสินว่าง {total} ช่อง ({detail}); ฉบับตรึงต้องมีมติครบทุกช่อง")

    # ------------------------------------------------ gold replaced by a decision (FK1)
    for iid, fname in sorted(effects["set_gold_from_sql"].items()):
        if iid not in cur:
            continue
        text = read_pinned_sql(b, decisions_obj, given, fname)
        new = norm_sql(text)
        before = cur[iid]["gold"]
        if norm_sql(before) != new:
            cur[iid]["gold"] = new
            b.change(iid, GOLD_FIELD, norm_sql(before), new, f"{SQL_DIR_LABEL}/{fname}",
                     f"gold replaced under '{TF_OTHER_SHEET}' decision", "applied")
    return th_mode, en_dec, effects


def conditional_alts(b, dec, cur, th_mode, effects, given):
    alts = {iid: [] for iid in cur}
    for iid, fname in sorted(effects["add_alt_gold_th"].items()):
        if iid in alts:
            alts[iid].append(("decision", fname))
    for rule in dec["conditional_alt_gold_th"]:
        iid = rule["id"]
        if iid not in cur:
            continue
        want = rule.get("when_th_decision")
        mode = th_mode.get(iid)
        hit = (mode == TH_VOCAB.get(want)) or (want == "คงเดิม" and mode == "norow")
        lacks = rule.get("when_final_th_lacks")
        if hit and lacks:
            hit = lacks not in cur[iid]["th"]
        if hit:
            alts[iid].append(("conditional", rule["sql"]))
    out = {}
    for iid, lst in alts.items():
        sqls = []
        for why, fname in lst:
            text = read_pinned_sql(b, dec, given, fname)
            s = norm_sql(text)
            sqls.append(s)
            b.change(iid, "alt_gold_th", "", s, f"{SQL_DIR_LABEL}/{fname}",
                     "acceptance reading added (" + why + ")", "applied")
        out[iid] = sqls
    return out


def verify_decision_stage_changes(b, rows, pre, cur):
    for n, r in rows:
        iid, field = (r.get("id") or "").strip(), (r.get("field") or "").strip()
        if iid not in cur:
            continue
        key = {"question_en": "en", "question_th": "th", GOLD_FIELD: "gold"}.get(field)
        if key is None:
            b.block("input", iid, f"item_changes_add:row{n}: unknown field '{field}'",
                    f"item_changes_add:row{n}: field '{field}' ไม่รู้จัก")
            continue
        before, after = r.get("before") or "", r.get("after") or ""
        same = (lambda x, y: norm_sql(x) == norm_sql(y)) if key == "gold" else (lambda x, y: x.strip() == y.strip())
        if not same(pre[iid][key], before):
            b.block("input", iid, f"item_changes_add:row{n}: 'before' of {field} differs from the pre-decision value",
                    f"item_changes_add:row{n}: ค่า 'before' ของ {field} ไม่ตรงกับค่าก่อนใช้มติ")
        if not same(cur[iid][key], after):
            b.block("input", iid, f"item_changes_add:row{n}: 'after' of {field} differs from the value built from the decisions",
                    f"item_changes_add:row{n}: ค่า 'after' ของ {field} ไม่ตรงกับค่าที่สร้างจากมติ")
        else:
            b.change(iid, field, norm_sql(before) if key == "gold" else before,
                     norm_sql(after) if key == "gold" else after, f"item_changes_add:row{n}",
                     "audit row verified against the decisions", "verified")


# ======================================================================= anonymity sweep
def letter_boundary(pat):
    lb = "(?:(?<![A-Za-z])(?=[A-Za-z])|(?<=[A-Za-z])(?![A-Za-z]))"
    return pat.replace(r"\b", lb)


def runtime_identity_tokens():
    toks = set()
    try:
        toks.update(re.findall(r"[A-Za-z]{4,}", getpass.getuser()))
    except Exception:
        pass
    try:
        import pwd
        toks.update(re.findall(r"[A-Za-z]{4,}", pwd.getpwuid(os.getuid()).pw_gecos or ""))
    except Exception:
        pass
    try:
        toks.update(re.findall(r"[A-Za-z]{4,}", socket.gethostname().split(".")[0]))
    except Exception:
        pass
    try:
        toks.update(re.findall(r"[A-Za-z]{4,}", os.path.basename(os.path.expanduser("~"))))
    except Exception:
        pass
    return sorted({t.lower() for t in toks} - GENERIC_HOST_WORDS)


STUDENT_WORD = "\u0e19\u0e31\u0e01\u0e28\u0e36\u0e01\u0e29\u0e32"   # Thai word for 'student' (escaped so the source itself stays clean)
HOME_PATHS = "\\x2fUsers\\x2f|\\x2fhome\\x2f"                         # absolute home paths (escaped for the same reason)


def default_pattern_source():
    """the CLAUDE.md two folders above the project root; the project root is the nearest folder above
    this script that holds both harness/ and suite/ (harness/ in production, kst_rev/gate0/suite_tools/
    during Gate 0 resolve to the same root)"""
    here = Path(__file__).resolve().parent
    for anc in [here] + list(here.parents):
        if (anc / "harness").is_dir() and (anc / "suite").is_dir():
            return anc.parent.parent / "CLAUDE.md"
    return None


def claude_md_alternatives(path):
    """alternatives of the first back-quoted sweep pattern of a CLAUDE.md file; None when unreadable"""
    if path is None:
        return None
    try:
        text = Path(path).read_text(encoding="utf-8")
    except OSError:
        return None
    m = SWEEP_LINE_RE.search(text)
    if not m:
        return None
    alts = [x.strip() for x in m.group(1).split("|") if x.strip()]
    return alts or None


def claude_md_regex(alt):
    """as anon_sweep.py: an alternative written \\bX\\b gets letter boundaries, the others stay substrings"""
    m = re.fullmatch(r"\\b(.+?)\\b", alt)
    return LB_PRE + m.group(1) + LB_POST if m else alt


def build_sweep_patterns(pattern_files, extra, patterns_from):
    """(patterns, counts per source); no pattern text is ever written to an output"""
    pats = [("builtin", re.compile(EMAIL_RE)), ("builtin", re.compile(STUDENT_WORD)),
            ("builtin", re.compile(HOME_PATHS))]
    src = {"builtin": 3}
    toks = runtime_identity_tokens()
    for t in toks:
        pats.append(("runtime", re.compile(re.escape(t), re.I)))
    src["runtime"] = len(toks)
    alts = claude_md_alternatives(Path(patterns_from) if patterns_from else default_pattern_source())
    for alt in alts or []:
        pats.append(("claude_md", re.compile(claude_md_regex(alt), re.I)))
    src["claude_md"] = len(alts or [])
    n_file = 0
    for pf in pattern_files or []:
        for line in Path(pf).read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if s and not s.startswith("#"):
                pats.append(("file", re.compile(letter_boundary(s), re.I)))
                n_file += 1
    src["file"] = n_file
    lits = [x.strip() for e in (extra or []) for x in e.split(",") if x.strip()]
    for lit in lits:
        pats.append(("extra", re.compile(LB_PRE + re.escape(lit) + LB_POST, re.I)))
    src["extra"] = len(lits)
    return pats, src


def sweep_texts(b, named_texts, pats):
    for name, text in named_texts:
        b.sweep["files"] += 1
        for ln, line in enumerate(text.splitlines(), 1):
            for k, (kind, rx) in enumerate(pats):
                if rx.search(line):
                    b.sweep["hits"].append((name, ln, f"{kind}#{k}"))


# ======================================================================= database checks
def manifest_instance_dbs(manifest):
    """{instance name: dbname}"""
    out = {}
    for x in manifest.get("instances") or []:
        n = x.get("name") or x.get("dbname")
        if n:
            out[n] = x.get("dbname")
    return out


def fingerprint(eng, tables):
    """{table: (rows, md5)}: md5 over to_jsonb(row)::text sorted in C order -- the definition of
    grade_v13n.mi_fingerprint (design 3.5), which build_instances --record writes into the manifest"""
    out = {}
    for t in tables:
        if not FP_TABLE_RE.match(str(t)):
            raise ValueError("bad table name in fingerprint_tables")
        n, h = eng.run(f'SELECT COUNT(*), md5(COALESCE(string_agg(to_jsonb(r)::text, '
                       f'E\'\\n\' ORDER BY to_jsonb(r)::text COLLATE "C"), \'\')) '
                       f'FROM public."{t}" r')[1][0]
        out[t] = (int(n), str(h))
    return out


def fp_norm(v):
    if isinstance(v, dict):
        return int(v["rows"]), str(v["md5"])
    return int(v[0]), str(v[1])


def load_schema_stmt(manifest_path):
    """SCHEMA_STMT of db_fingerprint.py in the folder of the manifest (the single definition of the schema
    digest that build_instances.py records as schema_md5); (statement, '') or (None, reason)"""
    if not manifest_path:
        return None, "no manifest"
    p = Path(manifest_path).resolve().parent / "db_fingerprint.py"
    if not p.is_file():
        return None, "db_fingerprint.py not found next to the manifest"
    try:
        stmt = getattr(load_module(p, "_ext_db_fingerprint"), "SCHEMA_STMT", None)
    except Exception as e:
        return None, "db_fingerprint.py cannot be loaded (" + type(e).__name__ + ")"
    if not isinstance(stmt, str) or not stmt.strip():
        return None, "db_fingerprint.py has no SCHEMA_STMT"
    return stmt, ""


def check_fingerprints(b, manifest, pg, eng, base_db, schema_stmt=None, schema_why=""):
    """every recorded fingerprint (data) and schema_md5 (schema digest) of the manifest is recomputed on its
    database and compared"""
    tables = manifest.get("fingerprint_tables") or []
    schema_skipped = []
    for inst in manifest.get("instances") or []:
        name = inst.get("name") or inst.get("dbname")
        dbname = inst.get("dbname")
        rec = inst.get("fingerprint")
        rec_schema = inst.get("schema_md5")
        row = {"instance": name, "status": "unrecorded"}
        b.fp_results.append(row)
        b.schema_results[name] = "unrecorded" if not rec_schema else "not checked"
        want = None
        if rec:
            if not tables:
                row["status"] = "no fingerprint_tables"
                b.block("check", name, "manifest has recorded fingerprints but no fingerprint_tables",
                        "manifest มี fingerprint ที่บันทึกแล้วแต่ไม่มี fingerprint_tables")
            else:
                try:
                    want = {t: fp_norm(v) for t, v in rec.items()}
                except Exception:
                    row["status"] = "malformed"
                    b.block("check", name, "recorded fingerprint is malformed (expected {table: [rows, md5]})",
                            "fingerprint ที่บันทึกมีรูปแบบผิด (ต้องเป็น {table: [rows, md5]})")
        check_schema = bool(rec_schema) and schema_stmt is not None
        if rec_schema and schema_stmt is None:
            schema_skipped.append(name)
        if want is None and not check_schema:
            continue
        e2 = eng if dbname == base_db else None
        try:
            if e2 is None:
                e2 = Engine(dsn_with_db(pg, dbname))
            got = fingerprint(e2, tables) if want is not None else None
            got_schema = str(e2.run(schema_stmt)[1][0][0]) if check_schema else None
        except Exception as e:
            if want is not None:
                row["status"] = "error " + type(e).__name__
            if check_schema:
                b.schema_results[name] = "error " + type(e).__name__
            b.block("check", name, f"fingerprint or schema digest of instance {name} cannot be computed: {type(e).__name__}",
                    f"คำนวณ fingerprint หรือ schema digest ของ instance {name} ไม่ได้: {type(e).__name__}")
            continue
        finally:
            if e2 is not None and e2 is not eng:
                e2.close()
        if want is not None:
            diff = sorted(t for t in set(tables) | set(want) if want.get(t) != got.get(t))
            if diff:
                row["status"] = "mismatch " + ",".join(diff)
                b.block("check", name, f"fingerprint computed on the database of instance {name} differs from the "
                        f"fingerprint recorded in the manifest (table(s): {', '.join(diff)})",
                        f"fingerprint ที่คำนวณบนฐานของ instance {name} ไม่ตรงกับค่าที่บันทึกใน manifest "
                        f"(ตาราง: {', '.join(diff)})")
            else:
                row["status"] = "match"
        if check_schema:
            if got_schema == str(rec_schema):
                b.schema_results[name] = "match"
            else:
                b.schema_results[name] = "mismatch"
                b.block("check", name, f"schema digest computed on the database of instance {name} differs from the "
                        "schema_md5 recorded in the manifest",
                        f"schema digest ที่คำนวณบนฐานของ instance {name} ไม่ตรงกับ schema_md5 ที่บันทึกใน manifest")
    if schema_skipped:
        b.warn("-", "schema_md5 is recorded in the manifest but not rechecked by this builder (" + schema_why
               + "); build_instances.py checks it at Gate 1a step 1a.45: " + ", ".join(schema_skipped),
               "manifest มี schema_md5 ที่บันทึกแล้ว แต่ตัวสร้างไม่ได้ตรวจซ้ำ (" + schema_why
               + ") build_instances.py ตรวจค่านี้ใน Gate 1a ขั้น 1a.45: " + ", ".join(schema_skipped))


def run_db_checks(b, dec, cols_cfg, manifest, items, alts, pg, g13, vg, final40, reserves,
                  schema_stmt=None, schema_why=""):
    base_db = dbname_of(pg)
    eng = Engine(pg)
    try:
        b.notes.append("server_version ของฐานที่ใช้ตรวจ: " + str(eng.scalar("SHOW server_version")))
        b.notes.append("ฐานหลัก (--pg): " + str(base_db))

        def digest(rows):
            canon = sorted(tuple(g13.cv13(v) for v in r) for r in rows)
            return sha256_bytes(json.dumps(canon, ensure_ascii=False).encode("utf-8"))[:16]

        mi_items = set(manifest.get("items", {})) if manifest else set()
        for iid in final40 + reserves:
            it = items[iid]
            is_final = iid in final40

            def report(kind, item, en, th, _final=is_final):
                if _final:
                    b.block(kind, item, en, th)
                else:
                    b.warn(item, en, th)

            res = {"rows": None, "cols": None, "colnames": [], "error": None}
            b.gold_results[iid] = res
            raw = it["gold"]
            one = it["gold_one_line"]
            try:
                cols0, rows0 = eng.run(raw)
                cols1, rows1 = eng.run(one)
                cols2, rows2 = eng.run(one)
            except Exception as e:
                res["error"] = type(e).__name__
                report("check", iid, "gold does not run on the base database: " + type(e).__name__,
                       "gold รันบนฐานหลักไม่ได้: " + type(e).__name__)
                continue
            res.update(rows=len(rows1), cols=len(cols1), colnames=cols1)
            if digest(rows0) != digest(rows1) or len(cols0) != len(cols1):
                b.block("check", iid, "one-line gold gives a different result from the source gold",
                        "gold แบบบรรทัดเดียวให้ผลต่างจาก gold ต้นฉบับ")
            if digest(rows1) != digest(rows2):
                b.block("check", iid, "gold is not deterministic (two runs differ)", "gold ให้ผลไม่คงที่ (สองรอบได้ผลต่างกัน)")
            if g13.has_toplevel_order(one):
                b.block("check", iid, "gold has a top-level ORDER BY but the extension grades row order 'no'",
                        "gold มี ORDER BY ระดับบนสุด แต่ชุดขยายไม่ตรวจลำดับแถว (order no)")
            if not rows1:
                if iid in mi_items and manifest["items"][iid].get("empty_gold_on_base_ok"):
                    pass
                elif is_final:
                    b.block("check", iid, "gold is empty on the base database (D3 would exclude a non-MI item)",
                            "gold ว่างบนฐานหลัก (D3 จะตัดข้อที่ไม่ใช่ MI)")
                else:
                    b.warn(iid, "reserve gold is empty on the base database", "gold ของข้อสำรองว่างบนฐานหลัก")
            for k, alt in enumerate(alts.get(iid, []), 1):
                try:
                    ca, ra = eng.run(alt)
                    ca2, ra2 = eng.run(alt)
                except Exception as e:
                    b.block("check", iid, f"alternative {k} does not run: {type(e).__name__}",
                            f"alternative ที่ {k} รันไม่ได้: {type(e).__name__}")
                    continue
                if len(ca) != len(cols1):
                    b.block("check", iid, f"alternative {k} has {len(ca)} columns, primary has {len(cols1)}",
                            f"alternative ที่ {k} มี {len(ca)} คอลัมน์ แต่ primary มี {len(cols1)} คอลัมน์")
                if digest(ra) != digest(ra2):
                    b.block("check", iid, f"alternative {k} is not deterministic", f"alternative ที่ {k} ให้ผลไม่คงที่")
                b.notes.append(f"{iid} alternative ที่ {k}: {len(ra)}x{len(ca)} (primary {len(rows1)}x{len(cols1)})")
            # col_roles indices within the projection
            cr = it.get("col_roles", "")
            if cr and cr != "*":
                idx = [int(x) for g in cr.split(";") for x in g.split(",")]
                if max(idx) >= len(cols1):
                    b.block("check", iid, f"col_roles '{cr}' refers to a column outside the {len(cols1)}-column gold",
                            f"col_roles '{cr}' อ้างคอลัมน์ที่อยู่นอก gold ซึ่งมี {len(cols1)} คอลัมน์")
            # VG (final TH)
            lits = vg.value_grounding_literals(one, it["th"])
            it["vg_literals"] = lits
        # multi-instance items (an instance may carry "name" for the suite and "dbname" for the
        # connection, as in grade_v13n.mi_setup; without "name" the name is the dbname)
        if manifest:
            check_fingerprints(b, manifest, pg, eng, base_db, schema_stmt, schema_why)
            inst_db = manifest_instance_dbs(manifest)
            for iid in sorted(mi_items):
                spec = manifest["items"][iid]
                inst = spec.get("instances") or []
                if iid not in items:
                    b.block("check", iid, "manifest item is not in final40", "ข้อใน manifest ไม่อยู่ใน final40")
                    continue
                if not inst or inst[0] != manifest.get("base"):
                    b.block("check", iid, "manifest instance list does not start with the base",
                            "รายการ instance ใน manifest ไม่ได้เริ่มที่ฐานหลัก")
                exp = spec.get("expected_gold") or {}
                mg = spec.get("gold_sql")
                if mg is None or norm_sql(mg) != norm_sql(items[iid]["gold_one_line"]):
                    b.block("check", iid, "gold_sql of the manifest differs from gold_sql_draft (C32)",
                            "gold_sql ใน manifest ไม่ตรงกับ gold_sql_draft (C32)")
                any_rows = False
                for db in inst:
                    rec = {"item": iid, "instance": db, "rows": None, "match": False, "error": None}
                    b.mi_results.append(rec)
                    if db not in inst_db:
                        b.block("check", iid, f"instance {db} is not registered in the manifest",
                                f"instance {db} ไม่ได้ลงทะเบียนใน manifest")
                        continue
                    e2 = eng if inst_db[db] == base_db else None
                    try:
                        if e2 is None:
                            e2 = Engine(dsn_with_db(pg, inst_db[db]))
                        _, rows = e2.run(items[iid]["gold_one_line"])
                    except Exception as e:
                        rec["error"] = type(e).__name__
                        b.block("check", iid, f"gold does not run on instance {db}: {type(e).__name__}",
                                f"gold รันบน instance {db} ไม่ได้: {type(e).__name__}")
                        continue
                    finally:
                        if e2 is not None and e2 is not eng:
                            e2.close()
                    rec["rows"] = len(rows)
                    any_rows = any_rows or bool(rows)
                    if db not in exp:
                        b.block("check", iid, f"manifest has no expected_gold for instance {db}",
                                f"manifest ไม่มี expected_gold ของ instance {db}")
                        continue
                    want = sorted(tuple(g13.cv13(v) for v in r) for r in exp[db])
                    got = sorted(tuple(g13.cv13(v) for v in r) for r in rows)
                    rec["match"] = want == got
                    if not rec["match"]:
                        b.block("check", iid, f"gold on instance {db} differs from expected_gold of the manifest",
                                f"gold บน instance {db} ไม่ตรงกับ expected_gold ใน manifest")
                if not any_rows:
                    b.block("check", iid, "gold is empty on every instance", "gold ว่างบนทุก instance")
    finally:
        eng.close()


# ======================================================================= main build
def build(a):
    mode = "check" if a.check else "draft" if a.draft else "freeze"
    b = Build(mode)
    out_dir = Path(a.out_dir) if a.out_dir else None
    if mode in ("draft", "freeze"):
        for need, name in ((a.pg, "--pg"), (a.manifest, "--manifest"), (a.columns, "--columns"), (a.out_dir, "--out-dir")):
            if not need:
                raise Fatal(f"{name} is required with --{mode}")
    if mode == "draft" and under_results(a.out_dir):
        raise Fatal("a DRAFT suite may not be written under results/ (use a scratch directory)")
    if out_dir is not None and out_dir.exists() and not out_dir.is_dir():
        raise Fatal("--out-dir names an existing file, not a directory")
    if mode == "check":
        b.incomplete = [n for v, n in ((a.pg, "--pg"), (a.manifest, "--manifest"), (a.columns, "--columns")) if not v]
    if mode == "freeze" and not a.approved_decisions_sha256:
        b.block("approval", "-", "--approved-decisions-sha256 was not given (the author types the sha256 of the approved ext_decisions)",
                "ไม่ได้ส่ง --approved-decisions-sha256 (ผู้เขียนต้องพิมพ์ sha256 ของ ext_decisions ที่อนุมัติเอง)")

    # ---------------------------------------------------------------- decisions, library, inputs
    dec_bytes = Path(a.decisions).read_bytes()
    dec_sha = sha256_bytes(dec_bytes)
    try:
        dec = json.loads(dec_bytes.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        raise Fatal(f"--decisions is not a UTF-8 JSON file ({type(e).__name__}"
                    + (f" at line {e.lineno} column {e.colno}" if isinstance(e, json.JSONDecodeError) else "") + ")")
    if not isinstance(dec, dict):
        raise Fatal("--decisions does not hold a JSON object")
    check_decisions_schema(dec)
    validate_decisions(b, dec)
    lib_dir = Path(a.lib_dir) if a.lib_dir else Path(__file__).resolve().parent
    lib_sha = verify_lib(dec, lib_dir)
    g13 = load_module(lib_dir / "grade_v13.py", "_ext_grade_v13")
    vg = load_module(lib_dir / "vg_rule.py", "_ext_vg_rule")
    lib_sha["builder/build_ext_suite.py"] = sha256_file(Path(__file__).resolve())
    given = parse_inputs(a.input)
    verify_inputs(b, dec, given)
    if dec.get("author_approved") is not True:
        b.block("approval", "-", "ext_decisions.author_approved is not true (the author has not approved the file)",
                "ext_decisions.author_approved ไม่เป็น true (ผู้เขียนยังไม่อนุมัติไฟล์)")
    if mode == "freeze" and a.approved_decisions_sha256:
        if a.approved_decisions_sha256.strip().lower() != dec_sha:
            b.block("approval", "-", "--approved-decisions-sha256 differs from the sha256 of the ext_decisions file read",
                    "ค่า --approved-decisions-sha256 ไม่ตรงกับ sha256 ของไฟล์ ext_decisions ที่อ่าน")

    sel_book = read_xlsx(given["selection_xlsx"])
    tf_book = read_xlsx(given["translation_fixes_xlsx"])
    typo_rows = read_tsv(given["typo_fixes"])
    ic_rows = read_tsv(given["item_changes"])
    add_rows = read_tsv(given["item_changes_add"])
    refresh_in = read_tsv(given["metadata_refresh"])
    items_json = load_json_input(given["items_json"], "items_json")

    wb_items, _ = load_workbook_items(b, sel_book)
    final40, reserves = list(dec["final40"]), list(dec["reserves"])
    check_membership(b, dec, wb_items)
    ids = [i for i in final40 + reserves if i in wb_items]
    if len(ids) != len(final40) + len(reserves):
        raise Fatal("final40/reserves refer to ids that are not in the selection workbook")
    cross_check_items_json(b, items_json, wb_items, ids)
    for iid in ids:
        if wb_items[iid]["en_edit"]:
            b.block("decision", iid, "the selection workbook carries an EN edit that is not recorded in ITEM_CHANGES",
                    "workbook การคัดเลือกมีการแก้ EN ที่ไม่ได้บันทึกใน ITEM_CHANGES")

    cur = {iid: {"en": wb_items[iid]["en"], "th": wb_items[iid]["th"], "gold": wb_items[iid]["gold"]} for iid in ids}

    # ---------------------------------------------------------------- application order
    apply_item_changes(b, ic_rows, cur, "item_changes", "workbook", wb_items)
    pending_add = apply_item_changes(b, add_rows, cur, "item_changes_add", "workbook", wb_items)
    apply_typo_fixes(b, typo_rows, cur, wb_items)
    pre = {iid: dict(v) for iid, v in cur.items()}
    th_mode, _, effects = apply_translation_fixes(b, dec, tf_book, cur, mode, given, dec)
    verify_decision_stage_changes(b, pending_add, pre, cur)
    alts = conditional_alts(b, dec, cur, th_mode, effects, given)

    # ---------------------------------------------------------------- set sheet cross-check
    try:
        recs = sheet_records(tf_book, TF_SET_SHEET, [H_ID])
        set_ids = [cell_str(r.get(H_ID)).strip() for r in recs if cell_str(r.get(H_ID)).strip()]
        if set_ids != final40:
            b.block("decision", "-", f"'{TF_SET_SHEET}' sheet lists a different set or order than ext_decisions.final40",
                    f"ชีต '{TF_SET_SHEET}' มีชุดหรือลำดับข้อต่างจาก ext_decisions.final40")
        for r in recs:
            iid = cell_str(r.get(H_ID)).strip()
            if iid in wb_items:
                if family_of(r.get("ตระกูล")) != wb_items[iid]["family"] or tier_of(r.get("Tier")) != wb_items[iid]["tier"]:
                    b.block("decision", iid, f"'{TF_SET_SHEET}' family/tier differs from the selection workbook",
                            f"family/tier ในชีต '{TF_SET_SHEET}' ไม่ตรงกับ workbook การคัดเลือก")
        sheet_vg = sorted(cell_str(r.get(H_ID)).strip() for r in recs if cell_str(r.get("VG")).strip() == "ใช่")
        if sheet_vg != sorted(dec["expected"]["vg"]):
            b.block("decision", "-", f"'{TF_SET_SHEET}' VG column differs from ext_decisions.expected.vg",
                    f"คอลัมน์ VG ในชีต '{TF_SET_SHEET}' ไม่ตรงกับ ext_decisions.expected.vg")
    except Fatal as e:
        b.block("input", "-", str(e), f"อ่านชีต '{TF_SET_SHEET}' ไม่ได้: {e}")

    # ---------------------------------------------------------------- text checks
    for iid in ids:
        c = cur[iid]
        is_final = iid in final40

        def report(kind, item, en, th, _final=is_final):
            if _final:
                b.block(kind, item, en, th)
            else:
                b.warn(item, en, th)

        if THAI_RE.search(c["en"]):
            report("check", iid, "question_en contains Thai characters", "question_en มีอักษรไทย")
        for fld, val in (("question_en", c["en"]), ("question_th", c["th"])):
            if not val.strip():
                report("check", iid, f"{fld} is empty", f"{fld} ว่าง")
            if val != val.strip():
                report("check", iid, f"{fld} has leading or trailing spaces", f"{fld} มีช่องว่างหน้าหรือท้าย")
            if "  " in val or "\t" in val or "\n" in val:
                report("check", iid, f"{fld} has doubled spaces, tabs or line breaks", f"{fld} มีช่องว่างซ้อน tab หรือการขึ้นบรรทัด")
            if NONE_RE.search(val):
                report("check", iid, f"{fld} still contains 'None'", f"{fld} ยังมีคำว่า 'None'")
        if "'None'" in c["gold"] or NONE_RE.search(norm_sql(c["gold"])):
            report("check", iid, "gold still contains 'None'", "gold ยังมี 'None'")

    # ---------------------------------------------------------------- per-item columns
    cols_cfg = load_json_input(a.columns, "--columns") if a.columns else None
    manifest = load_json_input(a.manifest, "--manifest") if a.manifest else None
    ext_cols = []
    if cols_cfg is not None:
        ext_cols = list(cols_cfg.get("ext_required") or [])
        unknown = [c for c in ext_cols if c not in KNOWN_EXT_COLUMNS]
        if unknown:
            raise Fatal("suite_columns.json ext_required has unknown column(s): " + ", ".join(unknown))
        for c in cols_cfg.get("required") or []:
            if c not in CORE_COLUMNS:
                raise Fatal(f"suite_columns.json required column '{c}' is not a core column")
        dirs = cols_cfg.get("directional") or {}
        rdirs = cols_cfg.get("reserve_directional") or {}
        if sorted(dirs) != sorted(dec["directional"]):
            b.block("decision", "-", "suite_columns.json directional items differ from ext_decisions.directional",
                    "รายการข้อมีทิศทางใน suite_columns.json ไม่ตรงกับ ext_decisions.directional")
        if sorted(rdirs) != sorted(dec["reserve_directional"]):
            b.block("decision", "-", "suite_columns.json reserve_directional items differ from ext_decisions.reserve_directional",
                    "รายการ reserve_directional ใน suite_columns.json ไม่ตรงกับ ext_decisions.reserve_directional")
        if sorted(cols_cfg.get("mi_items") or []) != sorted(dec["mi_items"]):
            b.block("decision", "-", "suite_columns.json mi_items differ from ext_decisions.mi_items",
                    "mi_items ใน suite_columns.json ไม่ตรงกับ ext_decisions.mi_items")
    else:
        dirs, rdirs = {}, {}
    if manifest is not None:
        if manifest.get("format") != "kst-mi-2":
            b.block("check", "-", "manifest format is not kst-mi-2", "รูปแบบของ manifest ไม่ใช่ kst-mi-2")
        if manifest.get("rule") != dec["mi_rule"]:
            b.block("check", "-", "manifest rule differs from ext_decisions.mi_rule", "กฎใน manifest ไม่ตรงกับ ext_decisions.mi_rule")
        if manifest.get("base") != "k3n":
            b.block("check", "-", "manifest base is not k3n", "ฐานหลักของ manifest ไม่ใช่ k3n")
        if a.pg and manifest_instance_dbs(manifest).get(manifest.get("base")) != dbname_of(a.pg):
            b.block("check", "-", "--pg does not name the database of the manifest base",
                    "--pg ไม่ได้ชี้ไปที่ฐานของ base ใน manifest")
        if sorted(manifest.get("items", {})) != sorted(dec["mi_items"]):
            b.block("check", "-", "manifest items differ from ext_decisions.mi_items", "รายการข้อใน manifest ไม่ตรงกับ ext_decisions.mi_items")
        if sorted(manifest.get("single_instance_items", [])) != sorted(dec["single_instance_items"]):
            b.block("check", "-", "manifest single_instance_items differ from ext_decisions.single_instance_items",
                    "single_instance_items ใน manifest ไม่ตรงกับ ext_decisions.single_instance_items")
        unrecorded = [i.get("name") or i.get("dbname") for i in manifest.get("instances", []) if not i.get("fingerprint")]
        if unrecorded:
            en = ("manifest instances without a recorded fingerprint (run build_instances --record first): "
                  + ", ".join(unrecorded))
            th = "instance ใน manifest ที่ยังไม่มี fingerprint ที่บันทึก (ต้องรัน build_instances --record ก่อน): " + ", ".join(unrecorded)
            if mode == "freeze":
                b.block("check", "-", en, th)
            else:
                b.warn("-", en, th)
    if dec.get("fk1_format") != "list_violating_rows":
        b.block("decision", "FK1", "ext_decisions.fk1_format must be list_violating_rows (brief 1.3)",
                "ext_decisions.fk1_format ต้องเป็น list_violating_rows (brief 1.3)")

    author_rules = dec["author_class_rule"]
    items = {}
    for iid in ids:
        w = wb_items[iid]
        c = cur[iid]
        it = {"id": iid, "family": w["family"], "tier": w["tier"], "en": c["en"], "th": c["th"],
              "gold": c["gold"], "gold_one_line": one_line_gold(c["gold"])}
        cls, note = None, ""
        for rule in author_rules:
            if rule["workbook_author_contains"] in w["author_raw"]:
                cls, note = str(rule.get("class") or ""), rule.get("source_note", "")
                break
        if cls is None:
            b.block("decision", iid, "no author_class_rule matches the workbook author column",
                    "ไม่มี author_class_rule ที่ตรงกับคอลัมน์ผู้เขียนใน workbook")
            cls = ""
        it["author_class"] = cls
        if w["source_raw"]:
            it["source"] = w["source_raw"]
        elif iid.startswith("F7C-"):
            it["source"] = "F7C relational-calculus set"
        else:
            it["source"] = note or "proposal sheet"
        if iid in final40:
            it["fallback_rank"] = w["rank_raw"]
        else:
            it["fallback_rank"] = str(reserves.index(iid) + 1)
        reg = dirs if iid in final40 else rdirs
        decl = dec["directional"] if iid in final40 else dec["reserve_directional"]
        cr = ""
        if iid in decl and cols_cfg is not None:
            val = reg.get(iid)
            if val is None or not COL_ROLES_RE.match(str(val)):
                b.block("decision", iid, "col_roles value in suite_columns.json is unresolved or malformed (OQ2)",
                        "ค่า col_roles ใน suite_columns.json ยังไม่กำหนดหรือรูปแบบผิด (OQ2)")
            else:
                cr = str(val)
        it["col_roles"] = cr
        mi = []
        if manifest is not None and iid in final40 and iid in (manifest.get("items") or {}):
            mi = list(manifest["items"][iid].get("instances") or [])
        it["mi_instances"] = mi
        it["alt_gold_th"] = alts.get(iid, [])
        items[iid] = it

    # ---------------------------------------------------------------- counts
    fam = Counter(items[i]["family"] for i in final40)
    tier = Counter(str(items[i]["tier"]) for i in final40)
    if dict(fam) != dict(dec["expected"]["family"]):
        b.block("check", "-", f"family counts {dict(sorted(fam.items()))} differ from ext_decisions.expected.family",
                f"จำนวนข้อต่อ family {dict(sorted(fam.items()))} ไม่ตรงกับ ext_decisions.expected.family")
    if dict(tier) != dict(dec["expected"]["tier"]):
        b.block("check", "-", f"tier counts {dict(sorted(tier.items()))} differ from ext_decisions.expected.tier",
                f"จำนวนข้อต่อ tier {dict(sorted(tier.items()))} ไม่ตรงกับ ext_decisions.expected.tier")

    # ---------------------------------------------------------------- database
    if a.pg:
        schema_stmt, schema_why = load_schema_stmt(a.manifest)
        run_db_checks(b, dec, cols_cfg, manifest, items, {i: items[i]["alt_gold_th"] for i in items},
                      a.pg, g13, vg, final40, reserves, schema_stmt, schema_why)
    else:
        for iid in items:
            items[iid]["vg_literals"] = vg.value_grounding_literals(items[iid]["gold_one_line"], items[iid]["th"])
        b.warn("-", "no --pg: database checks were not run", "ไม่ได้ส่ง --pg จึงไม่ได้ตรวจบนฐานข้อมูล")
    vg_ids = sorted(i for i in final40 if items[i].get("vg_literals"))
    if vg_ids != sorted(dec["expected"]["vg"]):
        b.block("check", "-", f"VG items {vg_ids} differ from ext_decisions.expected.vg",
                f"ข้อ VG {vg_ids} ไม่ตรงกับ ext_decisions.expected.vg")

    # ---------------------------------------------------------------- metadata refresh
    for n, r in enumerate(refresh_in, 2):
        iid, col, kind, after = (r.get("id") or "").strip(), (r.get("column") or "").strip(), \
            (r.get("kind") or "").strip(), r.get("after") or ""
        row = {"id": iid, "column": col, "kind": kind, "before": r.get("before") or "", "after": after,
               "computed": "", "status": ""}
        if iid not in items:
            row["status"] = "skipped (id not in final40/reserves)"
            b.refresh_rows.append(row)
            continue
        it = items[iid]
        if kind == "note":
            it.setdefault("notes", []).append(after)
            row["computed"], row["status"] = after, "note added"
        elif kind == "assert":
            if col == "gold_shape_k3n":
                gr = b.gold_results.get(iid) or {}
                comp = f"{gr.get('rows')}x{gr.get('cols')}" if gr.get("rows") is not None else ""
            elif col == "vg_literals":
                comp = json.dumps(it.get("vg_literals", []), ensure_ascii=False)
            elif col in ("order_en", "order_th"):
                comp = "no"
            elif col == "col_roles":
                comp = it["col_roles"]
            elif col == "mi_instances":
                comp = json.dumps(it["mi_instances"], ensure_ascii=False)
            elif col == "v13_status":
                comp = "primary"
            else:
                comp = None
            if comp is None:
                row["status"] = "FAIL (unknown column)"
                b.block("input", iid, f"metadata_refresh:row{n}: unknown column '{col}'",
                        f"metadata_refresh:row{n}: คอลัมน์ '{col}' ไม่รู้จัก")
            else:
                row["computed"] = comp
                ok = False
                if after == "<directional>":
                    ok = bool(comp) and (iid in dec["directional"] or iid in dec["reserve_directional"])
                elif after.startswith("<manifest:") and after.endswith(">"):
                    k = int(after[len("<manifest:"):-1])
                    ok = len(it["mi_instances"]) == k and manifest is not None
                else:
                    ok = comp == after
                missing_src = ((col == "gold_shape_k3n" and not a.pg) or (col == "col_roles" and cols_cfg is None)
                               or (col == "mi_instances" and manifest is None))
                if missing_src:
                    row["status"] = "not checked (source not given in this run)"
                else:
                    row["status"] = "ok" if ok else "FAIL"
                    if not ok:
                        b.block("check", iid, f"metadata_refresh:row{n}: {col} is '{comp}', expected '{after}'",
                                f"metadata_refresh:row{n}: ค่า {col} คือ '{comp}' แต่ค่าที่คาดคือ '{after}'")
        else:
            row["status"] = "FAIL (unknown kind)"
            b.block("input", iid, f"metadata_refresh:row{n}: unknown kind '{kind}'",
                    f"metadata_refresh:row{n}: kind '{kind}' ไม่รู้จัก")
        b.refresh_rows.append(row)

    # ---------------------------------------------------------------- rows
    status = "FROZEN" if mode == "freeze" else "DRAFT"

    def make_row(iid, frozen_ok):
        it = items[iid]
        mi = it["mi_instances"]
        rule, rationale = "", ""
        if it["alt_gold_th"]:
            rule = "D2c"
            rationale = "TH reading accepted as an alternative under the translation-check decisions"
        if mi:
            empty_ok = bool(manifest and manifest["items"][iid].get("empty_gold_on_base_ok"))
            rationale = (f"multi-instance item graded under {dec['mi_rule']} on {len(mi)} instances"
                         + ("; gold is empty on the base k3n by design and the item is not excluded (D3 does not apply)" if empty_ok else ""))
        lits = it.get("vg_literals", [])
        row = {"id": iid, "tier": str(it["tier"]), "schema": "P", "eff": "no",
               "question_en": it["en"], "question_th": it["th"], "gold_sql_draft": it["gold_one_line"],
               "notes": "; ".join(it.get("notes", [])), "gold_sql_v12": "", "v13_status": "primary",
               "order_en": "no", "order_th": "no", "sort_keys": "", "norm": "", "alt_gold_en": "[]",
               "alt_gold_th": json.dumps(it["alt_gold_th"], ensure_ascii=False),
               "v13_rule": rule, "v13_rationale": rationale,
               "family": it["family"], "col_roles": it["col_roles"],
               "mi_instances": json.dumps(mi, ensure_ascii=False),
               "vg": "yes" if lits else "no", "vg_literals": json.dumps(lits, ensure_ascii=False),
               "source": it["source"], "author_class": it["author_class"],
               "ai_drafted": str(dec["ai_drafted"].get("value") or ""), "fallback_rank": it["fallback_rank"],
               "build_status": status if frozen_ok else "DRAFT"}
        return row

    header = CORE_COLUMNS + ext_cols
    legal = (cols_cfg or {}).get("legal") or {}
    suite_rows = [make_row(i, True) for i in final40]
    reserve_rows = [make_row(i, False) for i in reserves]
    for r in suite_rows + reserve_rows:
        for col, ok_vals in legal.items():
            if col in r and r[col] not in ok_vals:
                b.block("check", r["id"], f"column {col} value '{r[col]}' is not legal",
                        f"ค่า '{r[col]}' ของคอลัมน์ {col} ไม่อยู่ในค่าที่อนุญาต")

    suffix = "" if mode == "freeze" else "_DRAFT"
    files = {}
    files[f"{SUITE_BASENAME}{suffix}.tsv"] = tsv_bytes(header, suite_rows)
    files[f"{RESERVES_BASENAME}{suffix}.tsv"] = tsv_bytes(header, reserve_rows)
    ch_header = ["id", "field", "before", "after", "source", "rule", "status"]
    order_ix = {iid: k for k, iid in enumerate(final40 + reserves)}
    ch_rows = sorted(b.changes, key=lambda r: (order_ix.get(r["id"], 999), ))
    files[f"{CHANGES_BASENAME}{suffix}.tsv"] = tsv_bytes(ch_header, ch_rows)
    files[f"{REFRESH_BASENAME}{suffix}.tsv"] = tsv_bytes(
        ["id", "column", "kind", "before", "after", "computed", "status"], b.refresh_rows)

    inputs_sha = dict(b.used_inputs)
    inputs_sha["ext_decisions"] = dec_sha
    if a.manifest:
        inputs_sha["mi_manifest"] = sha256_file(a.manifest)
    if a.columns:
        inputs_sha["suite_columns"] = sha256_file(a.columns)
    inputs_sha.update(lib_sha)
    files[f"{INPUTS_BASENAME}{suffix}.sha256"] = "".join(
        f"{v}  {k}\n" for k, v in sorted(inputs_sha.items())).encode("utf-8")

    # ---------------------------------------------------------------- sweep (outputs + git-bound inputs)
    pats, b.sweep_sources = build_sweep_patterns(a.anon_patterns, a.anon_extra, a.anon_patterns_from)
    if not b.sweep_sources["claude_md"]:
        en = ("anonymity sweep: the sweep pattern of CLAUDE.md could not be read (default: the CLAUDE.md two folders "
              "above the project root; or pass --anon-patterns-from FILE)")
        th = ("anonymity sweep: อ่าน sweep pattern จาก CLAUDE.md ไม่ได้ (ตำแหน่งตั้งต้นคือ CLAUDE.md ที่อยู่สองโฟลเดอร์เหนือ "
              "project root หรือส่ง --anon-patterns-from FILE)")
        if mode == "freeze":
            b.block("check", "-", en, th)
        else:
            b.warn("-", en, th)
            if mode == "check":
                b.incomplete.append("CLAUDE.md sweep pattern")
    if not b.sweep_sources["extra"]:
        en = ("anonymity sweep: no short name of the teaching institution was given (--anon-extra \"<short name>\"); "
              "this builder did not sweep for it, anon_sweep does at Gate 1a step 1a.73")
        th = ("anonymity sweep: ไม่ได้ส่งชื่อย่อของสถาบันที่สอน (--anon-extra \"<ชื่อย่อ>\") ตัวสร้างจึงไม่ได้ตรวจชื่อย่อนี้ "
              "ส่วน anon_sweep ตรวจใน Gate 1a ขั้น 1a.73")
        if mode == "freeze" and REQUIRE_ANON_EXTRA_AT_FREEZE:
            b.block("check", "-", en, th)
        else:
            b.warn("-", en, th)
            if mode == "check":
                b.incomplete.append("--anon-extra")
    git_bound = [("ext_decisions", dec_bytes.decode("utf-8")),
                 ("item_changes_add", Path(given["item_changes_add"]).read_text(encoding="utf-8")),
                 ("metadata_refresh", Path(given["metadata_refresh"]).read_text(encoding="utf-8"))]
    sweep_texts(b, git_bound + [(n, v.decode("utf-8")) for n, v in sorted(files.items())], pats)
    if b.sweep["hits"]:
        for name, ln, kind in b.sweep["hits"]:
            b.block("check", "-", f"anonymity sweep hit in {name}:{ln} ({kind})",
                    f"anonymity sweep พบ pattern ใน {name}:{ln} ({kind})")

    # ---------------------------------------------------------------- conflict copies in --out-dir
    report_name = f"{REPORT_BASENAME}{suffix}.md"
    if out_dir is not None and out_dir.is_dir():
        ours = set(files) | {report_name}
        for f in sorted(out_dir.iterdir()):
            m = CONFLICT_COPY_RE.match(f.name)
            if m and (m.group("stem") + m.group("ext")) in ours:
                b.out_dir_copies.append(f.name)
        if b.out_dir_copies:
            b.warn("-", "--out-dir holds copies of output files made by a file-sync service (not written by this "
                   "builder; remove them): " + ", ".join(b.out_dir_copies),
                   "--out-dir มีสำเนาของไฟล์ผลที่บริการซิงก์ไฟล์สร้างขึ้น (ไม่ได้มาจากตัวสร้างนี้ ควรลบออก): "
                   + ", ".join(b.out_dir_copies))

    # ---------------------------------------------------------------- overwrite guard (freeze)
    if mode == "freeze" and out_dir is not None and out_dir.exists():
        for name in files:
            p = out_dir / name
            if p.exists() and p.read_bytes() != files[name]:
                b.block("check", "-", f"{name} already exists in --out-dir with different content (refusing to overwrite)",
                        f"มี {name} อยู่แล้วใน --out-dir และเนื้อหาต่างกัน (ไม่เขียนทับ)")

    approved_typed = (a.approved_decisions_sha256 or "").strip().lower()

    def render():
        return render_report(b, dec, dec_sha, approved_typed, items, final40, reserves, files,
                             inputs_sha, fam, tier, suite_rows, mode)

    report = render()
    rep_hits = []
    for ln, line in enumerate(report.splitlines(), 1):
        for k, (kind, rx) in enumerate(pats):
            if rx.search(line):
                rep_hits.append((report_name, ln, f"{kind}#{k}"))
    if rep_hits:
        b.sweep["hits"].extend(rep_hits)
        for name, ln, kind in rep_hits:
            b.block("check", "-", f"anonymity sweep hit in {name}:{ln} ({kind})",
                    f"anonymity sweep พบ pattern ใน {name}:{ln} ({kind})")
        report = render()
    if mode == "freeze" and out_dir is not None and (out_dir / report_name).exists():
        if (out_dir / report_name).read_bytes() != report.encode("utf-8"):
            b.block("check", "-", f"{report_name} already exists in --out-dir with different content (refusing to overwrite)",
                    f"มี {report_name} อยู่แล้วใน --out-dir และเนื้อหาต่างกัน (ไม่เขียนทับ)")
            report = render()
    files[report_name] = report.encode("utf-8")
    return b, files, out_dir, dec_sha


# ======================================================================= report (Thai)
FP_STATUS_TH = {"match": "ตรงกับค่าที่บันทึก", "unrecorded": "ยังไม่บันทึก (ตรวจไม่ได้)",
                "no fingerprint_tables": "manifest ไม่มี fingerprint_tables", "malformed": "ค่าที่บันทึกมีรูปแบบผิด"}


def _schema_status_th(s):
    return {"match": "ตรงกับค่าที่บันทึก", "mismatch": "ไม่ตรง", "unrecorded": "ยังไม่บันทึก",
            "not checked": "ไม่ได้ตรวจซ้ำ (ตรวจโดย build_instances.py)"}.get(
        s, "คำนวณไม่ได้ (" + s[len("error "):] + ")" if s.startswith("error ") else s)


def _fp_status_th(s):
    if s in FP_STATUS_TH:
        return FP_STATUS_TH[s]
    if s.startswith("mismatch "):
        return "ไม่ตรง (ตาราง " + s[len("mismatch "):] + ")"
    if s.startswith("error "):
        return "คำนวณไม่ได้ (" + s[len("error "):] + ")"
    return s


def render_report(b, dec, dec_sha, typed, items, final40, reserves, files, inputs_sha, fam, tier, suite_rows, mode):
    L = []
    title = {"check": "ผลตรวจ (--check)", "draft": "ฉบับร่าง (DRAFT)", "freeze": "ฉบับตรึง (FROZEN)"}[mode]
    ok = not b.blockers
    L.append(f"# รายงานการสร้าง suite ชุดขยาย {SUITE_BASENAME}: {title}")
    L.append("")
    L.append(f"- ตัวสร้าง: {BUILDER_VERSION}")
    L.append(f"- โหมด: `--{mode}`")
    if mode == "freeze":
        L.append("- สถานะ: " + ("ตรึงแล้ว (ไม่มี blocker)" if ok else "ปฏิเสธการตรึง (มี blocker)"))
    elif mode == "check" and ok and b.incomplete:
        L.append("- สถานะ: ไม่มี blocker แต่การตรวจไม่ครบ (INCOMPLETE CHECK): ไม่ได้ตรวจส่วนที่ต้องใช้ "
                 + ", ".join(b.incomplete) + " ผลนี้จึงไม่ได้หมายความว่า --freeze จะผ่าน")
    else:
        L.append(f"- สถานะ: {'ไม่มี blocker' if ok else f'มี blocker {len(b.blockers)} รายการ'} (ไฟล์ทุกไฟล์ในโหมดนี้ติดป้าย DRAFT)")
    L.append("- ตัวเลขทุกตัวในรายงานนี้มาจากฐานที่ระบุใน `--pg` ของการรันครั้งนี้ ถ้ารันบน scratch ถือเป็น TEST-ONLY")
    L.append("")
    L.append("## 1. การอนุมัติ ext_decisions")
    L.append("")
    L.append(f"- sha256 ของ ext_decisions ที่อ่าน: `{dec_sha}`")
    L.append(f"- sha256 ที่ผู้เขียนพิมพ์ (`--approved-decisions-sha256`): `{typed or '(ไม่ได้ส่ง)'}`")
    L.append(f"- ตรงกัน: {'ใช่' if typed and typed == dec_sha else 'ไม่ใช่'}")
    L.append(f"- author_approved: `{json.dumps(dec.get('author_approved'))}`")
    appr = dec.get("approval") or {}
    if appr:
        L.append(f"- การอนุมัติที่บันทึกในไฟล์: เวลา `{appr.get('approved_at_ict') or '-'}`, อ้างอิง `{appr.get('master_log_ref') or '-'}`")
    L.append("")
    L.append("## 2. blocker")
    L.append("")
    if b.blockers:
        L.append("| ประเภท | ข้อ | รายละเอียด |")
        L.append("|---|---|---|")
        for kind, iid, _en, th in b.blockers:
            L.append(f"| {KIND_TH.get(kind, kind)} | {iid} | {th.replace('|', '/')} |")
    else:
        L.append("ไม่มี")
    L.append("")
    L.append("ช่องการตัดสินที่ว่างใน TRANSLATION_FIXES: " + ", ".join(
        f"ชีต {k} {v} ช่อง" for k, v in sorted(b.blank_cells.items())))
    L.append("")
    if b.warnings:
        L.append("ข้อสังเกต (ไม่เป็น blocker):")
        for iid, _en, th in b.warnings:
            L.append(f"- {iid}: {th}")
        L.append("")
    if b.flags_recheck:
        L.append("ข้อที่ใช้ถ้อยคำของผู้เขียนเอง (ต้องตรวจ TEST-ONLY ซ้ำก่อนตรึง): " + ", ".join(b.flags_recheck))
        L.append("")
    L.append("## 3. input (label กลางและ sha256; ไม่บันทึก path และไม่ใช้ชื่อไฟล์ที่มีชื่อบุคคล)")
    L.append("")
    L.append("label `sql_TESTONLY` คือ digest ของทั้งโฟลเดอร์แบบเดียวกับแถวโฟลเดอร์ของ freeze_stamp.py "
             "ส่วน `sql_TESTONLY/<ไฟล์>` คือไฟล์ที่ตัวสร้างอ่านจริง ซึ่ง pin ไว้ใน ext_decisions")
    L.append("")
    L.append("| label | sha256 |")
    L.append("|---|---|")
    for k, v in sorted(inputs_sha.items()):
        L.append(f"| {k} | `{v}` |")
    L.append("")
    L.append("## 4. สมาชิกและจำนวน")
    L.append("")
    L.append("- ชุด 40 ข้อ (ลำดับรัน): " + ", ".join(final40))
    L.append("- ข้อสำรอง (ไฟล์ข้อสำรองติด DRAFT ทุกแถวจนกว่าจะใช้กฎแทนที่): " + ", ".join(reserves))
    L.append("- ตระกูล: " + ", ".join(f"{k} {v}" for k, v in sorted(fam.items(), key=lambda x: int(x[0][1:]))))
    L.append("- tier: " + ", ".join(f"T{k} {v}" for k, v in sorted(tier.items())))
    L.append("- ข้อ VG: " + ", ".join(sorted(i for i in final40 if items[i].get("vg_literals"))))
    L.append("- ข้อมีทิศทาง (col_roles จาก suite_columns.json): " + ", ".join(
        f"{i} `{items[i]['col_roles'] or '(ยังไม่กำหนด)'}`" for i in dec["directional"] if i in items))
    L.append("- ข้อหลาย instance (" + dec["mi_rule"] + "): " + ", ".join(
        f"{i} {len(items[i]['mi_instances'])} instance" for i in dec["mi_items"] if i in items))
    L.append("- กฎข้อสำรอง: " + dec["reserve_rule"])
    L.append("")
    L.append("## 5. gold บนฐานหลัก (แถว x คอลัมน์)")
    L.append("")
    L.append("| ข้อ | ตระกูล | tier | gold | VG | col_roles | หมายเหตุ |")
    L.append("|---|---|---|---|---|---|---|")
    for iid in final40 + reserves:
        it = items[iid]
        gr = b.gold_results.get(iid) or {}
        shape = f"{gr.get('rows')}x{gr.get('cols')}" if gr.get("rows") is not None else "-"
        tag = "สำรอง" if iid in reserves else ""
        L.append(f"| {iid} | {it['family']} | T{it['tier']} | {shape} | {'yes' if it.get('vg_literals') else 'no'} "
                 f"| {it['col_roles'] or '-'} | {tag} |")
    L.append("")
    if b.mi_results:
        L.append("## 6. gold บน instance ของข้อหลาย instance")
        L.append("")
        L.append("| ข้อ | instance | แถว | ตรง expected_gold |")
        L.append("|---|---|---|---|")
        for r in b.mi_results:
            L.append(f"| {r['item']} | {r['instance']} | {r['rows'] if r['rows'] is not None else '-'} "
                     f"| {'ใช่' if r['match'] else 'ไม่ใช่'} |")
        L.append("")
    if b.fp_results:
        L.append("## 7. fingerprint และ schema_md5 ของ instance ใน manifest (คำนวณซ้ำบนฐานแล้วเทียบกับค่าที่บันทึก)")
        L.append("")
        L.append("| instance | fingerprint ของข้อมูล | schema_md5 |")
        L.append("|---|---|---|")
        for r in b.fp_results:
            L.append(f"| {r['instance']} | {_fp_status_th(r['status'])} "
                     f"| {_schema_status_th(b.schema_results.get(r['instance'], 'unrecorded'))} |")
        L.append("")
        L.append("schema_md5 ใช้ SCHEMA_STMT ของ db_fingerprint.py ในโฟลเดอร์เดียวกับ manifest (นิยามเดียวกับ build_instances.py); "
                 "ถ้าไม่พบไฟล์นั้น ตัวสร้างไม่ตรวจซ้ำ และค่านี้ตรวจโดย build_instances.py ใน Gate 1a ขั้น 1a.45")
        L.append("")
    L.append("## 8. การเปลี่ยนแปลงจาก workbook")
    L.append("")
    cnt = Counter((c["field"], c["status"]) for c in b.changes)
    for (field, st), n in sorted(cnt.items()):
        L.append(f"- {field} ({st}): {n} แถว")
    L.append("- รายละเอียดหนึ่งแถวต่อ field อยู่ในไฟล์ ITEM_CHANGES_generated")
    L.append(f"- แถว ITEM_CHANGES ที่ค่าใน workbook เท่ากับ 'after' อยู่แล้ว (สถานะ already_in_workbook) {b.n_before_unverified} แถว: "
             "ตัวสร้างตรวจได้เพียงว่า 'before' ไม่ว่างและต่างจาก 'after' เพราะค่าเดิมไม่อยู่ใน workbook แล้ว "
             "ค่า 'before' ของไฟล์ที่ pin ไว้ตรวจครั้งเดียวใน Gate 0 (test EX-T7g) เทียบกับร่าง EXTENSION_v2_DRAFT_2026-10-13.tsv")
    if b.skipped_rows:
        L.append("- แถวของข้อที่ถูกตัด (ไม่ได้ใช้): " + ", ".join(b.skipped_rows))
    L.append("- gold ทุกข้อเขียนเป็นบรรทัดเดียวลงท้าย ';' และตรวจว่าผลบนฐานหลักเท่ากับ gold ต้นฉบับ (digest แบบไม่สนลำดับแถว)")
    L.append("")
    L.append("## 9. การตรวจอื่น")
    L.append("")
    src = b.sweep_sources or {}
    L.append("- anonymity sweep: แหล่ง pattern ได้แก่ CLAUDE.md {} รายการ, --anon-extra {} รายการ, --anon-patterns {} รายการ, "
             "บัญชีของเครื่องที่รัน {} รายการ, pattern ในตัว {} รายการ (ไม่บันทึกข้อความของ pattern)".format(
                 src.get("claude_md", 0), src.get("extra", 0), src.get("file", 0), src.get("runtime", 0), src.get("builtin", 0)))
    L.append(f"- anonymity sweep: ตรวจ {b.sweep['files']} ไฟล์ พบ {len(b.sweep['hits'])} จุด (แสดงเฉพาะไฟล์และบรรทัด)")
    if not src.get("extra"):
        L.append("- anonymity sweep: ไม่ได้ส่ง --anon-extra จึงไม่ได้ตรวจชื่อย่อของสถาบันที่สอนในการรันนี้ "
                 "(ตรวจโดย anon_sweep ใน Gate 1a ขั้น 1a.73 ก่อน commit)")
    for name, ln, kind in b.sweep["hits"]:
        L.append(f"  - {name}:{ln} ({kind})")
    ai = dec["ai_drafted"]
    L.append("- ค่า ai_drafted: " + str(ai.get("value") or "-") + " ทุกข้อ (" + (ai.get("rationale_th") or ai.get("rationale", "")) + ")")
    for n in b.notes:
        L.append(f"- {n}")
    L.append("")
    L.append("## 10. ไฟล์ผล (sha256)")
    L.append("")
    for name in sorted(files):
        L.append(f"- `{name}` `{sha256_bytes(files[name])}`")
    L.append("")
    return "\n".join(L)


# ======================================================================= CLI
def parse_args(argv=None):
    ap = argparse.ArgumentParser(description="build the extension suite (AMENDMENT-9)")
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--check", action="store_true")
    g.add_argument("--draft", action="store_true")
    g.add_argument("--freeze", action="store_true")
    ap.add_argument("--pg")
    ap.add_argument("--manifest")
    ap.add_argument("--decisions", required=True)
    ap.add_argument("--columns")
    ap.add_argument("--input", action="append", default=[])
    ap.add_argument("--out-dir")
    ap.add_argument("--approved-decisions-sha256")
    ap.add_argument("--lib-dir", help="directory holding grade_v13.py and vg_rule.py (default: this script's directory)")
    ap.add_argument("--anon-patterns-from", help="file holding the CLAUDE.md sweep pattern (default: the CLAUDE.md two "
                                                 "folders above the project root)")
    ap.add_argument("--anon-patterns", action="append", default=[], help="file with one sweep regex per line")
    ap.add_argument("--anon-extra", action="append", default=[],
                    help="comma-separated literals swept with letter boundaries (e.g. the short name of the teaching institution)")
    return ap.parse_args(argv)


def refusal_text(e):
    """one line for an input or environment error (no traceback, no path, no DSN)"""
    if isinstance(e, Fatal):
        return str(e)
    mod = type(e).__module__ or ""
    if mod.startswith("psycopg2"):
        first = (str(e).strip().splitlines() or [""])[0]
        first = re.sub(r'server at "[^"]*"', 'server at "<host>"', first)
        return f"database error ({type(e).__name__}): {first}"
    if isinstance(e, zipfile.BadZipFile):
        return "an --input workbook is not a valid xlsx file (BadZipFile)"
    if isinstance(e, ET.ParseError):
        return "an --input workbook has malformed XML (ParseError)"
    if isinstance(e, UnicodeDecodeError):
        return "an input file is not UTF-8 (UnicodeDecodeError)"
    if isinstance(e, OSError):
        return f"file error ({type(e).__name__}): {e.strerror or 'see the paths given'}"
    return f"{type(e).__name__}"


def main(argv=None):
    a = parse_args(argv)
    try:
        b, files, out_dir, dec_sha = build(a)
    except Fatal as e:
        print("REFUSED:", refusal_text(e))
        return EXIT_REFUSED
    except (OSError, UnicodeDecodeError, zipfile.BadZipFile, ET.ParseError) as e:
        print("REFUSED:", refusal_text(e), "-- no file written")
        return EXIT_REFUSED
    except Exception as e:
        if not (type(e).__module__ or "").startswith("psycopg2"):
            raise
        print("REFUSED:", refusal_text(e), "-- no file written")
        return EXIT_REFUSED
    mode = b.mode
    print(f"build_ext_suite --{mode}: {len(b.blockers)} blocker(s), {len(b.warnings)} warning(s)")
    print("blank decision cells: " + ", ".join(f"{k}={v}" for k, v in sorted(b.blank_cells.items())))
    for kind, iid, msg, _th in b.blockers:
        print(f"  BLOCKER [{kind}] {iid}: {msg}")
    for iid, msg, _th in b.warnings:
        print(f"  warning {iid}: {msg}")
    print(f"ext_decisions sha256 {dec_sha}")
    if mode == "check":
        if b.blockers:
            return EXIT_REFUSED
        if b.incomplete:
            print("INCOMPLETE CHECK: not run or not given: " + ", ".join(b.incomplete)
                  + " -- this result does not mean that --freeze will pass (exit 3)")
            return EXIT_INCOMPLETE
        return EXIT_OK
    if mode == "freeze" and b.blockers:
        print("FREEZE REFUSED: no file written")
        return EXIT_REFUSED
    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        for name in sorted(files):
            dest = out_dir / name
            if dest.is_file() and dest.read_bytes() == files[name]:
                print(f"{sha256_bytes(files[name])}  {name} (unchanged, not rewritten)")
                continue
            tmp = out_dir / (name + ".tmp")
            tmp.write_bytes(files[name])
            os.replace(tmp, dest)
            print(f"{sha256_bytes(files[name])}  {name}")
    except OSError as e:
        print("REFUSED:", refusal_text(e), "-- the output folder may hold a partial set of files")
        return EXIT_REFUSED
    if mode == "freeze":
        print("FROZEN: k3n_ext_suite_v1.0.tsv written (build_status FROZEN); reserves stay DRAFT")
    else:
        print("DRAFT written (build_status DRAFT on every row; not for official runs)")
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
