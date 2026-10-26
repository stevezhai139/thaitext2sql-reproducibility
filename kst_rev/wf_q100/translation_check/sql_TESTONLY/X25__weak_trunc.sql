-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- X25 | DEF? | two decimals by truncation (TRUNC) instead of rounding
SELECT TRUNC(AVG(t.first_start - t.YearBorn), 2) FROM (SELECT p.PresidentName, p.YearBorn, MIN(h.YearHolding) AS first_start FROM President p JOIN PresidentHolding h ON h.PresidentName = p.PresidentName GROUP BY p.PresidentName, p.YearBorn) t;
