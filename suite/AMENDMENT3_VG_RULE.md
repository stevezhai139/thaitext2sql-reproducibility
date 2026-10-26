# Amendment 3 — value-grounding derivation rule (2026-08-13, pre-submission)

**Discovered by:** author review of the C-2 annotation sheet (the author): item Q06
("starts with 'J'") flagged as value-grounding although the literal 'J%' differs
from the Thai question only by the SQL wildcard.

**Rule change (canonical implementation: `harness/vg_rule.py`, imported by
analyze.py / analyze_typhoon.py / make_annotation_sheet.py):**
1. strip SQL wildcards %/_ from literals before the verbatim-absence check;
2. exclude literals that are date/time-unit ARGUMENTS of
   DATE_TRUNC/EXTRACT/DATE_PART (SQL-construct knowledge, not stored constants).

**Impact:** set 13 → 10 items (Q06 wildcard; Q39, Q54 'month' function args).
Recomputed (run-of-record unchanged; derived tables regenerated):
- subset TH accuracy: gpt 40.0 / gemini 50.0 / claude 80.0 (was 38.5/46.2/69.2)
- elsewhere TH accuracy: 82.0 / 80.0 / 84.0 (was 85.1/83.0/87.2)
- frontier TH errors in set: 6/15, 5/15, 2/10 (was 8/15, 7/15, 4/10)
- headline phrase "roughly half of frontier Thai errors" REVISED to
  "up to 40%" + new observation: claude-sonnet-5 largely robust to the
  failure mode (subset ≈ elsewhere)
- typhoon-vs-llama VG overlap: 6/10 vs 5/10 (was 8/13 vs 7/13)

Paper sections touched: abstract, §III (protocol definition, now states the
rule precisely), RQ2, Discussion, typhoon mechanism paragraph.
