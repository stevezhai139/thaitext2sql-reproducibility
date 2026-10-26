-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- X02 alt_every_own_term_longest (alt) TEST-ONLY on k3n
SELECT DISTINCT p.PresidentName FROM President p
JOIN PresidentHolding h0 ON h0.PresidentName = p.PresidentName
WHERE NOT EXISTS (SELECT 1 FROM PresidentHolding h WHERE h.PresidentName = p.PresidentName
  AND h.YearEnd - h.YearHolding < (SELECT MAX(h2.YearEnd - h2.YearHolding)
    FROM PresidentHolding h2 JOIN President p2 ON p2.PresidentName = h2.PresidentName WHERE p2.PartyName = p.PartyName));
