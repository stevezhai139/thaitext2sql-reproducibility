# AMENDMENT-2 (ข้อเสนอ — รอผู้เขียนเคาะ) — 7 ส.ค. 2026

## เหตุผล
Smoke run แรก (Gemini EN, 21 cells) เผย instrument flaw ระบบเดียว: **projection ambiguity**
— โจทย์ไม่ล็อกคอลัมน์ หรือ gold แสดงคอลัมน์เกิน/ต่างจากที่โจทย์ขอ ทำให้โมเดลที่ logic ถูกต้อง
ถูกหักคะแนน (พิสูจน์แล้ว 6 กรณีจริง: Q13, Q14, Q15, Q20, Q23, Q44 — logic ถูกทั้งหมด)

## หลักการแก้ (แก้ข้อความโจทย์เท่านั้น — gold SQL ไม่แตะแม้แต่ตัวเดียว)
1. เติมวงเล็บระบุคอลัมน์ "(show …)" / "(แสดง …)" ตามธรรมเนียมที่ suite ใช้อยู่แล้ว (Q09, Q10, Q22, Q26, Q27, Q51)
2. ธรรมเนียมที่ประกาศใน prereg (ไม่ต้องแก้โจทย์): "For each X, show Y" ⇒ ผลลัพธ์มี X ด้วย
   (ครอบ Q31, Q35, Q36, Q37, Q39, Q43, Q45, Q47, Q55, Q57, Q59, Q60)
3. "List presidents…" บน schema P ⇒ PresidentName คอลัมน์เดียว (TH เขียน "รายชื่อ" ชัดอยู่แล้ว;
   หลักฐาน smoke: Gemini ตีความแบบนี้ 4/4 ข้อ) — ไม่ต้องแก้
4. gold ยังคง FROZEN ⇒ self-test 60/60 เดิมยังใช้ได้ ไม่ต้อง re-validate

## รายการแก้ 17 ข้อ

| # | ปัญหา | EN ใหม่ | TH ใหม่ |
|---|-------|---------|---------|
| Q13 | โจทย์ไม่ล็อกคอลัมน์ | List orders paid by 'Credit Card' with quantity of at least 5 (show OrderID, ProductName, Quantity). | แสดงรายการสั่งซื้อที่จ่ายเงินด้วยบัตรเครดิตและมีจำนวนอย่างน้อย 5 (แสดง OrderID, ProductName, Quantity) |
| Q14 | ไม่ล็อกคอลัมน์ + "not returned" กำกวม (ข้อมูลมี 'Exchanged' ด้วย) | List orders that were neither returned nor exchanged and have a product rating of at least 4.5 (show OrderID, ProductName, ProductRating). | แสดงรายการคำสั่งซื้อที่ไม่มีการคืนหรือเปลี่ยนสินค้า โดยสินค้ามีเรตติ้งตั้งแต่ 4.5 (แสดง OrderID, ProductName, ProductRating) |
| Q15 | ไม่ล็อกคอลัมน์ + typo เครื่องแค่งกาย | Show orders in the 'Clothing' category placed by female customers (show OrderID, ProductName). | แสดงคำสั่งซื้อของสินค้าในกลุ่มเครื่องแต่งกายที่สั่งซื้อโดยผู้หญิง (แสดง OrderID, ProductName) |
| Q20 | gold มีชื่อประธานาธิบดีที่โจทย์ EN ไม่ได้ขอ (TH ถูกกว่า EN — ยึดตาม TH) | For each presidential marriage, show the president's name, the spouse's name, and the president's party. | ในการสมรสแต่ละครั้งของประธานาธิบดี ให้แสดงชื่อประธานาธิบดี ชื่อคู่สมรส และพรรคที่ประธานาธิบดีสังกัด |
| Q23 | gold แถม SpouseName เกินโจทย์ | For presidents whose spouse was born before the president himself, show the president's name and that spouse's name. | สำหรับประธานาธิบดีที่คู่สมรสเกิดก่อนตัวประธานาธิบดีเอง ให้แสดงชื่อประธานาธิบดีและชื่อคู่สมรสคนนั้น |
| Q29 | อ่านตรงตัวได้ status คอลัมน์เดียว | Show the marriage status of every president who began a term in the twentieth century (show president name and marriage status). | แสดงสถานะการสมรสของประธานาธิบดีทุกคนที่เริ่มดำรงตำแหน่งในศตวรรษที่ 20 (แสดงชื่อประธานาธิบดีและสถานะการสมรส) |
| Q38 | gold แถม count | Show the top 5 customer cities by number of orders (show city and order count; break ties alphabetically). | แสดง 5 เมืองของลูกค้าที่มีคำสั่งซื้อมากที่สุด (แสดงชื่อเมืองและจำนวนคำสั่งซื้อ; ถ้าเท่ากันให้เรียงตามตัวอักษร) |
| Q40 | gold แถม avg | List categories whose average product rating exceeds 3 (show category and average rating). | แสดงหมวดหมู่สินค้าที่มีเรตติ้งเฉลี่ยเกิน 3 (แสดงหมวดหมู่และเรตติ้งเฉลี่ย) |
| Q44 | gold แถม count (พิสูจน์แล้วจาก smoke) | List parties that have had at least three presidents (show party and president count). | แสดงชื่อพรรคที่มีประธานาธิบดีตั้งแต่ 3 คน (แสดงชื่อพรรคและจำนวนประธานาธิบดี) |
| Q46 | gold แถม term_len | List presidents whose term length exceeded the average term length (show president and term length). | แสดงรายชื่อประธานาธิบดีที่มีระยะเวลาดำรงตำแหน่งเกินกว่าค่าเฉลี่ย (แสดงชื่อประธานาธิบดีและระยะเวลาดำรงตำแหน่ง) |
| Q47 | gold แถม YearBorn | For each party, show the earliest-born president and his birth year (break ties by name). | สำหรับแต่ละพรรค แสดงประธานาธิบดีที่เกิดก่อนใครที่สุดของพรรคนั้นพร้อมปีเกิด (ถ้าปีเกิดเท่ากันให้เอาชื่อที่มาก่อนตามตัวอักษร) |
| Q49 | gold แถม term_len + typo "และดับ" | Rank all presidencies by term length, longest first (show president, term length, and rank). | แสดงอันดับประธานาธิบดีตามระยะเวลาดำรงตำแหน่ง นานสุดก่อน (แสดงชื่อประธานาธิบดี ระยะเวลาดำรงตำแหน่ง และอันดับ) |
| Q50 | gold แถม age gap | Show the three presidents with the largest age gap between president and spouse (show president and age gap in years; break ties by president name). | แสดงประธานาธิบดี 3 คนที่อายุห่างจากคู่สมรสมากที่สุด (แสดงชื่อประธานาธิบดีและผลต่างอายุเป็นปี; ถ้าเท่ากันให้เรียงตามชื่อประธานาธิบดี) |
| Q53 | ไม่ล็อกคอลัมน์ | List orders whose final price is above the average final price of their own category (show OrderID, Category, FinalPrice). | แสดงรายการคำสั่งซื้อที่มีราคาสุดท้ายเหนือค่าเฉลี่ยของสินค้าในหมวดหมู่ตนเอง (แสดง OrderID, Category, FinalPrice) |
| Q54 | gold แถม total รายเดือน | Show month-over-month change in total revenue for 2024 (show month, monthly total, and change from previous month). | แสดงการเปลี่ยนแปลงของรายได้รวมรายเดือนเทียบกับเดือนก่อนหน้าของปี 2024 (แสดงเดือน รายได้รวมของเดือน และผลต่างจากเดือนก่อนหน้า) |
| Q55 | gold แถม total | For each category, show its top 3 products by total revenue (show product and total revenue; break ties by product name). | สำหรับแต่ละหมวดสินค้า แสดงสินค้า 3 อันดับแรกตามรายได้รวม (แสดงชื่อสินค้าและรายได้รวม; ถ้าเท่ากันให้เรียงตามชื่อสินค้า) |
| Q56 | gold แถม total + typo เปอร์เซ็นต์ไทร์ | List customers whose total spending is above the 95th percentile of customer totals (show CustomerID and total spending). | แสดงรายชื่อลูกค้าที่มียอดใช้จ่ายรวมสูงกว่าเปอร์เซ็นไทล์ที่ 95 ของยอดรวมลูกค้าทั้งหมด (แสดง CustomerID และยอดใช้จ่ายรวม) |

(17 ข้อ: Q13–Q15, Q20, Q23, Q29, Q38, Q40, Q44, Q46, Q47, Q49, Q50, Q53–Q56)

## ผลกระทบต่อข้อมูลที่เก็บแล้ว
- ลบ 7 records จาก results.jsonl (Gemini EN: Q13, Q14, Q15, Q20, Q23, Q44, Q55 — โจทย์เปลี่ยน)
  → บันทึกการลบใน CHANGELOG; อีก 14 records โจทย์ไม่เปลี่ยน เก็บไว้ได้
- ฝั่ง TH ยังไม่เคยรัน — ไม่กระทบ
- Suite ใหม่ = k3_suite_v1.2.tsv; prereg บันทึก AMENDMENT-2 พร้อมเหตุผล
