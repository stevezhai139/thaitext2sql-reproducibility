SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentMarriage m ON p.PresidentName = m.PresidentName
WHERE p.PartyName = 'Democratic-Republican'
  AND m.MarriageStatus = 'Widowed';