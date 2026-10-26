```sql
SELECT
    MarketingChannel,
    SUM(Revenue) AS TotalRevenue
FROM Ecommerce
GROUP BY MarketingChannel
HAVING COUNT(DISTINCT OrderID) > 100;
```

**คำอธิบาย**
- `GROUP BY MarketingChannel` จัดกลุ่มข้อมูลตามช่องทางการตลาด
- `SUM(Revenue)` รวมรายได้ของแต่ละช่องทาง
- `HAVING COUNT(DISTINCT OrderID) > 100` กรองเฉพาะช่องทางที่มีจำนวนคำสั่งซื้อมากกว่า 100 รายการ (ใช้ `HAVING` เพราะเป็นเงื่อนไขที่ใช้ฟังก์ชันรวมข้อมูล ซึ่งใช้ `WHERE` ไม่ได้)

**หมายเหตุ:** ผมใช้ `COUNT(DISTINCT OrderID)` เผื่อกรณีที่ 1 คำสั่งซื้อมีหลายแถว (หลายสินค้า) ถ้าข้อมูลของคุณ 1 แถวคือ 1 คำสั่งซื้อ จะใช้ `COUNT(*) > 100` ก็ให้ผลเหมือนกัน