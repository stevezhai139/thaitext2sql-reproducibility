นี่คือคำสั่ง SQL (PostgreSQL) สำหรับดึงรายชื่อประธานาธิบดีที่ **แต่งงาน (แต่งงานปีเดียวกับหรือหลังจาก) ปีที่เข้ารับตำแหน่ง** ครับ

```sql
SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentMarriage pm 
  ON p.PresidentName = pm.PresidentName
JOIN PresidentHolding ph 
  ON p.PresidentName = ph.PresidentName
WHERE pm.MarriageYear >= ph.YearHolding;

```

---

### 💡 คำอธิบายการทำงาน:

1. **`JOIN` ตาราง**: เชื่อมตาราง `PresidentMarriage` (ข้อมูลการแต่งงาน) และ `PresidentHolding` (ข้อมูลการดำรงตำแหน่ง) ด้วยชื่อประธานาธิบดี (`PresidentName`)
2. **`WHERE pm.MarriageYear >= ph.YearHolding`**: กรองเฉพาะประธานาธิบดีที่มีปีที่แต่งงาน (`MarriageYear`) เท่ากับหรือมากกว่าปีที่เริ่มดำรงตำแหน่ง (`YearHolding`)
3. **`DISTINCT`**: ช่วยกำจัดรายชื่อที่ซ้ำกัน (ในกรณีที่ประธานาธิบดีแต่งงานหลายครั้ง หรือดำรงตำแหน่งหลายสมัย)

> **หมายเหตุ:** หากต้องการเงื่อนไขแบบ *หลังจากเข้ารับตำแหน่งอย่างเคร่งครัด* (ไม่นับปีที่เข้ารับตำแหน่งพอดี) สามารถเปลี่ยนเครื่องหมายเป็น `pm.MarriageYear > ph.YearHolding` ได้เลยครับ

มีส่วนไหนของเงื่อนไขที่อยากให้ปรับแต่งเพิ่มเติมไหมครับ?