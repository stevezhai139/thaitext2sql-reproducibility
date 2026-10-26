-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- candidate alternative: average over all terms of the OTHER presidents born in his state (TH dropped 'his own terms included')
SELECT DISTINCT h.presidentname FROM presidentholding h JOIN president p USING (presidentname)
WHERE h.yearend - h.yearholding < (SELECT AVG(h2.yearend - h2.yearholding)
  FROM presidentholding h2 JOIN president p2 USING (presidentname)
  WHERE p2.stateborn = p.stateborn AND p2.presidentname <> p.presidentname)
