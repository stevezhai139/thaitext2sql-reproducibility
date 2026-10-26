"""
answers_mi_PREREG_v2.py -- answers and foils for the multi-instance items of the
extension suite (AMENDMENT-9), graded under rule MI-1b on instances built from k3n.

Written 2026-10-14 (UTC+7) BEFORE any k3n-derived instance (k3_pk_n_*,
k3_fk_i_* rebuilt from k3n, or their g0_ test copies) was built and BEFORE any
SQL below was executed on such an instance. The frozen copy is
answers_mi_PREREG_v2_frozen.py; its sha256 and freeze time are in
answers_mi_PREREG_v2_frozen.sha256. selftest_mi.py reads only the frozen copy.

Disclosure (for AMENDMENT-9): before writing this file the drafting assistant had
seen (a) a TEST-ONLY simulation of the 45 PK1 answers below on the five proposed
PK1 instances, simulated with a CTE that shadows PresidentMarriage inside each
query on the scratch database k3n (no model output, no student data); the PK1
predictions below are the simulated results; (b) TEST-ONLY runs of earlier FK
answer forms on FK instances built from k3 (13 Oct; President and Party are
identical in k3 and k3n). The two post-hoc PK gaps of the 13 Oct three-instance
design (ph_null_spouse_only, ph_uniq_spouse_alone) are registered foils here.

Every entry of ANSWERS has the keys
  id        unique answer id (PK ids follow the 13 Oct drafts: a1..m1, pk_*, ph_*)
  item      PK1 | FK1 | FK2
  kind      gold     the item's gold                      (must be graded correct)
            correct  an equivalent correct answer           (must be graded correct)
            foil     a plausible wrong answer  (must be graded wrong and fail on
                     at least one instance of the item)
  brief_category   for foils that brief 1.3 names as classroom forms that must
                   fail: uniqueness-only | nullity-only | constant | catalog;
                   "" otherwise
  origin    classroom                                  (SQL shape of a classroom
                                                         partial answer; no student
                                                         text, no counts)
            assistant-devised loophole foil
            derived from the instructor's answer key   (FK exam item; assistant's
                                                         reading)
            assistant-devised
  classroom True only when origin == "classroom"
  label     short English description
  sql       the answer (PostgreSQL 16)
  predict   expected result per instance, in the order of INSTANCES[item],
            written before any run on a k3n-derived instance:
              "YES" / "NO" / "True" / "False"  one row, one column, this value
              "shape"   anything but one row of one column (or an error)
              "error"   execution error
              {"rows": n}    n rows (any number of columns)
              [[...], ...]   exactly these rows, order irrelevant (None = NULL)
PK1 author review of origin labels and foils: OQ24 (Gate 0 approval round).
"""

INSTANCES = {
    "PK1": ["k3n", "k3_pk_n_named", "k3_pk_n_dup", "k3_pk_n_pnull", "k3_pk_n_spdup"],
    "FK1": ["k3n", "k3_fk_i_null", "k3_fk_i_orphan"],
    "FK2": ["k3n", "k3_fk_i_null"],
}

# gold per instance (manifest expected_gold, written here for the predictions)
PK1_GOLD = ["NO", "YES", "NO", "NO", "YES"]
FK1_ORPHAN = [["Planted President Orphan", "Know Nothing"]]
FK1_NOPARTY = [["Planted President NoParty", None]]
FK2_GOLD = [["Progressive"], ["Union"]]

PK_DUP_EXISTS = ("EXISTS (SELECT 1 FROM PresidentMarriage "
                 "GROUP BY PresidentName, SpouseName HAVING COUNT(*) > 1)")
PK_NULL_EXISTS = ("EXISTS (SELECT 1 FROM PresidentMarriage "
                  "WHERE PresidentName IS NULL OR SpouseName IS NULL)")

U_ONLY = ["YES", "YES", "NO", "YES", "YES"]      # uniqueness without nullity
N_ONLY = ["NO", "YES", "YES", "NO", "YES"]       # nullity without uniqueness
ALL_NO = ["NO"] * 5
ALL_YES = ["YES"] * 5


def _a(id, item, kind, sql, predict, label, brief_category="", origin="assistant-devised"):
    return dict(id=id, item=item, kind=kind, brief_category=brief_category, origin=origin,
                classroom=(origin == "classroom"), label=label, sql=sql, predict=predict)


ANSWERS = [
    # ================================================================ PK1
    # ---- 13 Oct PK draft answers (26)
    _a("a1", "PK1", "correct",
       "SELECT CASE WHEN COUNT(*) = COUNT(DISTINCT (PresidentName, SpouseName)) "
       "AND COUNT(*) = COUNT(PresidentName) AND COUNT(*) = COUNT(SpouseName) "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       PK1_GOLD, "COUNT(*) = COUNT(DISTINCT row) and COUNT(col) = COUNT(*) for both columns"),
    _a("a2", "PK1", "correct",
       "SELECT CASE WHEN COUNT(*) = COUNT(DISTINCT (PresidentName, SpouseName)) "
       "AND COUNT(*) FILTER (WHERE PresidentName IS NULL OR SpouseName IS NULL) = 0 "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       PK1_GOLD, "COUNT(DISTINCT row) plus a FILTER count of NULL keys = 0"),
    _a("a3", "PK1", "correct",
       "SELECT CASE WHEN SUM(CASE WHEN PresidentName IS NULL OR SpouseName IS NULL "
       "THEN 1 ELSE 0 END) = 0 AND COUNT(*) = (SELECT COUNT(*) FROM (SELECT DISTINCT "
       "PresidentName, SpouseName FROM PresidentMarriage) d) "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       PK1_GOLD, "SUM(CASE ... IS NULL) = 0 and COUNT(*) against SELECT DISTINCT"),
    _a("a4", "PK1", "correct",
       "SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM PresidentMarriage "
       "GROUP BY PresidentName, SpouseName HAVING COUNT(*) > 1) "
       "AND NOT EXISTS (SELECT 1 FROM PresidentMarriage "
       "WHERE PresidentName IS NULL OR SpouseName IS NULL) "
       "THEN 'YES' ELSE 'NO' END AS verdict",
       PK1_GOLD, "NOT EXISTS (duplicate keys) AND NOT EXISTS (NULL keys)"),
    _a("a5", "PK1", "correct",
       "SELECT CASE WHEN NOT EXISTS (SELECT PresidentName, SpouseName FROM PresidentMarriage "
       "EXCEPT ALL SELECT DISTINCT PresidentName, SpouseName FROM PresidentMarriage) "
       "AND NOT EXISTS (SELECT PresidentName, SpouseName FROM PresidentMarriage "
       "EXCEPT SELECT PresidentName, SpouseName FROM PresidentMarriage "
       "WHERE PresidentName IS NOT NULL AND SpouseName IS NOT NULL) "
       "THEN 'YES' ELSE 'NO' END AS verdict",
       PK1_GOLD, "EXCEPT ALL for duplicates, EXCEPT for rows with a NULL key"),
    _a("a6", "PK1", "correct",
       "SELECT CASE WHEN bool_and((PresidentName, SpouseName) IS NOT NULL) "
       "AND COUNT(*) = COUNT(DISTINCT (PresidentName, SpouseName)) "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       PK1_GOLD, "bool_and(row IS NOT NULL) plus COUNT(DISTINCT row)"),
    _a("a7", "PK1", "correct",
       "WITH s AS (SELECT COUNT(*) AS n, COUNT(DISTINCT (PresidentName, SpouseName)) AS nd, "
       "COUNT(*) FILTER (WHERE PresidentName IS NULL) AS n_pn_null, "
       "COUNT(*) FILTER (WHERE SpouseName IS NULL) AS n_sn_null FROM PresidentMarriage) "
       "SELECT CASE WHEN n = nd AND n_pn_null = 0 AND n_sn_null = 0 "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM s",
       PK1_GOLD, "statistics in a CTE, verdict in the outer SELECT"),
    _a("b1", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM PresidentMarriage "
       "GROUP BY PresidentName, SpouseName HAVING COUNT(*) > 1) "
       "THEN 'NO' ELSE 'YES' END AS verdict",
       U_ONLY, "uniqueness only: EXISTS (GROUP BY ... HAVING COUNT(*) > 1)",
       "uniqueness-only", "classroom"),
    _a("b2", "PK1", "foil",
       "SELECT CASE WHEN (SELECT COUNT(*) FROM PresidentMarriage) = "
       "(SELECT COUNT(*) FROM (SELECT DISTINCT PresidentName, SpouseName "
       "FROM PresidentMarriage) t) THEN 'YES' ELSE 'NO' END AS verdict",
       U_ONLY, "uniqueness only: COUNT(*) against COUNT of SELECT DISTINCT",
       "uniqueness-only", "classroom"),
    _a("b3", "PK1", "foil",
       "SELECT CASE WHEN COUNT(DISTINCT CONCAT(PresidentName, '|', SpouseName)) = COUNT(*) "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       U_ONLY, "uniqueness only: COUNT(DISTINCT CONCAT(...)) (CONCAT skips NULL)",
       "uniqueness-only", "classroom"),
    _a("c1", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM PresidentMarriage "
       "WHERE PresidentName = NULL OR SpouseName = NULL) "
       "OR EXISTS (SELECT 1 FROM PresidentMarriage "
       "GROUP BY PresidentName, SpouseName HAVING COUNT(*) > 1) "
       "THEN 'NO' ELSE 'YES' END AS verdict",
       U_ONLY, "uniqueness + nullity written as '= NULL' (EXISTS form)"),
    _a("c2", "PK1", "foil",
       "SELECT CASE WHEN COUNT(*) = COUNT(DISTINCT (PresidentName, SpouseName)) "
       "AND SUM(CASE WHEN PresidentName = NULL OR SpouseName = NULL THEN 1 ELSE 0 END) = 0 "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       U_ONLY, "uniqueness + nullity written as '= NULL' (SUM CASE form)"),
    _a("d1", "PK1", "foil",
       "SELECT CASE WHEN COUNT(DISTINCT (PresidentName, SpouseName)) = COUNT(*) "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       U_ONLY, "COUNT(DISTINCT (PresidentName, SpouseName)) = COUNT(*) only",
       "uniqueness-only", "classroom"),
    _a("e1", "PK1", "foil",
       "SELECT CASE WHEN COUNT(*) = COUNT(DISTINCT (PresidentName, SpouseName)) "
       "AND COUNT(*) FILTER (WHERE PresidentName IS NULL) = 0 "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       ["YES", "YES", "NO", "NO", "YES"], "uniqueness + nullity of PresidentName only"),
    _a("f1", "PK1", "foil", "SELECT 'NO' AS verdict", ALL_NO, "constant 'NO'",
       "constant", "assistant-devised loophole foil"),
    _a("f2", "PK1", "foil", "SELECT 'YES' AS verdict", ALL_YES, "constant 'YES'",
       "constant", "assistant-devised loophole foil"),
    _a("g1", "PK1", "correct",
       "SELECT CASE WHEN COUNT(DISTINCT PresidentName || '|' || SpouseName) = COUNT(*) "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       PK1_GOLD, "COUNT(DISTINCT a || '|' || b) = COUNT(*) ('||' turns a NULL key into NULL; "
       "accepted, OQ21)"),
    _a("h1", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM PresidentMarriage "
       "WHERE (PresidentName, SpouseName) IS NULL) "
       "OR EXISTS (SELECT 1 FROM PresidentMarriage "
       "GROUP BY PresidentName, SpouseName HAVING COUNT(*) > 1) "
       "THEN 'NO' ELSE 'YES' END AS verdict",
       U_ONLY, "row-constructor IS NULL (true only when every field is NULL) + uniqueness"),
    _a("i1", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM information_schema.table_constraints "
       "WHERE table_name = 'presidentmarriage' AND constraint_type = 'PRIMARY KEY') "
       "THEN 'YES' ELSE 'NO' END AS verdict",
       ALL_NO, "declared PRIMARY KEY lookup in information_schema.table_constraints",
       "catalog", "assistant-devised loophole foil"),
    _a("i2", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM information_schema.columns "
       "WHERE table_name = 'presidentmarriage' AND column_name IN ('presidentname', 'spousename') "
       "AND is_nullable = 'YES') THEN 'NO' ELSE 'YES' END AS verdict",
       ALL_NO, "is_nullable lookup in information_schema.columns",
       "catalog", "assistant-devised loophole foil"),
    _a("j1", "PK1", "foil",
       "SELECT CASE WHEN NOT EXISTS (SELECT 1 FROM PresidentMarriage "
       "WHERE PresidentName IS NULL OR SpouseName IS NULL) "
       "AND NOT EXISTS (SELECT 1 FROM PresidentMarriage "
       "GROUP BY PresidentName, SpouseName HAVING COUNT(*) > 1) "
       "AND (EXISTS (SELECT 1 FROM PresidentMarriage GROUP BY PresidentName HAVING COUNT(*) > 1) "
       "OR EXISTS (SELECT 1 FROM PresidentMarriage WHERE PresidentName IS NULL)) "
       "AND (EXISTS (SELECT 1 FROM PresidentMarriage GROUP BY SpouseName HAVING COUNT(*) > 1) "
       "OR EXISTS (SELECT 1 FROM PresidentMarriage WHERE SpouseName IS NULL)) "
       "THEN 'YES' ELSE 'NO' END AS verdict",
       ["NO", "NO", "NO", "NO", "YES"], "uniqueness + nullity + minimality (minimality is "
       "not asked)"),
    _a("k1", "PK1", "foil",
       "SELECT CASE WHEN COUNT(*) > 1 OR PresidentName IS NULL OR SpouseName IS NULL "
       "THEN 'NO' ELSE 'YES' END AS verdict FROM PresidentMarriage "
       "GROUP BY PresidentName, SpouseName",
       ["shape"] * 5, "one verdict per key group (many rows)"),
    _a("k2", "PK1", "foil",
       "SELECT (COUNT(*) = COUNT(DISTINCT (PresidentName, SpouseName)) "
       "AND COUNT(*) FILTER (WHERE PresidentName IS NULL OR SpouseName IS NULL) = 0) "
       "AS verdict FROM PresidentMarriage",
       ["False", "True", "False", "False", "True"], "right logic, boolean instead of 'YES'/'NO'"),
    _a("k3", "PK1", "foil",
       "SELECT CASE WHEN COUNT(DISTINCT PresidentName, SpouseName) = COUNT(*) "
       "AND COUNT(*) = COUNT(SpouseName) THEN 'YES' ELSE 'NO' END AS verdict "
       "FROM PresidentMarriage",
       ["error"] * 5, "MySQL-style COUNT(DISTINCT a, b) (error in PostgreSQL)"),
    _a("l1", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM PresidentMarriage "
       "WHERE PresidentName IS NULL OR SpouseName IS NULL) "
       "THEN 'NO' ELSE 'YES' END AS verdict",
       N_ONLY, "nullity only (no uniqueness test)", "nullity-only", "classroom"),
    _a("m1", "PK1", "foil",
       "SELECT CASE WHEN COUNT(DISTINCT PresidentName) = COUNT(*) "
       "AND COUNT(DISTINCT SpouseName) = COUNT(*) THEN 'YES' ELSE 'NO' END AS verdict "
       "FROM PresidentMarriage",
       ALL_NO, "reads the pair as two single-column keys"),
    # ---- 13 Oct multi-instance draft answers (16; item renamed F10-PK -> PK1)
    _a("pk_full", "PK1", "gold",
       f"SELECT CASE WHEN {PK_NULL_EXISTS} OR {PK_DUP_EXISTS} "
       f"THEN 'NO' ELSE 'YES' END AS verdict",
       PK1_GOLD, "gold: uniqueness + nullity"),
    _a("pk_full_agg", "PK1", "correct",
       "SELECT CASE WHEN COUNT(*) = COUNT(DISTINCT (PresidentName, SpouseName)) "
       "AND COUNT(*) = COUNT(*) FILTER (WHERE PresidentName IS NOT NULL "
       "AND SpouseName IS NOT NULL) THEN 'YES' ELSE 'NO' END AS verdict "
       "FROM PresidentMarriage",
       PK1_GOLD, "full check, aggregate form"),
    _a("pk_uniq_only", "PK1", "foil",
       f"SELECT CASE WHEN {PK_DUP_EXISTS} THEN 'NO' ELSE 'YES' END AS verdict",
       U_ONLY, "uniqueness only (classroom partial, verdict form)",
       "uniqueness-only", "classroom"),
    _a("pk_null_only", "PK1", "foil",
       f"SELECT CASE WHEN {PK_NULL_EXISTS} THEN 'NO' ELSE 'YES' END AS verdict",
       N_ONLY, "nullity only (classroom partial, verdict form)",
       "nullity-only", "classroom"),
    _a("pk_uniq_raw", "PK1", "foil",
       "SELECT PresidentName, SpouseName, COUNT(*) FROM PresidentMarriage "
       "GROUP BY PresidentName, SpouseName HAVING COUNT(*) > 1",
       ["shape"] * 5, "uniqueness only, classroom shape (list duplicated keys)",
       "uniqueness-only", "classroom"),
    _a("pk_null_raw", "PK1", "foil",
       "SELECT PresidentName, SpouseName FROM PresidentMarriage "
       "WHERE PresidentName IS NULL OR SpouseName IS NULL",
       ["shape"] * 5, "nullity only, classroom shape (list NULL keys)",
       "nullity-only", "classroom"),
    _a("pk_eq_null", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM PresidentMarriage "
       "WHERE PresidentName = NULL OR SpouseName = NULL) OR "
       f"{PK_DUP_EXISTS} THEN 'NO' ELSE 'YES' END AS verdict",
       U_ONLY, "full check but '= NULL' instead of IS NULL"),
    _a("pk_countdistinct_row", "PK1", "foil",
       "SELECT CASE WHEN COUNT(DISTINCT (PresidentName, SpouseName)) = COUNT(*) "
       "THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       U_ONLY, "COUNT(DISTINCT (a, b)) = COUNT(*) only", "uniqueness-only", "classroom"),
    _a("pk_const_yes", "PK1", "foil", "SELECT 'YES' AS verdict", ALL_YES, "constant YES",
       "constant", "assistant-devised loophole foil"),
    _a("pk_const_no", "PK1", "foil", "SELECT 'NO' AS verdict", ALL_NO, "constant NO",
       "constant", "assistant-devised loophole foil"),
    _a("pk_wholerow_dup", "PK1", "foil",
       f"SELECT CASE WHEN {PK_NULL_EXISTS} OR EXISTS (SELECT 1 FROM PresidentMarriage "
       "GROUP BY PresidentName, SpouseName, SpouseBirthDay, MarriageYear, "
       "MarriageStatus HAVING COUNT(*) > 1) THEN 'NO' ELSE 'YES' END AS verdict",
       N_ONLY, "nullity + duplicate WHOLE rows (not key values)"),
    _a("pk_null_one_col", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM PresidentMarriage "
       f"WHERE PresidentName IS NULL) OR {PK_DUP_EXISTS} "
       "THEN 'NO' ELSE 'YES' END AS verdict",
       ["YES", "YES", "NO", "NO", "YES"], "uniqueness + NULL test on PresidentName only"),
    _a("pk_concat_distinct", "PK1", "foil",
       "SELECT CASE WHEN COUNT(DISTINCT CONCAT(PresidentName, '|', SpouseName)) "
       "= COUNT(*) THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       U_ONLY, "COUNT(DISTINCT CONCAT(a, '|', b)) = COUNT(*) (CONCAT turns NULL into '')",
       "uniqueness-only", "classroom"),
    _a("pk_minimality", "PK1", "foil",
       f"SELECT CASE WHEN {PK_NULL_EXISTS} OR {PK_DUP_EXISTS} OR "
       "(SELECT COUNT(DISTINCT SpouseName) = COUNT(*) FROM PresidentMarriage) OR "
       "(SELECT COUNT(DISTINCT PresidentName) = COUNT(*) FROM PresidentMarriage) "
       "THEN 'NO' ELSE 'YES' END AS verdict",
       ["NO", "NO", "NO", "NO", "YES"], "full check + minimality (minimality is not asked)"),
    _a("pk_catalog", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM information_schema.table_constraints "
       "WHERE table_name = 'presidentmarriage' AND constraint_type = 'PRIMARY KEY') "
       "THEN 'YES' ELSE 'NO' END AS verdict",
       ALL_NO, "declared PRIMARY KEY lookup in information_schema",
       "catalog", "assistant-devised loophole foil"),
    _a("pk_pipe_distinct", "PK1", "correct",
       "SELECT CASE WHEN COUNT(DISTINCT PresidentName || '|' || SpouseName) "
       "= COUNT(*) THEN 'YES' ELSE 'NO' END AS verdict FROM PresidentMarriage",
       PK1_GOLD, "COUNT(DISTINCT a || '|' || b) = COUNT(*) (accepted, OQ21)"),
    # ---- 13 Oct post-hoc gaps of the three-instance design, registered foils here (3)
    _a("ph_null_spouse_only", "PK1", "foil",
       "SELECT CASE WHEN EXISTS (SELECT 1 FROM PresidentMarriage WHERE SpouseName IS NULL) "
       f"OR {PK_DUP_EXISTS} THEN 'NO' ELSE 'YES' END",
       ["NO", "YES", "NO", "YES", "YES"], "uniqueness + NULL test on SpouseName only"),
    _a("ph_uniq_spouse_alone", "PK1", "foil",
       f"SELECT CASE WHEN {PK_NULL_EXISTS} OR EXISTS (SELECT 1 FROM PresidentMarriage "
       "GROUP BY SpouseName HAVING COUNT(*) > 1) THEN 'NO' ELSE 'YES' END",
       ["NO", "YES", "NO", "NO", "NO"], "nullity + uniqueness of SpouseName alone"),
    _a("ph_uniq_president_alone", "PK1", "foil",
       f"SELECT CASE WHEN {PK_NULL_EXISTS} OR EXISTS (SELECT 1 FROM PresidentMarriage "
       "GROUP BY PresidentName HAVING COUNT(*) > 1) THEN 'NO' ELSE 'YES' END",
       ALL_NO, "nullity + uniqueness of PresidentName alone"),

    # ================================================================ FK1 (list the violating rows)
    _a("fk1_gold", "FK1", "gold",
       "SELECT p.PresidentName, p.PartyName FROM President p WHERE p.PartyName IS NOT NULL "
       "AND NOT EXISTS (SELECT 1 FROM Party pa WHERE pa.PartyName = p.PartyName)",
       [[], [], FK1_ORPHAN], "gold: non-NULL PartyName with no Party row"),
    _a("fk1_notin", "FK1", "correct",
       "SELECT PresidentName, PartyName FROM President "
       "WHERE PartyName NOT IN (SELECT PartyName FROM Party)",
       [[], [], FK1_ORPHAN], "NOT IN (Party.PartyName has no NULL; a NULL PartyName gives "
       "UNKNOWN)"),
    _a("fk1_leftjoin_guarded", "FK1", "correct",
       "SELECT p.PresidentName, p.PartyName FROM President p LEFT JOIN Party pa "
       "ON pa.PartyName = p.PartyName WHERE pa.PartyName IS NULL AND p.PartyName IS NOT NULL",
       [[], [], FK1_ORPHAN], "LEFT JOIN anti-join with the NULL guard"),
    _a("fk1_except_rows", "FK1", "correct",
       "SELECT PresidentName, PartyName FROM President WHERE PartyName IS NOT NULL "
       "EXCEPT SELECT p.PresidentName, p.PartyName FROM President p "
       "JOIN Party pa ON pa.PartyName = p.PartyName",
       [[], [], FK1_ORPHAN], "EXCEPT of the joined rows, NULL removed first"),
    _a("fk1_leftjoin_noguard", "FK1", "foil",
       "SELECT p.PresidentName, p.PartyName FROM President p LEFT JOIN Party pa "
       "ON pa.PartyName = p.PartyName WHERE pa.PartyName IS NULL",
       [[], FK1_NOPARTY, FK1_ORPHAN], "LEFT JOIN anti-join without the NULL guard (the NULL "
       "row is listed)", "", "derived from the instructor's answer key"),
    _a("fk1_notexists_noguard", "FK1", "foil",
       "SELECT p.PresidentName, p.PartyName FROM President p "
       "WHERE NOT EXISTS (SELECT 1 FROM Party pa WHERE pa.PartyName = p.PartyName)",
       [[], FK1_NOPARTY, FK1_ORPHAN], "NOT EXISTS without the NULL guard",
       "", "derived from the instructor's answer key"),
    _a("fk1_coalesce_notin", "FK1", "foil",
       "SELECT PresidentName, PartyName FROM President "
       "WHERE COALESCE(PartyName, '') NOT IN (SELECT PartyName FROM Party)",
       [[], FK1_NOPARTY, FK1_ORPHAN], "COALESCE(PartyName, '') NOT IN Party (NULL becomes a "
       "violation)"),
    _a("fk1_nullity_only", "FK1", "foil",
       "SELECT PresidentName, PartyName FROM President WHERE PartyName IS NULL",
       [[], FK1_NOPARTY, []], "nullity only (PK-style NULL test applied to the FK)"),
    _a("fk1_wrong_direction", "FK1", "foil",
       "SELECT pa.PartyName FROM Party pa "
       "WHERE NOT EXISTS (SELECT 1 FROM President p WHERE p.PartyName = pa.PartyName)",
       [FK2_GOLD, FK2_GOLD, FK2_GOLD], "wrong direction: parties that no president refers to"),
    _a("fk1_const_empty", "FK1", "foil",
       "SELECT PresidentName, PartyName FROM President WHERE 1 = 0",
       [[], [], []], "constant empty answer (right on the clean instances only)"),
    _a("fk1_select_star", "FK1", "foil",
       "SELECT * FROM President p WHERE p.PartyName IS NOT NULL "
       "AND NOT EXISTS (SELECT 1 FROM Party pa WHERE pa.PartyName = p.PartyName)",
       [[], [], "shape"], "right rows, every column of President (wrong projection)"),
    _a("fk1_dangling_values", "FK1", "foil",
       "SELECT DISTINCT p.PartyName FROM President p WHERE p.PartyName IS NOT NULL "
       "AND NOT EXISTS (SELECT 1 FROM Party pa WHERE pa.PartyName = p.PartyName)",
       [[], [], [["Know Nothing"]]], "dangling PartyName values only (one column)"),
    _a("fk1_except_values", "FK1", "foil",
       "SELECT PartyName FROM President EXCEPT SELECT PartyName FROM Party",
       [[], [[None]], [["Know Nothing"]]], "EXCEPT on values (keeps the NULL, one column)"),

    # ================================================================ FK2 (deletable parties, RESTRICT)
    _a("fk2_gold", "FK2", "gold",
       "SELECT pa.PartyName FROM Party pa "
       "WHERE NOT EXISTS (SELECT 1 FROM President p WHERE p.PartyName = pa.PartyName)",
       [FK2_GOLD, FK2_GOLD], "gold: parties with no president"),
    _a("fk2_except", "FK2", "correct",
       "SELECT PartyName FROM Party EXCEPT SELECT PartyName FROM President",
       [FK2_GOLD, FK2_GOLD], "set difference (a NULL on the right removes nothing)"),
    _a("fk2_notin_guarded", "FK2", "correct",
       "SELECT PartyName FROM Party WHERE PartyName NOT IN "
       "(SELECT PartyName FROM President WHERE PartyName IS NOT NULL)",
       [FK2_GOLD, FK2_GOLD], "NOT IN with the NULL guard in the subquery"),
    _a("fk2_leftjoin", "FK2", "correct",
       "SELECT pa.PartyName FROM Party pa LEFT JOIN President p "
       "ON p.PartyName = pa.PartyName WHERE p.PresidentName IS NULL",
       [FK2_GOLD, FK2_GOLD], "LEFT JOIN anti-join from Party"),
    _a("fk2_notin_trap", "FK2", "foil",
       "SELECT PartyName FROM Party WHERE PartyName NOT IN (SELECT PartyName FROM President)",
       [FK2_GOLD, []], "NOT IN trap: one NULL PartyName makes every NOT IN unknown",
       "", "derived from the instructor's answer key"),
    _a("fk2_fulljoin_trap", "FK2", "foil",
       "SELECT pa.PartyName FROM Party pa FULL JOIN President p "
       "ON p.PartyName = pa.PartyName WHERE p.PartyName IS NULL",
       [FK2_GOLD, [["Progressive"], ["Union"], [None]]],
       "FULL JOIN anti-join (the president with a NULL PartyName adds a NULL row)"),
    _a("fk2_inverted", "FK2", "foil",
       "SELECT DISTINCT pa.PartyName FROM Party pa JOIN President p "
       "ON p.PartyName = pa.PartyName",
       [{"rows": 7}, {"rows": 7}], "inverted: the parties that RESTRICT protects"),
]
