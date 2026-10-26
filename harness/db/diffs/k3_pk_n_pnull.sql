-- k3_pk_n_pnull = k3_pk_n_named with ONE cell changed (PK1 instance 4 of 5; gold 'NO')
--
-- PresidentMarriage, row of James Buchanan (whose SpouseName is the synthetic
-- value of k3_pk_n_named): PresidentName -> NULL. Afterwards PresidentName is
-- NULL in exactly one row, SpouseName is never NULL and no key value repeats.
-- Effect on PK1: nullity fails on PresidentName only -> gold 'NO'. An answer that
-- tests NULL in SpouseName only (or uniqueness only) passes k3n but fails here.
--
-- Order-preserving rewrite (see k3_pk_n_named.sql; delta in_place, changed 1).
--
-- OQ4: literal value(s) below approved by the author (2026-10-14)
-- Literal value (pinned by the sha256 of this file): pnull_president = 'James Buchanan'
-- (TEST-ONLY: the row of George Washington gives the same result for every
-- registered answer)
--
-- Applied by build_instances.py in ONE transaction:
--   psql -X -v ON_ERROR_STOP=1 -1 -f k3_pk_n_pnull.sql

CREATE TEMP TABLE _pk1_param ON COMMIT DROP AS
  SELECT 'James Buchanan'::text AS pnull_president;

DO $$
DECLARE v text := (SELECT pnull_president FROM _pk1_param);
BEGIN
  IF (SELECT COUNT(*) FROM presidentmarriage) <> 49
     OR EXISTS (SELECT 1 FROM presidentmarriage
                WHERE presidentname IS NULL OR spousename IS NULL)
     OR EXISTS (SELECT 1 FROM presidentmarriage
                GROUP BY presidentname, spousename HAVING COUNT(*) > 1)
     OR (SELECT COUNT(*) FROM presidentmarriage WHERE presidentname = v) <> 1 THEN
    RAISE EXCEPTION 'k3_pk_n_pnull: parent PresidentMarriage is not as expected (49 rows, 0 NULL key, 0 repeated key, one row of %)', v;
  END IF;
END $$;

CREATE TEMP TABLE _k3_rows ON COMMIT DROP AS
  SELECT ctid AS _pos, * FROM presidentmarriage;
TRUNCATE presidentmarriage;
INSERT INTO presidentmarriage
       (presidentname, spousename, spousebirthday, marriageyear, marriagestatus)
SELECT CASE WHEN presidentname = (SELECT pnull_president FROM _pk1_param)
            THEN NULL ELSE presidentname END,
       spousename, spousebirthday, marriageyear, marriagestatus
FROM _k3_rows
ORDER BY _pos;

DO $$
BEGIN
  IF (SELECT COUNT(*) FROM presidentmarriage) <> 49
     OR (SELECT COUNT(*) FROM presidentmarriage WHERE presidentname IS NULL) <> 1
     OR EXISTS (SELECT 1 FROM presidentmarriage WHERE spousename IS NULL)
     OR EXISTS (SELECT 1 FROM presidentmarriage
                GROUP BY presidentname, spousename HAVING COUNT(*) > 1) THEN
    RAISE EXCEPTION 'k3_pk_n_pnull: result is not 49 rows / 1 NULL PresidentName / 0 NULL SpouseName / 0 repeated key';
  END IF;
END $$;
