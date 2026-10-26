นี่คือคำสั่ง SQL (PostgreSQL) สำหรับดึงข้อมูลตามโจทย์ครับ:

```sql
SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentMarriage pm ON p.PresidentName = pm.PresidentName
WHERE p.PartyName = 'Democratic-Republican'
  AND pm.MarriageStatus = 'Widowed';

```

---

### **คำอธิบายเพิ่มเติม:**

* **`JOIN PresidentMarriage`**: เชื่อมตาราง `President` กับ `PresidentMarriage` ด้วยชื่อประธานาธิบดี (`PresidentName`) เพื่อดูข้อมูลสถานะการสมรส
* **`WHERE`**:
* `p.PartyName = 'Democratic-Republican'`: กรองเอาเฉพาะสังกัดพรรค Democratic-Republican
* `pm.MarriageStatus = 'Widowed'`: กรองเอาเฉพาะผู้ที่มีสถานะการสมรสเป็นหม้าย (Widowed)


* **`DISTINCT`**: ใส่ไว้เพื่อป้องกันกรณีที่ประธานาธิบดีคนเดิมมีประวัติการแต่งงานมากกว่า 1 ครั้งแล้วชื่อขึ้นซ้ำในผลลัพธ์

หากต้องการให้ดึงข้อมูลอื่นเพิ่มเติม เช่น ชื่อคู่สมรส หรือปีที่แต่งงาน สามารถบอกเพิ่มได้เลยครับ!