# v0.xlsx (instructor) → v1_candidate

- typo sweep (ประธานาธิบดี/การคืน/สินค้า): แก้ 32 ข้อ
- Q08: EN → 'in the nineteenth century' (คู่กับ ศตวรรษที่ 19) + convention note
- Q47: TH semantic fix — เดิม 'แสดงรายชื่อประธานาธิบดีของแต่ละพรรคเรียงลำดับจากผู้ที่เกิดก่อน' = เรียงทุกคน แต่โจทย์คือ 'คนที่เกิดแรกสุดต่อพรรค' (window rn=1) → ใหม่ตามความหมาย gold

รออนุมัติจากผู้เขียนก่อน rename เป็น k3_suite_v1.tsv (FROZEN)

## AMENDMENT-1 (v1 → v1.1_candidate, 6 ส.ค. — รออนุมัติ)
พบจาก gold validation + grader self-test (ก่อนแตะ LLM ใดๆ):
- **Q24**: คำตอบว่างบนข้อมูลจริง (ทุกประธานาธิบดีมีบันทึกสมรส 45/45) → เปลี่ยนเป้า anti-join เป็น "never served as vice president" (35 แถว, ทักษะ LEFT JOIN เดิม)
- **Q40**: threshold rating >4 ให้คำตอบว่าง (ค่าเฉลี่ยจริง ~3.0–3.1) → ปรับเป็น >3 (6 หมวด)
- **Tiebreak determinism 9 ข้อ** (Q04, Q12, Q32, Q38, Q47, Q50, Q51, Q55, Q58): เพิ่มตัวตัดเสมอใน gold + วลี "(break ties by …)" ทั้งสองภาษา — กัน top-k/window ambiguity ที่ทำให้คำตอบถูกหลายแบบเทียบกันไม่ได้
- Grader fix (ไม่ใช่ตัว suite): ตรวจ ORDER BY เฉพาะระดับนอกสุด + float 6 sig digits
- Self-test หลังแก้: gold-vs-gold **60/60 สองรอบติด**

## บันทึกค้างคืน 6 ส.ค. 23:15 — พบจาก smoke run แรก (21 cells, Gemini EN, 15/21=71%)
- **พบ instrument flaw ระบบเดียว: projection ambiguity** — Q13 (โจทย์ไม่ระบุคอลัมน์ → SELECT * ของโมเดลชอบธรรมแต่ถูกหัก) และ Q23 (gold แถม SpouseName เกินโจทย์ → โมเดลตอบตามโจทย์แต่ถูกหัก)
- **งานพรุ่งนี้ (7 ส.ค.): AMENDMENT-2** — audit ทั้ง 60 ข้อ ล็อก projection โจทย์↔gold ให้ตรงกันทุกข้อ (สองภาษา) → ผู้เขียนเคาะ → ลบ records ที่กระทบ (บันทึกการลบ) → rerun
- ค้างวินิจฉัย: Q14, Q15, Q20, Q44 (อาจ class เดียวกัน) / รอ billing Google เพื่อเก็บ 99 cells ที่เหลือ

## AMENDMENT-2 — อนุมัติและบังคับใช้ 7 ส.ค. 2026 (ก่อนรันเก็บจริงรอบใหม่)
- **สาเหตุ**: smoke run (21 cells) พิสูจน์ projection ambiguity — ทุกข้อที่ตก (6/6) โมเดล logic ถูกแต่คอลัมน์ไม่ตรง
- **แก้ 17 ข้อ** (ข้อความโจทย์ EN+TH เท่านั้น, gold FROZEN): Q13-Q15, Q20, Q23, Q29, Q38, Q40, Q44, Q46, Q47, Q49, Q50, Q53-Q56 — รายละเอียดใน AMENDMENT2_PROPOSAL.md
- typo ไทยพลอยได้ 3 จุด: Q15 เครื่องแค่งกาย→เครื่องแต่งกาย, Q49 และดับ→อันดับ, Q56 เปอร์เซ็นต์ไทร์→เปอร์เซ็นไทล์
- Q14 แก้ความกำกวมเพิ่ม: "not returned" → "neither returned nor exchanged" (ข้อมูลจริงมี 'Exchanged')
- **ธรรมเนียมประกาศเพิ่ม (ลง prereg)**: "For each X, show Y" ⇒ ผลลัพธ์รวม X / "List presidents…" (schema P) ⇒ PresidentName เดียว
- **ไฟล์**: suite v1.2 = k3_suite_v1.2.tsv (v1.1 เก็บไว้เพื่อ audit trail)
- **ข้อมูล**: ลบ 7 good records (Q13,Q14,Q15,Q20,Q23,Q44,Q55 EN) + 88 error records ค้าง — เหลือ 14 good records ที่โจทย์ไม่เปลี่ยน
- gold self-test v1.2 (DuckDB): 60/60 ✔
