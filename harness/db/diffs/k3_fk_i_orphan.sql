-- k3_fk_i_orphan = k3n + ONE appended President row whose PartyName has no Party row
-- (FK1 instance 3 of 3)
--
-- New row: ('Planted President Orphan', 1950, 'Ohio', 'Know Nothing') -- the
-- PLANTED row of the FK item drafts. 'Know Nothing' differs from every Party
-- value by more than letter case or spaces (no collation or trim quirk), so the
-- row breaks the foreign key President.PartyName -> Party.PartyName: FK1 gold is
-- this one row (PresidentName, PartyName). No PartyName is NULL.
-- INSERT only: the row is appended at the physical end (build_instances.py
-- checks delta append, added 1). No other table changes.
--
-- Applied by build_instances.py in ONE transaction:
--   psql -X -v ON_ERROR_STOP=1 -1 -f k3_fk_i_orphan.sql

DO $$
BEGIN
  IF (SELECT COUNT(*) FROM president) <> 45
     OR EXISTS (SELECT 1 FROM president WHERE partyname IS NULL)
     OR EXISTS (SELECT 1 FROM president p
                WHERE NOT EXISTS (SELECT 1 FROM party y WHERE y.partyname = p.partyname))
     OR EXISTS (SELECT 1 FROM president WHERE presidentname LIKE 'Planted President%')
     OR EXISTS (SELECT 1 FROM party
                WHERE lower(btrim(partyname)) = lower(btrim('Know Nothing'))) THEN
    RAISE EXCEPTION 'k3_fk_i_orphan: parent President/Party is not as expected (45 rows, no NULL or orphan PartyName, no planted row, Know Nothing not a party)';
  END IF;
END $$;

INSERT INTO president (presidentname, yearborn, stateborn, partyname)
VALUES ('Planted President Orphan', 1950, 'Ohio', 'Know Nothing');

DO $$
BEGIN
  IF (SELECT COUNT(*) FROM president) <> 46
     OR EXISTS (SELECT 1 FROM president WHERE partyname IS NULL)
     OR (SELECT COUNT(*) FROM president p
         WHERE NOT EXISTS (SELECT 1 FROM party y WHERE y.partyname = p.partyname)) <> 1 THEN
    RAISE EXCEPTION 'k3_fk_i_orphan: result is not 46 rows / 0 NULL PartyName / 1 orphan';
  END IF;
END $$;
