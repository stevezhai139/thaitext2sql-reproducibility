# CHANGELOG k3_suite_v1.3 → k3n_suite_v1.3n (answer key สำหรับฐาน k3n; 14 ต.ค. 2026)

ไฟล์นี้บันทึกเฉพาะส่วนที่ `CHANGELOG_v1.2_to_v1.3.md` ไม่ครอบคลุม ส่วนที่เหลือของ answer key ใช้ตามไฟล์นั้นทุกข้อ

**ขอบเขต:** v1.3n คือ answer key v1.3 ที่ปรับให้ใช้กับฐาน k3n (k3 ที่แปลงสตริง 'None' เป็น NULL ใน 6 cell ตามกฎข้อมูล) suite ทางการของ v1.3n มีสองไฟล์ตามมติ D11 (หัวข้อ 5)
- `suite/k3n_suite_v1.3n.tsv` (สำเนาของ `kst_rev/wf_null/core/k3n_suite_v1.3n_DRAFT.tsv`, sha256 195839ec…): suite ของการ re-grade log ส.ค. (Gate 2) ซึ่ง Q27 ยังเป็นข้อความเดิมและเป็น excluded
- `suite/k3n_suite_v1.3n_oct.tsv` (สร้างโดย `kst_rev/gate0/suite_tools/build_oct_core_suite.py`, sha256 96b8e9f2…): suite core ของรอบ ต.ค. (Gate 3) ซึ่ง Q27 เป็นโจทย์ฉบับซ่อมและเป็น primary

ส่วน `suite/k3_suite_v1.3.tsv` (7e46649c…) ใช้กับฐาน k3 เป็น sensitivity เท่านั้น

**สิ่งที่ไม่เปลี่ยน (suite ของ ส.ค. `suite/k3n_suite_v1.3n.tsv`):** id, tier, schema, eff, question_en, question_th, notes, gold_sql_draft, gold_sql_v12, v13_status, order_en, order_th, sort_keys, norm, v13_rule และ alternative ทุกตัวยกเว้นของ Q20 เหมือน v1.3 ทุกตัวอักษร (ตรวจแบบ TEST-ONLY: ระหว่างสองไฟล์มีเพียง 5 cell ที่ต่างกัน คือ Q16 v13_rationale, Q20 alt_gold_en, Q20 alt_gold_th, Q20 v13_rationale และ Q48 v13_rationale); suite ของรอบ ต.ค. (`suite/k3n_suite_v1.3n_oct.tsv`) ต่างจาก suite ของ ส.ค. เพิ่มเฉพาะบรรทัดของ Q27 (หัวข้อ 5) suite v1.3n ไม่เพิ่มคอลัมน์ และ `selftest_v13n.py` ตรวจความเหมือนกับ v1.2 ของคอลัมน์โจทย์ทุกข้อ ยกเว้นข้อที่ซ่อมตามมติ D11 ใน suite ของรอบ ต.ค. (หัวข้อ 5)

## 1. รายข้อ (3 ข้อ)

| ข้อ | v1.3 (บน k3) | v1.3n (บน k3n) | เหตุผล |
|---|---|---|---|
| Q20 | alternative (EN, TH) `WHERE m.SpouseName <> 'None'` ได้ 48 แถว | alternative (EN, TH) `WHERE m.SpouseName IS NOT NULL` ได้ 48 แถว | บน k3n ชื่อคู่สมรสของ James Buchanan เป็น NULL ข้อความเดิมยังได้ 48 แถวเพียงเพราะ `NULL <> 'None'` ให้ผล unknown จึงเขียนใหม่ให้ตรงความหมายของ D2c (ไม่นับแถวที่ไม่มีคู่สมรส); primary แสดงแถว (Buchanan, NULL, Democratic) ตามเดิม รวม 49 แถว |
| Q16 | gold เดิม | gold เดิม (เพิ่มเหตุผลใน v13_rationale เท่านั้น) | บน k3n ประธานาธิบดีทุกคนยังแสดงพร้อมชื่อคู่สมรส โดยแถวของ Buchanan มีชื่อคู่สมรสเป็น NULL; คำตอบที่ตัด Buchanan ยังผิดเพราะโจทย์ถาม "each president" |
| Q48 | gold เดิม | gold เดิม (เพิ่มเหตุผลใน v13_rationale เท่านั้น) | บน k3n คอลัมน์ RunnerUp มี NULL 1 ค่า (Washington 1789) เงื่อนไข `IS NOT NULL` ใน gold จึงมีผลจริง (กับดัก NOT IN กับ NULL ทำงาน) ส่วนเงื่อนไข `<> 'None'` ไม่มีผลบน k3n |

ค่า TEST-ONLY (scratch PostgreSQL 16, อ่านอย่างเดียว): Q20 primary 49 แถวทั้งบน k3 และ k3n; alternative ของ v1.3n ได้ 48 แถวบน k3n และ 49 แถวบน k3 (ข้อความ v1.3n จึงใช้กับ k3n เท่านั้น); Q48 primary 29 แถวทั้งสองฐาน

## 2. Errata ของ v1.3 ที่ไม่เป็นจริงบน k3n

`CHANGELOG_v1.2_to_v1.3.md` บรรทัด 55 ระบุว่า "Q48 NULL trap ไม่ทำงาน (RunnerUp ไม่มี NULL)" ข้อความนี้ถูกต้องสำหรับ k3 เท่านั้น บน k3n ค่า RunnerUp ของ Washington 1789 เป็น NULL คำตอบที่ใช้ `NOT IN (SELECT RunnerUp FROM PresidentHolding)` โดยไม่ตัด NULL จะได้ 0 แถวและผิด ไม่แก้ไฟล์เดิม (เป็นบันทึกของ v1.3) แต่ให้อ่านคู่กับหัวข้อนี้

ผลต่อ log เดือน ส.ค. (TEST-ONLY): เมื่อ grade ด้วย v1.3 บน k3 เทียบ v1.3n บน k3n ผลต่างกัน 15 run เท่านั้น (llama31-8b EN Q25 ×5, EN Q48 ×5, TH Q48 ×5 จากถูกเป็นผิด) ตัวเลขทางการมาจากการรันของผู้เขียนใน Gate 2

## 3. ข้อยกเว้นลำดับคอลัมน์ที่มีทิศทาง (issue 11) กับข้อ core

**มติที่มีอยู่:** brief 1.2 กำหนด G1 (ไม่ให้คะแนนลำดับคอลัมน์) พร้อมข้อยกเว้นเมื่อโจทย์ให้คอลัมน์มีบทบาทต่างกัน รายการข้อมีทิศทางใน brief คือ X34, X37, F7C-6 และ FK4 ถ้าใช้ข้อสำรอง ซึ่งไม่มีข้อ core ส่วนชีต "ประเด็นค้าง" ข้อ 11 ของ workbook การคัดเลือกชุดขยายระบุว่ากฎ "ใช้กับทั้ง core และชุดขยาย"

**การ scan ข้อ core (อ่านอย่างเดียวบน `k3n_suite_v1.3n_DRAFT.tsv` และ k3n, TEST-ONLY):**
- ข้อที่ gold มีคอลัมน์ชนิดเดียวกันอย่างน้อยสองคอลัมน์ซึ่งการสลับยังผ่าน G1 ได้ เช่น Q23 (ชื่อประธานาธิบดี/ชื่อคู่สมรส), Q28 (ประธานาธิบดี/รองประธานาธิบดี), Q35 (first_start/last_end), Q42 (returned/kept), Q54 (total/mom_change), Q58 (CustomerID/days_between)
- การคัดกรอง OQ (14 ต.ค.) แยกต่อเป็น 7 ข้อที่คอลัมน์มาจาก domain เดียวกันและการสลับเปลี่ยนความหมาย ได้แก่ Q17 (ปีเริ่ม/ปีสิ้นสุด), Q22 (ประธานาธิบดี/ผู้ได้อันดับสอง), Q28 (ประธานาธิบดี/รองประธานาธิบดี), Q35 (ปีเริ่มแรก/ปีสิ้นสุดสุดท้าย), Q42 (คืน/ไม่คืน), Q49 (ระยะเวลา/อันดับ) และ Q54 (รายได้รวม/ผลต่าง) โดยไม่รวม Q16/Q20/Q23 (คู่ประธานาธิบดีกับคู่สมรสเป็นความสัมพันธ์สมมาตรและค่าบอกบทบาทเอง) และ Q58/Q59 (คอลัมน์ต่าง domain)

**สถานะ:** ผู้เขียนตอบ OQ35 ทาง (ก) เมื่อ 14 ต.ค. 2026 (คำตอบ triage ใน brief หัวข้อ 1.0c และ `TRIAGE_OQ_2026-10-14.md`) และบันทึกคำตอบลงใน entry `core_directional` แล้ว ข้อความ `"status"` จึงไม่มี marker ว่ารอผู้เขียน

**ที่บันทึกการตัดสิน (OQ35):** การตัดสินของผู้เขียนและค่าที่ใช้ grade จริงอยู่ที่เดียว คือ entry `core_directional` ใน `harness/suite_columns.json` (ค่า `"apply"`, รายการ `"items"` และข้อความ `"status"`) ไฟล์นี้ไม่ทำซ้ำค่าปัจจุบันของ entry นั้น ค่าที่ใช้ในการรันแต่ละครั้งอ่านได้จาก stderr ของ `grade_v13n.py` และ stdout ของ `selftest_v13n.py` ซึ่งพิมพ์ apply, รายการข้อ และ status จาก entry นี้ ทางเลือกสามทางเขียนลงใน entry ได้ดังนี้
- ทาง (ก): `"apply": true` กับรายการใน `"items"` (รายการที่การคัดกรองเสนอคือ 7 ข้อข้างต้น; ค่าของแต่ละข้อเป็นกลุ่มของ index คอลัมน์ใน gold เริ่มที่ 0; ภายในกลุ่มคำตอบต้องเรียงคอลัมน์ตาม gold ส่วนคอลัมน์อื่นยังสลับได้ตาม G1)
- ทาง (ข): `"apply": false` (core ใช้ G1 ล้วน)
- ทาง (ค): `"apply": false` และ grade sensitivity ของรายการใน `"items"` ด้วย `grade_v13n.py --core-directional on` (flag นี้แทนค่า apply เฉพาะการรันครั้งนั้น และพิมพ์ใน stderr ว่าแทนค่าแล้ว; ไม่ต้องมีสำเนาของไฟล์) ทางนี้จึงมีการ grade เพิ่มหนึ่งครั้งต่อ log ที่รายงาน
- การบันทึกคำตอบของผู้เขียนแก้เฉพาะ entry นี้ คือค่า `"apply"`, รายการ `"items"` (ถ้าเปลี่ยน) และข้อความ `"status"` (เช่น `DECIDED (OQ35): option (a)`) จึงไม่ต้องแก้โค้ด ไม่เกิด diff ใหม่ และ hash ของโค้ดไม่เปลี่ยน
- ระหว่างที่ข้อความ `"status"` ยังมี marker ว่ารอผู้เขียน (ค่าคงที่ `PENDING_MARK` ของ `selftest_v13n.py`) self-test ไม่ผ่านในขั้นทางการ (ผ่านได้เฉพาะ test ที่ส่ง `--allow-draft-testonly`) เพื่อไม่ให้ entry ที่ยังไม่ตัดสินเข้าสู่ commit ของ Gate 1b
- ถ้าผู้เขียนเพิ่มหรือตัดข้อจากรายการที่เสนอ ให้แก้ย่อหน้า "การ scan ข้อ core" ข้างต้นให้ตรงด้วย เพราะย่อหน้านั้นเป็นเหตุผลของรายการ ไม่ใช่ค่าที่ใช้ grade
- suite v1.3n ไม่มีคอลัมน์ col_roles; `grade_v13n.py` และ `selftest_v13n.py` อ่านรายการจาก entry นี้เท่านั้น ถ้า suite ใดมีคอลัมน์ col_roles ค่าในคอลัมน์ต้องเท่ากับทะเบียน มิฉะนั้น grader ปฏิเสธ
- sensitivity ที่มีในทุกทาง: `--no-col-roles` (G1 ล้วน) และ `--colperm off` (เทียบตามตำแหน่งทั้ง projection); `--core-directional on|off` ใช้เป็น sensitivity เท่านั้น

**ผลต่อ log เดือน ส.ค. (TEST-ONLY):** เมื่อใช้ทาง (ก) กับรายการที่เสนอ ผลของ `grade_v13n.py` บน k3n กับ v1.3n เหมือน `grade_v13.py` ทุก byte ทั้ง CSV และ stdout (default: CSV 30d29a82…, stdout 0c49a638…) จึงไม่มี run ใดของ ส.ค. ที่ผลเปลี่ยน ทางเลือกนี้จึงไม่กระทบการเทียบความสอดคล้อง ส.ค.–ต.ค. ผลต่อรอบ ต.ค. ยังไม่มีข้อมูล (การเลือกต้องตรึงก่อน commit ของ Gate 1b)

## 4. Grader และ selftest ที่ใช้กับ v1.3n

- `harness/grade_v13n.py`: grader ของ record ตัวเดียวสำหรับ k3n (G1–G4, ข้อยกเว้นทิศทาง, MI-1b, guard ว่าฐานตรงกับ fingerprint และสถิติแยกตาม arm) โดยเก็บ `harness/grade_v13.py` (aed86b26…) เป็นฉบับอ้างอิงที่ไม่แก้; `parity_grader.py` พิสูจน์ว่าผลเหมือนกันทุก byte นอกข้อ MI และข้อมีทิศทาง
- `harness/selftest_v13n.py`: ตรวจ suite บน k3n (TEST-ONLY: suite ของ ส.ค. 60 ข้อ, primary 59, รัน gold key 151 ตัว, PASS; suite ของรอบ ต.ค. 60 ข้อ, primary 60, รัน gold key 151 ตัว, PASS) และพิมพ์บรรทัด `core session: ...` ว่า suite ที่ตรวจเป็นของ ส.ค. หรือของรอบ ต.ค.
- การตัดข้อมาจากคอลัมน์ `v13_status` ของ suite เท่านั้น gold ที่ว่างไม่ทำให้ข้อถูกตัดโดยอัตโนมัติ
  - suite ของ ส.ค.: Q27 excluded; การ re-grade log ส.ค. ใช้ n=59 และรายงาน n=60 (`--keep-excluded`) เป็น sensitivity; การเทียบ ส.ค.–ต.ค. ใช้ 59 ข้อที่เหมือนกัน
  - suite ของรอบ ต.ค. (มติ D11): ไม่มีข้อ excluded ผลหลักของรอบ ต.ค. ใช้ n=60
- sensitivity ของชุดขยายบน k3 (OQ28.3) ใช้ `grade_v13n.py --skip-mi-items` ซึ่งนำข้อ MI (PK1, FK1, FK2) และ record ของข้อเหล่านั้นออกก่อน grade พิมพ์จำนวน record ที่นำออก และ grade ข้อที่เหลือบนฐานของ `--pg` เพียงฐานเดียว โหมดนี้ใช้ร่วมกับ `--mi-manifest` ไม่ได้
- `grade_v13n.py` ไม่เขียนทับไฟล์ผลที่มีอยู่แล้ว เว้นแต่ส่ง `--overwrite` และไม่เขียน `results/graded.csv` หรือ log `results*.jsonl` ในทุกกรณี; ข้อ MI (คอลัมน์ `mi_instances` หรือรายการ `mi_items` ของ `suite_columns.json`) ต้อง grade ด้วย manifest ที่ `build_instances.py --record` บันทึกแล้วเท่านั้น (manifest สถานะอื่นใช้ได้เฉพาะ test ที่ส่ง `--allow-draft-testonly`)
- สำหรับข้อ MI คอลัมน์ `matched_gold` ของไฟล์ graded คือ key ที่ตรงกันบนทุก instance ตามกฎ MI-1b (ว่างเมื่อไม่มี key ใดตรงทุก instance) ส่วน key ที่ตรงในแต่ละ instance อยู่ใน sidecar ของ `--mi-log`; ข้อนี้ต่างจากแบบงานหัวข้อ 3.9 ซึ่งให้ใช้ key ของ base

## 5. มติ D11: suite core ของรอบ ต.ค. (`k3n_suite_v1.3n_oct.tsv`)

**มติ:** ผู้เขียนตัดสินเมื่อ 14 ต.ค. 2026 (brief หัวข้อ 1.0b) ให้ซ่อม Q27 แทนการตัดออก โดยใช้กับรอบ ต.ค. เท่านั้น รอบ ต.ค. จึง grade core ครบ 60 ข้อ (100 ข้อเมื่อรวมชุดขยาย) ส่วนการ re-grade log ส.ค. คง Q27 ฉบับเดิมเป็น excluded (n=59) และการเทียบ ส.ค.–ต.ค. ใช้ 59 ข้อที่เหมือนกัน

**รายละเอียดที่ใช้ค่าตั้งต้นของผู้ช่วย** (ผู้เขียนอนุมัติค่าตั้งต้นทั้งหมดแล้ว จึงเปิดเผยเป็นค่าตั้งต้น):
- suite ของรอบ ต.ค. เป็นไฟล์ใหม่แยกจาก suite ของ ส.ค. และไม่แก้ไฟล์ของ ส.ค.
- การตรวจ byte ของ prompt มีข้อยกเว้นเพียงรายการเดียว คือ call ของแขน base ของ Q27 และประกาศในค่าคงที่เดียว
- n=60 เป็นผลหลักของรอบ ต.ค. และ 59 ข้อที่เหมือนกันใช้ในการเทียบ ส.ค.–ต.ค.
- RQ3 ของรอบ ต.ค. ใช้ gold ฉบับซ่อมของ Q27 ส่วน RQ3 ของ ส.ค. ไม่เปลี่ยน
- ข้อความ TH ของ Q27 ใน `Q27_REPAIR_2026-10-14.tsv` เป็นฉบับสุดท้าย

**ข้อมูลเข้า:** `kst_rev/gate0/suite_tools/Q27_REPAIR_2026-10-14.tsv` (sha256 229ea98a…) คอลัมน์ `decided` ระบุผู้ตัดสินเป็นบทบาท ("author") ไม่มีชื่อบุคคล

**บรรทัดของ Q27 ในสอง suite:**

| คอลัมน์ | suite ของ ส.ค. (`k3n_suite_v1.3n.tsv`) | suite ของรอบ ต.ค. (`k3n_suite_v1.3n_oct.tsv`) |
|---|---|---|
| question_en | Find pairs of orders placed by the same customer on the same date (show CustomerID, both OrderIDs). | Find pairs of orders placed by the same customer in the same month (show CustomerID and both OrderIDs; list each pair once). |
| question_th | ข้อความเดิม (เหมือน v1.2) | หาคู่ของคำสั่งซื้อที่สั่งโดยลูกค้าคนเดียวกันในเดือนเดียวกัน (โดยให้แสดง CustomerID และ OrderID ของทั้งสองคำสั่งซื้อ และให้แสดงแต่ละคู่เพียงแค่ครั้งเดียวเท่านั้น) |
| gold_sql_draft | self-join ที่ `e1.OrderDate = e2.OrderDate AND e1.OrderID < e2.OrderID` | self-join ที่ `date_trunc('month', e1.OrderDate) = date_trunc('month', e2.OrderDate) AND e1.OrderID < e2.OrderID` |
| gold_sql_v12 | gold ของ v1.2 (โจทย์เดิม) | ว่าง (v1.2 ไม่มี gold ของโจทย์ฉบับซ่อม) |
| v13_status | excluded | primary |
| v13_rule | D3 | D11 |
| v13_rationale | gold ว่างบนฐานที่ใช้รัน (n=59) | เหตุผลของ D11 (ซ่อมสำหรับรอบ ต.ค. เท่านั้น) |

คอลัมน์อื่นของ Q27 (tier 2, schema E, eff no, notes ว่าง, order_en และ order_th เป็น no, sort_keys, norm, alt_gold_en และ alt_gold_th ว่าง) เหมือนกันในสอง suite ผู้เขียนไม่ได้บันทึก alternative ของโจทย์ใหม่ บรรทัดอื่นทั้ง 59 บรรทัดและ header ของ suite ของรอบ ต.ค. เหมือน suite ของ ส.ค. ทุก byte (ตรวจแบบ TEST-ONLY)

**ตัวสร้างและการตรวจซ้ำ:** `kst_rev/gate0/suite_tools/build_oct_core_suite.py` สร้าง suite ของรอบ ต.ค. จาก suite ของ ส.ค. (ต้องมี sha256 195839ec…) และไฟล์ซ่อม
- แทนเฉพาะบรรทัดของข้อที่ซ่อม บรรทัดอื่นคัดลอกจาก byte ของ suite ของ ส.ค. (CRLF และการ quote แบบเดิม)
- ปฏิเสธ input ที่ไม่ตรงเงื่อนไข (exit 2 และไม่เขียนไฟล์) เช่น ไฟล์ซ่อมที่มีช่อง `decided` ว่างหรือยังมีคำว่า PENDING, ข้อความเดิมในไฟล์ซ่อมที่ไม่ตรงกับ suite ของ ส.ค. หรือผลที่มีบรรทัดอื่นเปลี่ยน
- โหมด `--check` สร้างใหม่ในหน่วยความจำแล้วเทียบกับไฟล์ที่มีอยู่ทุก byte โดยไม่เขียนไฟล์ ส่วน `--pg` พิมพ์จำนวนแถวของ gold ใหม่และ gold เดิมบนฐานที่ระบุ (อ่านอย่างเดียว)
- ไฟล์ `k3n_suite_v1.3n_oct.sha256` ข้าง suite บันทึก sha256 ของ suite ของรอบ ต.ค. (96b8e9f2…), ของ suite ของ ส.ค. (195839ec…), ของไฟล์ซ่อม (229ea98a…) และของตัวสร้าง

**ค่า TEST-ONLY บน k3n (scratch PostgreSQL 16, อ่านอย่างเดียว):** gold ใหม่ได้ 6 แถว; คำตอบที่แสดงคู่ทั้งสองทิศได้ 12 แถว (ผิด เพราะโจทย์ให้แสดงแต่ละคู่ครั้งเดียว); การอ่านเป็น "ภายใน 30 วัน" ได้ 9 แถว (ผิด); การเทียบเดือนด้วย `EXTRACT(MONTH ...)` โดยไม่ดูปีได้ 6 แถวเท่ากับ gold เพราะข้อมูลทั้งหมดอยู่ในปี 2024; gold เดิมได้ 0 แถว คำตอบที่สลับลำดับ OrderID ทั้งสองคอลัมน์ยังถูกตาม G1

**prompt ของแขน base:** prompt ของรอบ ต.ค. ตรงกับ run-of-record ส.ค. ทุก byte ยกเว้นข้อความผู้ใช้ของ Q27 ซึ่งเป็นโจทย์ฉบับซ่อม ข้อยกเว้นนี้ประกาศครั้งเดียวในค่าคงที่ `D11_PROMPT_EXCEPTION` ของ `harness/check_prompts_rc1.py` (sha256 ของข้อความ EN b4f5803d… และ TH e68798bf…)
- `check_prompts_rc1.py` สร้าง prompt และ body ของ ส.ค. จาก runner ของ commit 2f8db3d กับ `suite/k3_suite_v1.2.tsv` ใน commit เดียวกัน (อ่านด้วย `git show`) แล้วตรวจว่า prompt และ body ของแขน base ของข้ออื่นทุกข้อเท่ากับของ ส.ค.
- call ของ Q27 ต้องใช้ข้อความใหม่ (6 โมเดล × 2 ภาษา × 5 run = 60 call) และต้องต่างจาก body ของ ส.ค.
- แผน dry-run ที่สร้างจาก suite ของ ส.ค. (Q27 ข้อความเดิม) จึง FAIL สองรายการของ D11

**ทะเบียนข้อที่ซ่อม:** entry `core_repaired` ใน `harness/suite_columns.json` (items: Q27) ใช้โดย `selftest_v13n.py`
- check 2: ยอมให้เฉพาะข้อในทะเบียนต่างจาก v1.2 และเฉพาะเมื่อเป็น primary (tier, schema, eff และ notes ยังต้องเท่ากับ v1.2; question_en และ question_th ต้องต่างจาก v1.2; gold_sql_v12 ต้องว่าง)
- check 5: รับ suite core ที่มีเฉพาะข้อในทะเบียนเป็น excluded (suite ของ ส.ค.) หรือไม่มีข้อ excluded เลย (suite ของรอบ ต.ค.) และพิมพ์บรรทัด `core session: ...`

**grader:** `harness/grade_v13n.py` ไม่เปลี่ยน
- บน suite ของรอบ ต.ค. ค่าตั้งต้น grade ครบ 60 ข้อ และ `--keep-excluded` ไม่เปลี่ยนผล (TEST-ONLY)
- คอลัมน์ `correct_v12` ของ Q27 ในรอบ ต.ค. เทียบตามวิธีของ v1.2 กับ gold ฉบับซ่อม (grader ใช้ `gold_sql_draft` เมื่อ `gold_sql_v12` ว่าง) จึงไม่ใช่ผลของ answer key v1.2

**RQ3:** Q27 มี eff = no ในทุก suite จึงไม่อยู่ในชุดข้อของ RQ3 ทั้งสองรอบ กฎการเลือก gold ของข้อที่ซ่อมใน RQ3 อยู่ใน `harness/plan_quality.py`

ตัวเลขทุกตัวในไฟล์นี้เป็น TEST-ONLY จาก scratch PostgreSQL 16 ตัวเลขทางการมาจากการรันของผู้เขียนเท่านั้น
