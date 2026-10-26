-- TEST-ONLY (k3n scratch, read-only) adversarial review 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- X17: why the fix needs 'แต่ละคน': without it 'วาระที่สั้นที่สุดของประธานาธิบดีที่เกิดรัฐเดียวกันแต่อยู่คนละพรรค'
-- can be read as ONE group-level shortest term -> k3n: 6 rows (Van Buren and Fillmore drop) vs gold 8
WITH m AS (SELECT p.PresidentName, p.PartyName, p.StateBorn, MIN(h.YearEnd - h.YearHolding) AS min_len
           FROM President p JOIN PresidentHolding h ON h.PresidentName = p.PresidentName GROUP BY p.PresidentName, p.PartyName, p.StateBorn)
SELECT m.PresidentName, m.min_len FROM m
WHERE m.min_len < (SELECT MIN(m2.min_len) FROM m m2 WHERE m2.StateBorn = m.StateBorn AND m2.PartyName <> m.PartyName);
-- variant 'lowest per-party average' (memo's 'ค่าเฉลี่ยรายพรรคที่ต่ำที่สุด'): 7 rows if the party averages use all terms
-- or per-president average terms (Van Buren drops); 6 rows if they use each president's shortest term
