#!/usr/bin/env python3
"""make_audit_sheet_rc1.py -- blind manual audit of the B2.3 classes (AMENDMENT-7 A6).

Reads rc1_audit_rows.csv (analyze_rc1.py) and writes, in --out-dir,
  rc1_audit_sheet.xlsx  rows shuffled with seed 20261012; shows only an opaque audit_id,
                        the item, the Thai question, the target column/literal of the
                        gold and the SQL; arm, model, run and the classifier class are
                        hidden; a drop-down column for the author's class
  rc1_audit_key.csv     sealed key: audit_id -> row_key and every hidden column
                        (do not open before the coding is finished)
Generic: every column of the rows file other than SHOWN goes to the key only, so the
chat audit (OQ33.4: app/form hidden) can use the same tool. Does not read any jsonl.
Refuses to overwrite. Run with: python3 -B -E -P (openpyxl is in the user site).
Cell safety: every shown value is written as a text cell (data type 's'), so model SQL
that starts with '=' is never stored as a live formula; a control character that XML
cannot hold (e.g. ESC) is written as a visible escape such as \x1b, and the key records
the sha256 of the ORIGINAL sql and whether the shown text was escaped (sql_escaped).

Usage: python3 -B -E -P make_audit_sheet_rc1.py --rows ../results/rc1/h1h4/rc1_audit_rows.csv \
         --out-dir ../results/rc1/audit
"""
import argparse
import csv
import hashlib
import os
import random
import re
import sys

sys.dont_write_bytecode = True

SEED = 20261012
SHOWN = ["qid", "question_th", "targets", "sql"]
CLASS_CHOICES = ["THAI_COPY", "INVENTED", "NO_PRED", "GROUNDED", "STORED"]
SHEET = "rc1_audit_sheet.xlsx"
KEY = "rc1_audit_key.csv"
README_TH = [
    "แบบตรวจคลาสของ run ที่ผิดบนข้อ value-grounding ภาษาไทย (AMENDMENT-7 A6 และ B2.3)",
    "กรอกคอลัมน์ author_class หนึ่งค่าต่อแถวจากรายการ: THAI_COPY, INVENTED, NO_PRED, GROUNDED, STORED",
    "ตรวจตามลำดับนี้: THAI_COPY = string literal ใดใน SQL มีอักษรไทย",
    "ข้อความในคอมเมนต์ของ SQL (-- ถึงท้ายบรรทัด หรือ /* ... */) ไม่ใช่ literal: อักษรไทยหรือเครื่องหมาย ' "
    "ในคอมเมนต์ไม่นับในทุกคลาส",
    "INVENTED = literal ที่เทียบกับคอลัมน์เป้าหมาย (=, <>, !=, IN, NOT IN, LIKE, NOT LIKE, ILIKE) "
    "ไม่ตรงกับค่าที่เก็บจริงของคอลัมน์นั้น (LIKE อ่านเป็น pattern; ILIKE ไม่สนตัวพิมพ์)",
    "NO_PRED = คอลัมน์เป้าหมายไม่มี predicate ที่เป็น literal (รวม run ที่ไม่มี SQL)",
    "GROUNDED = literal เป้าหมายทุกตัวปรากฏบนคอลัมน์ของตน (ผิดด้วยเหตุอื่น)",
    "STORED = บนคอลัมน์เป้าหมายใช้เฉพาะค่าที่เก็บจริง แต่ไม่ใช่ literal เป้าหมาย",
    "คอลัมน์ targets แสดงคอลัมน์และ literal เป้าหมายจาก gold; แถวถูกสลับลำดับ และไม่แสดงแขน โมเดล "
    "ลำดับ run หรือคลาสของตัวจำแนก",
    "ห้ามเปิดไฟล์ rc1_audit_key.csv จนกว่าจะกรอกครบทุกแถว; เมื่อกรอกครบให้บันทึกไฟล์ในชื่อเดิม",
    "ช่อง note ใช้บันทึกข้อสังเกตได้ตามต้องการ (ไม่บังคับ)",
]


def load_rows(path):
    with open(path, encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        sys.exit("no audit rows")
    need = ["row_key"] + SHOWN
    miss = [c for c in need if c not in rows[0]]
    if miss:
        sys.exit(f"rows file lacks columns {miss}")
    keys = [r["row_key"] for r in rows]
    if len(set(keys)) != len(keys):
        sys.exit("row_key is not unique")
    return rows


_ILLEGAL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sheet_text(v):
    """(text safe for an xlsx cell, escaped?): XML-illegal control characters become a
    visible \\xNN escape (the original stays identifiable through sql_sha256 in the key)."""
    v = "" if v is None else str(v)
    out = _ILLEGAL.sub(lambda m: "\\x%02x" % ord(m.group(0)), v)
    return out, out != v


def shuffled(rows, seed=SEED):
    """deterministic: sort by row_key, then one Random(seed).shuffle."""
    out = sorted(rows, key=lambda r: r["row_key"])
    random.Random(seed).shuffle(out)
    return out


def main():
    ap = argparse.ArgumentParser(description="blind audit sheet (AM-7 A6)")
    ap.add_argument("--rows", required=True)
    ap.add_argument("--out-dir", required=True)
    a = ap.parse_args()
    os.makedirs(a.out_dir, exist_ok=True)
    sheet_p, key_p = os.path.join(a.out_dir, SHEET), os.path.join(a.out_dir, KEY)
    for p in (sheet_p, key_p):
        if os.path.exists(p):
            sys.exit(f"{os.path.basename(p)} exists; the audit files are written once")
    rows = shuffled(load_rows(a.rows))
    hidden = [c for c in rows[0].keys() if c not in SHOWN]

    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = "audit"
    header = ["audit_id"] + SHOWN + ["author_class", "note"]
    ws.append(header)
    for c in ws[1]:
        c.font = Font(bold=True)
    escaped = {}
    for i, r in enumerate(rows, 1):
        vals = [f"A{i:04d}"]
        for c in SHOWN:
            t, esc = sheet_text(r[c])
            vals.append(t)
            if esc:
                escaped[r["row_key"]] = True
        for j, v in enumerate(vals + ["", ""], 1):
            cell = ws.cell(row=i + 1, column=j)
            cell.value = v
            cell.data_type = "s"   # text, never a formula
    dv = DataValidation(type="list", formula1='"' + ",".join(CLASS_CHOICES) + '"',
                        allow_blank=True, showErrorMessage=True)
    ws.add_data_validation(dv)
    col = chr(ord("A") + header.index("author_class"))
    dv.add(f"{col}2:{col}{len(rows) + 1}")
    widths = {"audit_id": 9, "qid": 6, "question_th": 50, "targets": 30, "sql": 80,
              "author_class": 14, "note": 30}
    for j, h in enumerate(header):
        ws.column_dimensions[chr(ord("A") + j)].width = widths.get(h, 12)
    for row in ws.iter_rows(min_row=2):
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    ws.freeze_panes = "B2"
    rd = wb.create_sheet("README")
    for line in README_TH:
        rd.append([line])
    rd.column_dimensions["A"].width = 120
    wb.save(sheet_p)

    with open(key_p, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["audit_id"] + hidden + ["qid", "sql_sha256", "sql_escaped"])
        for i, r in enumerate(rows, 1):
            w.writerow([f"A{i:04d}"] + [r[c] for c in hidden] + [
                r["qid"], hashlib.sha256(r["sql"].encode("utf-8")).hexdigest(),
                bool(escaped.get(r["row_key"]))])
    order_sha = hashlib.sha256("\n".join(r["row_key"] for r in rows).encode("utf-8")).hexdigest()
    print(f"wrote {SHEET} ({len(rows)} rows; hidden columns: {', '.join(hidden)}) and {KEY}")
    if escaped:
        print(f"{len(escaped)} rows hold a control character, shown as a visible escape (sql_escaped)")
    print(f"shuffle seed {SEED}; order sha256 {order_sha[:16]}")


if __name__ == "__main__":
    main()
