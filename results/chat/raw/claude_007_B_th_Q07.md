ต้องดูว่าค่าในคอลัมน์ `MarriageStatus` ใช้คำว่าอะไรแทนสถานะ "หม้าย" ซึ่งโดยทั่วไปในชุดข้อมูลแบบนี้มักเป็น `'Widowed'` หรือ `'Widow'`

```sql
SELECT SpouseName
FROM PresidentMarriage
WHERE MarriageStatus = 'Widowed';
```

ถ้าไม่แน่ใจว่าเก็บเป็นค่าไหน หรืออาจมีตัวพิมพ์เล็กใหญ่ต่างกัน ใช้แบบนี้แทนได้:

```sql
SELECT SpouseName
FROM PresidentMarriage
WHERE MarriageStatus ILIKE 'widow%';
```

หากต้องการให้ชื่อไม่ซ้ำกัน ให้เพิ่ม `DISTINCT` เป็น `SELECT DISTINCT SpouseName`

ถ้าอยากตรวจสอบก่อนว่าในตารางมีค่าสถานะอะไรบ้าง รันคำสั่งนี้ได้:

```sql
SELECT DISTINCT MarriageStatus FROM PresidentMarriage;
```