#!/usr/bin/env python3
"""make_chat_log_xlsx.py -- blank CHAT_LOG.xlsx for the 84 hand-entered chats
(prereg AMENDMENT-8 sec.6-7). The workbook holds metadata only; reply text is never
typed into Excel (it goes to raw/<file>.md).

Sheets
  log     84 pre-filled rows, cell-major (order 1..28 x chatgpt, gemini, claude),
          columns LOG_COLUMNS (AMENDMENT-8 sec.7 + attempt). Key columns and the
          pre-filled file names are locked (sheet protection without a password);
          dropdowns for status (done/void) and turn2_sent (Y/N); then REDO_ROWS
          unlocked rows for re-done cells (attempt >= 2, app dropdown).
  setup   SETUP_FIELDS (AMENDMENT-8 sec.3 and sec.15), one value per row.
  README  formal Thai instructions (AMENDMENT-8 sec.6-7).

Run with openpyxl available (it lives in the user site): python3 -B -E -P.
This script never reads results*.jsonl.

Usage (from harness/):
  python3 -B -E -P "chatapp/make_chat_log_xlsx.py" --cells "../results/chat/cells.tsv"
      --out "../results/chat/CHAT_LOG.xlsx"
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import os  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draw_chat_items_v13 import die, sha256_file  # noqa: E402
from make_chat_cells import (APPS, CELLS_PER_APP, LOG_COLUMNS, raw_name,  # noqa: E402
                             read_cells, shot_name)

REDO_ROWS = 20
STATUS_VALUES = ("done", "void")
YN_VALUES = ("Y", "N")
LOCKED_PREFILLED = ("app", "order", "prompt_id", "attempt", "raw_file", "raw2_file", "screenshot")
TS_COLUMNS = ("ts_sent_ict", "ts_done_ict")
TS_FORMAT = "yyyy-mm-dd hh:mm:ss"

# (key, Thai label, kind) -- kind "Y" must be Y, "text" must be non-empty (chat_log_export checks)
SETUP_FIELDS = [
    ("account_chatgpt_free", "ChatGPT: บัญชี free แยกต่างหาก ไม่มี subscription (กรอก Y)", "Y"),
    ("account_gemini_personal_free", "Gemini: บัญชี Google ส่วนบุคคล (@gmail.com) ที่ไม่มีแผน AI แบบเสียเงิน "
     "และไม่ใช่บัญชี Google Workspace ขององค์กร (กรอก Y)", "Y"),
    ("account_claude_free", "Claude.ai: บัญชี free แยกต่างหาก ไม่มี subscription (กรอก Y)", "Y"),
    ("settings_off_all_apps", "ปิด memory, การอ้างอิงแชตเก่า, personalization และ custom instructions "
     "ครบทั้งสาม app (กรอก Y)", "Y"),
    ("training_opt_out_all_apps", "ปิดการใช้ข้อมูลเพื่อฝึกโมเดลเท่าที่แต่ละ app เปิดให้ปิด (กรอก Y)", "Y"),
    ("default_mode_all_apps", "ใช้ค่า default ของ free plan ไม่เลือกโหมด reasoning, search หรือ deep research เอง "
     "(กรอก Y)", "Y"),
    ("no_vpn", "ไม่ใช้ VPN ระหว่างป้อนแชต (กรอก Y)", "Y"),
    ("browser_and_version", "browser และเวอร์ชัน (ตัวเดียวกันทั้งสาม app)", "text"),
    ("ui_language", "ภาษาของ UI", "text"),
    ("settings_screenshots_before", "ชื่อไฟล์ screenshot หน้า settings ก่อนแชตแรก (ทุก app)", "text"),
    ("settings_screenshots_after", "ชื่อไฟล์ screenshot หน้า settings หลังแชตสุดท้าย (ทุก app)", "text"),
    ("rc1_base_arm_dates", "ช่วงวันที่เก็บแขน B (base) ของ AMENDMENT-7 รอบ ต.ค.", "text"),
    ("chat_dates", "ช่วงวันที่ป้อนแชต", "text"),
]

README_TH = [
    "CHAT_LOG.xlsx: บันทึกการป้อนแชตของ chat-app consistency check (AMENDMENT-8)",
    "ไฟล์นี้บันทึกข้อมูลกำกับของแต่ละแชตเท่านั้น ห้ามวางข้อความคำตอบของ app ลงในไฟล์นี้ "
    "คำตอบทุกข้อความบันทึกเป็นไฟล์ในโฟลเดอร์ raw/",
    "ก่อนแชตแรก: กรอกชีต setup ให้ครบ ตั้งค่าบัญชีตาม AMENDMENT-8 หัวข้อ 3 และถ่าย screenshot หน้า settings ของทุก app",
    "เวลาเริ่ม: ห้ามส่งแชตแรกก่อน commit และ push ของ Gate 2 ซึ่งตรึงรายการข้อและ FREEZE STAMP ของ AMENDMENT-8 "
    "เวลาของ commit นี้ (RUNBOOK_v2 ขั้น 2.38b) คือ CHAT_NOT_BEFORE ที่ใช้ในขั้น C2 และ C10 ไม่ใช่ NOT_BEFORE ของ Gate 1b "
    "chat_log_export.py ปฏิเสธค่าที่เร็วกว่าเวลาสร้าง prompt (created_at_ict ใน cells_meta.json)",
    "ลำดับการทำงาน: ทำตามคอลัมน์ order จาก 1 ถึง 28 โดย order เดียวกันต้องทำครบทั้งสาม app "
    "(chatgpt, gemini, claude) ติดกันก่อนไป order ถัดไป ชีต log เรียงแถวตามลำดับนี้แล้ว "
    "ถ้าลำดับนี้คลาดเคลื่อน ไม่ต้องทิ้งแชต รายงานจะนับจำนวน cell ที่คลาดเคลื่อนเป็น deviation",
    "การป้อน prompt: คัดลอกข้อความจากไฟล์ prompts/<prompt_id>.txt เท่านั้น ห้ามคัดลอกจาก cell ใน Excel "
    "ใช้คำสั่ง pbcopy ได้ เช่น pbcopy < \"prompts/<prompt_id>.txt\" ที่รันจากโฟลเดอร์ results/chat "
    "แล้ววางในแชตใหม่และกดส่งด้วยมือ",
    "หนึ่งแถวคือหนึ่งแชตใหม่แบบ single turn ห้าม regenerate ห้าม edit และห้ามถามซ้ำ "
    "ห้ามใช้ script, bot, browser extension หรือ agent ที่ควบคุม browser ทุกชนิด",
    "การบันทึกคำตอบ: คัดลอกคำตอบด้วยปุ่ม copy ของ app แล้วบันทึกลงไฟล์ตามชื่อในคอลัมน์ raw_file "
    "ภายใต้โฟลเดอร์ raw/ ทันที ใช้คำสั่ง pbpaste ได้ เช่น pbpaste > \"raw/<raw_file>\" "
    "ห้ามแก้ไฟล์ raw หลังบันทึก",
    "กันการเขียนทับไฟล์ raw: ก่อนใช้ pbpaste ให้รันคำสั่ง set -o noclobber หนึ่งครั้งในทุกหน้าต่าง terminal "
    "ที่ใช้บันทึกคำตอบ (zsh และ bash) เมื่อตั้งค่านี้แล้ว pbpaste > จะปฏิเสธชื่อไฟล์ที่มีอยู่แล้ว ห้ามใช้ >| "
    "ถ้าคำสั่งแจ้งว่าไฟล์มีอยู่แล้ว ให้ตรวจชื่อไฟล์และแถว ห้ามลบหรือแทนไฟล์เดิม ถ้าเป็นความผิดของผู้ป้อน "
    "ให้ใช้ status = void และทำ cell นั้นใหม่ในแถว redo",
    "turn 2: ใช้เฉพาะเมื่อ app ถามกลับแทนการให้ SQL ให้ส่งข้อความในไฟล์ prompts/TURN2.txt ครั้งเดียวในแชตเดิม "
    "บันทึกคำตอบลงไฟล์ตามคอลัมน์ raw2_file และกรอก turn2_sent = Y กรณีอื่นกรอก N "
    "ถ้า turn 1 มี SQL ห้ามส่ง turn 2 และถ้ามีไฟล์ตามชื่อใน raw2_file ต้องกรอก turn2_sent = Y "
    "ผลหลักคือ turn 1 ส่วน turn 2 เป็นผลรอง turn 1 ที่ไม่มี SQL นับว่าผิดและ code เป็น ASKED (AMENDMENT-8 หัวข้อ 6)",
    "ช่องเวลา: ts_sent_ict คือเวลาที่กดส่ง และ ts_done_ict คือเวลาที่ได้รับคำตอบครบ "
    "เป็นเวลาไทย (UTC+7) รูปแบบ YYYY-MM-DD HH:MM:SS",
    "ui_model_label: ป้ายรุ่นที่ UI แสดง หรือ not shown; limit_banner: ข้อความของ banner แจ้ง rate limit "
    "หรือการสลับโมเดล (เว้นว่างถ้าไม่มี); tools_visible: เครื่องมือที่ UI แสดงว่าใช้ เช่น search "
    "(กรอก none ถ้าไม่มี)",
    "rate limit หรือ banner แจ้งการสลับโมเดล: หยุดรอ แล้วทำต่อจาก cell ที่ยังไม่เสร็จ ไม่ข้ามและไม่ทำซ้ำ "
    "และบันทึกข้อความ banner",
    "ความผิดของผู้ป้อน เช่น วางผิดหรือกดส่งก่อน: กรอก status = void และเหตุผลในช่อง note โดยไม่ลบแถวเดิม "
    "แถว void ที่กดส่งแล้วต้องกรอก ts_sent_ict (และ ts_done_ict ถ้าได้คำตอบ) ส่วนแถว void ที่ไม่ได้กดส่ง "
    "ให้เว้นช่องเวลาและเขียน note ขึ้นต้นด้วย not sent "
    "จากนั้นทำ cell นั้นใหม่ในแชตใหม่ โดยกรอกแถวว่างส่วน redo ด้านล่างของชีต log ดังนี้ "
    "app, order และ prompt_id เดิม; attempt = 2 (หรือมากกว่า); raw_file = <app>_<prompt_id>_a<attempt>.md; "
    "raw2_file = <app>_<prompt_id>_a<attempt>_turn2.md; screenshot = <app>_<prompt_id>_a<attempt>.png "
    "(chat_log_export.py ปฏิเสธชื่อไฟล์ที่ไม่ตรงกับ app, prompt_id และ attempt ของแถว)",
    "status: done เมื่อได้คำตอบและบันทึกไฟล์ raw แล้ว; void เมื่อแถวนั้นใช้ไม่ได้ (ต้องมี note) "
    "ทุกคู่ app กับ prompt_id ต้องมีแถว done หนึ่งแถวพอดี",
    "screenshot: ถ่ายทุก cell บันทึกในโฟลเดอร์ shots/ ตามชื่อในคอลัมน์ screenshot "
    "และ crop ชื่อ อีเมล และรูปบัญชีออกก่อนใส่ artifact; ห้ามสร้าง share link สาธารณะของแชต",
    "ช่วงเวลา: ป้อนครบ 84 แชตภายใน 3 วันปฏิทินติดกัน (เวลาไทย) และทุกวันที่ต้องอยู่ภายใน ±7 วัน "
    "จากช่วงวันที่เก็บแขน B ของรอบ ต.ค. ของ proxy คู่กัน",
    "หลังแชตครบ: รันขั้น C2 ของ RUNBOOK_v2 (chat_log_export.py) ซึ่งตรวจไฟล์นี้และไฟล์ raw "
    "แล้วเขียน log_index.tsv และ raw_manifest.tsv",
]


def col_letter(name):
    from openpyxl.utils import get_column_letter
    return get_column_letter(LOG_COLUMNS.index(name) + 1)


def build(cells, out):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill, Protection
    from openpyxl.worksheet.datavalidation import DataValidation

    wb = Workbook()
    ws = wb.active
    ws.title = "log"
    ws.append(LOG_COLUMNS)
    for c in ws[1]:
        c.font = Font(bold=True)
    grey = PatternFill("solid", fgColor="EEEEEE")
    n_base = 0
    for cell in sorted(cells, key=lambda r: r["order"]):
        for app in APPS:
            pid = cell["prompt_id"]
            row = {k: None for k in LOG_COLUMNS}
            row.update({"app": app, "order": cell["order"], "prompt_id": pid, "attempt": 1,
                        "raw_file": raw_name(app, pid), "raw2_file": raw_name(app, pid, turn=2),
                        "screenshot": shot_name(app, pid)})
            ws.append([row[k] for k in LOG_COLUMNS])
            n_base += 1
    last_base = 1 + n_base
    last = last_base + REDO_ROWS
    for r in range(2, last + 1):
        for j, name in enumerate(LOG_COLUMNS, 1):
            c = ws.cell(row=r, column=j)
            locked = r <= last_base and name in LOCKED_PREFILLED
            c.protection = Protection(locked=locked)
            if locked:
                c.fill = grey
            if name in TS_COLUMNS:
                c.number_format = TS_FORMAT
    dv_status = DataValidation(type="list", formula1='"' + ",".join(STATUS_VALUES) + '"', allow_blank=True)
    dv_yn = DataValidation(type="list", formula1='"' + ",".join(YN_VALUES) + '"', allow_blank=True)
    dv_app = DataValidation(type="list", formula1='"' + ",".join(APPS) + '"', allow_blank=True)
    for dv in (dv_status, dv_yn, dv_app):
        ws.add_data_validation(dv)
    dv_status.add(f"{col_letter('status')}2:{col_letter('status')}{last}")
    dv_yn.add(f"{col_letter('turn2_sent')}2:{col_letter('turn2_sent')}{last}")
    dv_app.add(f"{col_letter('app')}{last_base + 1}:{col_letter('app')}{last}")
    widths = {"app": 9, "order": 6, "prompt_id": 18, "attempt": 8, "status": 8, "ts_sent_ict": 20,
              "ts_done_ict": 20, "ui_model_label": 18, "limit_banner": 18, "tools_visible": 14,
              "turn2_sent": 10, "raw_file": 34, "raw2_file": 40, "screenshot": 34, "note": 40}
    for name, w in widths.items():
        ws.column_dimensions[col_letter(name)].width = w
    ws.freeze_panes = "A2"
    ws.protection.sheet = True
    ws.protection.formatColumns = False
    ws.protection.formatRows = False

    st = wb.create_sheet("setup")
    st.append(["key", "รายการ", "ค่า", "หมายเหตุ"])
    for c in st[1]:
        c.font = Font(bold=True)
    for key, label, _kind in SETUP_FIELDS:
        st.append([key, label, None, None])
    for r in range(2, len(SETUP_FIELDS) + 2):
        for j in (1, 2):
            st.cell(row=r, column=j).protection = Protection(locked=True)
            st.cell(row=r, column=j).fill = grey
            st.cell(row=r, column=j).alignment = Alignment(wrap_text=True, vertical="top")
        for j in (3, 4):
            st.cell(row=r, column=j).protection = Protection(locked=False)
    st.column_dimensions["A"].width = 30
    st.column_dimensions["B"].width = 80
    st.column_dimensions["C"].width = 30
    st.column_dimensions["D"].width = 40
    st.protection.sheet = True
    st.protection.formatColumns = False
    st.protection.formatRows = False

    rd = wb.create_sheet("README")
    for line in README_TH:
        rd.append([line])
    rd.column_dimensions["A"].width = 140
    for row in rd.iter_rows():
        for c in row:
            c.alignment = Alignment(wrap_text=True, vertical="top")
    rd["A1"].font = Font(bold=True)
    wb.save(out)
    return n_base


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--cells", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if os.path.exists(a.out):
        die(f"--out exists, refusing to overwrite: {os.path.basename(a.out)}")
    cells = read_cells(a.cells)
    if len(cells) != CELLS_PER_APP:
        die(f"{len(cells)} cells in {os.path.basename(a.cells)}, expected {CELLS_PER_APP}")
    n = build(cells, a.out)
    print(f"log rows: {n} pre-filled (cell-major) + {REDO_ROWS} redo rows; setup fields: {len(SETUP_FIELDS)}")
    print(f"[out] {os.path.basename(a.out)} sha256={sha256_file(a.out)}")


if __name__ == "__main__":
    main()
