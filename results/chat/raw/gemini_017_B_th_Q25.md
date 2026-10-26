นี่คือคำสั่ง SQL (PostgreSQL) สำหรับค้นหาชื่อประธานาธิบดีที่ดำรงตำแหน่งแบบ **วาระไม่ต่อเนื่องกัน** (Non-consecutive terms) โดยใช้ Window Function `LAG()` เพื่อตรวจสอบว่าปีที่เริ่มดำรงตำแหน่งในวาระถัดไป มีช่วงเว้นว่าง (มากกว่า) ปีที่สิ้นสุดวาระก่อนหน้าหรือไม่ครับ

```sql
WITH RankedTerms AS (
    SELECT 
        PresidentName,
        YearHolding,
        YearEnd,
        LAG(YearEnd) OVER (PARTITION BY PresidentName ORDER BY YearHolding) AS PrevYearEnd
    FROM PresidentHolding
)
SELECT DISTINCT PresidentName
FROM RankedTerms
WHERE PrevYearEnd IS NOT NULL 
  AND YearHolding > PrevYearEnd;

```

---

### คำอธิบายการทำงาน:

1. **`RankedTerms` (Common Table Expression - CTE):**
* ดึงข้อมูลการดำรงตำแหน่งของประธานาธิบดีแต่ละคน
* ใช้ฟังก์ชัน `LAG(YearEnd) OVER (PARTITION BY PresidentName ORDER BY YearHolding)` เพื่อดึง `YearEnd` ของวาระก่อนหน้ามาเปรียบเทียบกับวาระปัจจุบัน โดยเรียงลำดับตามปีที่เริ่มดำรงตำแหน่ง (`YearHolding`)


2. **เงื่อนไข `WHERE PrevYearEnd IS NOT NULL AND YearHolding > PrevYearEnd`:**
* กรองเฉพาะประธานาธิบดีที่มีมากกว่า 1 วาระขึ้นไป (`PrevYearEnd IS NOT NULL`)
* ตรวจสอบว่าปีที่เริ่มวาระใหม่ (`YearHolding`) มากกว่าปีที่สิ้นสุดวาระก่อนหน้า (`PrevYearEnd`) หรือไม่ ซึ่งบ่งบอกถึงการเว้นช่วงและกลับมาดำรงตำแหน่งใหม่ (เช่น กรณีของ Grover Cleveland ที่ดำรงตำแหน่งปี 1885–1889 และ 1893–1897)


3. **`SELECT DISTINCT`:**
* เพื่อป้องกันการแสดงชื่อซ้ำในกรณีที่มีหลายวาระครับ