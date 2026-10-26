-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- A2 [alt?] state average taken over per-term lengths of all holding rows of presidents born in the state
WITH t AS (SELECT p.PresidentName, p.StateBorn, SUM(h.YearEnd - h.YearHolding) AS ty FROM President p JOIN PresidentHolding h ON h.PresidentName = p.PresidentName GROUP BY p.PresidentName, p.StateBorn)
SELECT PresidentName, ty FROM t WHERE ty > (SELECT AVG(h2.YearEnd - h2.YearHolding) FROM PresidentHolding h2 JOIN President p2 ON p2.PresidentName = h2.PresidentName WHERE p2.StateBorn = t.StateBorn);
