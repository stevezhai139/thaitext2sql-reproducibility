SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentMarriage pm ON p.PresidentName = pm.PresidentName
WHERE p.PartyName = 'Democratic-Republican'
AND (pm.MarriageStatus = 'Widowed' OR pm.MarriageStatus = 'Widower' OR pm.MarriageStatus = 'หม้าย');