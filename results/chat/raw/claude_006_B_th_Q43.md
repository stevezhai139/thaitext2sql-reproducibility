โจทย์ตีความได้ว่า "รายรับสูงสุดของคำสั่งซื้อ (ต่อ 1 ออเดอร์) ในแต่ละวิธีการชำระเงิน" ซึ่งใช้ `MAX` กับ `GROUP BY`:

```sql
SELECT
    PaymentMethod,
    MAX(Revenue) AS MaxRevenue
FROM Ecommerce
GROUP BY PaymentMethod
ORDER BY MaxRevenue DESC;
```

**หมายเหตุ**

- ถ้า 1 `OrderID` มีได้หลายแถว (เช่น สั่งหลายสินค้าในออเดอร์เดียว) และต้องการหาออเดอร์ที่มี **ยอดรวมต่อออเดอร์** สูงสุดในแต่ละวิธีชำระเงิน ให้ใช้แบบนี้แทน:

```sql
SELECT
    PaymentMethod,
    MAX(OrderRevenue) AS MaxOrderRevenue
FROM (
    SELECT
        OrderID,
        PaymentMethod,
        SUM(Revenue) AS OrderRevenue
    FROM Ecommerce
    GROUP BY OrderID, PaymentMethod
) AS t
GROUP BY PaymentMethod
ORDER BY MaxOrderRevenue DESC;
```

- ถ้าต้องการให้แสดง `OrderID` ของออเดอร์ที่ทำรายรับสูงสุดด้วย สามารถใช้ `DISTINCT ON` ของ PostgreSQL:

```sql
SELECT DISTINCT ON (PaymentMethod)
    PaymentMethod,
    OrderID,
    Revenue AS MaxRevenue
FROM Ecommerce
ORDER BY PaymentMethod, Revenue DESC;
```

หากโจทย์หมายถึง "รายรับรวมที่มากที่สุด" (คือวิธีชำระเงินไหนทำรายได้รวมสูงสุด) ให้เปลี่ยนเป็น `SUM(Revenue)` แล้วเรียงลำดับแทนได้เลยครับ