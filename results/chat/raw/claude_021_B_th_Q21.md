นี่คือคำสั่ง SQL ที่ตอบโจทย์ครับ:

```sql
SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentHolding h ON p.PresidentName = h.PresidentName
WHERE p.StateBorn = 'Virginia'
  AND h.YearHolding < 1850;
```

**อธิบายการทำงาน**

- `JOIN` ตาราง `President` กับ `PresidentHolding` ผ่านชื่อประธานาธิบดี เพราะข้อมูลรัฐที่เกิดอยู่ในตารางแรก ส่วนปีที่เริ่มดำรงตำแหน่งอยู่ในตารางหลัง
- `p.StateBorn = 'Virginia'` กรองเฉพาะคนที่เกิดในรัฐเวอร์จิเนีย
- `h.YearHolding < 1850` กรองเฉพาะคนที่เริ่มดำรงตำแหน่งก่อนปี 1850
- ใช้ `DISTINCT` เพื่อกันชื่อซ้ำ ในกรณีที่ประธานาธิบดีคนเดียวมีหลายแถวในตาราง `PresidentHolding` (เช่น ดำรงตำแหน่งสองสมัยแยกกัน)

**หมายเหตุ:** ตีความโจทย์ว่า "จากรัฐเวอร์จิเนีย" คือรัฐที่เกิด (`StateBorn`) เพราะเป็นคอลัมน์เดียวในโครงสร้างตารางที่เกี่ยวกับรัฐ และตรวจสอบให้แน่ใจว่าค่าในตารางเขียนว่า `'Virginia'` ตรงตามนี้ (ตัวพิมพ์ใหญ่เล็กมีผลใน PostgreSQL) ถ้าข้อมูลมีรูปแบบไม่แน่นอน อาจใช้ `LOWER(p.StateBorn) = 'virginia'` แทนได้ครับ