นี่คือคำสั่ง SQL สำหรับ PostgreSQL ที่ใช้ดึงข้อมูลคำสั่งซื้อทั้งหมดของลูกค้าในโตเกียวครับ:

```sql
SELECT OrderID, ProductName, CustomerCity
FROM Ecommerce
WHERE CustomerCity = 'Tokyo';

```