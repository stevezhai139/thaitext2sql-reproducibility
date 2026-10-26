นี่คือคำสั่ง SQL (PostgreSQL) สำหรับดึงข้อมูลคำสั่งซื้อสินค้าในกลุ่มเครื่องแต่งกายที่สั่งซื้อโดยผู้หญิง ตามโครงสร้างตารางที่คุณกำหนดครับ:

```sql
SELECT OrderID, ProductName
FROM Ecommerce
WHERE Category = 'Apparel' 
  AND CustomerGender = 'Female';

```

### คำอธิบายเพิ่มเติม:

* **`SELECT OrderID, ProductName`**: เลือกแสดงเฉพาะฟิลด์รหัสคำสั่งซื้อ (`OrderID`) และชื่อสินค้า (`ProductName`) ตามโจทย์
* **`WHERE Category = 'Apparel'`**: กรองเฉพาะสินค้าในกลุ่มเครื่องแต่งกาย *(คุณสามารถเปลี่ยนค่า `'Apparel'` เป็น `'Clothing'` หรือชื่อหมวดหมู่จริงในฐานข้อมูลของคุณได้)*
* **`AND CustomerGender = 'Female'`**: กรองเฉพาะลูกค้าที่เป็นผู้หญิง *(สามารถปรับเปลี่ยนเป็น `'หญิง'` หรือ `'F'` ได้ตามรูปแบบข้อมูลจริง)*