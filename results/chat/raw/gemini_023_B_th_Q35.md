นี่คือคำสั่ง SQL (PostgreSQL) สำหรับโจทย์ที่คุณต้องการครับ:

```sql
SELECT 
    PresidentName,
    MIN(YearHolding) AS FirstYearHolding,
    MAX(YearEnd) AS LastYearEnd
FROM 
    PresidentHolding
GROUP BY 
    PresidentName;

```

---

### **อธิบายการทำงาน:**

* **`MIN(YearHolding)`**: ใช้หาปีที่เริ่มดำรงตำแหน่งที่เก่าที่สุด (น้อยที่สุด) ของประธานาธิบดีแต่ละคน
* **`MAX(YearEnd)`**: ใช้หาปีที่สิ้นสุดการดำรงตำแหน่งที่ล่าสุด (มากที่สุด) ของประธานาธิบดีแต่ละคน
* **`GROUP BY PresidentName`**: เพื่อจัดกลุ่มข้อมูลตามรายชื่อประธานาธิบดี ให้ผลลัพธ์คำนวณแยกตามรายคน