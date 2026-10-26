โจทย์นี้หมายถึงประธานาธิบดีที่เคยดำรงตำแหน่งหลายวาระ โดยวาระที่สองไม่ได้ต่อเนื่องจากวาระแรก (เช่น Grover Cleveland หรือ Donald Trump) ในตาราง `PresidentHolding` หนึ่งแถวคือหนึ่งวาระ จึงต้องหาคนที่มีวาระถัดไปซึ่งเริ่มหลังจากวาระก่อนหน้าจบไปแล้วมากกว่าหนึ่งช่วงวาระ

## วิธีที่ 1: ใช้ `LAG` (แนะนำ)

```sql
SELECT DISTINCT PresidentName
FROM (
    SELECT
        PresidentName,
        YearHolding,
        LAG(YearEnd) OVER (
            PARTITION BY PresidentName
            ORDER BY YearHolding
        ) AS PrevYearEnd
    FROM PresidentHolding
) t
WHERE PrevYearEnd IS NOT NULL
  AND YearHolding > PrevYearEnd;
```

## วิธีที่ 2: ใช้ Self Join

```sql
SELECT DISTINCT a.PresidentName
FROM PresidentHolding a
JOIN PresidentHolding b
  ON a.PresidentName = b.PresidentName
 AND b.YearHolding > a.YearEnd;
```

## อธิบาย

- วิธีที่ 1 เรียงวาระของแต่ละคนตาม `YearHolding` แล้วใช้ `LAG(YearEnd)` ดึงปีที่วาระก่อนหน้าสิ้นสุดมาเทียบกับปีเริ่มของวาระปัจจุบัน
- ถ้า `YearHolding > PrevYearEnd` แปลว่ามีช่องว่างระหว่างสองวาระ ซึ่งก็คือไม่ต่อเนื่องกัน
- วาระที่ต่อเนื่องกันจะมี `YearHolding = PrevYearEnd` (เช่น วาระแรกจบปี 1893 วาระถัดไปเริ่มปี 1893) จึงไม่ถูกนับ
- `DISTINCT` ช่วยป้องกันชื่อซ้ำ ในกรณีที่คนเดียวมีช่วงห่างมากกว่าหนึ่งครั้ง

## หมายเหตุ

ถ้าข้อมูลของคุณเก็บ `YearEnd` เป็นปีสุดท้ายที่ดำรงตำแหน่งจริง (เช่น วาระแรก 1885-1889 วาระต่อเนื่องจะเริ่ม 1890) ให้เปลี่ยนเงื่อนไขเป็น `YearHolding > PrevYearEnd + 1` แทน ลองดูข้อมูลตัวอย่างของคุณเพื่อเลือกให้ตรงกับรูปแบบที่ใช้