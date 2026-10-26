# รายงานการสร้าง suite ชุดขยาย k3n_ext_suite_v1.0: ฉบับตรึง (FROZEN)

- ตัวสร้าง: build_ext_suite 1.2 (Gate 0, 2026-10-14)
- โหมด: `--freeze`
- สถานะ: ตรึงแล้ว (ไม่มี blocker)
- ตัวเลขทุกตัวในรายงานนี้มาจากฐานที่ระบุใน `--pg` ของการรันครั้งนี้ ถ้ารันบน scratch ถือเป็น TEST-ONLY

## 1. การอนุมัติ ext_decisions

- sha256 ของ ext_decisions ที่อ่าน: `8c333fac7dec3201e84b86dedb150f0a5c8a12cf6088931e0f36a1b0860091d2`
- sha256 ที่ผู้เขียนพิมพ์ (`--approved-decisions-sha256`): `8c333fac7dec3201e84b86dedb150f0a5c8a12cf6088931e0f36a1b0860091d2`
- ตรงกัน: ใช่
- author_approved: `true`
- การอนุมัติที่บันทึกในไฟล์: เวลา `2026-10-14, before 09:36 ICT (author approved in chat; content sha256 03144a34d6f197db8e18ba13fc4689a6d8150b85447e5c6ab2e4a7b571f73c7d)`, อ้างอิง `KST_REVISION_2026-10-12.md, entry of 14 Oct 2026: author approval of ext_decisions_2026-10-14.json (sha256 03144a34...)`

## 2. blocker

ไม่มี

ช่องการตัดสินที่ว่างใน TRANSLATION_FIXES: ชีต ตัด EN 0 ช่อง, ชีต ตัดสินอื่น 0 ช่อง, ชีต แก้ TH 0 ช่อง

## 3. input (label กลางและ sha256; ไม่บันทึก path และไม่ใช้ชื่อไฟล์ที่มีชื่อบุคคล)

label `sql_TESTONLY` คือ digest ของทั้งโฟลเดอร์แบบเดียวกับแถวโฟลเดอร์ของ freeze_stamp.py ส่วน `sql_TESTONLY/<ไฟล์>` คือไฟล์ที่ตัวสร้างอ่านจริง ซึ่ง pin ไว้ใน ext_decisions

| label | sha256 |
|---|---|
| builder/build_ext_suite.py | `85693132b1a9c339b525ca2a5dfb899a8e8db1924f56b30058ac7f9342d806a3` |
| ext_decisions | `8c333fac7dec3201e84b86dedb150f0a5c8a12cf6088931e0f36a1b0860091d2` |
| item_changes | `115efabdcfe1006c6e091b3bd03b9d33f5679441dea3b21e6e46db565c5087ba` |
| item_changes_add | `a38d8103a1156f17bc74b4a2ba8f9b16161a12e87c7c2ccbf0510710e5b48920` |
| items_json | `ca89abb17651c59c4a1baeb7d93141a8411fe8356cc324ff9571732f0ae7ce60` |
| lib/grade_v13.py | `aed86b26bd83548a215ee1999bd9c47d524558af1ca34b03909bc1144518e038` |
| lib/vg_rule.py | `1fd1e28e7fb47806f789e536ba5bd40c537f3b40c0dadcf4719ebdf9c38423f3` |
| metadata_refresh | `26724a108a08aee3f5a73ca6cef2c9765d66e9ace0f4d609b81436e3418d988a` |
| mi_manifest | `98d0ce0e11a0ee2df5f41412a4c36d98c5a9b5ec896011c8fa9f423856ebe0c5` |
| selection_xlsx | `63a7bbe058e25647e4c612be08b1fd549563191d83fd6424814d443d0e16a667` |
| sql_TESTONLY | `e9fa6501ff1b3d2d41bdcadfb0841aa68af2cafad2237f671d2575657ef6142a` |
| sql_TESTONLY/FK1__new_format_DRAFT.sql | `f13960c067198c358d3e0015890272fbce55abbf21c638bcf9fc71db8eb84ad3` |
| suite_columns | `46afcc4f3ef5a63702f2940bdf41efd2bbcfee13fa152474fa591284c83f65ce` |
| translation_fixes_xlsx | `fd6ffe00a3d81f5d25d68e255abafde43b2f5d33bc394be76e7193489f1125dc` |
| typo_fixes | `d9f8c8673daf70169fb357534dc63dac3c0fdccb4516338b54f19be1ff86c2be` |

## 4. สมาชิกและจำนวน

- ชุด 40 ข้อ (ลำดับรัน): X01, X02, X03, X04, X05, X07, X08, X09, X10, X11, X12, X13, X14, X17, X18, X19, X20, X21, X23, X24, X25, X26, X27, X28, R5, F7C-6, F7C-2, F7C-8, F7C-1, F7C-3, X33, X34, X35, X36, X37, X38, PK1, FK1, FK2, FK3
- ข้อสำรอง (ไฟล์ข้อสำรองติด DRAFT ทุกแถวจนกว่าจะใช้กฎแทนที่): F7C-7, F7C-5, F7C-4, FK4
- ตระกูล: F1 5, F2 4, F3 4, F4 5, F5 3, F6 4, F7 5, F8 4, F9 2, F10 4
- tier: T2 3, T3 3, T4 34
- ข้อ VG: F7C-1, F7C-2, F7C-3, X10, X26, X27
- ข้อมีทิศทาง (col_roles จาก suite_columns.json): X34 `2,3`, X37 `0,1`, F7C-6 `0,1`
- ข้อหลาย instance (MI-1b): PK1 5 instance, FK1 3 instance, FK2 2 instance
- กฎข้อสำรอง: กฎข้อสำรองของ AMENDMENT-9: (1) ค่าตั้งต้นคือไม่ใช้ข้อสำรอง และไฟล์ข้อสำรองติดป้าย DRAFT ทุกแถว (2) ข้อสำรองแทนข้อในชุด 40 ข้อได้เฉพาะก่อน call แรกของชุดขยาย และเฉพาะเมื่อผู้เขียนยืนยันว่าข้อนั้นมีข้อบกพร่องของคำแปลที่ทำให้ EN และ TH ถามคนละคำถาม โดยบันทึกเป็น addendum ลงวันที่ ซึ่งตรึง suite ฉบับ FROZEN ใหม่และ prompts ของ dry-run ก่อน call แรก (3) การเลือกใช้ข้อสำรองในตระกูลเดียวกันก่อน (F7: F7C-7, F7C-5, F7C-4; F10: FK4) ถ้าตระกูลนั้นไม่มีข้อสำรอง ใช้ตามลำดับ F7C-7, F7C-5, F7C-4, FK4 ข้อสำรองที่นำมาใช้ต้องแก้ TH ตามรายงานการตรวจคำแปลก่อนตรึง และรันครบทั้งหกโมเดล (2 ภาษา × 5 run แขน base) โดย FK4 ใช้ข้อยกเว้นลำดับคอลัมน์ที่มีทิศทางตาม brief 1.2 (4) หลัง call แรกของชุดขยายไม่มีการแทนหรือตัดข้อใด ข้อที่พบว่า gold ผิดแก้ด้วย R-v1.3 (D1/D2) และรายงานทั้งผลตาม key เดิมและ key ที่แก้ (5) การแทนที่ทุกครั้งรายงานในเล่ม

## 5. gold บนฐานหลัก (แถว x คอลัมน์)

| ข้อ | ตระกูล | tier | gold | VG | col_roles | หมายเหตุ |
|---|---|---|---|---|---|---|
| X01 | F1 | T4 | 4x2 | no | - |  |
| X02 | F1 | T4 | 13x1 | no | - |  |
| X03 | F1 | T4 | 7x1 | no | - |  |
| X04 | F1 | T4 | 23x3 | no | - |  |
| X05 | F1 | T4 | 9x3 | no | - |  |
| X07 | F2 | T4 | 6x3 | no | - |  |
| X08 | F2 | T4 | 7x1 | no | - |  |
| X09 | F2 | T4 | 7x1 | no | - |  |
| X10 | F2 | T4 | 15x1 | yes | - |  |
| X11 | F3 | T2 | 2x1 | no | - |  |
| X12 | F3 | T4 | 7x1 | no | - |  |
| X13 | F3 | T2 | 8x1 | no | - |  |
| X14 | F3 | T2 | 9x1 | no | - |  |
| X17 | F4 | T4 | 8x2 | no | - |  |
| X18 | F4 | T4 | 24x2 | no | - |  |
| X19 | F4 | T4 | 18x2 | no | - |  |
| X20 | F4 | T4 | 19x1 | no | - |  |
| X21 | F4 | T4 | 10x1 | no | - |  |
| X23 | F5 | T4 | 1x1 | no | - |  |
| X24 | F5 | T4 | 1x1 | no | - |  |
| X25 | F5 | T4 | 1x1 | no | - |  |
| X26 | F6 | T4 | 1x1 | yes | - |  |
| X27 | F6 | T3 | 1x1 | yes | - |  |
| X28 | F6 | T4 | 2x2 | no | - |  |
| R5 | F6 | T3 | 21x2 | no | - |  |
| F7C-6 | F7 | T4 | 9x2 | no | 0,1 |  |
| F7C-2 | F7 | T4 | 4x1 | yes | - |  |
| F7C-8 | F7 | T4 | 7x1 | no | - |  |
| F7C-1 | F7 | T4 | 2x1 | yes | - |  |
| F7C-3 | F7 | T3 | 8x1 | yes | - |  |
| X33 | F8 | T4 | 2x1 | no | - |  |
| X34 | F8 | T4 | 28x4 | no | 2,3 |  |
| X35 | F8 | T4 | 45x3 | no | - |  |
| X36 | F8 | T4 | 45x4 | no | - |  |
| X37 | F9 | T4 | 11x2 | no | 0,1 |  |
| X38 | F9 | T4 | 7x2 | no | - |  |
| PK1 | F10 | T4 | 1x1 | no | - |  |
| FK1 | F10 | T4 | 0x2 | no | - |  |
| FK2 | F10 | T4 | 2x1 | no | - |  |
| FK3 | F10 | T4 | 4x2 | no | - |  |
| F7C-7 | F7 | T3 | 2x1 | yes | - | สำรอง |
| F7C-5 | F7 | T4 | 10x1 | no | - | สำรอง |
| F7C-4 | F7 | T4 | 5x1 | no | - | สำรอง |
| FK4 | F10 | T4 | 4x3 | no | 1,2 | สำรอง |

## 6. gold บน instance ของข้อหลาย instance

| ข้อ | instance | แถว | ตรง expected_gold |
|---|---|---|---|
| FK1 | k3n | 0 | ใช่ |
| FK1 | k3_fk_i_null | 0 | ใช่ |
| FK1 | k3_fk_i_orphan | 1 | ใช่ |
| FK2 | k3n | 2 | ใช่ |
| FK2 | k3_fk_i_null | 2 | ใช่ |
| PK1 | k3n | 1 | ใช่ |
| PK1 | k3_pk_n_named | 1 | ใช่ |
| PK1 | k3_pk_n_dup | 1 | ใช่ |
| PK1 | k3_pk_n_pnull | 1 | ใช่ |
| PK1 | k3_pk_n_spdup | 1 | ใช่ |

## 7. fingerprint และ schema_md5 ของ instance ใน manifest (คำนวณซ้ำบนฐานแล้วเทียบกับค่าที่บันทึก)

| instance | fingerprint ของข้อมูล | schema_md5 |
|---|---|---|
| k3n | ตรงกับค่าที่บันทึก | ตรงกับค่าที่บันทึก |
| k3_pk_n_named | ตรงกับค่าที่บันทึก | ตรงกับค่าที่บันทึก |
| k3_pk_n_dup | ตรงกับค่าที่บันทึก | ตรงกับค่าที่บันทึก |
| k3_pk_n_pnull | ตรงกับค่าที่บันทึก | ตรงกับค่าที่บันทึก |
| k3_pk_n_spdup | ตรงกับค่าที่บันทึก | ตรงกับค่าที่บันทึก |
| k3_fk_i_null | ตรงกับค่าที่บันทึก | ตรงกับค่าที่บันทึก |
| k3_fk_i_orphan | ตรงกับค่าที่บันทึก | ตรงกับค่าที่บันทึก |

schema_md5 ใช้ SCHEMA_STMT ของ db_fingerprint.py ในโฟลเดอร์เดียวกับ manifest (นิยามเดียวกับ build_instances.py); ถ้าไม่พบไฟล์นั้น ตัวสร้างไม่ตรวจซ้ำ และค่านี้ตรวจโดย build_instances.py ใน Gate 1a ขั้น 1a.45

## 8. การเปลี่ยนแปลงจาก workbook

- gold_sql_draft (already_in_workbook): 5 แถว
- gold_sql_draft (applied): 1 แถว
- gold_sql_draft (verified): 1 แถว
- question_en (already_in_workbook): 4 แถว
- question_en (applied): 30 แถว
- question_en (verified): 1 แถว
- question_th (applied): 32 แถว
- question_th (verified): 1 แถว
- รายละเอียดหนึ่งแถวต่อ field อยู่ในไฟล์ ITEM_CHANGES_generated
- แถว ITEM_CHANGES ที่ค่าใน workbook เท่ากับ 'after' อยู่แล้ว (สถานะ already_in_workbook) 9 แถว: ตัวสร้างตรวจได้เพียงว่า 'before' ไม่ว่างและต่างจาก 'after' เพราะค่าเดิมไม่อยู่ใน workbook แล้ว ค่า 'before' ของไฟล์ที่ pin ไว้ตรวจครั้งเดียวใน Gate 0 (test EX-T7g) เทียบกับร่าง EXTENSION_v2_DRAFT_2026-10-13.tsv
- gold ทุกข้อเขียนเป็นบรรทัดเดียวลงท้าย ';' และตรวจว่าผลบนฐานหลักเท่ากับ gold ต้นฉบับ (digest แบบไม่สนลำดับแถว)

## 9. การตรวจอื่น

- anonymity sweep: แหล่ง pattern ได้แก่ CLAUDE.md 9 รายการ, --anon-extra 1 รายการ, --anon-patterns 0 รายการ, บัญชีของเครื่องที่รัน 4 รายการ, pattern ในตัว 3 รายการ (ไม่บันทึกข้อความของ pattern)
- anonymity sweep: ตรวจ 8 ไฟล์ พบ 0 จุด (แสดงเฉพาะไฟล์และบรรทัด)
- ค่า ai_drafted: yes ทุกข้อ (ผู้ช่วยเป็นผู้ร่าง gold SQL ของทุกข้อในชุดขยาย และผู้เขียนเป็นผู้อนุมัติ (ถ้อยแถลงการใช้ AI ตามมติ 13 ต.ค.))
- ตัดสินอื่น #1 = ค
- ตัดสินอื่น #2 = ข
- ตัดสินอื่น #3 = ข
- ตัดสินอื่น #4 = ก
- ตัดสินอื่น #5 = ก
- ตัดสินอื่น #6 = อนุมัติ
- ตัดสินอื่น #7 = ก
- ตัดสินอื่น #8 = รับทราบ
- server_version ของฐานที่ใช้ตรวจ: 16.9 (Homebrew)
- ฐานหลัก (--pg): k3n

## 10. ไฟล์ผล (sha256)

- `ITEM_CHANGES_generated_2026-10-14.tsv` `f737ada2041321c3cbf1fdc57ac689915144c6d7b1290a46b6e64617a4b22982`
- `ext_inputs.sha256` `e766032eeec0c540816c9be128e559bb9faf990278310d1446a6bd82c8fbe1b3`
- `ext_metadata_refresh.tsv` `f34139fd0c2f48d5f928aad84f1b7b6a32245610e9ddd8d0461768154a6a2f36`
- `k3n_ext_reserves_v1.0.tsv` `c506745567bd99c1415806e6a63a0af92bb2693a1989312f5b240df0e7fce31a`
- `k3n_ext_suite_v1.0.tsv` `838c732afd89066835de9f3eb60799029e76364af6f73a472bfee346e7cbdf14`
