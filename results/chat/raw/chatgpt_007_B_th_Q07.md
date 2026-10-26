```
SELECT SpouseName
FROM PresidentMarriage
WHERE MarriageStatus = 'Widowed';
```

หมายเหตุ: หากข้อมูลสถานะหม้ายในตารางใช้คำภาษาไทย ให้เปลี่ยนเงื่อนไขเป็น `WHERE MarriageStatus = 'หม้าย'` ตามค่าที่จัดเก็บไว้จริง