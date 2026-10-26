โจทย์นี้ต้องเปรียบเทียบปีที่สมรส (`MarriageYear`) กับปีที่เข้ารับตำแหน่ง (`YearHolding`) โดยเชื่อมตาราง `PresidentMarriage` กับ `PresidentHolding` ผ่านชื่อประธานาธิบดี

```sql
SELECT DISTINCT pm.PresidentName
FROM PresidentMarriage pm
JOIN PresidentHolding ph
  ON pm.PresidentName = ph.PresidentName
WHERE pm.MarriageYear > ph.YearHolding
ORDER BY pm.PresidentName;
```

**คำอธิบาย**

- `JOIN` เชื่อมข้อมูลการสมรสกับข้อมูลการดำรงตำแหน่งของประธานาธิบดีคนเดียวกัน
- เงื่อนไข `pm.MarriageYear > ph.YearHolding` กรองเฉพาะกรณีที่แต่งงานหลังปีที่เข้ารับตำแหน่ง
- `DISTINCT` ป้องกันชื่อซ้ำ เพราะประธานาธิบดีบางคนอาจสมรสหลายครั้ง หรือดำรงตำแหน่งหลายสมัย

**หมายเหตุ:** คิวรีนี้ใช้ปีเท่านั้น ถ้าแต่งงานในปีเดียวกับที่เข้ารับตำแหน่ง จะไม่ถูกนับ (เพราะใช้ `>` ไม่ใช่ `>=`) หากต้องการรวมกรณีปีเดียวกันด้วย ให้เปลี่ยนเป็น `>=`