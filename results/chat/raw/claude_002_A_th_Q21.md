SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentHolding h ON p.PresidentName = h.PresidentName
WHERE p.StateBorn = 'Virginia'
  AND h.YearHolding < 1850;