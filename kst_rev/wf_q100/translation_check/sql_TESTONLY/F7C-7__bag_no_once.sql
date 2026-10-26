-- TEST-ONLY (k3n scratch, read-only) adversarial review 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- F7C-7: TH has no 'each party once' (EN has '(show party name, each party once)'); a natural EXISTS-from-President answer
-- returns one row per president of a qualifying party -> k3n: 19 rows (bag) vs gold 2 rows -> graded WRONG under v1.3
SELECT p.PartyName FROM President p
WHERE EXISTS (SELECT 1 FROM President a WHERE a.PartyName = p.PartyName AND a.StateBorn = 'Virginia')
  AND EXISTS (SELECT 1 FROM President b WHERE b.PartyName = p.PartyName AND b.StateBorn = 'Massachusetts');
-- self-join variant: SELECT a.PartyName FROM President a JOIN President b ON a.PartyName = b.PartyName
--   WHERE a.StateBorn = 'Virginia' AND b.StateBorn = 'Massachusetts'   -> 4 rows (bag), WRONG
