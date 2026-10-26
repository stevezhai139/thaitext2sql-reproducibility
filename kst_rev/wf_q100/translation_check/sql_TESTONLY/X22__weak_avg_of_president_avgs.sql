-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- weak alternative: party average = average of each president's own average age at marriage
WITH a AS (SELECT p.partyname, m.presidentname, m.marriageyear - EXTRACT(YEAR FROM m.spousebirthday) AS age
  FROM presidentmarriage m JOIN president p USING (presidentname) WHERE m.marriageyear IS NOT NULL),
pp AS (SELECT partyname, presidentname, AVG(age) av FROM a GROUP BY 1,2),
pa AS (SELECT partyname, AVG(av) pav FROM pp GROUP BY 1)
SELECT DISTINCT a.presidentname FROM a JOIN pa USING (partyname) WHERE a.age > pa.pav
