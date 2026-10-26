-- TEST-ONLY (k3n scratch, read-only) adversarial review 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- F7C-1 (after the 'ทุกรัฐ' fix): TH has no 'each party once' (EN has it); division written over President without DISTINCT
-- k3n: 19 rows (15 Democratic + 4 Whig) vs gold 2 rows -> graded WRONG under v1.3
SELECT x.PartyName FROM President x
WHERE NOT EXISTS (SELECT 1 FROM President w WHERE w.PartyName = 'Whig'
                  AND NOT EXISTS (SELECT 1 FROM President y WHERE y.PartyName = x.PartyName AND y.StateBorn = w.StateBorn));
