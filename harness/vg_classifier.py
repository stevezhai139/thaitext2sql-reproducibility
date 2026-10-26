#!/usr/bin/env python3
"""vg_classifier.py -- the single implementation of the AMENDMENT-7 B2.3 classifier
(value-grounding failure classes of ONE failing run), shared by analyze_rc1.py and
chatapp/vg_outcome.py. Frozen before any October-session model call.

Origin: kst_rev/drafts/patch/analyze_rc1.py l.69-115 (vg_targets, literals_on_column,
classify_run). The only change of meaning against that draft is the one AM-7 B2.3
registers: the literal of LIKE / NOT LIKE is read as a pattern ('%' -> any run, '_' ->
one character, anchored at both ends, backslash escapes the next character) and ILIKE /
NOT ILIKE is the same pattern without regard to case.
Scan fixes (Gate 0 review, 14 Oct 2026; they make the scan follow the registered words
"a literal compared with a target column", they add no rule):
  * string literals are read whole: a literal that contains AND, OR, THEN or ')' (e.g.
    'Clothing and Accessories') is one literal, and '' inside a literal is one quote
    ('Widow''s' is the literal Widow's), for THAI_COPY and for the predicates alike;
  * the operand of a predicate ends at ')', ';', AND, OR, THEN, WHEN, ELSE, END, WHERE,
    GROUP, ORDER, HAVING, LIMIT, UNION, INTERSECT, EXCEPT or ESCAPE outside a literal, so a
    literal of a later clause on another column (HAVING PartyName = 'Whig'), of a
    subquery or of an ESCAPE clause is not read as compared with the target column;
  * the target column may be double-quoted ("MarriageStatus", optionally after an alias)
    and a scalar comparison may be written reversed ('Widow' = MarriageStatus);
  * SQL comments are not code: a -- line comment and a /* */ block comment (nested, as
    PostgreSQL reads them) outside a literal or a double-quoted identifier are skipped
    before the scan, so an apostrophe in a comment opens no literal and a quoted Thai word
    in a comment is not a Thai literal (strip_comments; second review, 14 Oct 2026).
Known blind spots (disclosed with B2.3): a target column inside a function call
(LOWER(MarriageStatus) = 'widowed') or a cast is not seen as a predicate (NO_PRED), and
dollar-quoted or E'...' strings are not parsed as literals (a backslash-escaped quote of
an E'...' string ends the literal early).

Classes of a failing run on a value-grounding (VG) item, checked in this order
  THAI_COPY  some string literal of the SQL contains Thai script
  INVENTED   a literal compared with a target column (=, <>, !=, IN, NOT IN, LIKE,
             NOT LIKE, ILIKE, NOT ILIKE) matches no stored value of that column
             (=, <>, !=, IN, NOT IN: exact and case-sensitive; LIKE family: pattern)
  NO_PRED    no target column carries a literal predicate (a run without SQL lands here)
  GROUNDED   every target literal appears on its column (the run is wrong for another reason)
  STORED     only stored values are used on the target column, but not the target literal
Grounding failure (GF) classes = THAI_COPY and INVENTED.
GF of a cell (AM-7 B2.2): VG item, majority of runs wrong, and the failing runs classed
THAI_COPY or INVENTED are strictly more than half of the failing runs (is_gf_cell).

Vocabulary: field 'full_values' of suite/value_hints_v1.json (columns with at most 100
distinct values; never shown to a model), keyed by lower-case column name.

Usage as a library only (no command line). Import with an explicit path; never writes
bytecode when run under 'python3 -I -B'.
"""
import hashlib
import json
import os
import re
import sys

sys.dont_write_bytecode = True
_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)

# --------------------------------------------------------------------------------------
# OQ6 (Q48 on the k3n vocabulary). Triage 14 Oct 2026 classed OQ6 as DROP: keep the
# registered B2.3 rule, and analyze_rc1.py prints how many failing runs are INVENTED only
# because of the literal 'None' (if any). This is the ONE switch for that rule:
#   "keep"              B2.3 as registered: vocabulary = stored values only
#   "add_gold_literals" OQ6 option (b): every VG gold literal is added to the vocabulary
#                       of its target column (on k3n this adds only Q48's 'None')
Q48_VOCAB_RULE = "keep"
Q48_VOCAB_RULES = ("keep", "add_gold_literals")
# --------------------------------------------------------------------------------------

THAI = re.compile(r"[฀-๿]")
CLASSES = ("THAI_COPY", "INVENTED", "NO_PRED", "GROUNDED", "STORED")
GF_CLASSES = ("THAI_COPY", "INVENTED")
# linear-time tokenizer (no nested quantifiers): a string literal is read whole, ''
# inside it is one quote; an unterminated quote opens no literal (as the draft's regex)
_TOK = re.compile(r"(?P<lit>'[^']*(?:''[^']*)*')|(?P<quote>')"
                  r'|(?P<ident>"[^"]*(?:""[^"]*)*")'
                  r"|(?P<word>\w+)|(?P<sym><>|!=|<=|>=|\|\||::|\S)")
# comment pass: literals and double-quoted identifiers are read exactly as _TOK reads them,
# so comment marks inside them are kept and quotes inside a comment open nothing
_SCAN = re.compile(r"(?P<lit>'[^']*(?:''[^']*)*')"
                   r'|(?P<ident>"[^"]*(?:""[^"]*)*")'
                   r"|(?P<line>--[^\n]*)|(?P<block>/\*)|(?P<other>[^'\"/-]+|[\s\S])")
_SCALAR = ("=", "<>", "!=")
_END_WORDS = {"and", "or", "then", "when", "else", "end", "where", "group", "order", "having",
              "limit", "union", "intersect", "except", "escape"}
_EQ_OPS = ("=", "<>", "!=", "in", "not in")
_LIKE_OPS = ("like", "not like")
_ILIKE_OPS = ("ilike", "not ilike")


def vg_targets(gold_sql, vg_lits):
    """[(column_lower or None, literal)] for each value-grounding literal of the gold:
    the column the gold compares with that literal by =, <> or != (draft l.69-75)."""
    out = []
    for lit in dict.fromkeys(vg_lits):
        m = re.search(r"(?i)(\w+)\s*(?:=|<>|!=)\s*'" + re.escape(lit) + "'", gold_sql or "")
        out.append((m.group(1).lower() if m else None, lit))
    return out


def strip_comments(sql):
    """the SQL with every -- line comment and every /* */ block comment (nested, as
    PostgreSQL reads them; an unterminated one runs to the end) replaced by one space.
    Comment marks inside a string literal or a double-quoted identifier are kept, and a
    quote inside a comment opens nothing."""
    sql = sql or ""
    out, i, n = [], 0, len(sql)
    while i < n:
        m = _SCAN.match(sql, i)
        k = m.lastgroup
        if k == "line":
            out.append(" ")
            i = m.end()
        elif k == "block":
            depth, j = 1, m.end()
            while j < n and depth:
                if sql.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif sql.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            out.append(" ")
            i = j
        else:
            out.append(m.group(0))
            i = m.end()
    return "".join(out)


def _tokens(sql):
    """[(kind, text)] of the SQL without its comments, with kind lit (text unquoted),
    ident (double-quoted, unquoted), word or sym."""
    out = []
    for m in _TOK.finditer(strip_comments(sql)):
        k, t = m.lastgroup, m.group(0)
        if k == "lit":
            out.append(("lit", t[1:-1].replace("''", "'")))
        elif k == "ident":
            out.append(("ident", t[1:-1].replace('""', '"')))
        elif k == "word":
            out.append(("word", t))
        else:
            out.append(("sym", t))
    return out


def string_literals(sql):
    """every single-quoted string literal of the SQL outside comments, read whole ('' is
    one quote)."""
    return [t for k, t in _tokens(sql) if k == "lit"]


def has_thai_literal(sql):
    """True when some string literal of the SQL (outside comments) contains Thai script:
    the THAI_COPY test of classify_run and the thai_literal flag of empty_split_v13.py
    (one definition)."""
    return any(THAI.search(x) for x in string_literals(sql))


def predicates_on_column(sql, col):
    """[(operator, literal)] for string literals compared with <col> (bare or
    double-quoted, optionally after an alias; a scalar comparison may be reversed).
    The operand of <col> <op> runs to ')', ';' or a clause keyword outside a literal.
    Operator is normalised to lower case with single spaces."""
    toks = _tokens(sql)
    col = (col or "").lower()
    n = len(toks)

    def is_col(i):
        return i < n and toks[i][0] in ("word", "ident") and toks[i][1].lower() == col

    def kw(i):
        return toks[i][1].lower() if i < n and toks[i][0] == "word" else None

    out = []
    for i in range(n):
        if not is_col(i):
            continue
        j, op = i + 1, None
        if j < n and toks[j] in (("sym", x) for x in _SCALAR):
            op, j = toks[j][1], j + 1
        elif kw(j) in ("like", "ilike", "in"):
            op, j = kw(j), j + 1
        elif kw(j) == "not" and kw(j + 1) in ("like", "ilike", "in"):
            op, j = "not " + kw(j + 1), j + 2
        if op is None:
            continue
        while j < n:
            k, t = toks[j]
            if (k == "sym" and t in (")", ";")) or (k == "word" and t.lower() in _END_WORDS):
                break
            if k == "lit":
                out.append((op, t))
            j += 1
    for i in range(n - 2):           # reversed scalar comparison: 'lit' op [alias.]col
        if toks[i][0] != "lit" or toks[i + 1] not in [("sym", x) for x in _SCALAR]:
            continue
        j = i + 2
        if j + 2 < n and toks[j][0] in ("word", "ident") and toks[j + 1] == ("sym", ".") \
                and is_col(j + 2):
            j += 2
        if is_col(j) and not (j + 1 < n and toks[j + 1] == ("sym", ".")):
            out.append((toks[i + 1][1], toks[i][1]))
    return out


def literals_on_column(sql, col):
    """string literals compared with <col> (draft API, kept for callers)."""
    return [lit for _, lit in predicates_on_column(sql, col)]


def like_regex(pattern, case_insensitive=False):
    """SQL LIKE pattern -> anchored Python regex ('%' any run, '_' one char, '\\x' literal x)."""
    out, i = [], 0
    while i < len(pattern):
        ch = pattern[i]
        if ch == "\\" and i + 1 < len(pattern):
            out.append(re.escape(pattern[i + 1]))
            i += 2
            continue
        if ch == "%":
            out.append(".*")
        elif ch == "_":
            out.append(".")
        else:
            out.append(re.escape(ch))
        i += 1
    return re.compile("".join(out), re.S | (re.I if case_insensitive else 0))


def literal_matches(op, lit, value):
    """does the predicate literal (under its operator) denote the stored value?"""
    if op in _LIKE_OPS:
        return like_regex(lit).fullmatch(value) is not None
    if op in _ILIKE_OPS:
        return like_regex(lit, True).fullmatch(value) is not None
    return lit == value


def in_vocabulary(op, lit, voc):
    if op in _EQ_OPS:
        return lit in voc
    return any(literal_matches(op, lit, v) for v in voc)


def invented_literals(sql, targets, vocab):
    """[(column, operator, literal)] that match no stored value (diagnostics only)."""
    out = []
    for col, _ in targets:
        if col is None:
            continue
        voc = vocab.get(col)
        if voc is None:
            continue
        for op, lit in predicates_on_column(sql, col):
            if not in_vocabulary(op, lit, voc):
                out.append((col, op, lit))
    return out


def classify_run(sql, targets, vocab):
    """Class of ONE failing run on a VG item (AM-7 B2.3; order of checks is registered)."""
    sql = sql or ""
    if has_thai_literal(sql):
        return "THAI_COPY"
    seen_any, all_hit = False, True
    for col, lit in targets:
        if col is None:
            continue
        on = predicates_on_column(sql, col)
        voc = vocab.get(col)
        if on:
            seen_any = True
            if voc is not None and any(not in_vocabulary(op, x, voc) for op, x in on):
                return "INVENTED"
        if not any(literal_matches(op, x, lit) for op, x in on):
            all_hit = False
    if not seen_any:
        return "NO_PRED"
    return "GROUNDED" if all_hit else "STORED"


def gf_union_majority(classes):
    """strict majority of THAI_COPY u INVENTED among the failing runs of one cell."""
    classes = list(classes)
    return bool(classes) and sum(c in GF_CLASSES for c in classes) > len(classes) / 2


def is_gf_cell(is_vg_item, majority_wrong, failing_classes):
    """AM-7 B2.2: GF(cell) = VG item and majority wrong and strict union majority."""
    return bool(is_vg_item and majority_wrong and gf_union_majority(failing_classes))


# ------------------------------------------------------------------- hints / vocabulary
def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def load_hints(path, expect_sha256=None):
    """(hints dict, sha256 of the file); raises SystemExit when the sha256 differs."""
    sha = sha256_file(path)
    if expect_sha256 is not None and sha != expect_sha256.strip().lower():
        raise SystemExit(f"hint file sha256 {sha[:12]}... differs from --hints-sha256 "
                         f"{expect_sha256.strip()[:12]}...; stop (AM-7 A5.3)")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh), sha


def build_vocab(hints, rule=None, gold_targets=None):
    """{column_lower: set(stored values)} from 'full_values'. With rule
    'add_gold_literals' (OQ6 option b) gold_targets [(col, lit), ...] are added."""
    rule = rule or Q48_VOCAB_RULE
    if rule not in Q48_VOCAB_RULES:
        raise SystemExit(f"unknown Q48 vocabulary rule {rule!r}")
    vocab = {}
    for sch in hints.get("schemas", {}).values():
        for c in sch.get("columns", []):
            if c.get("full_values") is not None:
                vocab.setdefault(c["column"].lower(), set()).update(
                    v for v in c["full_values"] if v is not None)
    if rule == "add_gold_literals":
        for col, lit in gold_targets or ():
            if col is not None and col in vocab:
                vocab[col].add(lit)
    return vocab


def shown_values(hints):
    """{(column_lower, value)} that appear in a prompt block (full lists and examples)."""
    out = set()
    for sch in hints.get("schemas", {}).values():
        for c in sch.get("columns", []):
            out |= {(c["column"].lower(), v) for v in c.get("values", []) if v is not None}
    return out


def item_targets(item):
    """targets of one suite row (dict with gold_sql_draft and question_th)."""
    from vg_rule import value_grounding_literals
    lits = value_grounding_literals(item["gold_sql_draft"], item["question_th"])
    return vg_targets(item["gold_sql_draft"], lits)


def covered(targets, shown):
    """True when every target (column, literal) is visible in the value block."""
    return bool(targets) and all(col is not None and (col, lit) in shown for col, lit in targets)


def suite_vg_targets(suite_rows):
    """{qid: targets} for every row whose gold has a VG literal (AMENDMENT-6 rule)."""
    out = {}
    for qid, item in suite_rows.items():
        t = item_targets(item)
        if t:
            out[qid] = t
    return out
