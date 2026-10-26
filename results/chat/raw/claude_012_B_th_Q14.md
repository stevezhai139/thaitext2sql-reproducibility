ข้อมูลในคอลัมน์ `ReturnStatus` ไม่ทราบค่าที่แน่นอน จึงเขียนให้ครอบคลุมทั้งกรณีเป็น NULL, ค่าว่าง และข้อความที่สื่อว่า "ไม่มีการคืน"

```sql
SELECT
    OrderID,
    ProductName,
    ProductRating
FROM Ecommerce
WHERE ProductRating >= 4.5
  AND (
        ReturnStatus IS NULL
        OR TRIM(ReturnStatus) = ''
        OR LOWER(TRIM(ReturnStatus)) IN ('not returned', 'no', 'none', 'n/a')
      );
```

**หมายเหตุ**

- `ProductRating >= 4.5` คือเรตติ้งตั้งแต่ 4.5 ขึ้นไป (รวม 4.5)
- ชุดค่าใน `IN (...)` เป็นการเดาค่าที่พบบ่อย ควรตรวจค่าจริงในตารางก่อนด้วยคำสั่งนี้:

```sql
SELECT DISTINCT ReturnStatus FROM Ecommerce;
```

- ถ้าพบว่าข้อมูลใช้ค่าอื่น เช่น `'Not Returned'` อย่างเดียว ก็ปรับเงื่อนไขให้ตรงกัน เช่น

```sql
WHERE ProductRating >= 4.5
  AND ReturnStatus = 'Not Returned'
```

- หรืออีกแนวทางคือเขียนแบบตัดค่าที่เป็นการคืนออก (เช่น `'Returned'`, `'Exchanged'`) ซึ่งเหมาะกว่าถ้าค่าที่หมายถึง "ไม่คืน" มีหลายรูปแบบ:

```sql
WHERE ProductRating >= 4.5
  AND (ReturnStatus IS NULL
       OR LOWER(TRIM(ReturnStatus)) NOT IN ('returned', 'exchanged'))
```

ถ้าส่งผลลัพธ์ของ `SELECT DISTINCT ReturnStatus` มาให้ ผมปรับคำสั่งให้ตรงกับข้อมูลจริงได้ครับ