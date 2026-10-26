-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- X20 | DEF? | state average over OTHER presidents born in the same state (own records excluded)
SELECT DISTINCT p.PresidentName FROM President p JOIN PresidentMarriage m ON m.PresidentName = p.PresidentName WHERE (m.MarriageYear - EXTRACT(YEAR FROM m.SpouseBirthDay)) < (SELECT AVG(m2.MarriageYear - EXTRACT(YEAR FROM m2.SpouseBirthDay)) FROM President p2 JOIN PresidentMarriage m2 ON m2.PresidentName = p2.PresidentName WHERE p2.StateBorn = p.StateBorn AND p2.PresidentName <> p.PresidentName);
