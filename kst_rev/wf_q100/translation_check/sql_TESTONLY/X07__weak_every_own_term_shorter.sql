-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- X07 alt_every_own_term_shorter (alt) TEST-ONLY on k3n
SELECT p.PartyName, p.PresidentName, (h.YearEnd - h.YearHolding) AS term_len
FROM President p JOIN PresidentHolding h ON h.PresidentName = p.PresidentName
WHERE NOT EXISTS (SELECT 1 FROM PresidentHolding hx JOIN President p2 ON p2.PartyName = p.PartyName AND p2.PresidentName <> p.PresidentName
  JOIN PresidentHolding h2 ON h2.PresidentName = p2.PresidentName
  WHERE hx.PresidentName = p.PresidentName AND h2.YearEnd - h2.YearHolding <= hx.YearEnd - hx.YearHolding);
