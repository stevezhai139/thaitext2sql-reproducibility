```sql
SELECT PresidentName
FROM President
WHERE StateBorn = 'Virginia';
```

คำสั่งนี้จะดึงชื่อประธานาธิบดีทุกคนจากตาราง `President` ที่มีค่าในคอลัมน์ `StateBorn` เป็น `'Virginia'`

หมายเหตุ: ถ้าข้อมูลในตารางอาจมีการสะกดหรือตัวพิมพ์เล็กพิมพ์ใหญ่ไม่สม่ำเสมอ (เช่น `'virginia'` หรือ `'VA'`) สามารถใช้แบบนี้แทนได้:

```sql
SELECT PresidentName
FROM President
WHERE LOWER(StateBorn) = 'virginia';
```