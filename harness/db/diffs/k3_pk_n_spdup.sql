-- k3_pk_n_spdup = k3n with ONE cell changed (PK1 instance 5 of 5; gold 'YES')
--
-- PresidentMarriage, row of James Buchanan: SpouseName NULL -> 'Mary Todd', a
-- spouse name that already exists for another president. Afterwards no key
-- column is NULL and no PAIR repeats, but SpouseName alone repeats across two
-- different presidents. Effect on PK1: the pair has the properties of a primary
-- key -> gold 'YES'. An answer that demands uniqueness of SpouseName alone (a
-- stronger condition than the pair) fails here.
--
-- Order-preserving rewrite (see k3_pk_n_named.sql; delta in_place, changed 1).
--
-- OQ4: literal value(s) below approved by the author (2026-10-14)
-- Literal value (pinned by the sha256 of this file): reused_spouse = 'Mary Todd'
--
-- Applied by build_instances.py in ONE transaction:
--   psql -X -v ON_ERROR_STOP=1 -1 -f k3_pk_n_spdup.sql

CREATE TEMP TABLE _pk1_param ON COMMIT DROP AS
  SELECT 'Mary Todd'::text AS reused_spouse;

DO $$
DECLARE v text := (SELECT reused_spouse FROM _pk1_param);
BEGIN
  IF (SELECT COUNT(*) FROM presidentmarriage) <> 49
     OR (SELECT COUNT(*) FROM presidentmarriage WHERE spousename IS NULL) <> 1
     OR (SELECT COUNT(*) FROM presidentmarriage
         WHERE presidentname = 'James Buchanan' AND spousename IS NULL) <> 1
     OR EXISTS (SELECT 1 FROM presidentmarriage WHERE presidentname IS NULL)
     OR EXISTS (SELECT 1 FROM presidentmarriage
                GROUP BY presidentname, spousename HAVING COUNT(*) > 1)
     OR (SELECT COUNT(*) FROM presidentmarriage
         WHERE spousename = v AND presidentname <> 'James Buchanan') <> 1 THEN
    RAISE EXCEPTION 'k3_pk_n_spdup: parent PresidentMarriage is not k3n as expected (49 rows, SpouseName NULL only for James Buchanan, % used once by another president)', v;
  END IF;
END $$;

CREATE TEMP TABLE _k3_rows ON COMMIT DROP AS
  SELECT ctid AS _pos, * FROM presidentmarriage;
TRUNCATE presidentmarriage;
INSERT INTO presidentmarriage
       (presidentname, spousename, spousebirthday, marriageyear, marriagestatus)
SELECT presidentname,
       CASE WHEN presidentname = 'James Buchanan' AND spousename IS NULL
            THEN (SELECT reused_spouse FROM _pk1_param) ELSE spousename END,
       spousebirthday, marriageyear, marriagestatus
FROM _k3_rows
ORDER BY _pos;

DO $$
DECLARE v text := (SELECT reused_spouse FROM _pk1_param);
BEGIN
  IF (SELECT COUNT(*) FROM presidentmarriage) <> 49
     OR EXISTS (SELECT 1 FROM presidentmarriage
                WHERE presidentname IS NULL OR spousename IS NULL)
     OR EXISTS (SELECT 1 FROM presidentmarriage
                GROUP BY presidentname, spousename HAVING COUNT(*) > 1)
     OR (SELECT COUNT(DISTINCT presidentname) FROM presidentmarriage
         WHERE spousename = v) <> 2 THEN
    RAISE EXCEPTION 'k3_pk_n_spdup: result is not 49 rows / 0 NULL key / 0 repeated key / one SpouseName under two presidents';
  END IF;
END $$;
