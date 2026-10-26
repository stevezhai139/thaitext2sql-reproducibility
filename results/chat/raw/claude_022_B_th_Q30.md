ใช้การ JOIN ตาราง `President` กับ `PresidentMarriage` แล้วกรองตามพรรคและสถานะการสมรส:

```sql
SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentMarriage pm ON p.PresidentName = pm.PresidentName
WHERE p.PartyName = 'Democratic-Republican'
  AND pm.MarriageStatus = 'Widowed';
```

**หมายเหตุ**

- ค่าใน `MarriageStatus` ที่ใช้แทนสถานะหม้ายอาจไม่ตรงกับ `'Widowed'` เช่น อาจเป็น `'Widower'`, `'Widow'` หรือค่าอื่น แนะนำให้ตรวจสอบก่อนด้วย
  ```sql
  SELECT DISTINCT MarriageStatus FROM PresidentMarriage;
  ```
- ถ้าไม่แน่ใจเรื่องตัวพิมพ์เล็ก/ใหญ่หรือรูปแบบคำ สามารถใช้ `ILIKE` ได้ เช่น
  ```sql
  AND pm.MarriageStatus ILIKE 'widow%'
  ```
- ใช้ `DISTINCT` เพราะประธานาธิบดีบางคนอาจมีหลายแถวในตาราง `PresidentMarriage` (เช่น แต่งงานหลายครั้ง) ซึ่งจะทำให้ชื่อซ้ำกัน