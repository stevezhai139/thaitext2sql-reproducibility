```sql
SELECT OrderID, ProductName, Quantity
FROM Ecommerce
WHERE PaymentMethod = 'Credit Card'
  AND Quantity >= 5;
```

**หมายเหตุ:**
- ค่าในคอลัมน์ `PaymentMethod` อาจเขียนต่างกันไปตามข้อมูลจริง เช่น `'Credit Card'`, `'credit_card'` หรือ `'CreditCard'` ถ้าไม่แน่ใจ ลองตรวจสอบก่อนด้วย:
  ```sql
  SELECT DISTINCT PaymentMethod FROM Ecommerce;
  ```
- หากต้องการให้ไม่สนใจตัวพิมพ์เล็ก/ใหญ่ ใช้แบบนี้แทนได้:
  ```sql
  WHERE LOWER(PaymentMethod) = 'credit card' AND Quantity >= 5
  ```