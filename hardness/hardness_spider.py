#!/usr/bin/env python3
"""
hardness_spider.py -- Spider-style hardness (Yu et al., EMNLP 2018) of the
frozen gold SQL of the 100-item set (core 60 of the October collection, Q27
repaired; extension 40). DESCRIPTIVE ONLY: computed after all results were
known; not used for item selection or for any analysis (preregistration,
AMENDMENT-9 section 8).

The hardness rule of Spider's evaluation.py (get_nestedSQL, count_component1,
count_component2, count_others, eval_hardness) is RE-IMPLEMENTED here from the
logic of the published evaluation script; Spider's own code is not run,
because its parser cannot read CTEs, window functions, EXISTS, IS NULL, CASE,
UNION ALL, casts and other PostgreSQL constructs that the gold uses. A
stdlib-only tokenizer (strings, E'' / $$ strings, quoted identifiers,
comments, Thai identifiers) and a parenthesis tree give the clause structure
of the TOP-LEVEL query, which is the only level Spider's rule looks at. See
METHOD.md for the rules, the rewrites (map:) and the extensions (ext:).

Gold column: gold_sql_draft (the primary key that harness/grade_v13n.py
grades against; alt_gold_* and gold_sql_v12 are not used).

usage (from the artifact root)
  python3 -I -B "hardness/hardness_spider.py" --core "suite/k3n_suite_v1.3n_oct.tsv" \
      --ext "suite/k3n_ext_suite_v1.0.tsv" --out "hardness/hardness_spider_100.tsv"
  python3 -I -B "hardness/hardness_spider.py" --selftest

The self-test runs before every table build. Output is deterministic (input
order, fixed column and token order). stdlib only.
"""
import argparse
import csv
import hashlib
import os
import sys
import unicodedata

GOLD_COLUMN = "gold_sql_draft"
EXPECTED_ROWS = {"core": 60, "ext": 40}
HARDNESS = ("easy", "medium", "hard", "extra")
OUT_COLUMNS = ("set", "id", "tier", "schema", "family", "hardness",
               "comp1", "comp2", "others", "extensions_fired")
# Spider AGG_OPS = ('none', 'max', 'min', 'count', 'sum', 'avg')
AGG_FUNCS = frozenset({"max", "min", "count", "sum", "avg"})
CMP_OPS = frozenset({"=", "<>", "!=", "<", ">", "<=", ">="})
# complement operator used when a NOT is pushed into a comparison (De Morgan)
COMPLEMENT = {"=": "!=", "!=": "=", "<>": "=", "<": ">=", ">=": "<", ">": "<=", "<=": ">"}
PRED_KWS = ("in", "like", "ilike", "similar", "between", "is")
NEGATABLE = ("in", "like", "ilike", "similar", "between")   # negated through Spider's not_op
CLAUSE_KWS = ("from", "where", "having", "window", "limit", "offset", "fetch")
SETOP_KWS = ("union", "intersect", "except")
# join words only when the run they start ends in JOIN (LEFT(...) is a function)
JOIN_MODS = ("left", "right", "full", "inner", "cross", "natural", "outer")
# words that end a FROM list at its own level
FROM_END = ("where", "group", "having", "window", "order", "limit", "offset", "fetch",
            "select", "union", "intersect", "except")
NOT_ALIAS = frozenset({"end", "null", "true", "false", "asc", "desc", "distinct"})
NOT_BEFORE_ALIAS = frozenset({"and", "or", "not", "is", "in", "like", "ilike",
                              "between", "case", "when", "then", "else", "as",
                              "select", "distinct", "all", "by", "on", "over",
                              "filter", "within", "interval", "similar", "to"})

# fixed output order of the per-item notes
EXT_KEYS = (("window", "comp1"), ("exists", "comp2"),
            ("expr_subquery", "comp2"), ("recursive_cte", "comp2"))
MAP_KEYS = ("cte_inline", "union_all", "order_alias_agg", "outer_join",
            "cross_join", "is_null", "bool_group", "de_morgan", "case", "no_from", "fetch")
NOTE_KEYS = ("derived_table",)


class SqlError(ValueError):
    pass


# ------------------------------------------------------------------ tokenizer
class Tok:
    __slots__ = ("kind", "val", "low")

    def __init__(self, kind, val):
        self.kind = kind          # word | qident | str | num | param | op | punct
        self.val = val
        self.low = val.lower() if kind == "word" else None

    def __repr__(self):
        return f"{self.kind}:{self.val}"


class Group(list):
    """the items between one matched pair of parentheses"""


def _ident_start(c):
    return c == "_" or unicodedata.category(c)[0] == "L"


def _ident_char(c):
    # letters, digits and combining marks (Thai vowels and tone marks are Mn)
    return c in "_$" or unicodedata.category(c)[0] in "LNM"


def _read_quoted(s, i, quote, backslash):
    """index just past the literal whose opening quote is s[i]"""
    j, n = i + 1, len(s)
    while j < n:
        c = s[j]
        if backslash and c == "\\":
            j += 2
            continue
        if c == quote:
            if j + 1 < n and s[j + 1] == quote:   # doubled quote = escaped quote
                j += 2
                continue
            return j + 1
        j += 1
    raise SqlError("unterminated quoted text")


OPS = ("->>", "#>>", "<>", "!=", "<=", ">=", "::", "||", "->", "#>", "~~",
       "!~", "@>", "<@", "&&")


def tokenize(sql):
    out, i, n = [], 0, len(sql)
    while i < n:
        c = sql[i]
        if c.isspace():
            i += 1
            continue
        if sql.startswith("--", i):
            j = sql.find("\n", i)
            i = n if j < 0 else j + 1
            continue
        if sql.startswith("/*", i):                 # PostgreSQL nests block comments
            depth, j = 1, i + 2
            while depth:
                if j >= n:
                    raise SqlError("unterminated block comment")
                if sql.startswith("/*", j):
                    depth, j = depth + 1, j + 2
                elif sql.startswith("*/", j):
                    depth, j = depth - 1, j + 2
                else:
                    j += 1
            i = j
            continue
        if c in "eEbBxXnN" and i + 1 < n and sql[i + 1] == "'":
            j = _read_quoted(sql, i + 1, "'", c in "eE")
            out.append(Tok("str", sql[i:j]))
            i = j
            continue
        if c in "uU" and sql.startswith("&'", i + 1):
            j = _read_quoted(sql, i + 2, "'", False)
            out.append(Tok("str", sql[i:j]))
            i = j
            continue
        if c in "uU" and sql.startswith('&"', i + 1):
            j = _read_quoted(sql, i + 2, '"', False)
            out.append(Tok("qident", sql[i:j]))
            i = j
            continue
        if c == "'":
            j = _read_quoted(sql, i, "'", False)
            out.append(Tok("str", sql[i:j]))
            i = j
            continue
        if c == '"':
            j = _read_quoted(sql, i, '"', False)
            out.append(Tok("qident", sql[i:j]))
            i = j
            continue
        if c == "$":
            j = i + 1
            if j < n and (sql[j] == "$" or _ident_start(sql[j])):
                while j < n and sql[j] != "$" and _ident_char(sql[j]):
                    j += 1
                if j < n and sql[j] == "$":         # $$...$$ or $tag$...$tag$
                    tag = sql[i:j + 1]
                    k = sql.find(tag, j + 1)
                    if k < 0:
                        raise SqlError("unterminated dollar-quoted text")
                    out.append(Tok("str", sql[i:k + len(tag)]))
                    i = k + len(tag)
                    continue
            j = i + 1
            while j < n and sql[j].isdigit():
                j += 1
            if j == i + 1:
                raise SqlError("stray '$'")
            out.append(Tok("param", sql[i:j]))
            i = j
            continue
        if c.isdigit() or (c == "." and i + 1 < n and sql[i + 1].isdigit()):
            j = i
            while j < n and sql[j].isdigit():
                j += 1
            if j < n and sql[j] == ".":
                j += 1
                while j < n and sql[j].isdigit():
                    j += 1
            if j < n and sql[j] in "eE":
                k = j + 1
                if k < n and sql[k] in "+-":
                    k += 1
                if k < n and sql[k].isdigit():
                    j = k
                    while j < n and sql[j].isdigit():
                        j += 1
            out.append(Tok("num", sql[i:j]))
            i = j
            continue
        if _ident_start(c):
            j = i + 1
            while j < n and _ident_char(sql[j]):
                j += 1
            out.append(Tok("word", sql[i:j]))
            i = j
            continue
        for op in OPS:
            if sql.startswith(op, i):
                out.append(Tok("op", op))
                i += len(op)
                break
        else:
            out.append(Tok("punct" if c in "(),;.[]" else "op", c))
            i += 1
    return out


def build_tree(tokens):
    stack = [[]]
    for t in tokens:
        if t.kind == "punct" and t.val == "(":
            g = Group()
            stack[-1].append(g)
            stack.append(g)
        elif t.kind == "punct" and t.val == ")":
            if len(stack) == 1:
                raise SqlError("unbalanced ')'")
            stack.pop()
        else:
            stack[-1].append(t)
    if len(stack) != 1:
        raise SqlError("unbalanced '('")
    return stack[0]


# ------------------------------------------------------------------ helpers
def kw(x, *words):
    return isinstance(x, Tok) and x.kind == "word" and x.low in words


def punct(x, val):
    return isinstance(x, Tok) and x.kind == "punct" and x.val == val


def name_of(x):
    """normalised name of an identifier token (None for anything else)"""
    if isinstance(x, Tok) and x.kind == "word":
        return x.low
    if isinstance(x, Tok) and x.kind == "qident" and x.val.startswith('"'):
        return x.val[1:-1].replace('""', '"')
    return None


def is_query_group(x):
    """a parenthesised SELECT / WITH / VALUES, i.e. a subquery"""
    if not isinstance(x, Group) or not x:
        return False
    if kw(x[0], "select", "with", "values"):
        return True
    return (isinstance(x[0], Group) and is_query_group(x[0])
            and (len(x) == 1 or any(kw(y, *SETOP_KWS) for y in x)))


def split_commas(items):
    parts, cur = [], []
    for x in items:
        if punct(x, ","):
            parts.append(cur)
            cur = []
        else:
            cur.append(x)
    parts.append(cur)
    if any(not p for p in parts):
        raise SqlError("empty list element")
    return parts


class Scan:
    """aggregate calls, window calls and subqueries inside one expression
    (not descending into subqueries)"""

    def __init__(self):
        self.aggs = 0
        self.windows = 0
        self.subq = []
        self.case = 0


def scan_expr(items, sc):
    i, n = 0, len(items)
    while i < n:
        x = items[i]
        if isinstance(x, Group):
            if is_query_group(x):
                sc.subq.append(x)
            else:
                scan_expr(x, sc)
            i += 1
            continue
        if kw(x, "case"):
            sc.case += 1
        nxt = items[i + 1] if i + 1 < n else None
        if (isinstance(x, Tok) and x.kind in ("word", "qident") and isinstance(nxt, Group)
                and not is_query_group(nxt)):       # function call name(args)
            j, extra = i + 2, []
            if j + 1 < n and kw(items[j], "filter") and isinstance(items[j + 1], Group):
                extra.append(items[j + 1])
                j += 2
            if (j + 2 < n and kw(items[j], "within") and kw(items[j + 1], "group")
                    and isinstance(items[j + 2], Group)):
                extra.append(items[j + 2])
                j += 3
            if j < n and kw(items[j], "over"):    # window call: not an aggregate itself
                sc.windows += 1
                if j + 1 < n and isinstance(items[j + 1], Group):
                    extra.append(items[j + 1])
                j += 2
            elif kw(x, *AGG_FUNCS):
                sc.aggs += 1
            scan_expr(nxt, sc)                      # plain aggregates inside still count
            for g in extra:
                scan_expr(g, sc)
            i = j
            continue
        i += 1


# ------------------------------------------------------------------ conditions
def split_bool(items):
    """split a condition at depth 0 on AND / OR (not the AND of BETWEEN, not
    inside CASE ... END)"""
    segs, conns, cur = [], [], []
    between = case = 0
    for x in items:
        if kw(x, "case"):
            case += 1
        elif kw(x, "end") and case:
            case -= 1
        elif case == 0 and kw(x, "between"):
            between += 1
        elif case == 0 and between and kw(x, "and"):
            between -= 1
        elif case == 0 and kw(x, "and", "or"):
            segs.append(cur)
            conns.append(x.low)
            cur = []
            continue
        cur.append(x)
    segs.append(cur)
    if any(not s for s in segs):
        raise SqlError("empty condition")
    return segs, conns


def is_bool_group(g):
    if not isinstance(g, Group) or is_query_group(g) or not g:
        return False
    segs, conns = split_bool(g)
    if conns:
        return True
    return any((isinstance(x, Tok) and x.kind == "op" and x.val in CMP_OPS)
               or kw(x, *PRED_KWS) or kw(x, "exists", "not") for x in g)


def conds_of(items, notes, neg=False):
    """Spider's flat condition list [cond, 'and'|'or', cond, ...]; a cond is a
    dict with Spider's not_op plus what the counters need. neg: the whole list
    is negated (De Morgan: AND and OR swap, each condition is negated)"""
    segs, conns = split_bool(items)
    if neg:
        conns = ["or" if c == "and" else "and" for c in conns]
    out = []
    for k, seg in enumerate(segs):
        if k:
            out.append(conns[k - 1])
        out.extend(_leaf(seg, notes, neg))
    return out


def _leaf(seg, notes, neg):
    k, flip = 0, False
    while k < len(seg) and kw(seg[k], "not"):
        flip, k = not flip, k + 1
    rest = seg[k:]
    if not rest:
        raise SqlError("dangling NOT")
    negate = neg ^ flip
    if len(rest) == 1 and is_bool_group(rest[0]):
        notes["bool_group"] += 1                    # (a OR b): flattened
        if flip:
            notes["de_morgan"] += 1                 # NOT (a AND b) -> NOT a OR NOT b
        return conds_of(rest[0], notes, negate)
    cond = {"not_op": False, "op": None, "like": False, "native": 0,
            "exists": 0, "expr": 0, "aggs": 0}
    if kw(rest[0], "exists") and len(rest) == 2 and is_query_group(rest[1]):
        cond["op"] = "exists"
        cond["not_op"] = negate                     # NOT EXISTS keeps not_op
        cond["exists"] = 1
        return [cond]
    case, op_idx = 0, None
    for idx, x in enumerate(rest):
        if kw(x, "case"):
            case += 1
        elif kw(x, "end") and case:
            case -= 1
        elif case:
            continue
        elif (isinstance(x, Tok) and x.kind == "op" and x.val in CMP_OPS) or kw(x, *PRED_KWS):
            op_idx = idx
            break
    direct = set()
    if op_idx is None:
        cond["op"] = "bool"                         # bare boolean expression
    else:
        op = rest[op_idx]
        cond["op"] = op.val if op.kind == "op" else op.low
    if cond["op"] in NEGATABLE:
        # x NOT IN / NOT LIKE / NOT BETWEEN, and NOT pushed into IN / LIKE / BETWEEN
        cond["not_op"] = negate ^ (op_idx > 0 and kw(rest[op_idx - 1], "not"))
    else:
        # comparison, IS, bare boolean: a NOT is pushed in as the complement
        # (= <-> !=, < <-> >=, > <-> <=, IS <-> IS NOT); never a not_op
        if flip:
            notes["de_morgan"] += 1
        if negate:
            cond["op"] = COMPLEMENT.get(cond["op"], cond["op"])
    if op_idx is not None:
        if cond["op"] in ("like", "ilike"):
            cond["like"] = True
        if cond["op"] == "is":
            notes["is_null"] += 1 if any(kw(y, "null") for y in rest[op_idx:]) else 0
        if op_idx + 1 < len(rest) and is_query_group(rest[op_idx + 1]):
            direct.add(id(rest[op_idx + 1]))        # Spider val1 is a subquery
        if cond["op"] == "between":
            for j in range(op_idx + 1, len(rest) - 1):
                if kw(rest[j], "and"):
                    if is_query_group(rest[j + 1]):
                        direct.add(id(rest[j + 1]))     # Spider val2
                    break
    sc = Scan()
    scan_expr(rest, sc)
    notes["case"] += sc.case
    for g in sc.subq:
        if id(g) in direct:
            cond["native"] += 1
        else:
            cond["expr"] += 1
    cond["aggs"] = sc.aggs
    return [cond]


# ------------------------------------------------------------------ one SELECT
def split_clauses(items):
    if not items or not kw(items[0], "select"):
        raise SqlError("expected SELECT")
    clauses, name, cur, i = {}, "select", [], 1
    while i < len(items):
        x = items[i]
        nxt = items[i + 1] if i + 1 < len(items) else None
        new, step = None, 1
        if kw(x, "group") and kw(nxt, "by"):
            new, step = "group", 2
        elif kw(x, "order") and kw(nxt, "by"):
            new, step = "order", 2
        elif kw(x, *CLAUSE_KWS):
            is_distinct_from = (kw(x, "from") and i >= 2 and kw(items[i - 1], "distinct")
                                and kw(items[i - 2], "is", "not"))
            if not is_distinct_from:
                new = x.low
        if new:
            if new in clauses or new == name:
                raise SqlError(f"clause {new} twice")
            clauses[name] = cur
            name, cur = new, []
            i += step
            continue
        cur.append(x)
        i += 1
    clauses[name] = cur
    return clauses


def strip_alias(item):
    if len(item) >= 3 and kw(item[-2], "as") and name_of(item[-1]) is not None:
        return item[:-2], name_of(item[-1])
    if len(item) >= 2 and name_of(item[-1]) is not None and not kw(item[-1], *NOT_ALIAS):
        prev = item[-2]
        if isinstance(prev, Group) or (isinstance(prev, Tok) and prev.kind in
                                       ("word", "qident", "num", "str")
                                       and not kw(prev, *NOT_BEFORE_ALIAS)):
            return item[:-1], name_of(item[-1])
    return item, None


def join_word(items, i):
    """items[i] is JOIN, or starts a run of LEFT/RIGHT/FULL/INNER/CROSS/
    NATURAL/OUTER that ends in JOIN (LEFT(s, 2) is a string function)"""
    if kw(items[i], "join"):
        return True
    j = i
    while j < len(items) and kw(items[j], *JOIN_MODS):
        j += 1
    return j > i and j < len(items) and kw(items[j], "join")


def parse_from(items, notes):
    """table units and ON-condition segments of a FROM clause"""
    units, on_segs, cur, state, curon = [], [], [], "unit", None
    for i, x in enumerate(items):
        if punct(x, ",") or join_word(items, i):
            if state == "unit" and cur:
                units.append(cur)
            if state == "on" and curon:
                on_segs.append(curon)
            if kw(x, "left", "right", "full"):
                notes["outer_join"] += 1
            if kw(x, "cross"):
                notes["cross_join"] += 1
            cur, state = [], "unit"
            continue
        if kw(x, "on"):
            if cur:
                units.append(cur)
            cur, state, curon = [], "on", []
            continue
        if kw(x, "using"):
            if cur:
                units.append(cur)
            cur, state = [], "using"
            continue
        if state == "unit":
            cur.append(x)
        elif state == "on":
            curon.append(x)
    if state == "unit" and cur:
        units.append(cur)
    if state == "on" and curon:
        on_segs.append(curon)
    derived = 0
    for u in units:
        head = u[1] if kw(u[0], "lateral") and len(u) > 1 else u[0]
        if is_query_group(head):
            derived += 1
    notes["derived_table"] += derived
    return units, on_segs, derived


def analyze_select(items, notes):
    cl = split_clauses(items)
    sel = cl["select"]
    if sel and kw(sel[0], "distinct"):
        sel = sel[1:]
        if sel and kw(sel[0], "on") and len(sel) > 1 and isinstance(sel[1], Group):
            sel = sel[2:]
    elif sel and kw(sel[0], "all"):
        sel = sel[1:]
    sel_items, aliases, sel_agg = [], {}, []
    windows = expr_subq = 0
    for it in split_commas(sel):
        expr, alias = strip_alias(it)
        sel_items.append(expr)
        if alias is not None and alias not in aliases:
            aliases[alias] = expr
        sc = Scan()
        scan_expr(expr, sc)
        sel_agg.append(1 if sc.aggs else 0)
        windows += sc.windows
        expr_subq += len(sc.subq)
        notes["case"] += sc.case

    # FROM
    if "from" in cl:
        units, on_segs, derived = parse_from(cl["from"], notes)
    else:
        units, on_segs, derived = [], [], 0
        notes["no_from"] += 1
    from_conds = []
    for seg in on_segs:
        c = conds_of(seg, notes)
        if from_conds:
            from_conds.append("and")
        from_conds.extend(c)
    where = conds_of(cl["where"], notes) if "where" in cl else []
    having = conds_of(cl["having"], notes) if "having" in cl else []

    group_n = 0
    if "group" in cl:
        g_items = split_commas(cl["group"])
        group_n = len(g_items)
        for it in g_items:
            sc = Scan()
            scan_expr(it, sc)
            expr_subq += len(sc.subq)

    order_agg = []
    if "order" in cl:
        for it in split_commas(cl["order"]):
            cut = [k for k, y in enumerate(it) if kw(y, "using")]
            if cut:
                it = it[:cut[0]]
            while it and kw(it[-1], "asc", "desc", "first", "last", "nulls"):
                it = it[:-1]
            if not it:
                raise SqlError("empty ORDER BY item")
            target, resolved = it, False
            if len(it) == 1 and name_of(it[0]) in aliases:
                target, resolved = aliases[name_of(it[0])], True
            elif len(it) == 1 and isinstance(it[0], Tok) and it[0].kind == "num" \
                    and it[0].val.isdigit() and 1 <= int(it[0].val) <= len(sel_items):
                target, resolved = sel_items[int(it[0].val) - 1], True
            sc = Scan()
            scan_expr(target, sc)
            order_agg.append(1 if sc.aggs else 0)
            if resolved:
                notes["order_alias_agg"] += 1 if sc.aggs else 0
            else:
                windows += sc.windows
                expr_subq += len(sc.subq)

    limit = False
    if "limit" in cl:
        limit = not (len(cl["limit"]) == 1 and kw(cl["limit"][0], "all"))
    if "fetch" in cl:
        limit = True
        notes["fetch"] += 1

    conds = [c for c in from_conds + where + having if isinstance(c, dict)]
    connectors = [c for c in from_conds + where + having if isinstance(c, str)]

    # ---- Spider count_component1 (+ window extension)
    c1 = ((1 if where else 0) + (1 if group_n else 0) + (1 if order_agg else 0)
          + (1 if limit else 0) + (len(units) - 1 if units else 0)
          + connectors.count("or") + sum(1 for c in conds if c["like"]))
    ext = {"window": 1 if windows else 0,
           "exists": sum(c["exists"] for c in conds),
           "expr_subquery": expr_subq + sum(c["expr"] for c in conds),
           "recursive_cte": 0}
    c1 += ext["window"]
    # ---- Spider count_component2: subqueries that are condition operands
    c2 = sum(c["native"] for c in conds) + ext["exists"] + ext["expr_subquery"]

    # ---- Spider count_others; the aggregate count is literal evaluation.py:
    # has_agg(unit) tests unit[0], which for a condition is not_op and for a
    # HAVING connector string is its first letter
    agg_lit = (sum(sel_agg)
               + sum(1 for c in where if isinstance(c, dict) and c["not_op"])
               + 0                                  # groupBy col_units carry agg 'none'
               + sum(order_agg)
               + sum(1 for c in having if isinstance(c, str) or c["not_op"]))
    agg_int = (sum(sel_agg)
               + sum(1 for c in where if isinstance(c, dict) and c["aggs"])
               + sum(order_agg)
               + sum(1 for c in having if isinstance(c, dict) and c["aggs"]))

    def others_with(agg):
        return ((1 if agg > 1 else 0) + (1 if len(sel_items) > 1 else 0)
                + (1 if len(where) > 1 else 0) + (1 if group_n > 1 else 0))

    return {"c1": c1, "c2": c2, "others": others_with(agg_lit),
            "others_intended": others_with(agg_int), "ext": ext,
            "derived": derived}


# ------------------------------------------------------------------ statement
def references(items, name, in_from=False):
    """True when a FROM-list position inside items names the relation `name`:
    right after FROM or JOIN, or after a comma of a FROM list (not a comma of a
    SELECT list or of a function call). in_from: items is a parenthesised join"""
    prev, query = None, False
    for x in items:
        if isinstance(x, Group):
            unit_pos = in_from and (prev is None or kw(prev, "from", "join") or punct(prev, ","))
            if references(x, name, unit_pos and not is_query_group(x)):
                return True
        elif kw(x, "select"):
            query, in_from = True, False
        elif kw(x, "from") and query and not kw(prev, "distinct"):   # not IS DISTINCT FROM
            in_from = True
        elif kw(x, *FROM_END):
            in_from = False
        elif name_of(x) == name and (kw(prev, "join") or (in_from and (
                prev is None or kw(prev, "from") or punct(prev, ",")))):
            return True
        prev = x
    return False


def analyze(sql):
    """Spider-style counts of one statement; returns a dict (see row())"""
    tree = build_tree(tokenize(sql))
    while tree and punct(tree[-1], ";"):
        tree = tree[:-1]
    if any(punct(x, ";") for x in tree):
        raise SqlError("more than one statement")
    notes = {k: 0 for k in MAP_KEYS + NOTE_KEYS}
    items, n_cte, n_rec = tree, 0, 0
    if items and kw(items[0], "with"):
        i = 1
        recursive = kw(items[i], "recursive")
        if recursive:
            i += 1
        while True:
            name = name_of(items[i])
            if name is None:
                raise SqlError("CTE without a name")
            i += 1
            if isinstance(items[i], Group):         # column list
                i += 1
            if not kw(items[i], "as"):
                raise SqlError("CTE without AS")
            i += 1
            if kw(items[i], "not"):
                i += 1
            if kw(items[i], "materialized"):
                i += 1
            body = items[i]
            if not is_query_group(body):
                raise SqlError("CTE body is not a query")
            i += 1
            n_cte += 1
            if recursive and references(body, name):
                n_rec += 1
            if i < len(items) and punct(items[i], ","):
                i += 1
                continue
            break
        items = items[i:]
    notes["cte_inline"] = n_cte - n_rec
    # set operations at depth 0 (Spider nests the chain: one IUE at the top)
    first, setop = [], None
    for k, x in enumerate(items):
        if kw(x, *SETOP_KWS):
            setop = x.low
            if k + 1 < len(items) and kw(items[k + 1], "all"):
                notes["union_all"] += 1
            break
        first.append(x)
    while len(first) == 1 and is_query_group(first[0]):
        first = list(first[0])
    r = analyze_select(first, notes)
    if setop:
        r["c2"] += 1
    r["ext"]["recursive_cte"] = n_rec
    r["c2"] += n_rec
    r["n_cte"] = n_cte
    r["notes"] = notes
    r["hardness"] = eval_hardness(r["c1"], r["c2"], r["others"])
    return r


def eval_hardness(c1, c2, others):
    """Spider eval_hardness thresholds"""
    if c1 <= 1 and others == 0 and c2 == 0:
        return "easy"
    if (others <= 2 and c1 <= 1 and c2 == 0) or (c1 <= 2 and others < 2 and c2 == 0):
        return "medium"
    if ((others > 2 and c1 <= 2 and c2 == 0) or (2 < c1 <= 3 and others <= 2 and c2 == 0)
            or (c1 <= 1 and others == 0 and c2 <= 1)):
        return "hard"
    return "extra"


def readings(r):
    """hardness under the primary reading and three sensitivity readings"""
    e = r["ext"]
    pure_c1 = r["c1"] - e["window"]
    pure_c2 = r["c2"] - e["exists"] - e["expr_subquery"] - e["recursive_cte"]
    nested_c2 = r["c2"] - e["recursive_cte"] + r["n_cte"] + r["derived"]
    return {"primary": r["hardness"],
            "pure": eval_hardness(pure_c1, pure_c2, r["others"]),
            "nested": eval_hardness(r["c1"], nested_c2, r["others"]),
            "agg_intended": eval_hardness(r["c1"], r["c2"], r["others_intended"])}


def fired(r):
    parts = []
    for key, comp in EXT_KEYS:
        v = r["ext"][key]
        if v:
            parts.append(f"ext:{key}({comp}+{v})")
    for key in MAP_KEYS:
        v = r["notes"][key]
        if v:
            parts.append(f"map:{key}({v})")
    for key in NOTE_KEYS:
        v = r["notes"][key]
        if v:
            parts.append(f"note:{key}({v})")
    return ";".join(parts) if parts else "none"


# ------------------------------------------------------------------ self-test
SELFTEST = [
    # (sql, hardness, comp1, comp2, others) expected under Spider's rule
    ("SELECT count(*) FROM singer WHERE age > 20", "easy", 1, 0, 0),
    ("SELECT name, country, age FROM singer ORDER BY age DESC", "medium", 1, 0, 1),
    ("SELECT T2.name, count(*) FROM concert AS T1 JOIN stadium AS T2 "
     "ON T1.stadium_id = T2.stadium_id GROUP BY T1.stadium_id", "medium", 2, 0, 1),
    ("SELECT name FROM stadium WHERE stadium_id NOT IN (SELECT stadium_id FROM concert)",
     "hard", 1, 1, 0),
    # literal has_agg: NOT IN counts as an aggregate next to avg -> extra
    ("SELECT avg(life_expectancy) FROM country WHERE name NOT IN (SELECT T1.name FROM "
     "country AS T1 JOIN countrylanguage AS T2 ON T1.code = T2.countrycode "
     "WHERE T2.language = 'English' AND T2.isofficial = 'T')", "extra", 1, 1, 1),
    ("SELECT name FROM singer WHERE name LIKE '%a%'", "medium", 2, 0, 0),
    ("SELECT a FROM t WHERE b = 1 OR c = 2", "medium", 2, 0, 1),
    ("SELECT a, b FROM t WHERE x = 1 AND y = 2 ORDER BY a LIMIT 3", "hard", 3, 0, 2),
    ("SELECT a, max(b), min(c) FROM t WHERE x = 1 AND y = 2 GROUP BY a, d", "hard", 2, 0, 4),
    ("SELECT T1.a FROM t1 AS T1 JOIN t2 AS T2 ON T1.id = T2.id JOIN t3 AS T3 "
     "ON T2.k = T3.k WHERE T3.x = 'y'", "hard", 3, 0, 0),
    ("SELECT name FROM a UNION SELECT name FROM b", "hard", 0, 1, 0),
    ("SELECT a, count(*) FROM t GROUP BY a ORDER BY count(*) DESC", "extra", 2, 0, 2),
    ("SELECT name FROM singer WHERE age > (SELECT avg(age) FROM singer) AND country = 'France'",
     "extra", 1, 1, 1),
    ("SELECT a FROM t1 JOIN t2 ON t1.k = t2.k JOIN t3 ON t2.j = t3.j "
     "JOIN t4 ON t3.m = t4.m WHERE t4.z = 1", "extra", 4, 0, 0),
    # tokenizer: keywords inside literals (English and Thai), comments, quoted identifiers
    ("SELECT name FROM t WHERE note = 'x ORDER BY y LIMIT 1 UNION (SELECT ''a'' OR'",
     "easy", 1, 0, 0),
    ("SELECT ชื่อ FROM ลูกค้า WHERE เมือง = 'เชียงใหม่ OR WHERE (SELECT หรือ'", "easy", 1, 0, 0),
    ('SELECT "order" FROM "group" -- ORDER BY 1 LIMIT 2\n/* WHERE (x = 1 /* nested */ */',
     "easy", 0, 0, 0),
    (r"SELECT a FROM t WHERE b = E'it\'s ORDER BY' AND c = $q$ LIMIT 5 ) $q$", "medium", 1, 0, 1),
    ("SELECT a FROM t WHERE b BETWEEN 1 AND 2", "easy", 1, 0, 0),
    # ORDER BY inside OVER (...) is not a query-level ORDER BY (window ext +1 comp1)
    ("SELECT rank() OVER (PARTITION BY g ORDER BY b DESC) FROM t LIMIT 3", "medium", 2, 0, 0),
    # select alias resolved to its aggregate (map:order_alias_agg)
    ("SELECT g, count(*) AS n FROM t GROUP BY g ORDER BY n DESC", "extra", 2, 0, 2),
    # HAVING: literal has_agg counts connectors, not the aggregate
    ("SELECT a, count(*) FROM t GROUP BY a HAVING count(*) > 1", "medium", 1, 0, 1),
    # CTE inlined as a derived table; derived tables are table units (Spider)
    ("WITH s AS (SELECT a, count(*) AS n FROM t GROUP BY a) SELECT a FROM s WHERE n > 1",
     "easy", 1, 0, 0),
    ("SELECT count(*) FROM (SELECT a FROM t GROUP BY a HAVING count(*) > 1) AS x",
     "easy", 0, 0, 0),
    ("SELECT a FROM t WHERE NOT EXISTS (SELECT 1 FROM u WHERE u.k = t.k)", "hard", 1, 1, 0),
    ("WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT n + 1 FROM r WHERE n < 5) "
     "SELECT n FROM r", "hard", 0, 1, 0),
    ("SELECT a FROM t WHERE (b = 1 OR c = 2) AND d IS NOT NULL", "medium", 2, 0, 1),
    # De Morgan: NOT (b = 1 AND c = 2) is b != 1 OR c != 2 (one OR, no not_op)
    ("SELECT a FROM t WHERE NOT (b = 1 AND c = 2)", "medium", 2, 0, 1),
    ("SELECT DISTINCT h1.p FROM h AS h1 JOIN h AS h2 ON h2.r = h1.v "
     "AND NOT (h2.p = h1.p AND h2.y = h1.y)", "medium", 2, 0, 0),
    # NOT (IN OR LIKE) is NOT IN AND NOT LIKE: both keep not_op (literal agg 2)
    ("SELECT a FROM t WHERE NOT (b IN (1, 2) OR c LIKE 'x%')", "extra", 2, 0, 2),
    # LEFT(...) / RIGHT(...) string functions are not join words
    ("SELECT a.x FROM a JOIN b ON LEFT(a.x, 3) = b.y", "easy", 1, 0, 0),
    ("SELECT a.x FROM a LEFT OUTER JOIN b ON RIGHT(a.x, 3) = b.y WHERE a.z = 1",
     "medium", 2, 0, 0),
    # WITH RECURSIVE: only a FROM-list comma makes a CTE recursive, not a SELECT-list one
    ("WITH RECURSIVE n AS (SELECT id, n FROM t) SELECT id FROM n", "easy", 0, 0, 0),
    ("WITH RECURSIVE r(n) AS (SELECT 1 UNION ALL SELECT r.n + 1 FROM t, r WHERE r.n < t.m) "
     "SELECT n FROM r", "hard", 0, 1, 0),
]
SELFTEST_FIRED = [
    # (sql, extensions_fired)
    ("SELECT DISTINCT h1.p FROM h AS h1 JOIN h AS h2 ON h2.r = h1.v "
     "AND NOT (h2.p = h1.p AND h2.y = h1.y)", "map:bool_group(1);map:de_morgan(1)"),
    ("SELECT a.x FROM a LEFT OUTER JOIN b ON RIGHT(a.x, 3) = b.y WHERE a.z = 1",
     "map:outer_join(1)"),
    ("WITH RECURSIVE n AS (SELECT id, n FROM t) SELECT id FROM n", "map:cte_inline(1)"),
]
SELFTEST_READINGS = [
    # (sql, reading, expected)
    ("WITH s AS (SELECT a, count(*) AS n FROM t GROUP BY a) SELECT a FROM s WHERE n > 1",
     "nested", "hard"),
    ("SELECT a FROM t WHERE NOT EXISTS (SELECT 1 FROM u WHERE u.k = t.k)", "pure", "easy"),
    ("SELECT a, avg(b) FROM t GROUP BY a HAVING avg(b) > 3 ORDER BY a", "primary", "medium"),
    ("SELECT a, avg(b) FROM t GROUP BY a HAVING avg(b) > 3 ORDER BY a", "agg_intended", "extra"),
]
SELFTEST_ERRORS = ["SELECT a FROM t WHERE (b = 1", "SELECT a FROM t WHERE b = 'x",
                   "SELECT a FROM t /* open"]


def selftest():
    bad = []
    for sql, h, c1, c2, o in SELFTEST:
        r = analyze(sql)
        got = (r["hardness"], r["c1"], r["c2"], r["others"])
        if got != (h, c1, c2, o):
            bad.append(f"  {sql!r}\n    expected {(h, c1, c2, o)} got {got}")
    for sql, f in SELFTEST_FIRED:
        got = fired(analyze(sql))
        if got != f:
            bad.append(f"  {sql!r} expected fired {f} got {got}")
    for sql, reading, h in SELFTEST_READINGS:
        got = readings(analyze(sql))[reading]
        if got != h:
            bad.append(f"  {sql!r} [{reading}] expected {h} got {got}")
    for sql in SELFTEST_ERRORS:
        try:
            analyze(sql)
            bad.append(f"  {sql!r} should be refused")
        except SqlError:
            pass
    if bad:
        sys.exit("SELFTEST FAILED\n" + "\n".join(bad))
    return len(SELFTEST) + len(SELFTEST_FIRED) + len(SELFTEST_READINGS) + len(SELFTEST_ERRORS)


# ------------------------------------------------------------------ table
def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 16), b""):
            h.update(b)
    return h.hexdigest()


def load(path, set_name):
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f, delimiter="\t"))
    if not rows or GOLD_COLUMN not in rows[0]:
        sys.exit(f"{path}: no column {GOLD_COLUMN}")
    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        sys.exit(f"{path}: duplicate id")
    if len(rows) != EXPECTED_ROWS[set_name]:
        sys.exit(f"{path}: {len(rows)} rows, expected {EXPECTED_ROWS[set_name]}")
    return rows


def md_table(head, rows):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def crosstab(records, keyf, reading="primary"):
    keys = sorted({keyf(r) for r in records})
    rows = []
    for k in keys:
        sub = [r for r in records if keyf(r) == k]
        cnt = [sum(1 for r in sub if r["readings"][reading] == h) for h in HARDNESS]
        rows.append([k] + cnt + [len(sub)])
    tot = [sum(1 for r in records if r["readings"][reading] == h) for h in HARDNESS]
    rows.append(["all"] + tot + [len(records)])
    return md_table(["", *HARDNESS, "n"], rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--core", help="core suite TSV (60 items)")
    ap.add_argument("--ext", help="extension suite TSV (40 items)")
    ap.add_argument("--out", help="output TSV")
    ap.add_argument("--selftest", action="store_true", help="run the self-test only")
    a = ap.parse_args(argv)
    n = selftest()
    if a.selftest:
        print(f"selftest OK ({n} checks)")
        return 0
    if not (a.core and a.ext and a.out):
        ap.error("--core, --ext and --out are required (or --selftest)")
    if os.path.realpath(a.out) in (os.path.realpath(a.core), os.path.realpath(a.ext)):
        sys.exit("--out must not be an input file")
    records, status = [], {}
    for set_name, path in (("core", a.core), ("ext", a.ext)):
        for row in load(path, set_name):
            key = (set_name, row.get("v13_status", ""), row.get("build_status", ""))
            status[key] = status.get(key, 0) + 1
            sql = row[GOLD_COLUMN].strip()
            if not sql:
                sys.exit(f"{row['id']}: empty {GOLD_COLUMN}")
            try:
                r = analyze(sql)
            except (SqlError, IndexError) as e:
                sys.exit(f"{row['id']}: cannot analyse gold ({e})")
            records.append({"set": set_name, "id": row["id"], "tier": row["tier"],
                            "schema": row["schema"],
                            "family": row.get("family", "") if set_name == "ext" else "",
                            "r": r, "readings": readings(r)})
    with open(a.out, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(OUT_COLUMNS)
        for rec in records:
            r = rec["r"]
            w.writerow([rec["set"], rec["id"], rec["tier"], rec["schema"], rec["family"],
                        r["hardness"], r["c1"], r["c2"], r["others"], fired(r)])

    print(f"selftest OK ({n} checks)")
    print(f"gold column: {GOLD_COLUMN}")
    for set_name, path in (("core", a.core), ("ext", a.ext)):
        print(f"{set_name}: {os.path.basename(path)} sha256 {sha256(path)}")
    print(f"out: {os.path.basename(a.out)} sha256 {sha256(a.out)}")
    print("items by (set, v13_status, build_status): "
          + ", ".join(f"{k} {v}" for k, v in sorted(status.items())))
    print("\n## set x hardness (primary)\n" + crosstab(records, lambda r: r["set"]))
    print("\n## tier x hardness, pooled 100 (primary)\n"
          + crosstab(records, lambda r: "T" + r["tier"]))
    print("\n## set-tier x hardness (primary)\n"
          + crosstab(records, lambda r: f"{r['set']} T{r['tier']}"))
    for reading in ("pure", "nested", "agg_intended"):
        moved = [f"{r['id']} {r['readings']['primary']}->{r['readings'][reading]}"
                 for r in records if r["readings"][reading] != r["readings"]["primary"]]
        print(f"\n## sensitivity reading '{reading}': set x hardness\n"
              + crosstab(records, lambda r: r["set"], reading))
        print(f"changed ({len(moved)}): " + (", ".join(moved) if moved else "none"))
    print("\n## items per fired token")
    tally = {}
    for rec in records:
        f = fired(rec["r"])
        for tok in ([] if f == "none" else f.split(";")):
            key = tok.split("(")[0]
            tally.setdefault(key, []).append(rec["id"])
    for key in sorted(tally):
        print(f"- {key}: {len(tally[key])} ({', '.join(tally[key])})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
