นี่คือคำสั่ง SQL (PostgreSQL) สำหรับดึงข้อมูลตามเงื่อนไขที่คุณต้องการครับ:

```sql
SELECT OrderID, ProductName, ProductRating
FROM Ecommerce
WHERE ProductRating >= 4.5
  AND ReturnStatus NOT IN ('Returned', 'Exchanged');

```

---

### คำอธิบายเพิ่มเติม:

* **`SELECT OrderID, ProductName, ProductRating`**: เลือกแสดงเฉพาะคอลัมน์ `OrderID`, `ProductName` และ `ProductRating` ตามที่โจทย์กำหนด
* **`WHERE ProductRating >= 4.5`**: กรองเฉพาะสินค้าที่มีเรตติ้งตั้งแต่ 4.5 ขึ้นไป
* **`AND ReturnStatus NOT IN ('Returned', 'Exchanged')`**: กรองรายการที่ไม่มีการคืนสินค้า (Returned) หรือเปลี่ยนสินค้า (Exchanged) *(หมายเหตุ: คุณสามารถปรับเปลี่ยนค่าในวงเล็บ `'Returned', 'Exchanged'` ให้ตรงกับข้อมูลจริงในตารางของคุณได้ เช่น หากใช้คำว่า `'None'` หรือ `'No'` สามารถเปลี่ยนเป็น `ReturnStatus = 'None'` ได้ครับ)*