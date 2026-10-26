นี่คือคำสั่ง SQL (PostgreSQL) สำหรับดึงข้อมูลตามเงื่อนไขที่คุณต้องการครับ:

```sql
SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentHolding ph ON p.PresidentName = ph.PresidentName
WHERE p.StateBorn = 'Virginia'
  AND ph.YearHolding < 1850;

```

---

### 💡 อธิบายการทำงาน:

* **`JOIN PresidentHolding`**: เชื่อมตาราง `President` และ `PresidentHolding` ด้วยชื่อประธานาธิบดี (`PresidentName`) เพื่อเอาข้อมูลปีที่เริ่มดำรงตำแหน่ง
* **`WHERE p.StateBorn = 'Virginia'`**: กรองเฉพาะประธานาธิบดีที่เกิดในรัฐเวอร์จิเนีย
* **`AND ph.YearHolding < 1850`**: กรองเฉพาะประธานาธิบดีที่เริ่มดำรงตำแหน่ง (`YearHolding`) ก่อนปี ค.ศ. 1850
* **`SELECT DISTINCT`**: ป้องกันการแสดงชื่อประธานาธิบดีซ้ำกัน (กรณีที่ดำรงตำแหน่งหลายสมัยก่อนปี 1850)