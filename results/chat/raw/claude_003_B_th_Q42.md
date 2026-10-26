โจทย์นี้ไม่ได้ระบุค่าใน `ReturnStatus` ไว้ชัดเจน ผมจึงเขียนโดยสมมติว่าคอลัมน์นี้มีค่าประมาณ `'Returned'`, `'Exchanged'`, `'None'` (หรือ NULL) คุณควรตรวจสอบค่าจริงก่อนด้วย:

```sql
SELECT DISTINCT ReturnStatus FROM Ecommerce;
```

**คำสั่งหลัก (นับตามจำนวนคำสั่งซื้อ แยกตามยี่ห้อ)**

```sql
SELECT
    Brand,
    COUNT(DISTINCT OrderID) FILTER (
        WHERE ReturnStatus IN ('Returned', 'Exchanged')
    ) AS returned_or_exchanged_orders,
    COUNT(DISTINCT OrderID) FILTER (
        WHERE ReturnStatus IS NULL OR ReturnStatus NOT IN ('Returned', 'Exchanged')
    ) AS no_return_orders
FROM Ecommerce
GROUP BY Brand
ORDER BY Brand;
```

**หมายเหตุ**

- `FILTER (WHERE ...)` เป็นไวยากรณ์เฉพาะของ PostgreSQL ใช้นับแบบมีเงื่อนไขในคิวรีเดียว
- ใช้ `COUNT(DISTINCT OrderID)` เผื่อหนึ่งคำสั่งซื้อมีหลายแถว หากหนึ่งแถวคือหนึ่งคำสั่งซื้ออยู่แล้ว เปลี่ยนเป็น `COUNT(*)` ได้
- เงื่อนไข `IS NULL OR NOT IN (...)` ช่วยให้แถวที่เป็น NULL ถูกนับเป็น "ไม่มีการคืน" ด้วย
- หากค่าจริงในข้อมูลสะกดต่างจากนี้ (เช่น `'Yes'`/`'No'` หรือ `'Return'`) ให้แก้รายการใน `IN (...)` ให้ตรงกัน

**ถ้าต้องการแบบมีสัดส่วนการคืนด้วย**

```sql
SELECT
    Brand,
    COUNT(DISTINCT OrderID) FILTER (WHERE ReturnStatus IN ('Returned', 'Exchanged')) AS returned_or_exchanged_orders,
    COUNT(DISTINCT OrderID) FILTER (WHERE ReturnStatus IS NULL OR ReturnStatus NOT IN ('Returned', 'Exchanged')) AS no_return_orders,
    ROUND(
        100.0 * COUNT(DISTINCT OrderID) FILTER (WHERE ReturnStatus IN ('Returned', 'Exchanged'))
        / COUNT(DISTINCT OrderID), 2
    ) AS return_rate_pct
FROM Ecommerce
GROUP BY Brand
ORDER BY return_rate_pct DESC;
```

ถ้าบอกค่าจริงของ `ReturnStatus` ได้ ผมปรับเงื่อนไขให้ตรงเป๊ะได้ครับ