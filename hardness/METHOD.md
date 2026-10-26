# Spider-style hardness of the 100 frozen gold queries

## Purpose and status

The preregistration (`prereg/preregistration_FROZEN.md`, AMENDMENT-9 section 8, line 1833) says, in paraphrase,
that the artifact will include a Spider-style hardness table. The table is computed from the frozen gold of the
100 items (the 60 core items of the October collection and the 40 extension items). It is not used for item
selection or for any analysis.

This table was computed on 26 Oct 2026 (UTC+7), **after all results were known**, and revised the same day after
review (see *Revision*). It is **descriptive only**. The script reads only the two suite files below and never
opens a results file.

## Inputs and outputs

| role | file | rows | sha256 |
|---|---|---|---|
| core | `suite/k3n_suite_v1.3n_oct.tsv` (Q27 repaired) | 60, all `v13_status` = primary | `96b8e9f2e48398111aa6b2d555995a2b726a54e62efe1474668477dda7eed46b` |
| extension | `suite/k3n_ext_suite_v1.0.tsv` | 40, all primary, `build_status` = FROZEN | `838c732afd89066835de9f3eb60799029e76364af6f73a472bfee346e7cbdf14` |
| script | `hardness/hardness_spider.py` | n/a | `f6ceee32af111217c590634dd1c062da6789f80eea6ccf7b6f382d8a8b2e3029` |
| table | `hardness/hardness_spider_100.tsv` | 100 | `c0d59aa1ba34dcf7facf440a909e75ab6e0465159c02fc675b75e1e51acbd29f` |

**Gold column: `gold_sql_draft`.** `harness/grade_v13n.py` grades against `item["gold_sql_draft"]` as the primary
accepted key (`item_keys`, `key_sqls` and the manifest gold check). `gold_sql_v12`, falling back to
`gold_sql_draft` when it is blank, feeds only the diagnostic `correct_v12` column; it becomes the key of `correct`
only in the `--legacy` parity mode. `alt_gold_en` and `alt_gold_th` are accepted alternatives, and this table does
not use them.

Reproduce from the artifact root (stdlib only, deterministic; two runs gave byte-identical output):

```
python3 -I -B "hardness/hardness_spider.py" --core "suite/k3n_suite_v1.3n_oct.tsv" --ext "suite/k3n_ext_suite_v1.0.tsv" --out "hardness/hardness_spider_100.tsv"
```

## Spider's rule, as re-implemented

**Spider's rules were re-implemented from the logic of the published evaluation script, `evaluation.py` of Spider
(Yu et al., EMNLP 2018): `get_nestedSQL`, `count_component1`, `count_component2`, `count_others` and
`eval_hardness`. Spider's own code was not run.** Its parser cannot read CTEs, window functions, EXISTS, IS NULL,
CASE, UNION ALL, `::` casts and other PostgreSQL syntax that the gold uses. A stdlib tokenizer and a
parenthesis tree recover the clause structure instead. The tokenizer handles quoted strings including `''`, `E''`
and `$$` forms, quoted identifiers, `--` and nested `/* */` comments, and Thai identifiers.

Three points, checked against `evaluation.py` (repository taoyds/spider, master branch) on 26 Oct 2026:
1. **FROM subqueries are not counted by `get_nestedSQL`.** It collects only subqueries that are condition operands
   in ON, WHERE or HAVING, plus the INTERSECT, UNION or EXCEPT branch. A subquery in FROM enters only
   `count_component1`, as a table unit.
2. **The `has_agg` quirk.** `has_agg(unit)` tests `unit[0]`. For a condition tuple
   `(not_op, op, val_unit, val1, val2)`, `unit[0]` is `not_op`, so `count_agg(sql['where'][::2])` counts negated
   conditions (NOT IN, NOT LIKE, NOT BETWEEN), not aggregates. `count_agg(sql['having'])` runs over the whole list,
   including the `'and'`/`'or'` strings, so it counts negated conditions and every connector. The script keeps
   this literal behaviour.
3. **ORDER BY aggregates.** `count_others` counts each aggregated column unit of an ORDER BY expression
   (`unit[1]` and `unit[2]`) separately; this script counts an ORDER BY item once. No top-level ORDER BY in the
   100 gold queries has an expression with two aggregates, so no label changes.

The rule looks only at the **top-level query**. When the query is a set operation, that means its first branch.
A nested query adds only the fact that it exists.

- **comp1** is the sum of: 1 if WHERE is present; 1 if GROUP BY is present; 1 if ORDER BY is present; 1 if LIMIT
  is present; the number of FROM table units minus 1; the number of OR connectors in ON, WHERE and HAVING; the
  number of LIKE conditions in ON, WHERE and HAVING. HAVING itself is not counted.
- **comp2** is the number of nested queries that `get_nestedSQL` returns: one for each condition operand in ON,
  WHERE or HAVING that is a subquery, and one for an INTERSECT, UNION or EXCEPT at the top level. Spider parses
  the chain `A UNION B UNION C` right-recursively, so the top level holds at most one set operation.
- **others** = [agg_count > 1] + [more than one SELECT item] + [more than one WHERE condition] + [more than one
  GROUP BY item]. agg_count adds the SELECT items that hold an aggregate, the ORDER BY items that hold an
  aggregate, `count_agg(WHERE conditions)` and `count_agg(HAVING list)` (the quirk above); GROUP BY adds 0. The
  aggregates are Spider's `AGG_OPS`: MAX, MIN, COUNT, SUM and AVG. An item counts once, however many aggregate
  calls it contains. The sensitivity reading `agg_intended` counts real aggregates in WHERE and HAVING instead,
  and **no item changes**.
- **eval_hardness**
  - easy: comp1 ≤ 1 and others = 0 and comp2 = 0
  - medium: (others ≤ 2 and comp1 ≤ 1 and comp2 = 0) or (comp1 ≤ 2 and others < 2 and comp2 = 0)
  - hard: (others > 2 and comp1 ≤ 2 and comp2 = 0) or (2 < comp1 ≤ 3 and others ≤ 2 and comp2 = 0) or
    (comp1 ≤ 1 and others = 0 and comp2 ≤ 1)
  - extra: every other case

  The thresholds are not monotone. For example, comp1 = 2 with others = 2 is extra (Q36, Q45), but comp1 = 3 with
  others = 2 is hard (Q32, Q38, Q39).

## Author decisions

1. **The main reading is Spider's code reading.** A derived table or a non-recursive CTE in FROM is a table unit,
   because `get_nestedSQL` does not count FROM subqueries. Counting them in comp2 is reported as the alternative
   `nested` reading (see *Sensitivity readings*).
2. **X36: an aggregate inside a window's ORDER BY counts as an aggregate**, because the query computes it.
   `RANK() OVER (… ORDER BY SUM(…))` makes that SELECT item an aggregate item, which gives others = 3 and
   **extra**. Alternative: if aggregates inside a window specification were not counted, others would be 2 and
   X36 would be **hard** (ext 5/6/9/20, all 13/46/15/26).

## Rewrites into Spider's grammar (`map:`; they add no count of their own)

These rewrites map PostgreSQL forms onto Spider's grammar, and the counts are then Spider's counts of the rewritten
query. Two of them, `bool_group` and `de_morgan`, keep the conditions and connectors but not the grouping, which
Spider's flat condition list cannot express; they are counting conventions rather than equivalences.

- `cte_inline(n)`: a non-recursive CTE is read as the derived table it names. Its reference in FROM is a table unit.
  As with any derived table in Spider, its body is not examined.
- `union_all`: UNION ALL, INTERSECT ALL and EXCEPT ALL are read as UNION, INTERSECT and EXCEPT.
- `order_alias_agg(n)`: an ORDER BY item that names a SELECT alias or ordinal is read as that SELECT expression.
  Spider's grammar has no SELECT-list aliases. The token is listed only when the expression holds an aggregate,
  because that is the only case in which the rewrite changes a count.
- `outer_join`, `cross_join`: LEFT, RIGHT, FULL and CROSS JOIN count as joins. LEFT, RIGHT, FULL, INNER, CROSS,
  NATURAL and OUTER are join words only when the run they start ends in JOIN, so the string functions
  `LEFT(…)` and `RIGHT(…)` are not joins.
- `is_null`: IS [NOT] NULL is one condition. IS NOT NULL is not a Spider `not_op`, because Spider sets `not_op` only
  for a NOT placed before the operator.
- `bool_group`: a parenthesised boolean group is flattened into its conditions and connectors.
- `de_morgan`: a leading NOT before a group is pushed inside by De Morgan. AND and OR swap, and each condition is
  negated. A comparison takes its complement operator (= ↔ !=, < ↔ >=, > ↔ <=; IS ↔ IS NOT) and no `not_op`.
  IN, LIKE, BETWEEN and EXISTS keep Spider's `not_op` (NOT IN, NOT LIKE, NOT BETWEEN, NOT EXISTS). A leading NOT
  before a single comparison is complemented the same way. Example: X13 `ON a = b AND NOT (c = d AND e = f)` is
  read as `ON a = b AND c != d OR e != f`.
- `case`: a CASE expression is treated as an opaque expression. Conditions inside it are not WHERE conditions and
  are not ORs.
- `no_from`: a SELECT without FROM has 0 table units.
- `fetch`: FETCH FIRST is read as LIMIT (no item uses it).

Other functions and casts are treated as opaque expressions: EXTRACT, DATE_TRUNC, ROUND, ABS, `::date` and
PERCENTILE_CONT … WITHIN GROUP.

## Extensions (`ext:`; each one adds to a single component)

1. `window(comp1+1)`: when the top-level SELECT or ORDER BY has at least one window function (OVER), comp1 gets
   +1, once, however many window calls there are.
   - Why: OVER (PARTITION BY … ORDER BY …) is a clause-level construct like the GROUP BY and ORDER BY that comp1
     counts. Adding it to *others* would almost never matter, because others tests only "more than one".
   - A window call is not an aggregate. Plain aggregates inside it still make the item an aggregate item, as in
     `SUM(SUM(x)) OVER ()` and `RANK() OVER (… ORDER BY SUM(x))` (author decision 2).
   - An ORDER BY inside `OVER (…)` or `WITHIN GROUP (…)` is not a query-level ORDER BY.
2. `exists(comp2+n)`: each [NOT] EXISTS condition counts its subquery as a nested operand, and NOT EXISTS sets
   `not_op`. Spider lists `exists` in `WHERE_OPS`, but its parser cannot read it.
3. `expr_subquery(comp2+n)`: a subquery outside Spider's operand positions counts as nested. These positions
   include a scalar subquery in the SELECT list and CASE WHEN EXISTS.
4. `recursive_cte(comp2+n)`: a recursive CTE cannot be inlined. Its anchor UNION [ALL] recursive member is a set
   operation, which Spider counts in comp2. Its reference in FROM is a table unit. A CTE under WITH RECURSIVE is
   recursive only when its body names it in a FROM list (after FROM, after JOIN or after a FROM-list comma); a
   SELECT-list column of the same name does not count.

**Recomputing the pure Spider reading:** subtract each `ext:` increment from the row's comp1 or comp2, then apply
eval_hardness again. `ext:` increments change only comp1 and comp2; an [NOT] EXISTS predicate still counts as one WHERE condition (and NOT EXISTS as a `not_op`) in *others*, and the pure reading keeps both (F7C-6 is the one pure label that depends on this). `note:derived_table(n)` counts the derived tables in the
top-level FROM. These are Spider-native, and the note exists only for the `nested` reading below.

Table columns: set, id, tier, schema, family (extension only), hardness, comp1, comp2, others, extensions_fired.
comp1, comp2 and others are the values after rewrites and extensions. extensions_fired is a semicolon-separated
list of `ext:`, `map:` and `note:` tokens, or `none`.

## Results (primary reading)

| set | easy | medium | hard | extra | n |
|---|---|---|---|---|---|
| core | 8 | 40 | 6 | 6 | 60 |
| ext | 5 | 6 | 8 | 21 | 40 |
| all | 13 | 46 | 14 | 27 | 100 |

| tier (pooled) | easy | medium | hard | extra | n |
|---|---|---|---|---|---|
| T1 | 5 | 10 | 0 | 0 | 15 |
| T2 | 2 | 13 | 2 | 1 | 18 |
| T3 | 3 | 10 | 3 | 2 | 18 |
| T4 | 3 | 13 | 9 | 24 | 49 |
| all | 13 | 46 | 14 | 27 | 100 |

| set × tier | easy | medium | hard | extra | n |
|---|---|---|---|---|---|
| core T1 | 5 | 10 | 0 | 0 | 15 |
| core T2 | 1 | 12 | 2 | 0 | 15 |
| core T3 | 2 | 8 | 3 | 2 | 15 |
| core T4 | 0 | 10 | 1 | 4 | 15 |
| ext T2 | 1 | 1 | 0 | 1 | 3 |
| ext T3 | 1 | 2 | 0 | 0 | 3 |
| ext T4 | 3 | 3 | 8 | 20 | 34 |

Tokens that fired, with the number of items:
- `ext:exists`: 13
- `ext:window`: 7 (Q49, Q52, Q54, Q57, Q60, X35, X36)
- `ext:expr_subquery`: 2 (PK1, FK3)
- `ext:recursive_cte`: 2 (X37, X38)
- `map:cte_inline`: 15
- `map:order_alias_agg`: 4 (Q32, Q36, Q38, Q45)
- `map:is_null`: 5
- `map:case`: 3
- `map:no_from`: 2 (PK1, FK3)
- `map:bool_group`, `map:de_morgan`: 1 each (X13)
- `map:outer_join`, `map:cross_join`, `map:union_all`: 1 each
- `note:derived_table`: 6 (Q47, Q51, Q55, X23, X24, X25)

## Sensitivity readings (not in the table)

| reading | core e/m/h/x | ext e/m/h/x | all e/m/h/x | items that change |
|---|---|---|---|---|
| primary | 8/40/6/6 | 5/6/8/21 | 13/46/14/27 | (none) |
| `pure` (all `ext:` off) | 8/40/6/6 | 13/12/2/13 | 21/52/8/19 | 15, all in ext |
| `nested` (CTE bodies + top-level derived tables count in comp2) | 8/33/6/13 | 2/4/10/24 | 10/37/16/37 | 13, all upward |
| `agg_intended` (count real aggregates in WHERE/HAVING) | same as primary | same | same | 0 |
| X36 alternative (author decision 2) | same as primary | 5/6/9/20 | 13/46/15/26 | X36 extra→hard |

- **pure:** X07, X08 and X09 move extra→medium. X10, X12, X26, F7C-1, F7C-2, F7C-8 and FK2 move hard→easy.
  X36 moves extra→hard. X37, X38 and FK1 move extra→medium. PK1 moves extra→easy.
- **nested:** Q47, Q51, Q54, Q55, Q58, Q59, Q60, X33 and X34 move medium→extra. X21 moves hard→extra. X23, X24
  and X25 move easy→hard. A recursive CTE counts once, as a CTE body. This reading shows a blind spot of
  Spider's rule: top-N-per-group and staged-CTE items rate only medium, because Spider does not look inside derived
  tables.

## Spot check by hand (9 items)

| id | top-level structure, counted by hand | comp1/comp2/others | by hand | table |
|---|---|---|---|---|
| Q26 | self-join (2 units → 1); ON a AND b (no OR); 1 SELECT item | 1/0/0 | easy | easy ✓ |
| F7C-3 | GROUP BY (1); HAVING COUNT(*) = SUM(CASE …): HAVING not in comp1, no connector, not negated → agg 0 | 1/0/0 | easy | easy ✓ |
| X13 | self-join (2 units → 1); ON a AND NOT (b AND c) → a AND b' OR c' (1 OR); 1 SELECT item; ON is not WHERE | 2/0/0 | medium | medium ✓ |
| Q13 | WHERE (1); 3 SELECT items (+1); 2 WHERE conditions (+1) | 1/0/2 | medium | medium ✓ |
| Q60 | CTE inlined; window AVG … OVER (ORDER BY d ROWS BETWEEN … AND …): no query ORDER BY, ext +1 comp1; 2 items (+1); window call is not an aggregate | 1/0/1 | medium | medium ✓ |
| Q39 | WHERE + GROUP BY + ORDER BY = 3; 2 items (+1); 2 WHERE conditions (+1); agg = SUM only (ORDER BY month → DATE_TRUNC) | 3/0/2 | hard | hard ✓ |
| X26 | WHERE (1); EXISTS subquery ext +1 comp2; COUNT(DISTINCT) is the only aggregate; 1 item | 1/1/0 | hard | hard ✓ |
| Q36 | GROUP BY + ORDER BY = 2; 2 items (+1); agg = SUM + ORDER BY total_revenue → SUM = 2 (+1) | 2/0/2 | extra | extra ✓ |
| FK3 | 2 CTEs inlined; first branch has no FROM (0 units); UNION ALL chain → 1; scalar subquery in SELECT ext +1; 2 items (+1) | 0/2/1 | extra | extra ✓ |

All 9 agree with the table.

## Points of uncertainty

- **Q36, Q45**: these are extra only because the ORDER BY alias resolves to SUM or AVG. Without the alias rewrite
  they would be medium. Q32 and Q38 are hard either way.
- **PK1**: extra comes entirely from `ext:expr_subquery` (two EXISTS inside a CASE in the SELECT list, no FROM). In
  the pure reading it is easy.
- **FK3**: a four-branch UNION ALL counts as one set operation at the top level, as Spider's right-recursive parse
  does.
- **X13**: medium under the De Morgan convention (one OR); easy if the negated group kept AND as its connector, as
  the first version of this table did.
- **Derived tables and CTEs**: twelve tier-4 items built on a derived table or a CTE rate medium or easy (Q47, Q51, Q54,
  Q55, Q58, Q59, Q60, X23, X24, X25, X33, X34). This is faithful to Spider's top-level-only rule (author
  decision 1); ten others (Q56, X05, X17, X18, X19, X21, F7C-6, X37, X38, FK3) rate hard or extra. See the `nested`
  reading.
- **IS NOT NULL** is not a `not_op`. Treating it as one would change no hardness label: X08, X09 and FK1 are already
  extra, and Q50 would only reach agg = 1.
- The three points under *Spider's rule, as re-implemented* were checked against `evaluation.py` on 26 Oct 2026:
  points 1 and 2 match the script; point 3 is a difference that changes no item.

## Self-test

The self-test runs before every build and makes 44 checks:
- 34 hand-made queries, each with the expected hardness, comp1, comp2 and others. Examples:
  - a single-table COUNT with one WHERE condition gives easy;
  - NOT IN with a subquery gives hard;
  - three tables (two joins) and a WHERE give hard; four tables and a WHERE give extra;
  - GROUP BY a with ORDER BY COUNT(*) DESC gives extra;
  - NOT (b = 1 AND c = 2) gives one OR and no `not_op` (medium); NOT (b IN … OR c LIKE …) keeps both `not_op`s;
  - `LEFT(…)` and `RIGHT(…)` in an ON condition are not joins;
  - under WITH RECURSIVE, a SELECT-list column named like the CTE does not make it recursive, and a FROM-list
    comma does.
- 3 checks of the `extensions_fired` tokens (`de_morgan`, `outer_join` with `RIGHT(…)`, `cte_inline`).
- 4 checks of the sensitivity readings.
- 3 malformed inputs that must be refused: an unclosed parenthesis, an unclosed string and an unclosed comment.

Tokenizer cases covered: English and Thai string literals containing SQL keywords, and Thai identifiers; line
comments and nested block comments; quoted identifiers named "order" and "group"; `E'…\'…'` and `$q$…$q$`
strings; BETWEEN … AND; ORDER BY inside OVER (…); a SELECT alias used in ORDER BY; HAVING.

## Revision (26 Oct 2026, after review)

- NOT (…) was flattened to `NOT a AND NOT b`; it now follows De Morgan (`map:de_morgan`). X13 moves easy→medium:
  ext 6/5/8/21 → 5/6/8/21, all 14/45/14/27 → 13/46/14/27. No other item changes.
- `LEFT(…)`/`RIGHT(…)` read as join words, and a SELECT-list comma marking a CTE recursive: both fixed; neither
  occurs in the gold, so no item changes.
- Previous table sha256 `634fa10178c7c91634ff598324c485ec7887d3034175748d4ce4cf11022cff24`.
