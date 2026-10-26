-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- DEFENSIBLE under current TH ('เทียบกับคู่สมรสของประธานาธิบดีคนอื่นในพรรคเดียวกัน'): spouse age >= the maximum over spouses of OTHER presidents of the party; single-president parties have no comparison group (MAX = NULL) and drop out
SELECT p.partyname, p.presidentname, m.marriageyear - EXTRACT(YEAR FROM m.spousebirthday) AS age
FROM president p JOIN presidentmarriage m USING (presidentname)
WHERE m.marriageyear - EXTRACT(YEAR FROM m.spousebirthday) >= (
  SELECT MAX(m2.marriageyear - EXTRACT(YEAR FROM m2.spousebirthday))
  FROM president p2 JOIN presidentmarriage m2 USING (presidentname)
  WHERE p2.partyname = p.partyname AND p2.presidentname <> p.presidentname)
