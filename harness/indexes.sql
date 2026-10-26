-- indexes.sql — ดัชนีสำหรับ phase "with-index" ของ RQ3 (บน Ecommerce1M)
-- เลือกตาม access paths ของ 12 ข้อ eff=yes
CREATE INDEX idx_e1m_orderdate ON Ecommerce1M(OrderDate);
CREATE INDEX idx_e1m_category  ON Ecommerce1M(Category);
CREATE INDEX idx_e1m_city      ON Ecommerce1M(CustomerCity);
CREATE INDEX idx_e1m_region    ON Ecommerce1M(Region);
CREATE INDEX idx_e1m_customer  ON Ecommerce1M(CustomerID, OrderDate DESC);
CREATE INDEX idx_e1m_ret_rate  ON Ecommerce1M(ReturnStatus, ProductRating);
ANALYZE Ecommerce1M;
-- phase "no-index": DROP INDEX ทุกตัวข้างบน แล้ว ANALYZE ใหม่ (ดู RUNBOOK)
