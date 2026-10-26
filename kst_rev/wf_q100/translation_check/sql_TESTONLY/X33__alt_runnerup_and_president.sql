-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- X33 alt_runnerup_and_president (alt) TEST-ONLY on k3n
WITH r AS (SELECT presidentname, runnerup,
  LAG(runnerup) OVER (ORDER BY yearholding, yearend) AS prev_ru,
  LEAD(runnerup) OVER (ORDER BY yearholding, yearend) AS next_ru
  FROM presidentholding)
SELECT DISTINCT runnerup, presidentname FROM r WHERE runnerup = prev_ru OR runnerup = next_ru;
