```
SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentHolding ph ON p.PresidentName = ph.PresidentName
GROUP BY p.PresidentName
HAVING COUNT(*) >= 2
   AND COUNT(DISTINCT ph.YearHolding) >= 2
   AND MAX(ph.YearHolding) > MIN(ph.YearEnd);
```