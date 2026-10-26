```sql
SELECT PresidentName, YearBorn
FROM President
WHERE YearBorn > 1850
ORDER BY YearBorn DESC;
```

**คำอธิบาย**
- `WHERE YearBorn > 1850` กรองเฉพาะประธานาธิบดีที่เกิดหลังปี 1850 (ไม่รวมปี 1850 เอง)
- `ORDER BY YearBorn DESC` เรียงจากปีเกิดมากไปน้อย ทำให้คนที่เกิดล่าสุดอยู่ด้านบน

ถ้าต้องการให้เรียงตามชื่อด้วยเมื่อปีเกิดเท่ากัน สามารถเพิ่ม `, PresidentName ASC` ต่อท้าย `ORDER BY` ได้