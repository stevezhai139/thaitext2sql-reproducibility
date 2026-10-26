-- rq3_drop_indexes.sql — phase "no-index" ของ RQ3 (Ecommerce1M)
-- ลบดัชนีทั้ง 6 ตัวที่ harness/indexes.sql สร้างไว้ แล้ว ANALYZE ใหม่
-- ใช้กับสำเนา k3n_rq3 เท่านั้น (createdb -T "k3n" "k3n_rq3"; ห้ามรันบน k3n หรือ k3)
-- ใช้: psql -d "k3n_rq3" -f "db/rq3_drop_indexes.sql"
\set ON_ERROR_STOP on
DO $$
BEGIN
  IF current_database() IN ('k3', 'k3n') THEN
    RAISE EXCEPTION 'rq3_drop_indexes.sql: run it on the RQ3 copy (k3n_rq3), not on %', current_database();
  END IF;
END $$;
DROP INDEX IF EXISTS idx_e1m_orderdate;
DROP INDEX IF EXISTS idx_e1m_category;
DROP INDEX IF EXISTS idx_e1m_city;
DROP INDEX IF EXISTS idx_e1m_region;
DROP INDEX IF EXISTS idx_e1m_customer;
DROP INDEX IF EXISTS idx_e1m_ret_rate;
ANALYZE Ecommerce1M;
