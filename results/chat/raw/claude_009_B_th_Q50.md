```sql
SELECT
    p.PresidentName,
    MAX(ABS(p.YearBorn - EXTRACT(YEAR FROM pm.SpouseBirthDay)::INT)) AS AgeDifference
FROM President p
JOIN PresidentMarriage pm
    ON p.PresidentName = pm.PresidentName
GROUP BY p.PresidentName
ORDER BY AgeDifference DESC, p.PresidentName ASC
LIMIT 3;
```

**คำอธิบาย**
- `EXTRACT(YEAR FROM pm.SpouseBirthDay)::INT` ดึงปีเกิดของคู่สมรสออกมาจากวันที่ แล้วแปลงเป็นจำนวนเต็ม
- `ABS(...)` หาผลต่างอายุเป็นปี โดยไม่สนใจว่าใครอายุมากกว่า
- `GROUP BY` + `MAX(...)` ใช้กรณีที่ประธานาธิบดีบางคนแต่งงานหลายครั้ง จะนำคู่สมรสที่อายุห่างมากที่สุดมาใช้ และแสดงชื่อประธานาธิบดีแต่ละคนเพียงครั้งเดียว
- `ORDER BY AgeDifference DESC, p.PresidentName ASC` เรียงจากผลต่างมากไปน้อย ถ้าเท่ากันให้เรียงตามชื่อ
- `LIMIT 3` เลือกเฉพาะ 3 อันดับแรก

หมายเหตุ: ผลต่างนี้คำนวณจากปีเกิดเท่านั้น (`YearBorn` เทียบกับปีของ `SpouseBirthDay`) เพราะตาราง `President` ไม่มีวันเกิดเต็ม