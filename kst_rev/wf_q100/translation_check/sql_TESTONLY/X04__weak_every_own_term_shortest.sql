-- TEST-ONLY (k3n scratch, read-only) adversarial review 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- X04 [weak, same class as X02/X07] 'ในแต่ละวาระ' read as: EVERY term of the president must be the shortest in his birth state
-- k3n: 21 rows x 3 cols; gold 23 (Kentucky|Abraham Lincoln|0 and New York|Franklin D Roosevelt|0 drop, both also have a longer term)
SELECT DISTINCT p.StateBorn, p.PresidentName, (h.YearEnd - h.YearHolding) AS term_len
FROM President p JOIN PresidentHolding h ON h.PresidentName = p.PresidentName
WHERE (h.YearEnd - h.YearHolding) = (SELECT MIN(h2.YearEnd - h2.YearHolding) FROM President p2 JOIN PresidentHolding h2 ON h2.PresidentName = p2.PresidentName WHERE p2.StateBorn = p.StateBorn)
  AND NOT EXISTS (SELECT 1 FROM PresidentHolding hx WHERE hx.PresidentName = p.PresidentName
                  AND hx.YearEnd - hx.YearHolding > (SELECT MIN(h2.YearEnd - h2.YearHolding) FROM President p2 JOIN PresidentHolding h2 ON h2.PresidentName = p2.PresidentName WHERE p2.StateBorn = p.StateBorn));
