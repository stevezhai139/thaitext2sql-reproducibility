คำถามนี้ต้องการค้นหารายชื่อประธานาธิบดีที่ไม่เคยมีชื่อปรากฏอยู่ในคอลัมน์ `RunnerUp` (ผู้ได้คะแนนมาเป็นอันดับสอง) ในตาราง `PresidentHolding`

คำสั่ง SQL (PostgreSQL) สามารถเขียนได้หลายรูปแบบ โดยวิธีที่นิยมและมีประสิทธิภาพ ได้แก่:

### วิธีที่ 1: ใช้ `NOT EXISTS` (แนะนำ)

วิธีนี้อ่านเข้าใจง่าย และประสิทธิภาพสูงสำหรับ PostgreSQL

```sql
SELECT DISTINCT p.PresidentName
FROM President p
WHERE NOT EXISTS (
    SELECT 1 
    FROM PresidentHolding ph 
    WHERE ph.RunnerUp = p.PresidentName
);

```

---

### วิธีที่ 2: ใช้ `LEFT JOIN`

ดึงรายชื่อประธานาธิบดีทั้งหมด แล้วเชื่อมกับตาราง `PresidentHolding` โดยดูจากตำแหน่ง `RunnerUp` หากไม่มีข้อมูล matching (`ph.RunnerUp IS NULL`) แสดงว่าไม่เคยเป็นอันดับสอง

```sql
SELECT DISTINCT p.PresidentName
FROM President p
LEFT JOIN PresidentHolding ph 
       ON p.PresidentName = ph.RunnerUp
WHERE ph.RunnerUp IS NULL;

```

---

### วิธีที่ 3: ใช้ `NOT IN` (ต้องระวัง `NULL`)

กรณีใช้ `NOT IN` จะต้องตัดค่า `NULL` ในคอลัมน์ `RunnerUp` ออกด้วย เพื่อป้องกันไม่ให้ผลลัพธ์เป็นค่าว่างเปล่า (Empty Set)

```sql
SELECT DISTINCT PresidentName
FROM President
WHERE PresidentName NOT IN (
    SELECT RunnerUp 
    FROM PresidentHolding 
    WHERE RunnerUp IS NOT NULL
);

```

> **หมายเหตุ:** ใส่ `DISTINCT` เพื่อป้องกันกรณีที่ชื่อประธานาธิบดีปรากฏซ้ำในตาราง `President`