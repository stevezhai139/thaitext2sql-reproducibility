```

SELECT
    p.PresidentName,
    ABS(p.YearBorn - EXTRACT(YEAR FROM pm.SpouseBirthDay)::INT) AS AgeDifference
FROM President p
JOIN PresidentMarriage pm
    ON p.PresidentName = pm.PresidentName
WHERE pm.SpouseBirthDay IS NOT NULL
ORDER BY
    AgeDifference DESC,
    p.PresidentName ASC
LIMIT 3;

```