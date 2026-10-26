-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- E4 [error] literal reading of 'แสดงรายชื่อประธานาธิบดีที่มีปีที่แต่งงานเท่ากันทั้งหมด' (gold UNION presidents sharing a marriage year in party)
SELECT DISTINCT p.PresidentName FROM President p JOIN PresidentMarriage m ON m.PresidentName = p.PresidentName
WHERE m.MarriageYear = (SELECT MAX(m2.MarriageYear) FROM President p2 JOIN PresidentMarriage m2 ON m2.PresidentName = p2.PresidentName WHERE p2.PartyName = p.PartyName)
UNION SELECT p.PresidentName FROM President p JOIN PresidentMarriage m ON m.PresidentName = p.PresidentName
WHERE EXISTS (SELECT 1 FROM President p2 JOIN PresidentMarriage m2 ON m2.PresidentName = p2.PresidentName WHERE p2.PartyName = p.PartyName AND p2.PresidentName <> p.PresidentName AND m2.MarriageYear = m.MarriageYear);
