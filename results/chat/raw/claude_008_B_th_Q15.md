```sql
SELECT OrderID, ProductName
FROM Ecommerce
WHERE Category = 'Clothing'
  AND CustomerGender = 'Female';
```

**หมายเหตุ:**
- ค่าในคอลัมน์ `Category` และ `CustomerGender` ขึ้นอยู่กับข้อมูลจริงในตาราง เช่น กลุ่มเครื่องแต่งกายอาจเป็น `'Clothing'`, `'Apparel'` หรือ `'Fashion'` และเพศหญิงอาจเป็น `'Female'`, `'F'` หรือ `'หญิง'` แนะนำให้ตรวจสอบค่าที่มีอยู่ก่อนด้วย:

```sql
SELECT DISTINCT Category FROM Ecommerce;
SELECT DISTINCT CustomerGender FROM Ecommerce;
```

- ถ้าต้องการให้ไม่สนใจตัวพิมพ์เล็ก/ใหญ่ สามารถใช้ `ILIKE` แทนได้ เช่น

```sql
SELECT OrderID, ProductName
FROM Ecommerce
WHERE Category ILIKE 'clothing'
  AND CustomerGender ILIKE 'female';
```