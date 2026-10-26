# CHANGELOG k3_suite_v1.2 → k3_suite_v1.3 (answer key; ร่าง 12 ต.ค. 2569 — รอผู้เขียนอนุมัติ)

**สิ่งที่ไม่เปลี่ยน:** id, tier, schema, eff, question_en, question_th, notes เหมือน v1.2 ทุกตัวอักษร
(selftest_v13.py ตรวจ) ข้อมูลใน DB และ log ของโมเดล (results/results.jsonl) ไม่แตะ
v1.2 เก็บไว้เป็นฉบับ preregistered และรายงานคู่กันทุก headline

**คอลัมน์ใหม่:** gold_sql_v12 (gold เดิม), v13_status (primary | excluded), order_en / order_th,
sort_keys, norm, alt_gold_en / alt_gold_th (JSON list), v13_rule, v13_rationale

**กฎเดียว R-v1.3** (รายละเอียดใน amendment): แก้ key เฉพาะเมื่อ
D1 ผลของ gold ไม่ใช่คำตอบของโจทย์ตามที่เขียน / D2 gold ตรึงสิ่งที่โจทย์เปิดไว้ /
D3 gold คืน 0 แถวบน DB ของ record — ตัดสินจากโจทย์ gold และข้อมูลเท่านั้น

## กฎทั่วไปใน grader (grade_v13.py; ใช้กับทุกข้อ ทุกภาษา)
- G1 ไม่ให้คะแนนลำดับคอลัมน์ (column permutation) แต่จำนวนคอลัมน์ต้องตรง (projection ตาม AMENDMENT-2 ยังตรึง)
- G2 ตัวเลขเทียบด้วยค่า ไม่ขึ้นกับชนิด (int/NUMERIC/float) หรือ scale ที่ 6 ตำแหน่งทศนิยม
- G3 date เท่ากับ timestamp/timestamptz เวลาเที่ยงคืนของวันเดียวกัน (ไม่ให้คะแนน time-zone suffix)
- G4 ให้คะแนนลำดับแถวเฉพาะเมื่อโจทย์ภาษานั้นขอ (order_en/order_th; คำขอ top-k นับเป็นคำขอลำดับ)
  แถวที่เสมอกันบน sort key ที่โจทย์ขอ (sort_keys) สลับกันได้

## รายข้อ (24 ข้อที่ key เปลี่ยน)
| ข้อ | กฎ | v1.2 | v1.3 |
|---|---|---|---|
| Q02 | D2a | ordered ตรงตัวรวมลำดับปีที่เสมอ | ordered, sort_keys=1 (ปีเสมอสลับได้) |
| Q04 | D2a | tiebreak ชื่อ ASC เท่านั้น | + alt ชื่อ DESC (EN, TH) |
| Q12 | D2a | tiebreak OrderID DESC เท่านั้น | + alt OrderID ASC (EN, TH); sort_keys=1,0 |
| Q19 | D1 | `h2.YearHolding > h.YearHolding` (8 แถว) | `h2.YearHolding >= h.YearHolding` (10 แถว) |
| Q20 | D2c | 49 แถว (รวมแถว placeholder ของ Buchanan) | + alt 48 แถว `WHERE m.SpouseName <> 'None'` (EN, TH) |
| Q25 | D2c | gap logic (2 แถว) | + alt EN: นิยามตามวงเล็บ `HAVING COUNT(DISTINCT YearHolding) >= 2` (4 แถว) |
| Q27 | D3 | gold คืน 0 แถว | v13_status=excluded (primary n=59; รายงาน n=60 เป็น sensitivity) |
| Q31 | D2c | 7 พรรคจาก President | + alt 9 พรรค `Party LEFT JOIN President` (EN, TH) |
| Q33 | D2c | เฉลี่ยต่อ record | + alt TH: เฉลี่ยต่อประธานาธิบดี |
| Q39 | D2a,D2b | month = timestamptz; ordered ทั้งสองภาษา | norm 0:month2024; order_en=yes, order_th=no |
| Q42 | D1 | `(Brand, kept, returned)` | `(Brand, returned, kept)` ตามลำดับในโจทย์ |
| Q46 | D2c | ต่อ record | + alt TH: tenure รวมต่อประธานาธิบดี |
| Q47 | D2a | tiebreak ชื่อ ASC | + alt EN: ชื่อ DESC (TH ระบุทิศแล้ว) |
| Q49 | D2a,D2c,D2d | ไม่บังคับลำดับ; RANK ต่อ record | + `ORDER BY term_len DESC` (sort_keys=1); alt EN: DENSE_RANK; alt TH: DENSE_RANK, ต่อประธานาธิบดี RANK/DENSE_RANK |
| Q50 | D1,D2a,D2b | NULLS FIRST จัด Buchanan (ไม่มีคู่สมรส) อันดับ 1; gap มีเครื่องหมาย | `ABS(...)`, `WHERE m.SpouseBirthDay IS NOT NULL` → Tyler 30, Cleveland 27, B. Harrison 25; norm 1:abs; + alt ชื่อ DESC |
| Q51 | D2a | tiebreak OrderID DESC | + alt EN: OrderID ASC (TH ระบุ "มากสุด") |
| Q52 | D2a,D2c | ไม่บังคับลำดับ; ต่อ order 2,390 แถว | + `ORDER BY OrderDate` (sort_keys=0); + alt ต่อวัน 243 แถว (EN, TH) |
| Q54 | D2b | month = timestamptz | norm 0:month2024 |
| Q55 | D2a | tiebreak ชื่อสินค้า ASC | + alt ชื่อสินค้า DESC (EN, TH) |
| Q56 | D2d | PERCENTILE_CONT | + alt PERCENTILE_DISC (EN, TH) |
| Q57 | D2b | ROUND 2 ตำแหน่ง เทียบ string ตรงตัว | norm 1:round2 (เทียบที่ความละเอียด 2 ตำแหน่งของ gold) |
| Q58 | D2a | tiebreak OrderID ASC | + alt OrderID DESC (EN, TH) |
| Q59 | D2a,D2b | `ORDER BY decade` (ordered ทั้งที่โจทย์ไม่ขอ) | ตัด ORDER BY; unordered; norm 0:decade |
| Q60 | D2d | ค่าเฉลี่ยรวม partial window 6 วันแรก | + alt strict window (6 วันแรกเป็น NULL หรือไม่แสดง) (EN, TH) |

## Errata สำหรับ suite รุ่นถัดไป (ไม่แก้ใน v1.3 เพราะโจทย์เป็น stimulus ที่โมเดลเห็นไปแล้ว)
- Q07 TH ขื่อ→ชื่อ; Q27 TH ลุกค้า→ลูกค้า และขอ "คู่" ของ OrderID ทั้งสอง; Q33 TH โดยฉลี่ย→โดยเฉลี่ย และระบุ "ต่อสมัย";
  Q35 TH President_Holding→PresidentHolding; Q37 TH เติม "ระดับสมาชิก (MembershipTier)"; Q43 TH ประเภภ→ประเภท;
  Q45 TH ภาค→ภูมิภาค; Q47 TH ถ้อยคำ "เกิดก่อนใครที่สุด"; Q18 TH เติม "ครั้งแรก"; Q08 TH เติม "(แสดง …)" และ convention ปี
- Q02, Q12, Q50, Q55, Q58, Q04 ระบุทิศ tiebreak; Q25 EN แก้วงเล็บเป็น "(one term ended before another began)" และเติมคำใบ้เดียวกันใน TH;
  Q46/Q49 ระบุหน่วย (ต่อสมัย vs ต่อคน); Q52 ระบุ grain; Q57 ระบุการปัดเศษ; Q39/Q54 ระบุรูปแบบเดือน; Q55 วงเล็บเติม category
- Q41 threshold >100 ไม่ทดสอบ HAVING (ทุก channel มี 282–317 orders); Q48 NULL trap ไม่ทำงาน (RunnerUp ไม่มี NULL)
- ข้อมูล: ชื่อรองประธานาธิบดี/ผู้ได้อันดับสองไม่ตรงชื่อใน President (Chester Arthur, Harry Truman, Lyndon Johnson,
  George Bush, Franklin Roosevelt), RunnerUp ผิดตามประวัติศาสตร์ (Q22), 'Lou Herbert', การสมรสที่ขาด (Fillmore 1858 ฯลฯ),
  OrderID ซ้ำ 3 ค่า, CustomerCity × CustomerCountry สุ่มอิสระ → บันทึกใน DATA_PROVENANCE (คำตอบเป็น DB-relative)
