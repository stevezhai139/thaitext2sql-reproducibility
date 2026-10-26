```sql
SELECT OrderID, ProductName, CustomerCity
FROM Ecommerce
WHERE CustomerCity = 'Tokyo';
```

**หมายเหตุ:**
- ถ้าข้อมูลในตารางสะกดหรือใช้ตัวพิมพ์เล็ก/ใหญ่ไม่แน่นอน (เช่น `tokyo`, `TOKYO`) ให้ใช้แบบนี้แทน:

```sql
SELECT OrderID, ProductName, CustomerCity
FROM Ecommerce
WHERE LOWER(TRIM(CustomerCity)) = 'tokyo';
```

- หากข้อมูลเก็บชื่อเมืองเป็นภาษาญี่ปุ่น (東京) ก็ต้องปรับค่าที่ใช้เปรียบเทียบตามนั้น
- ถ้าต้องการตัดรายการซ้ำ (กรณีหนึ่งคำสั่งซื้อมีหลายสินค้า แล้วอยากเห็นแต่ละแถวเพียงครั้งเดียว) ให้เพิ่ม `DISTINCT` หลัง `SELECT`