-- k3_pk_n_dup = k3_pk_n_named + ONE appended row (PK1 instance 3 of 5; gold 'NO')
--
-- The new row repeats the key value (PresidentName, SpouseName) of the existing
-- row ('Grover Cleveland', 'Frances Cleveland'); its other columns are copied
-- from that row except MarriageStatus ('Widowed' instead of 'Married'), so what
-- repeats is a KEY VALUE, not a whole row (an answer that looks only for
-- repeated whole rows does not see it). Neither key column is NULL anywhere.
-- Effect on PK1: uniqueness fails, nullity holds -> gold 'NO'.
--
-- Brief 1.3: this instance must be built from a version in which Buchanan has a
-- spouse name. The first guard enforces that the parent has no NULL in either
-- key column (k3_pk_n_named); on k3n (Buchanan's SpouseName NULL) it stops.
-- The row is appended at the physical end (build_instances.py checks delta
-- append, added 1). No other table changes.
--
-- OQ4: literal value(s) below approved by the author (2026-10-14)
-- Literal values (pinned by the sha256 of this file): dup_president = 'Grover Cleveland',
-- dup_spouse = 'Frances Cleveland', dup_status = 'Widowed'
--
-- Applied by build_instances.py in ONE transaction:
--   psql -X -v ON_ERROR_STOP=1 -1 -f k3_pk_n_dup.sql

CREATE TEMP TABLE _pk1_param ON COMMIT DROP AS
  SELECT 'Grover Cleveland'::text AS dup_president,
         'Frances Cleveland'::text AS dup_spouse,
         'Widowed'::text AS dup_status;

DO $$
DECLARE p _pk1_param%ROWTYPE;
BEGIN
  SELECT * INTO p FROM _pk1_param;
  IF EXISTS (SELECT 1 FROM presidentmarriage
             WHERE presidentname IS NULL OR spousename IS NULL) THEN
    RAISE EXCEPTION 'k3_pk_n_dup: the parent has a NULL key column; build this instance from k3_pk_n_named (Buchanan with a spouse name), not from k3n';
  END IF;
  IF (SELECT COUNT(*) FROM presidentmarriage) <> 49
     OR EXISTS (SELECT 1 FROM presidentmarriage
                GROUP BY presidentname, spousename HAVING COUNT(*) > 1)
     OR (SELECT COUNT(*) FROM presidentmarriage
         WHERE presidentname = p.dup_president AND spousename = p.dup_spouse
           AND marriagestatus IS DISTINCT FROM p.dup_status) <> 1
     OR EXISTS (SELECT 1 FROM presidentmarriage
                WHERE presidentname = p.dup_president AND spousename = p.dup_spouse
                  AND marriagestatus = p.dup_status) THEN
    RAISE EXCEPTION 'k3_pk_n_dup: parent PresidentMarriage is not as expected (49 rows, no repeated key, the row to repeat present once with another status)';
  END IF;
END $$;

INSERT INTO presidentmarriage
       (presidentname, spousename, spousebirthday, marriageyear, marriagestatus)
SELECT m.presidentname, m.spousename, m.spousebirthday, m.marriageyear, p.dup_status
FROM presidentmarriage m, _pk1_param p
WHERE m.presidentname = p.dup_president AND m.spousename = p.dup_spouse;

DO $$
BEGIN
  IF (SELECT COUNT(*) FROM presidentmarriage) <> 50
     OR (SELECT COUNT(*) FROM (SELECT 1 FROM presidentmarriage
                               GROUP BY presidentname, spousename
                               HAVING COUNT(*) > 1) d) <> 1
     OR EXISTS (SELECT 1 FROM presidentmarriage
                WHERE presidentname IS NULL OR spousename IS NULL)
     OR (SELECT COUNT(*) FROM (SELECT DISTINCT * FROM presidentmarriage) w) <> 50 THEN
    RAISE EXCEPTION 'k3_pk_n_dup: result is not 50 rows / 1 repeated key / 0 NULL key / 0 repeated whole row';
  END IF;
END $$;
