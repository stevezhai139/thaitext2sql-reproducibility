-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- FK1 new format (issue 9 decision: list the violating rows, mirroring exam part (i)) -- DRAFT, TEST-ONLY
-- question_en (draft):
--   Suppose President.PartyName is a foreign key that refers to Party.PartyName, and PartyName in President
--   is allowed to be NULL. Judging only from the rows that are in the tables now, list the presidents whose
--   PartyName breaks this foreign key (show president name and PartyName).
-- question_th (draft, edited from the author's current TH):
--   สมมติให้ President.PartyName เป็น Foreign Key ที่อ้างอิงไปยัง Party.PartyName และอนุญาตให้ค่า PartyName
--   ในตาราง President เป็น NULL ได้ ให้ตรวจสอบข้อมูลในตารางปัจจุบันว่ามีประธานาธิบดีคนใดบ้างที่ค่า PartyName
--   ขัดต่อเงื่อนไขของ Foreign Key นี้ โดยแสดงชื่อประธานาธิบดีและค่า PartyName
-- gold (PostgreSQL 16):
SELECT p.PresidentName, p.PartyName
FROM President p
WHERE p.PartyName IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM Party pa WHERE pa.PartyName = p.PartyName);
-- expected per instance (TEST-ONLY run on scratch PG16, read-only):
--   k3n            : 0 rows
--   k3_fk_i_null   : 0 rows   (planted 'Planted President NoParty', PartyName NULL -> not a violation)
--   k3_fk_i_orphan : 1 row    ('Planted President Orphan', 'Know Nothing')
-- k3_fk_i_* were built from k3; President and Party are byte-identical (md5) in k3 and k3n, so these results carry
-- over to instances rebuilt from k3n (issue 14); the manifest fingerprints must be re-recorded after the rebuild.
-- correct alternatives (same result on every instance): NOT IN (SELECT PartyName FROM Party) [Party.PartyName has no NULL];
--   LEFT JOIN Party ... WHERE pa.PartyName IS NULL AND p.PartyName IS NOT NULL
-- foils graded wrong on >= 1 instance (TEST-ONLY): LEFT JOIN anti-join without NULL guard; NOT EXISTS without NULL guard;
--   COALESCE(PartyName,'') NOT IN Party; nullity-only; wrong direction (parties without presidents); EXCEPT on values;
--   constant empty; dangling values only (1 column); SELECT * (4 columns)
-- grading notes: gold is empty on the base k3n and on k3_fk_i_null, non-empty only on k3_fk_i_orphan, so
--   (a) the suite rule 'v13_status = excluded when gold is empty on the run DB' must not apply to this MI item,
--   (b) G1 (non-empty) holds on the orphan instance only; single-instance grading on k3n is not possible.
