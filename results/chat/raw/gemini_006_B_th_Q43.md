นี่คือคำสั่ง SQL (PostgreSQL) สำหรับค้นหารายรับที่มากที่สุดของคำสั่งซื้อแยกตามประเภทการจ่ายเงินครับ โดยผมแบ่งออกเป็น 2 แบบให้เลือกใช้ตามความต้องการ:

### แบบที่ 1: ใช้ `GROUP BY` (แสดงเฉพาะประเภทการจ่ายเงิน และยอดรายรับสูงสุด)

วิธีนี้ง่ายและรวดเร็วที่สุด เหมาะกับกรณีที่ต้องการดูแค่ตัวเลขสูงสุดของแต่ละประเภท

```sql
SELECT 
    PaymentMethod, 
    MAX(Revenue) AS MaxRevenue
FROM 
    Ecommerce
GROUP BY 
    PaymentMethod
ORDER BY 
    MaxRevenue DESC;

```

---

### แบบที่ 2: ใช้ Window Function (`ROW_NUMBER`)

หากต้องการทราบด้วยว่า **Order ID** ไหนที่เป็นคำสั่งซื้อที่มีรายรับสูงสุดของแต่ละประเภทการจ่ายเงิน วิธีนี้จะตอบโจทย์มากกว่าครับ

```sql
WITH RankedOrders AS (
    SELECT 
        OrderID,
        PaymentMethod,
        Revenue,
        ROW_NUMBER() OVER (PARTITION BY PaymentMethod ORDER BY Revenue DESC) as rn
    FROM 
        Ecommerce
)
SELECT 
    PaymentMethod,
    OrderID AS MaxRevenueOrderID,
    Revenue AS MaxRevenue
FROM 
    RankedOrders
WHERE 
    rn = 1
ORDER BY 
    MaxRevenue DESC;

```

---

**คำอธิบายเพิ่มเติม:**

* `MAX(Revenue)` ใช้หาค่ารายรับสูงสุดในแต่ละกลุ่ม
* `PARTITION BY PaymentMethod` ในแบบที่ 2 จะช่วยจัดกลุ่มตามประเภทการจ่ายเงิน และ `ORDER BY Revenue DESC` จะเรียงจากมากไปน้อย เพื่อให้ `ROW_NUMBER() = 1` เป็นรายการที่มีรายรับสูงที่สุดในกลุ่มนั้นๆ ครับ