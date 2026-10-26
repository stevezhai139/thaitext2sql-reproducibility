-- k3_fk_i_null = k3n + ONE appended President row whose PartyName is NULL
-- (FK1 instance 2 of 3, FK2 instance 2 of 2)
--
-- New row: ('Planted President NoParty', 1950, 'Ohio', NULL) -- the PLANTED row
-- of the FK item drafts. A NULL value of a nullable foreign key is NOT a
-- violation: FK1 gold (list the presidents whose PartyName breaks the foreign
-- key) stays empty. FK2 gold (parties that could be deleted under ON DELETE
-- RESTRICT) stays Progressive, Union; an answer written with
-- NOT IN (SELECT PartyName FROM President) returns no row here (NULL trap).
-- INSERT only: the row is appended at the physical end (build_instances.py
-- checks delta append, added 1). No other table changes.
--
-- Applied by build_instances.py in ONE transaction:
--   psql -X -v ON_ERROR_STOP=1 -1 -f k3_fk_i_null.sql

DO $$
BEGIN
  IF (SELECT COUNT(*) FROM president) <> 45
     OR EXISTS (SELECT 1 FROM president WHERE partyname IS NULL)
     OR EXISTS (SELECT 1 FROM president p
                WHERE NOT EXISTS (SELECT 1 FROM party y WHERE y.partyname = p.partyname))
     OR EXISTS (SELECT 1 FROM president WHERE presidentname LIKE 'Planted President%')
     OR EXISTS (SELECT 1 FROM party
                WHERE lower(btrim(partyname)) = lower(btrim('Know Nothing'))) THEN
    RAISE EXCEPTION 'k3_fk_i_null: parent President/Party is not as expected (45 rows, no NULL or orphan PartyName, no planted row, Know Nothing not a party)';
  END IF;
END $$;

INSERT INTO president (presidentname, yearborn, stateborn, partyname)
VALUES ('Planted President NoParty', 1950, 'Ohio', NULL);

DO $$
BEGIN
  IF (SELECT COUNT(*) FROM president) <> 46
     OR (SELECT COUNT(*) FROM president WHERE partyname IS NULL) <> 1
     OR EXISTS (SELECT 1 FROM president p WHERE p.partyname IS NOT NULL
                AND NOT EXISTS (SELECT 1 FROM party y WHERE y.partyname = p.partyname)) THEN
    RAISE EXCEPTION 'k3_fk_i_null: result is not 46 rows / 1 NULL PartyName / 0 orphan';
  END IF;
END $$;
