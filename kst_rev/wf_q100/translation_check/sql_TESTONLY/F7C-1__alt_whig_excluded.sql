-- TEST-ONLY (k3n scratch, read-only) copied 2026-10-13 for TRANSLATION_CHECK_2026-10-13.md
-- F7C-1 division_other_parties [ALT] TEST-ONLY
-- after adding 'ทุกรัฐ', the reading that leaves Whig itself out (EN clause 'the Whig party itself counts' not in TH)
-- instances: k3n
SELECT pa.PartyName FROM Party pa WHERE pa.PartyName <> 'Whig' AND NOT EXISTS (SELECT 1 FROM President w WHERE w.PartyName = 'Whig' AND NOT EXISTS (SELECT 1 FROM President x WHERE x.PartyName = pa.PartyName AND x.StateBorn = w.StateBorn));
