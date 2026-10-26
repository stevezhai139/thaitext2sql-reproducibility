นี่คือคำสั่ง SQL (PostgreSQL) สำหรับโจทย์ดังกล่าวครับ

```sql
SELECT PresidentName, YearBorn
FROM President
WHERE YearBorn > 1850
ORDER BY YearBorn DESC;

```

### คำอธิบาย:

* **`SELECT PresidentName, YearBorn`**: ดึงข้อมูลเฉพาะชื่อประธานาธิบดีและปีเกิด
* **`WHERE YearBorn > 1850`**: กรองเอาเฉพาะคนที่เกิดหลังปี 1850 (มากกว่า 1850)
* **`ORDER BY YearBorn DESC`**: เรียงลำดับจากปีเกิดล่าสุดลงไปหาปีที่เก่ากว่า (Descending)