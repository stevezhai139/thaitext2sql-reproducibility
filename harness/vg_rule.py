#!/usr/bin/env python3
"""vg_rule.py — canonical value-grounding derivation (single source of truth).

An item is VALUE-GROUNDING iff some gold string literal that denotes a STORED
DATA CONSTANT does not appear (wildcard-stripped) in the Thai question.
Amendment 2026-08-13 (pre-submission, caught by author review):
  (a) strip SQL wildcards %/_ before the verbatim check
      (fixes 'J%' -> "J" present in TH -> not VG);
  (b) exclude literals that are date/time-unit ARGUMENTS of
      DATE_TRUNC/EXTRACT/DATE_PART — SQL-construct knowledge, not stored
      constants (fixes 'month').
Original rule flagged 13 items; corrected rule flags 10.
"""
import re

_FN_ARG = re.compile(r"(?i)(?:DATE_TRUNC|EXTRACT|DATE_PART)\s*\(\s*'([^']+)'")


def value_grounding_literals(gold_sql: str, question_th: str):
    fn_args = set(m.group(1) for m in _FN_ARG.finditer(gold_sql))
    lits = re.findall(r"'([^']+)'", gold_sql)
    out = []
    for x in lits:
        if re.match(r"^[\d\-: .%]+$", x):
            continue
        if x in fn_args:
            continue
        core = x.replace("%", "").replace("_", "").strip()
        if core and core not in question_th:
            out.append(x)
    return out


def is_value_grounding(gold_sql: str, question_th: str) -> bool:
    return bool(value_grounding_literals(gold_sql, question_th))
