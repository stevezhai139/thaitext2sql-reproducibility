# K3 Suite v0 — งานของผู้เขียน (instructor pass)

ไฟล์: `k3_suite_v0.tsv` — 60 ข้อ, 4 tiers × 15, สอง schema:
**P** = President (4 ตาราง: President / Party / PresidentMarriage / PresidentHolding)
**E** = Ecommerce (ตารางกว้าง 38 คอลัมน์; จะ scale เป็น 1M แถวสำหรับข้อ eff=yes)

## สิ่งที่ต้องทำ (ประมาณ 2–3 เย็น)
1. **อ่านคำถาม EN ทั้ง 60** — แก้ถ้อยคำให้เหมือนโจทย์ที่คุณให้นักศึกษาจริง (คุณคือ instrument validity)
2. **เติมคอลัมน์ question_th** — ภาษาไทยแบบที่นักศึกษาพิมพ์ถาม ไม่ใช่แปลตรงตัว
3. **ตรวจ gold_sql_draft** — ผมร่างไว้ทุกข้อ (PostgreSQL) แต่คุณคือคนอนุมัติ; แก้ได้เต็มที่
4. จุดที่ผมจงใจวางกับดัก/ธงกำกวม (ดูคอลัมน์ notes): Q18 ("first term"), Q23 (ปี vs วันที่), Q41 (threshold จะ rescale ตอน 1M), Q48 (NOT IN + NULL trap — ตั้งใจ)

## กติกา
- แก้ไฟล์ตรงนี้ได้เลย บันทึกเป็น `k3_suite_v1.tsv` เมื่อพอใจ → v1 คือฉบับ freeze
- ห้ามแก้หลัง freeze (วินัย pre-registration เดิมของเรา)
