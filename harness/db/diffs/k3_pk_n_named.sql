-- k3_pk_n_named = k3n with ONE cell changed (PK1 instance 2 of 5; gold 'YES')
--
-- PresidentMarriage, row of James Buchanan: SpouseName NULL -> 'Planted Spouse'.
-- Afterwards neither key column (PresidentName, SpouseName) is NULL and no key
-- value repeats, so the pair has the properties of a primary key: PK1 gold 'YES'.
-- k3_pk_n_dup and k3_pk_n_pnull are built from this instance (brief 1.3: the
-- duplicate-row instance must come from a version in which Buchanan has a spouse
-- name, otherwise an answer that only checks for NULLs passes every instance).
-- The value is synthetic on purpose (no invented fact about a real person), in
-- the style of the 'Planted President ...' rows of the FK instances.
--
-- Order-preserving rewrite: an UPDATE would put the new row version at the end
-- of the heap and change the row order of scans without ORDER BY; the table is
-- rewritten in ctid order so every row keeps its position (build_instances.py
-- checks delta in_place, changed 1).
--
-- OQ4: literal value(s) below approved by the author (2026-10-14)
-- Literal value (pinned by the sha256 of this file): buchanan_spouse = 'Planted Spouse'
--
-- Applied by build_instances.py in ONE transaction:
--   psql -X -v ON_ERROR_STOP=1 -1 -f k3_pk_n_named.sql

CREATE TEMP TABLE _pk1_param ON COMMIT DROP AS
  SELECT 'Planted Spouse'::text AS buchanan_spouse;

DO $$
DECLARE v text := (SELECT buchanan_spouse FROM _pk1_param);
BEGIN
  IF (SELECT COUNT(*) FROM presidentmarriage) <> 49
     OR (SELECT COUNT(*) FROM presidentmarriage WHERE spousename IS NULL) <> 1
     OR (SELECT COUNT(*) FROM presidentmarriage
         WHERE presidentname = 'James Buchanan' AND spousename IS NULL) <> 1
     OR EXISTS (SELECT 1 FROM presidentmarriage WHERE presidentname IS NULL)
     OR EXISTS (SELECT 1 FROM presidentmarriage
                GROUP BY presidentname, spousename HAVING COUNT(*) > 1)
     OR EXISTS (SELECT 1 FROM presidentmarriage WHERE spousename = v) THEN
    RAISE EXCEPTION 'k3_pk_n_named: parent PresidentMarriage is not as expected (49 rows, SpouseName NULL only in the row of James Buchanan, no NULL PresidentName, no repeated key, % not used yet)', v;
  END IF;
END $$;

CREATE TEMP TABLE _k3_rows ON COMMIT DROP AS
  SELECT ctid AS _pos, * FROM presidentmarriage;
TRUNCATE presidentmarriage;
INSERT INTO presidentmarriage
       (presidentname, spousename, spousebirthday, marriageyear, marriagestatus)
SELECT presidentname,
       CASE WHEN presidentname = 'James Buchanan' AND spousename IS NULL
            THEN (SELECT buchanan_spouse FROM _pk1_param) ELSE spousename END,
       spousebirthday, marriageyear, marriagestatus
FROM _k3_rows
ORDER BY _pos;

DO $$
DECLARE v text := (SELECT buchanan_spouse FROM _pk1_param);
BEGIN
  IF (SELECT COUNT(*) FROM presidentmarriage) <> 49
     OR EXISTS (SELECT 1 FROM presidentmarriage
                WHERE presidentname IS NULL OR spousename IS NULL)
     OR EXISTS (SELECT 1 FROM presidentmarriage
                GROUP BY presidentname, spousename HAVING COUNT(*) > 1)
     OR (SELECT COUNT(*) FROM presidentmarriage
         WHERE presidentname = 'James Buchanan' AND spousename = v) <> 1 THEN
    RAISE EXCEPTION 'k3_pk_n_named: result is not 49 rows / 0 NULL key / 0 repeated key';
  END IF;
END $$;
