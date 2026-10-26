นี่คือคำสั่ง SQL (PostgreSQL) สำหรับโจทย์ดังกล่าวครับ:

```sql
SELECT 
    p.PresidentName,
    ABS(p.YearBorn - EXTRACT(YEAR FROM pm.SpouseBirthDay)) AS AgeDifference
FROM 
    President p
JOIN 
    PresidentMarriage pm ON p.PresidentName = pm.PresidentName
WHERE 
    pm.SpouseBirthDay IS NOT NULL
ORDER BY 
    AgeDifference DESC,
    p.PresidentName ASC
LIMIT 3;

```

---

### **คำอธิบายการทำงาน:**

1. **`JOIN`**: เชื่อมตาราง `President` และ `PresidentMarriage` ด้วยชื่อประธานาธิบดี (`PresidentName`)
2. **`EXTRACT(YEAR FROM pm.SpouseBirthDay)`**: ดึงเอาปี ค.ศ. เกิดของคู่สมรสออกจากฟิลด์ที่เป็น `DATE`
3. **`ABS(p.YearBorn - ...)`**: หาผลต่างระหว่างปีเกิดของประธานาธิบดีกับปีเกิดของคู่สมรส โดยใช้ `ABS()` เพื่อให้ค่าผลต่างเป็นบวกเสมอ (คำนวณระยะห่างของอายุเป็นจำนวนปี)
4. **`ORDER BY AgeDifference DESC, p.PresidentName ASC`**:
* เรียงลำดับจากผลต่างอายุมากที่สุดไปหาน้อยที่สุด (`DESC`)
* หากผลต่างอายุเท่ากัน ให้เรียงตามชื่อประธานาธิบดีจาก A-Z (`ASC`)


5. **`LIMIT 3`**: ดึงเฉพาะ 3 รายการแรกออกมาแสดงผล