```
SELECT DISTINCT p.PresidentName
FROM President p
JOIN PresidentMarriage pm
    ON p.PresidentName = pm.PresidentName
JOIN PresidentHolding ph
    ON p.PresidentName = ph.PresidentName
WHERE pm.MarriageYear > ph.YearHolding;
```