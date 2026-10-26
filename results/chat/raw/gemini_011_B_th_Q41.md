นี่คือคำสั่ง SQL (PostgreSQL) สำหรับสรุปรายได้รวมและจำนวนคำสั่งซื้อแยกตามช่องทางการตลาด (MarketingChannel) โดยคัดกรองเฉพาะช่องทางที่มีคำสั่งซื้อมากกว่า 100 รายการครับ

```sql
SELECT 
    MarketingChannel,
    SUM(Revenue) AS TotalRevenue,
    COUNT(OrderID) AS TotalOrders
FROM 
    Ecommerce
GROUP BY 
    MarketingChannel
HAVING 
    COUNT(OrderID) > 100
ORDER BY 
    TotalRevenue DESC;

```

---

### คำอธิบายคำสั่ง:

* **`SELECT MarketingChannel, SUM(Revenue), COUNT(OrderID)`**: เลือกแสดงชื่อช่องทางการตลาด, ผลรวมของรายได้ (`Revenue`), และนับจำนวนคำสั่งซื้อ (`OrderID`)
* **`GROUP BY MarketingChannel`**: จัดกลุ่มข้อมูลตามช่องทางการตลาด
* **`HAVING COUNT(OrderID) > 100`**: คัดกรองผลลัพธ์เฉพาะกลุ่มที่มีจำนวนคำสั่งซื้อ **มากกว่า 100 รายการ** *(ใช้ `HAVING` เนื่องจากเป็นการกรองข้อมูลหลังจากการจัดกลุ่มและคำนวณ `COUNT`)*
* **`ORDER BY TotalRevenue DESC`**: เรียงลำดับจากช่องทางการตลาดที่ทำรายได้สูงสุดไปหาน้อยที่สุด (ช่วยให้ดูข้อมูลได้ง่ายขึ้น)