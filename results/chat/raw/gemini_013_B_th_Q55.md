นี่คือคำสั่ง SQL (PostgreSQL) สำหรับแก้โจทย์ดังกล่าว โดยใช้เทคนิค Common Table Expression (CTE) และ Window Function (`ROW_NUMBER()`) เพื่อจัดอันดับสินค้าในแต่ละหมวดหมู่ครับ

```sql
WITH ProductSales AS (
    -- ขั้นที่ 1: จัดกลุ่มตามหมวดสินค้าและชื่อสินค้า เพื่อหายอดขายรวมของแต่ละสินค้า
    SELECT 
        Category,
        ProductName,
        SUM(Revenue) AS TotalRevenue
    FROM Ecommerce
    GROUP BY Category, ProductName
),
RankedProducts AS (
    -- ขั้นที่ 2: ใช้ Window Function จัดอันดับตามรายได้รวม (มากไปน้อย) และชื่อสินค้า (ก-ฮ)
    SELECT 
        Category,
        ProductName,
        TotalRevenue,
        ROW_NUMBER() OVER (
            PARTITION BY Category 
            ORDER BY TotalRevenue DESC, ProductName ASC
        ) AS rank_num
    FROM ProductSales
)
-- ขั้นที่ 3: กรองเอาเฉพาะ 3 อันดับแรกของแต่ละหมวดสินค้า
SELECT 
    Category,
    ProductName,
    TotalRevenue
FROM RankedProducts
WHERE rank_num <= 3;

```

---

### คำอธิบายการทำงาน:

1. **`ProductSales` (CTE แรก):** ทำการ `GROUP BY` หมวดหมู่ (`Category`) และชื่อสินค้า (`ProductName`) พร้อมรวมรายได้ทั้งหมด (`SUM(Revenue)`) ของสินค้าแต่ละตัว
2. **`RankedProducts` (CTE ที่สอง):** ใช้ `ROW_NUMBER()` ร่วมกับ `PARTITION BY Category` เพื่อแยกการจัดอันดับเป็นรายหมวดหมู่ และกำหนดเงื่อนไขการเรียงลำดับด้วย `ORDER BY TotalRevenue DESC, ProductName ASC` (หากรายได้เท่ากัน จะเรียงตามชื่อสินค้าจากน้อยไปมาก)
3. **Query สุดท้าย:** ดึงข้อมูลเฉพาะรายการที่มีลำดับ (`rank_num`) น้อยกว่าหรือเท่ากับ 3 ออกมาแสดงผล