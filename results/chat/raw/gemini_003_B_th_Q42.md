นี่คือคำสั่ง SQL (PostgreSQL) สำหรับนับจำนวนคำสั่งซื้อที่มีการคืนหรือเปลี่ยนสินค้า เทียบกับคำสั่งซื้อที่ไม่มีการคืนสินค้า แยกตามยี่ห้อ (`Brand`) โดยใช้เทคนิค Conditional Aggregation ครับ

```sql
SELECT 
    Brand,
    -- นับจำนวนคำสั่งซื้อที่มีการคืน หรือเปลี่ยนสินค้า
    COUNT(CASE 
        WHEN ReturnStatus ILIKE '%return%' OR ReturnStatus ILIKE '%exchange%' 
        THEN 1 
    END) AS ReturnOrExchangeCount,
    
    -- นับจำนวนคำสั่งซื้อที่ไม่มีการคืนสินค้า
    COUNT(CASE 
        WHEN ReturnStatus NOT ILIKE '%return%' 
         AND ReturnStatus NOT ILIKE '%exchange%' 
         OR ReturnStatus IS NULL 
        THEN 1 
    END) AS NoReturnCount,
    
    -- จำนวนคำสั่งซื้อทั้งหมดของแต่ละแบรนด์ (เผื่อไว้เปรียบเทียบภาพรวม)
    COUNT(*) AS TotalOrders
FROM 
    Ecommerce
GROUP BY 
    Brand
ORDER BY 
    Brand;

```

---

### อธิบายการทำงาน:

1. **`GROUP BY Brand`**: จัดกลุ่มข้อมูลแยกตามยี่ห้อสินค้าแต่ละแบรนด์
2. **`COUNT(CASE ... END)`**: ใช้สำหรับการนับจำนวนแบบมีเงื่อนไข (Conditional Count) โดย:
* เงื่อนไขแรก ตรวจสอบคำว่า `return` หรือ `exchange` ในฟิลด์ `ReturnStatus` (ใช้ `ILIKE` เพื่อให้ไม่ ⚠️ สนใจตัวพิมพ์เล็ก/ใหญ่)
* เงื่อนไขที่สอง คือกลุ่มที่ไม่มีการคืน/เปลี่ยน หรือค่าเป็น `NULL`


3. **`TotalOrders`**: แถมคอลัมน์รวมยอดคำสั่งซื้อทั้งหมดต่อแบรนด์มาให้ด้วย เพื่อให้เห็นสัดส่วนได้ง่ายขึ้นครับ