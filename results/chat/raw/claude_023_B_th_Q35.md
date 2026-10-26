โจทย์นี้ต้องการ GROUP BY ตามชื่อประธานาธิบดี เพราะประธานาธิบดีบางคนอาจดำรงตำแหน่งหลายสมัย (หลายแถวในตาราง) จึงใช้ `MIN` กับปีเริ่มและ `MAX` กับปีสิ้นสุด

```sql
SELECT
    PresidentName,
    MIN(YearHolding) AS EarliestYearHolding,
    MAX(YearEnd)     AS LatestYearEnd
FROM PresidentHolding
GROUP BY PresidentName
ORDER BY EarliestYearHolding;
```

**คำอธิบาย**
- `MIN(YearHolding)` คือปีเริ่มตำแหน่งที่เก่าที่สุดของประธานาธิบดีแต่ละคน
- `MAX(YearEnd)` คือปีสิ้นสุดการดำรงตำแหน่งล่าสุดของแต่ละคน
- `GROUP BY PresidentName` รวมแถวของคนเดียวกันให้เหลือแถวเดียว
- `ORDER BY` ใส่เพิ่มให้อ่านง่าย (เรียงตามปีเริ่มตำแหน่ง) ถ้าไม่ต้องการเรียงลำดับสามารถตัดออกได้

หมายเหตุ: โจทย์เขียนชื่อตารางว่า `President_Holding` แต่ในโครงสร้างตารางที่ให้มาชื่อ `PresidentHolding` (ไม่มีขีดล่าง) ผมจึงใช้ชื่อตามโครงสร้างตารางจริง