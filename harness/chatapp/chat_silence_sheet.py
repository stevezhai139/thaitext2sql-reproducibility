#!/usr/bin/env python3
"""chat_silence_sheet.py -- Excel sheets for the author's hand coding of the chat
check (prereg AMENDMENT-8 sec.8, OQ33.4-33.5 defaults). Run with openpyxl available:
python3 -B -E -P. Never reads results*.jsonl: replies come from the raw files listed in
log_index.tsv, each re-hashed against raw_manifest.tsv first.

Silence code (FLAGGED / ASKED / SILENT), two rounds at least 3 days apart:
  --round 1 --raw-manifest M --log-index L --out R1.xlsx
      one row per Form B done cell (turn-1 reply), 54 rows; app name, VG status and
      the right/wrong label are hidden; opaque code_id (S01..; assigned by
      random.Random(20261012)); row order random.Random(20261012 + round)
  --round 2 --raw-manifest M --log-index L --prev R1.xlsx --out R2.xlsx
      refused unless round 1 is fully coded and at least 3 days (72 h) have passed since
      round 1 was last saved (later of its creation stamp and file time); same code_ids,
      a different row order, round-1 codes are not shown; records the sha256 of the
      round-1 codes and of the round-1 key file, so a later edit of either is detected;
      log_index.tsv and raw_manifest.tsv must be the files round 1 was built from
  --agree --prev R1.xlsx --cur R2.xlsx --out silence_final.tsv [--reconcile X.xlsx]
      % agreement, Cohen's kappa and the 3 x 3 table (printed and written to
      <out stem>_agreement.tsv; neither file may exist). When the rounds disagree and the
      reconcile workbook (default silence_reconcile.xlsx next to --out) does not exist, it
      is written (rows that differ, both codes, final code, reason) and the script exits
      3; after the author fills it, the same command writes silence_final.tsv
      (code_id, app, prompt_id, form, lang, qid, attempt, code_round1, code_round2,
      code_final, reconciled, reason, log_index_sha256, raw_manifest_sha256; the last two
      tie the codes to the chat log they were coded from, and chat_report.py checks them)
Blind audit of the B2.3 classifier on the chat (OQ33.4):
  --vg-audit --rows vg_codes_chat_audit_rows.csv --out vg_audit_chat.xlsx
      rows shuffled with random.Random(20261012); app, form and the classifier class are
      hidden; the author fills author_class. With 0 rows (no wrong VG cell with SQL) an
      empty sheet is written and the audit is reported as not needed (n=0)
  --vg-audit-agree --sheet vg_audit_chat.xlsx --out vg_audit_agreement.tsv
      % agreement and Cohen's kappa (classifier vs author), GF verdict of each cell under
      both (GF = THAI_COPY or INVENTED) and the cells whose GF verdicts differ (both reported);
      n=0 is reported as such
Blinding: the key of every workbook (app, prompt_id, qid; for the audit also the
classifier class) and its stamps are written to a separate file <workbook stem>_key.json
that the coder never opens; the workbook itself holds no key (not even a hidden sheet).
The code_ids and row orders come from the public seed 20261012, so the blind is
procedural, not cryptographic; this is disclosed with OQ33.4-33.5.
Excel safety: reply and SQL text is always stored as text (never as a formula, even when
it starts with '='), and characters that XML 1.0 cannot hold (control characters other
than tab, line feed and carriage return) are replaced by a visible <U+XXXX>; the count is
recorded in the key file and printed.

Usage (from harness/; one command per RUNBOOK step):
  python3 -B -E -P "chatapp/chat_silence_sheet.py" --round 1 --raw-manifest "../results/chat/raw_manifest.tsv"
      --log-index "../results/chat/log_index.tsv" --out "../results/chat/silence_round1.xlsx"
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import csv  # noqa: E402
import datetime as dt  # noqa: E402
import hashlib  # noqa: E402
import os  # noqa: E402
import json  # noqa: E402
import random  # noqa: E402
import re  # noqa: E402
import tempfile  # noqa: E402
from collections import Counter  # noqa: E402
from fractions import Fraction  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draw_chat_items_v13 import SEED, die, sha256_file  # noqa: E402
from make_chat_cells import APPS, LOG_COLUMNS, read_cells  # noqa: E402
from vg_outcome import B23_CLASSES, GF_CLASSES  # noqa: E402

ICT = dt.timezone(dt.timedelta(hours=7))
CODES = ("FLAGGED", "ASKED", "SILENT")
FINAL_COLUMNS = ["code_id", "app", "prompt_id", "form", "lang", "qid", "attempt", "code_round1", "code_round2",
                 "code_final", "reconciled", "reason", "log_index_sha256", "raw_manifest_sha256"]
MIN_GAP = dt.timedelta(days=3)
CHUNK = 32000
N_CHUNKS = 3
TS = "%Y-%m-%dT%H:%M:%S"
ILLEGAL_XML = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")  # openpyxl ILLEGAL_CHARACTERS_RE

README_SILENCE = [
    "ชีตนี้ใช้ code ความเงียบ (silence code) ของคำตอบ Form B ตาม AMENDMENT-8 หัวข้อ 8",
    "แต่ละแถวคือคำตอบ turn 1 หนึ่งข้อความ ชื่อ app สถานะ VG และผลถูกผิดถูกซ่อนไว้ "
    "code_id เป็นรหัสทึบ และลำดับแถวต่างกันในแต่ละรอบ",
    "กรอกคอลัมน์ code ด้วยค่าใดค่าหนึ่ง: FLAGGED = คำตอบเตือนว่าค่าที่เก็บจริงอาจต่าง แนะนำให้ตรวจค่า "
    "หรือให้ query ตรวจค่า เช่น SELECT DISTINCT; ASKED = ถามกลับแทนหรือก่อนให้ SQL; "
    "SILENT = ไม่เข้าทั้งสองแบบ",
    "คำตอบที่ไม่มี SQL ให้ code เป็น ASKED ตาม AMENDMENT-8 หัวข้อ 6 (turn 1 ที่ไม่มี SQL นับว่าผิดและ code เป็น ASKED) "
    "รายงานใช้กฎนี้กับ cell ที่ไม่มี SQL โดยอัตโนมัติ และแสดงรายการ cell ที่ code ต่างจากกฎ",
    "code ทุกแถว รวมคำตอบที่อาจถูก เพราะผลถูกผิดถูกซ่อนไว้ การวิเคราะห์ใช้เฉพาะแถวที่ SQL ผิดหรือไม่มี SQL",
    "รอบที่ 2 สร้างได้เมื่อผ่านไปอย่างน้อย 3 วันหลังบันทึกรอบที่ 1 ครั้งสุดท้าย "
    "และห้ามเปิดดูไฟล์รอบที่ 1 ระหว่าง code รอบที่ 2",
    "รูปแบบของคำตอบอาจบอกได้ว่ามาจาก app ใด ข้อจำกัดนี้เปิดเผยในเล่ม",
    "คอลัมน์ reply_cont_1 และ reply_cont_2 คือส่วนต่อของคำตอบที่ยาวเกินหนึ่ง cell",
    "กรอกเฉพาะคอลัมน์ code และ note ห้ามเปลี่ยนชื่อชีต ห้ามลบหรือย้ายแถว",
    "กุญแจของ code_id (ชื่อ app และข้อ) อยู่ในไฟล์ <ชื่อ workbook>_key.json แยกจาก workbook นี้ "
    "ห้ามเปิดไฟล์นั้นระหว่าง code; code_id และลำดับแถวได้จาก seed ที่เปิดเผย การปิดตาจึงเป็นแบบปฏิบัติ ไม่ใช่แบบรหัสลับ",
    "ข้อความที่ขึ้นต้นด้วย = แสดงเป็นข้อความตามจริง และอักขระควบคุมที่ Excel เก็บไม่ได้แสดงเป็น <U+XXXX>",
]
README_AUDIT = [
    "ชีตนี้ใช้ตรวจคลาสของตัวจำแนก B2.3 (AMENDMENT-7) แบบปิดตา สำหรับ cell VG ของ chat ที่ผิดและมี SQL (OQ33.4)",
    "ชื่อ app, form และคลาสที่ตัวจำแนกให้ถูกซ่อนไว้ ลำดับแถวสลับด้วย seed 20261012",
    "คอลัมน์ targets คือคอลัมน์เป้าหมายและ literal ที่ gold ใช้ ในรูป คอลัมน์ = 'ค่า'",
    "กรอก author_class ตามลำดับการตรวจของ B2.3 ดังนี้ (ใช้คลาสแรกที่เข้าเงื่อนไข)",
    "1. THAI_COPY: string literal ใดใน SQL มีอักษรไทย",
    "2. INVENTED: literal ที่เทียบกับคอลัมน์เป้าหมาย (=, <>, !=, IN, NOT IN, LIKE, NOT LIKE, ILIKE) "
    "ไม่ตรงกับค่าที่เก็บจริงใดๆ โดย LIKE และ NOT LIKE อ่านเป็น pattern และ ILIKE ไม่สนตัวพิมพ์",
    "3. NO_PRED: คอลัมน์เป้าหมายไม่มี predicate ที่เป็น literal (รวมแถวที่ช่อง sql ว่าง "
    "ซึ่งหมายถึง SQL ที่ parse ไม่ผ่าน และตัวจำแนกถือเป็น run ที่ไม่มี SQL แบบเดียวกับแขน API)",
    "4. GROUNDED: literal เป้าหมายทุกตัวปรากฏบนคอลัมน์ของตน (ผิดด้วยเหตุอื่น)",
    "5. STORED: บนคอลัมน์เป้าหมายใช้เฉพาะค่าที่เก็บจริง แต่ไม่ใช่ literal เป้าหมาย",
    "ค่าที่เก็บจริงของคอลัมน์เป้าหมายดูได้จาก full_values ในไฟล์ suite/value_hints_v1.json",
    "กรอกเฉพาะคอลัมน์ author_class และ note ห้ามเปลี่ยนชื่อชีต ห้ามลบหรือย้ายแถว",
    "กุญแจ (app, form และคลาสของตัวจำแนก) อยู่ในไฟล์ <ชื่อ workbook>_key.json แยกจาก workbook นี้ ห้ามเปิดระหว่าง code",
]


def now_ict():
    return dt.datetime.now(ICT).replace(microsecond=0)


def clean_text(s):
    """(text, n): XML-illegal control characters replaced by a visible <U+XXXX>."""
    s = s or ""
    n = len(ILLEGAL_XML.findall(s))
    return (ILLEGAL_XML.sub(lambda m: "<U+%04X>" % ord(m.group(0)), s) if n else s), n


def key_path_of(xlsx):
    return os.path.splitext(xlsx)[0] + "_key.json"


def chunks(s):
    s = s or ""
    parts = [s[i:i + CHUNK] for i in range(0, len(s), CHUNK)] or [""]
    if len(parts) > N_CHUNKS:
        die(f"a reply is longer than {CHUNK * N_CHUNKS} characters")
    return parts + [""] * (N_CHUNKS - len(parts))


def codes_sha(codes):
    return hashlib.sha256("".join(f"{k}\t{codes[k]}\n" for k in sorted(codes)).encode("utf-8")).hexdigest()


def cohen_kappa(pairs, labels):
    """Exact po and kappa (Fractions); kappa None when expected agreement is 1."""
    n = len(pairs)
    if n == 0:
        return None, None
    po = Fraction(sum(1 for x, y in pairs if x == y), n)
    ca, cb = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    pe = Fraction(sum(ca[lab] * cb[lab] for lab in labels), n * n)
    return po, (None if pe == 1 else (po - pe) / (1 - pe))


def fmt(x):
    return "undefined" if x is None else f"{float(x):.4f}"


# ---------------------------------------------------------------- inputs
def load_form_b_replies(log_index, raw_manifest):
    base = os.path.dirname(os.path.abspath(raw_manifest))
    man = {}
    with open(raw_manifest, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            man[r["path"]] = r
    cells = {c["prompt_id"]: c for c in read_cells(os.path.join(os.path.dirname(os.path.abspath(log_index)),
                                                                  "cells.tsv"))}
    with open(log_index, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh, delimiter="\t"))
    if not rows or list(rows[0].keys()) != LOG_COLUMNS:
        die(f"log_index.tsv header is not {LOG_COLUMNS}")
    out = []
    app_rank = {x: i for i, x in enumerate(APPS)}
    for r in sorted((r for r in rows if r["status"] == "done"),
                    key=lambda x: (int(x["order"]), app_rank[x["app"]])):
        c = cells[r["prompt_id"]]
        if c["form"] != "B":
            continue
        m = man.get(r["raw_file"])
        p = os.path.join(base, r["raw_file"])
        if m is None or not os.path.isfile(p) or sha256_file(p) != m["sha256"]:
            die(f"raw file missing from raw_manifest.tsv or changed: {r['raw_file']}", 1)
        with open(p, encoding="utf-8") as fh:
            txt = fh.read()
        out.append({"app": r["app"], "prompt_id": r["prompt_id"], "form": "B", "lang": c["lang"],
                    "qid": c["qid"], "attempt": r["attempt"], "text": txt})
    return out


def assign_ids(items, prefix):
    idx = list(range(len(items)))
    random.Random(SEED).shuffle(idx)
    for n, i in enumerate(idx, 1):
        items[i]["code_id"] = f"{prefix}{n:02d}"
    return items


# ---------------------------------------------------------------- workbook helpers
def write_book(out, sheet, header, rows, edit_cols, dropdown_col, dropdown_vals, readme, meta, key_header, key_rows):
    """workbook (data sheet + README, no key) and <out stem>_key.json (meta + key). Every
    str cell is stored as text (data_type 's', quote prefix), never as a formula; illegal
    XML characters are replaced (clean_text) and counted in the key file."""
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, Protection
    from openpyxl.worksheet.datavalidation import DataValidation
    from openpyxl.utils import get_column_letter

    kp = key_path_of(out)
    for p in (out, kp):
        if os.path.exists(p):
            die(f"output exists, refusing to overwrite: {os.path.basename(p)}")
    n_clean = 0
    safe_rows = []
    for r in rows:
        row = []
        for v in r:
            if isinstance(v, str):
                v, k = clean_text(v)
                n_clean += k
            row.append(v)
        safe_rows.append(row)
    wb = Workbook()
    ws = wb.active
    ws.title = sheet
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    for r in safe_rows:
        ws.append(r)
    for row in ws.iter_rows(min_row=2, max_row=len(safe_rows) + 1):
        for c in row:
            name = header[c.column - 1]
            c.protection = Protection(locked=name not in edit_cols)
            c.alignment = Alignment(wrap_text=True, vertical="top")
            if isinstance(c.value, str):
                c.data_type = "s"
                c.quotePrefix = True
    if safe_rows:
        col = get_column_letter(header.index(dropdown_col) + 1)
        dv = DataValidation(type="list", formula1='"' + ",".join(dropdown_vals) + '"', allow_blank=True)
        ws.add_data_validation(dv)
        dv.add(f"{col}2:{col}{len(safe_rows) + 1}")
    for j, name in enumerate(header, 1):
        ws.column_dimensions[get_column_letter(j)].width = 90 if name in ("reply", "sql") else (
            30 if name in ("targets", "note", "reason") else 14)
    ws.freeze_panes = "A2"
    ws.protection.sheet = True
    ws.protection.formatColumns = False
    ws.protection.formatRows = False
    rd = wb.create_sheet("README")
    for line in readme:
        rd.append([line])
    rd.column_dimensions["A"].width = 140
    for row in rd.iter_rows():
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    meta = dict(meta, sanitised_control_chars=meta.get("sanitised_control_chars", 0) + n_clean,
                workbook=os.path.basename(out))
    # both files are written to temporary names and put in place together (no overwrite), so a
    # failure never leaves a workbook without its key file or the reverse
    d = os.path.dirname(os.path.abspath(out)) or "."
    os.makedirs(d, exist_ok=True)
    fd1, t_wb = tempfile.mkstemp(prefix="." + os.path.basename(out) + ".", suffix=".partial", dir=d)
    fd2, t_key = tempfile.mkstemp(prefix="." + os.path.basename(kp) + ".", suffix=".partial", dir=d)
    os.close(fd1)
    os.close(fd2)
    placed = []
    try:
        wb.save(t_wb)
        with open(t_key, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(json.dumps({"meta": meta, "key_header": key_header, "key_rows": key_rows},
                                ensure_ascii=False, indent=1, default=str) + "\n")
        for tmp, final in ((t_wb, out), (t_key, kp)):
            os.link(tmp, final)
            placed.append(final)
    except BaseException:
        for f in placed:
            os.unlink(f)
        raise
    finally:
        for tmp in (t_wb, t_key):
            if os.path.exists(tmp):
                os.unlink(tmp)
    return meta


def read_book(path, sheet, id_col, value_col):
    """(values, meta, key, texts, ids in sheet order) of a workbook and its _key.json."""
    from openpyxl import load_workbook
    kp = key_path_of(path)
    if not os.path.isfile(kp):
        die(f"{os.path.basename(path)}: key file {os.path.basename(kp)} missing (written beside the workbook)")
    wb = load_workbook(path, data_only=True)
    if sheet not in wb.sheetnames:
        die(f"{os.path.basename(path)}: sheet '{sheet}' missing")
    rows = list(wb[sheet].iter_rows(values_only=True))
    header = [str(x) if x is not None else "" for x in rows[0]]
    data = [dict(zip(header, r)) for r in rows[1:] if any(v not in (None, "") for v in r)]
    values = {str(d[id_col]).strip(): ("" if d.get(value_col) is None else str(d[value_col]).strip().upper())
              for d in data}
    with open(kp, encoding="utf-8") as fh:
        kd = json.load(fh)
    meta = {k: ("" if v is None else str(v)) for k, v in kd["meta"].items()}
    kh = [str(x) for x in kd["key_header"]]
    key = {str(r[0]): dict(zip(kh, ["" if v is None else str(v) for v in r])) for r in kd["key_rows"] if r[0]}
    texts = {str(d[id_col]).strip(): "".join(str(d.get(c) or "") for c in ("reply", "reply_cont_1", "reply_cont_2"))
             for d in data}
    order = [str(d[id_col]).strip() for d in data]
    if sorted(order) != sorted(key):
        die(f"{os.path.basename(path)}: the rows of sheet '{sheet}' differ from its key file")
    return values, meta, key, texts, order


def require_complete(values, legal, label):
    bad = sorted(k for k, v in values.items() if v not in legal)
    if bad:
        die(f"{label}: {len(bad)} rows without a legal code (first {bad[0]})")


# ---------------------------------------------------------------- modes
def silence_round(a):
    for p in (a.out, key_path_of(a.out)):
        if os.path.exists(p):
            die(f"output exists, refusing to overwrite: {os.path.basename(p)}")
    items = assign_ids(load_form_b_replies(a.log_index, a.raw_manifest), "S")
    ids = sorted(it["code_id"] for it in items)
    order = list(ids)
    random.Random(SEED + a.round).shuffle(order)
    meta = {"kind": "silence", "round": a.round, "created_at_ict": now_ict().strftime(TS), "seed": SEED,
            "n_rows": len(items), "order_sha256": hashlib.sha256(",".join(order).encode()).hexdigest(),
            "log_index_sha256": sha256_file(a.log_index), "raw_manifest_sha256": sha256_file(a.raw_manifest)}
    key_rows = [[it["code_id"], it["app"], it["prompt_id"], it["form"], it["lang"], it["qid"], it["attempt"]]
                for it in sorted(items, key=lambda x: x["code_id"])]
    if a.round == 2:
        if not a.prev:
            die("--round 2 needs --prev (the coded round-1 workbook)")
        pv, pmeta, pkey, _t, porder = read_book(a.prev, "code", "code_id", "code")
        if pmeta.get("kind") != "silence" or pmeta.get("round") != "1":
            die("--prev is not a round-1 silence workbook")
        require_complete(pv, CODES, "round 1")
        created = dt.datetime.strptime(pmeta["created_at_ict"], TS).replace(tzinfo=ICT)
        saved = dt.datetime.fromtimestamp(os.path.getmtime(a.prev), ICT)
        ref = max(created, saved)
        if now_ict() - ref < MIN_GAP:
            die(f"round 2 refused: round 1 was last saved {ref.strftime(TS)} ICT; "
                f"wait until {(ref + MIN_GAP).strftime(TS)} ICT (at least 3 days)")
        if (pmeta.get("log_index_sha256"), pmeta.get("raw_manifest_sha256")) != \
                (meta["log_index_sha256"], meta["raw_manifest_sha256"]):
            die("round 1 was built from another log_index.tsv or raw_manifest.tsv")
        if sorted(pkey) != ids or any(pkey[r[0]]["prompt_id"] != r[2] or pkey[r[0]]["app"] != r[1]
                                      for r in key_rows):
            die("round-1 workbook covers different cells (log_index or raw files changed?)")
        if order == porder:
            die("round-2 order equals round-1 order")
        meta.update({"prev_codes_sha256": codes_sha(pv), "prev_file_sha256": sha256_file(a.prev),
                     "prev_key_sha256": sha256_file(key_path_of(a.prev)), "prev_saved_ict": ref.strftime(TS)})
    by_id = {it["code_id"]: it for it in items}
    rows, n_clean = [], 0
    for cid in order:
        txt, k = clean_text(by_id[cid]["text"])
        n_clean += k
        rows.append([cid] + chunks(txt) + [None, None])
    meta["sanitised_control_chars"] = n_clean
    header = ["code_id", "reply", "reply_cont_1", "reply_cont_2", "code", "note"]
    write_book(a.out, "code", header, rows, ("code", "note"), "code", CODES, README_SILENCE, meta,
               ["code_id", "app", "prompt_id", "form", "lang", "qid", "attempt"], key_rows)
    print(f"silence round {a.round}: {len(rows)} Form B replies; order_sha256={meta['order_sha256']}; "
          f"control characters replaced: {n_clean}")
    print(f"[out] {os.path.basename(a.out)} sha256={sha256_file(a.out)}")
    print(f"[out] {os.path.basename(key_path_of(a.out))} (key; the coder does not open it)")


def silence_agree(a):
    agr = os.path.splitext(a.out)[0] + "_agreement.tsv"
    for p in (a.out, agr):
        if os.path.exists(p):
            die(f"output exists, refusing to overwrite: {os.path.basename(p)}")
    v1, m1, k1, texts, _ = read_book(a.prev, "code", "code_id", "code")
    v2, m2, k2, _t2, _ = read_book(a.cur, "code", "code_id", "code")
    if m1.get("kind") != "silence" or m1.get("round") != "1" or m2.get("kind") != "silence" or m2.get("round") != "2":
        die("--prev must be round 1 and --cur round 2 silence workbooks")
    if m2.get("prev_key_sha256") != sha256_file(key_path_of(a.prev)):
        die("round-1 key file changed after round 2 was created", 1)
    require_complete(v1, CODES, "round 1")
    require_complete(v2, CODES, "round 2")
    if m2.get("prev_codes_sha256") != codes_sha(v1):
        die("round-1 codes changed after round 2 was created", 1)
    if (m1.get("log_index_sha256"), m1.get("raw_manifest_sha256")) != \
            (m2.get("log_index_sha256"), m2.get("raw_manifest_sha256")):
        die("the two rounds were built from different log_index.tsv or raw_manifest.tsv")
    if k1 != k2:
        die("the two rounds have different keys")
    ids = sorted(k1)
    pairs = [(v1[i], v2[i]) for i in ids]
    po, kappa = cohen_kappa(pairs, CODES)
    table = Counter(pairs)
    agree = sum(1 for x, y in pairs if x == y)
    print(f"silence agreement: {agree} of {len(ids)} = {fmt(po)}; Cohen's kappa = {fmt(kappa)}")
    print("round1 \\ round2  " + "  ".join(f"{c:>8}" for c in CODES))
    for x in CODES:
        print(f"{x:16} " + "  ".join(f"{table[(x, y)]:>8}" for y in CODES))
    diff = [i for i in ids if v1[i] != v2[i]]
    final, reason = {i: v1[i] for i in ids if i not in diff}, {}
    if diff:
        rec_path = a.reconcile or os.path.join(os.path.dirname(os.path.abspath(a.out)), "silence_reconcile.xlsx")
        if not os.path.exists(rec_path) and os.path.exists(key_path_of(rec_path)):
            die(f"{os.path.basename(key_path_of(rec_path))} exists without its workbook; restore the workbook")
        if not os.path.exists(rec_path):
            rows = [[i] + chunks(texts[i]) + [v1[i], v2[i], None, None] for i in diff]
            header = ["code_id", "reply", "reply_cont_1", "reply_cont_2", "code_round1", "code_round2",
                      "code_final", "reason"]
            write_book(rec_path, "reconcile", header, rows, ("code_final", "reason"), "code_final", CODES,
                       ["อ่านคำตอบที่สองรอบ code ไม่ตรงกันซ้ำ แล้วกรอก code_final และเหตุผลในคอลัมน์ reason ทุกแถว "
                        "จากนั้นรันคำสั่ง --agree เดิมอีกครั้ง"],
                       {"kind": "silence_reconcile", "created_at_ict": now_ict().strftime(TS),
                        "pairs_sha256": codes_sha({i: v1[i] + "|" + v2[i] for i in ids})},
                       ["code_id"], [[i] for i in diff])
            print(f"{len(diff)} rows differ; fill {os.path.basename(rec_path)} (code_final and reason), "
                  f"then run the same --agree command again")
            sys.exit(3)
        rv, rmeta, _rk, _rt, _ = read_book(rec_path, "reconcile", "code_id", "code_final")
        if rmeta.get("pairs_sha256") != codes_sha({i: v1[i] + "|" + v2[i] for i in ids}):
            die("reconcile workbook does not belong to these two rounds")
        if sorted(rv) != sorted(diff):
            die("reconcile workbook rows differ from the disagreements")
        require_complete(rv, CODES, "reconcile")
        from openpyxl import load_workbook
        ws = load_workbook(rec_path, data_only=True)["reconcile"]
        hdr = [c.value for c in ws[1]]
        for r in ws.iter_rows(min_row=2, values_only=True):
            d = dict(zip(hdr, r))
            if d.get("code_id"):
                reason[str(d["code_id"]).strip()] = str(d.get("reason") or "").strip()
        if any(not reason.get(i) for i in diff):
            die("every reconciled row needs a reason")
        final.update({i: rv[i] for i in diff})
    with open(agr, "x", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["metric", "value"])
        w.writerow(["n", len(ids)])
        w.writerow(["agree", agree])
        w.writerow(["percent_agreement", fmt(po)])
        w.writerow(["cohen_kappa", fmt(kappa)])
        for x in CODES:
            for y in CODES:
                w.writerow([f"round1={x};round2={y}", table[(x, y)]])
    with open(a.out, "x", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(FINAL_COLUMNS)
        for i in ids:
            k = k1[i]
            w.writerow([i, k["app"], k["prompt_id"], k["form"], k["lang"], k["qid"], k["attempt"], v1[i], v2[i],
                        final[i], "Y" if i in diff else "N", reason.get(i, ""),
                        m1["log_index_sha256"], m1["raw_manifest_sha256"]])
    print(f"[out] {os.path.basename(a.out)} sha256={sha256_file(a.out)}")
    print(f"[out] {os.path.basename(agr)}")


def vg_audit(a):
    for p in (a.out, key_path_of(a.out)):
        if os.path.exists(p):
            die(f"output exists, refusing to overwrite: {os.path.basename(p)}")
    with open(a.rows, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    need = ["app", "form", "qid", "targets", "sql", "classifier_class"]
    if rows and any(k not in rows[0] for k in need):
        die(f"--rows needs columns {need}")
    items = assign_ids([dict(r) for r in rows], "V")
    items.sort(key=lambda r: r["code_id"])
    sheet_rows, n_clean = [], 0
    for it in items:
        txt, k = clean_text(it["sql"])
        n_clean += k
        sheet_rows.append([it["code_id"], it["qid"], it["targets"]] + chunks(txt) + [None, None])
    header = ["audit_id", "qid", "targets", "sql", "sql_cont_1", "sql_cont_2", "author_class", "note"]
    meta = {"kind": "vg_audit", "created_at_ict": now_ict().strftime(TS), "seed": SEED,
            "rows_sha256": sha256_file(a.rows), "n_rows": len(items), "sanitised_control_chars": n_clean}
    key_rows = [[it["code_id"], it["app"], it["form"], it["qid"], it["classifier_class"]] for it in items]
    readme = README_AUDIT if items else ["ไม่มี cell VG ที่ผิดและมี SQL จึงไม่ต้อง audit (n=0)"] + README_AUDIT
    write_book(a.out, "audit", header, sheet_rows, ("author_class", "note"), "author_class", B23_CLASSES,
               readme, meta, ["audit_id", "app", "form", "qid", "classifier_class"], key_rows)
    if not items:
        print("no wrong VG cells with SQL: audit not needed (n=0); an empty sheet is written")
    print(f"blind B2.3 audit sheet: {len(items)} rows")
    print(f"[out] {os.path.basename(a.out)} sha256={sha256_file(a.out)}")
    print(f"[out] {os.path.basename(key_path_of(a.out))} (key; the coder does not open it)")


def vg_audit_agree(a):
    if os.path.exists(a.out):
        die(f"--out exists, refusing to overwrite: {os.path.basename(a.out)}")
    vals, meta, key, _t, _ = read_book(a.sheet, "audit", "audit_id", "author_class")
    if meta.get("kind") != "vg_audit":
        die("--sheet is not a vg_audit workbook")
    require_complete(vals, B23_CLASSES, "audit")
    ids = sorted(key)
    pairs = [(key[i]["classifier_class"], vals[i]) for i in ids]
    po, kappa = cohen_kappa(pairs, B23_CLASSES)
    gf_diff = [i for i in ids if (key[i]["classifier_class"] in GF_CLASSES) != (vals[i] in GF_CLASSES)]
    if not ids:
        print("B2.3 audit: n=0 (no wrong VG cells with SQL); agreement and kappa undefined")
    print(f"B2.3 audit agreement: {sum(1 for x, y in pairs if x == y)} of {len(ids)} = {fmt(po)}; "
          f"Cohen's kappa = {fmt(kappa)}")
    print(f"cells whose GF verdict differs (classifier vs author): {len(gf_diff)}")
    with open(a.out, "x", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh, delimiter="\t", lineterminator="\n")
        w.writerow(["audit_id", "app", "form", "qid", "classifier_class", "author_class",
                    "gf_classifier", "gf_author", "class_agree", "gf_agree"])
        for i in ids:
            c, u = key[i]["classifier_class"], vals[i]
            w.writerow([i, key[i]["app"], key[i]["form"], key[i]["qid"], c, u,
                        "Y" if c in GF_CLASSES else "N", "Y" if u in GF_CLASSES else "N",
                        "Y" if c == u else "N", "N" if i in gf_diff else "Y"])
        w.writerow([])
        w.writerow(["# n", len(ids)])
        w.writerow(["# percent_agreement", fmt(po)])
        w.writerow(["# cohen_kappa", fmt(kappa)])
        w.writerow(["# gf_verdict_differs", len(gf_diff)])
    print(f"[out] {os.path.basename(a.out)} sha256={sha256_file(a.out)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--round", type=int, choices=[1, 2])
    mode.add_argument("--agree", action="store_true")
    mode.add_argument("--vg-audit", action="store_true")
    mode.add_argument("--vg-audit-agree", action="store_true")
    ap.add_argument("--raw-manifest")
    ap.add_argument("--log-index")
    ap.add_argument("--prev")
    ap.add_argument("--cur")
    ap.add_argument("--reconcile")
    ap.add_argument("--rows")
    ap.add_argument("--sheet")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.round:
        if not (a.raw_manifest and a.log_index):
            die("--round needs --raw-manifest and --log-index")
        silence_round(a)
    elif a.agree:
        if not (a.prev and a.cur):
            die("--agree needs --prev and --cur")
        silence_agree(a)
    elif a.vg_audit:
        if not a.rows:
            die("--vg-audit needs --rows")
        vg_audit(a)
    else:
        if not a.sheet:
            die("--vg-audit-agree needs --sheet")
        vg_audit_agree(a)


if __name__ == "__main__":
    main()
