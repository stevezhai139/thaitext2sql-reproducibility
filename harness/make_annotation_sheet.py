#!/usr/bin/env python3
"""make_annotation_sheet.py — C-2 kit (part 1). Emits the bilingual judgment
sheet (NO translation involved: annotator READS existing Thai items and judges).
CHECK rows = value-grounding set from the canonical rule in vg_rule.py
(amended 2026-08-13: wildcard-stripped, date-unit function args excluded -> 10).

One run emits 4 files into --outdir: annotation_sheet_{A,B}.{tsv,xlsx}.
Sheet A = second annotator (clarity ทุกแถว + vg_check เฉพาะแถว CHECK).
Sheet B = original translator (clarity เท่านั้น — scorer อ่าน vg_check จาก A).

Fill codes: clarity 1=ชัดเจน/0=กำกวม; vg_check 1=ยืนยันไม่มี English literal
โผล่ในโจทย์ไทย/0=มี; note = เหตุผลถ้ากำกวม.

Usage: python3 make_annotation_sheet.py --outdir ../results
"""
import argparse
import csv
import os

from vg_rule import is_value_grounding

FIELDS = ["id", "tier", "question_en", "question_th", "clarity", "vg_check", "note"]

ROLE = {
    "A": ("ผู้ประเมินคนที่สอง (second annotator)",
          "กรอก clarity ทุกแถว (60 ข้อ) และ vg_check เฉพาะ 10 แถวสีส้มที่เขียนว่า CHECK"),
    "B": ("ผู้แปลต้นฉบับ (original translator)",
          "กรอกเฉพาะ clarity ทุกแถว (60 ข้อ) — ช่อง vg_check ไม่ต้องแตะ"),
}

INSTR = [
    ("clarity", "1 = อ่านโจทย์ไทยแล้วเข้าใจชัดว่าต้องการอะไร ถึงขั้นเขียน query ได้โดยไม่เดา / "
                "0 = กำกวม-ไม่เคลียร์ (กรุณาเขียน note ว่าติดตรงไหน)"),
    ("vg_check", "เฉพาะแถวสีส้ม: ขีดเส้นใต้ instance value ในโจทย์ EN (เช่น Virginia, "
                 "Widowed, Tokyo) แล้วดูว่าแต่ละค่าปรากฏในโจทย์ไทยอย่างไร — "
                 "แปลไทย/ทับศัพท์หมดทุกค่า → 1 | ปนกัน (บางค่าอังกฤษ บางค่าไทย) → 1 | "
                 "ทุกค่าเป็นอักษรอังกฤษครบ → 0 "
                 "(สรุป: 1 = มีอย่างน้อยหนึ่งค่าที่ระบบต้องเดาเอง / 0 = copy ได้ครบทุกค่า) "
                 "ตัวอย่าง: 'พรรค Democratic-Republican ...เป็นหม้าย' → Widowed ถูกแปล → 1"),
    ("instance vs attribute", "นับเฉพาะ instance value (ค่าในแถวข้อมูล เช่น Virginia, "
                 "Widowed, Tokyo, Democratic-Republican) — ไม่นับ attribute/relation name "
                 "(เช่น MarriageStatus, SpouseName, OrderID หรือคำแปลอย่าง 'สถานะการสมรส', "
                 "'ข้อมูลการสมรส') แม้จะถูกแปลเป็นไทยก็ไม่นับ"),
    ("กติกา", "ต่างคนต่างกรอก ห้ามปรึกษากันจนกว่าทั้งสองฝ่ายจะกรอกเสร็จ (ไม่งั้นค่า kappa ใช้ไม่ได้)"),
    ("สี", "เหลือง = ช่องที่ต้องกรอก / ส้มอ่อน = แถว value-grounding (10 แถว)"),
    ("ตัวอย่าง", "เช่น แถวตัวอย่าง: clarity = 1, vg_check = 1, note เว้นว่าง"),
]


def build_rows(suite_path):
    rows = list(csv.DictReader(open(suite_path, encoding="utf-8"), delimiter="\t"))
    out = []
    for r in rows:
        vg = is_value_grounding(r["gold_sql_draft"], r["question_th"])
        out.append({"id": r["id"], "tier": r["tier"],
                    "question_en": r["question_en"], "question_th": r["question_th"],
                    "clarity": "", "vg_check": "CHECK" if vg else "", "note": ""})
    return out


def write_tsv(out_rows, path):
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS, delimiter="\t")
        w.writeheader()
        w.writerows(out_rows)


def write_xlsx(out_rows, path, role):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    from openpyxl.worksheet.datavalidation import DataValidation

    thai = Font(name="Tahoma", size=10)          # Thai-capable professional font
    bold = Font(name="Tahoma", size=10, bold=True)
    wrap = Alignment(wrap_text=True, vertical="top")
    yellow = PatternFill("solid", fgColor="FFF2A6")   # fill-in cells
    orange = PatternFill("solid", fgColor="FCE4D6")   # value-grounding rows
    grey = PatternFill("solid", fgColor="D9D9D9")     # header

    wb = Workbook()

    ins = wb.active
    ins.title = "วิธีกรอก"
    ins.column_dimensions["A"].width = 14
    ins.column_dimensions["B"].width = 100
    ins["A1"], ins["B1"] = "บทบาท", f"{role[0]} — {role[1]}"
    for i, (k, v) in enumerate(INSTR, start=2):
        ins[f"A{i}"], ins[f"B{i}"] = k, v
    for row in ins.iter_rows(min_row=1, max_row=1 + len(INSTR), max_col=2):
        for c in row:
            c.font = bold if c.column == 1 else thai
            c.alignment = wrap

    ws = wb.create_sheet("annotation")
    widths = {"A": 6, "B": 5, "C": 46, "D": 46, "E": 8, "F": 9, "G": 26}
    for col, wd in widths.items():
        ws.column_dimensions[col].width = wd
    for j, name in enumerate(FIELDS, start=1):
        c = ws.cell(row=1, column=j, value=name)
        c.font, c.fill, c.alignment = bold, grey, wrap
    for i, r in enumerate(out_rows, start=2):
        is_vg = r["vg_check"] == "CHECK"
        for j, name in enumerate(FIELDS, start=1):
            c = ws.cell(row=i, column=j, value=r[name])
            c.font, c.alignment = thai, wrap
            if is_vg:
                c.fill = orange
        ws.cell(row=i, column=5).fill = yellow                    # clarity
        ws.cell(row=i, column=7).fill = yellow                    # note
        if is_vg:
            ws.cell(row=i, column=6).fill = yellow                # vg_check
    ws.freeze_panes = "A2"

    n = len(out_rows) + 1
    dv_c = DataValidation(type="list", formula1='"0,1"', allow_blank=True,
                          promptTitle="clarity", prompt="1=ชัดเจน / 0=กำกวม")
    dv_c.add(f"E2:E{n}")
    ws.add_data_validation(dv_c)
    dv_v = DataValidation(type="list", formula1='"0,1"', allow_blank=True,
                          promptTitle="vg_check",
                          prompt="1=ค่าอังกฤษไม่โผล่ในโจทย์ไทย / 0=โผล่")
    for i, r in enumerate(out_rows, start=2):
        if r["vg_check"] == "CHECK":
            dv_v.add(f"F{i}")
    ws.add_data_validation(dv_v)

    assert get_column_letter(len(FIELDS)) == "G"
    wb.save(path)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--suite", default="../suite/k3_suite_v1.2.tsv")
    ap.add_argument("--outdir", default="../results")
    a = ap.parse_args()

    out = build_rows(a.suite)
    n_vg = sum(1 for o in out if o["vg_check"])
    for key in ("A", "B"):
        base = os.path.join(a.outdir, f"annotation_sheet_{key}")
        write_tsv(out, base + ".tsv")
        write_xlsx(out, base + ".xlsx", ROLE[key])
        print(f"[sheet {key}] {len(out)} items -> {base}.tsv/.xlsx "
              f"(value-grounding CHECK rows: {n_vg})")
