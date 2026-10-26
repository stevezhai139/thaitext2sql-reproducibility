"""
db_fingerprint.py -- read-only fingerprint, cell diff and comparison tool for the
k3 / k3n databases (replaces diff_k3_k3n.py; KST revision, Gate 0).

Nothing is written to any database: every session is read-only and only
SELECT / COPY ... TO STDOUT is used. Connections take libpq DSNs; there is no
default server (libpq defaults and PG* environment variables apply).

Every session runs SET DateStyle='ISO, MDY', TimeZone='UTC',
extra_float_digits=1 and client_encoding='UTF8' before COPY, so the COPY-text
hashes do not depend on the settings of the machine.

Subcommands
  fingerprint --dsn DSN --out FILE [--label TEXT] [--grader PATH | --no-selfcheck]
      one row per base table of schema public:
        rows                count(*)
        columns             name:type in ordinal order
        md5_order_free      md5 of the COPY-text lines sorted by code point
                            (same value as diff_k3_k3n.py; '-' for ecommerce1m)
        mi_md5              md5 of to_jsonb(row)::text sorted COLLATE "C" (the
                            mi_fingerprint of the grader; '-' for ecommerce1m)
        rowhash_md5         md5 of the sorted per-row md5(to_jsonb(row)::text)
                            (computed in the server; used for ecommerce1m)
        md5_physical_order  md5 of the COPY-text lines in ctid order
        md5_ctids           md5 of the ctid list in ctid order
        dml_counters        pg_stat_user_tables ins/upd/del/hot
      line 1 is '#meta<TAB>{json}' (server version, encoding, locale, settings,
      indexes, constraints, schema_md5, time in UTC+7). The server time zone
      is stored as its UTC offset only. No role name, time zone name, host
      name, user name or path is stored, not even as a hash (a hash of a short
      name can be confirmed by guessing).
      schema_md5 = md5 over the sorted schema objects outside the system
      schemas (schemas, relations, columns with type/not null/default/
      collation, constraints, indexes, triggers, policies, rules, views,
      functions), the settings, connection limit and privileges of the
      database, the privileges of schemas, relations, columns and functions
      (grantee as owner / PUBLIC / other), comments, and other objects created
      after initdb (types, operators, casts, collations, extensions, ...);
      SCHEMA_STMT is the single definition, also used by build_instances.py.
      Self-check: mi_md5 must equal mi_fingerprint() of the grader on the same
      database (default grader: ../grade_v13n.py next to this folder; skipped
      with a note when that file does not exist and --grader is not given).
      The sha256 of the written file is printed at the end.
  crosscheck A B
      compare two fingerprint files taken on different machines.
      PASS when rows, columns, md5_order_free and mi_md5 of party, president,
      presidentholding, presidentmarriage and ecommerce are equal, and columns
      of ecommerce1m are equal, and rows + rowhash_md5 of ecommerce1m are equal
      when both files have rows in ecommerce1m. Settings differences are WARN;
      md5_physical_order, md5_ctids and dml_counters are INFO.
  samefp A B
      strict comparison for the same machine (rebuild, k3 untouched): every
      value of every table row and every meta value except taken_at_ict.
  diff --ref DSN --new DSN --out-tsv FILE [--log FILE] [--expect-changes N]
       [--expect-tables t=n,...] [--csv-dir DIR]
      cell-by-cell comparison in ctid order; every difference must be a text
      cell 'None' in REF that is NULL in NEW. ecommerce1m is compared by
      columns, rows and rowhash_md5 only; whether its ctid sequence is the
      same is printed as an INFO line (not a criterion: the copy keeps the
      rows, and the physical order of a reference heap that was not filled
      by plain COPY can differ).
      --expect-changes 0 is the control mode (database built without the rule):
      PASS only when no cell differs.
  csvcheck --csv-dir DIR --expect FILE [--ddl FILE]
      sha256 of every entry of FILE (k3n_inputs.sha256): the course CSV files
      in DIR and setup_db.sql (--ddl, default ../setup_db.sql next to this
      folder, as in build_k3n.sh); prints basenames only; never opens
      GradeStudent.csv.

Fingerprint files are read strictly: the header must be the current one (or
the legacy diff_k3_k3n.py one) and a table may appear only once.

Exit status: 0 PASS / IDENTICAL, 1 FAIL / DIFFERENT, 2 usage or connection error.

Run with: python3 -I -B db_fingerprint.py <subcommand> ...
"""
import argparse
import csv
import datetime as dt
import hashlib
import importlib.util
import io
import json
import os
import re
import sys

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_GRADER = os.path.join(HERE, "..", "grade_v13n.py")
DEFAULT_DDL = os.path.join(HERE, "..", "setup_db.sql")

CORE_TABLES = ["party", "president", "presidentholding", "presidentmarriage", "ecommerce"]
BIG_TABLES = ["ecommerce1m"]
TABLE_ORDER = CORE_TABLES + BIG_TABLES
HEADER = ["table", "rows", "columns", "md5_order_free", "mi_md5", "rowhash_md5",
          "md5_physical_order", "md5_ctids", "dml_counters"]
LEGACY_HEADER = ["table", "rows", "md5_physical_order", "md5_order_free", "md5_ctids",
                 "dml_counters", "columns"]
SESSION_SETTINGS = (("DateStyle", "ISO, MDY"), ("TimeZone", "UTC"),
                    ("extra_float_digits", "1"))
SETTINGS_KEYS = ["server_version", "server_version_num", "encoding", "datcollate",
                 "datctype", "datlocprovider", "daticulocale", "datestyle_server",
                 "timezone_server", "indexes", "constraints", "schema_md5"]

# Schema digest: one line per schema object outside the system schemas, sorted
# in C order, md5 of the lines joined by '\n'; returns (md5, number of objects).
# Run inside a transaction with search_path = pg_catalog (SCHEMA_STMT) so that
# names printed by pg_get_*def() are always schema-qualified and the value does
# not depend on the session's search_path. No role name, no database name.
# Besides the schema objects it covers what can change how a query runs or what
# a catalog query sees, without changing data: settings of this database
# (ALTER DATABASE / ALTER ROLE ... IN DATABASE ... SET), connection limit,
# privileges of the database, schemas, relations, columns and functions
# (grantee written as owner / PUBLIC / other, never as a role name), comments
# on user objects, schemas and the database, and other user-created objects
# (types, operators, casts, collations, extensions, statistics objects, ...;
# oid >= 16384, i.e. created after initdb). States that every database created
# from template0 has (the public schema's default privileges and comment) give
# no line, so the digest of a database without such objects is the same as
# before these parts were added.
SCHEMA_DIGEST_SQL = r"""
WITH ns AS (
  SELECT n.oid, n.nspname FROM pg_catalog.pg_namespace n
  WHERE n.nspname NOT IN ('pg_catalog', 'information_schema', 'pg_toast')
    AND n.nspname NOT LIKE 'pg\_temp\_%' AND n.nspname NOT LIKE 'pg\_toast\_temp\_%'),
rel AS (
  SELECT c.oid, n.nspname, c.relname, c.relkind, c.relpersistence, c.relrowsecurity,
         c.relforcerowsecurity, c.relowner, c.relacl
  FROM pg_catalog.pg_class c JOIN ns n ON n.oid = c.relnamespace
  WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f', 'S')),
cur_db AS (
  SELECT d.oid, d.datdba, d.datacl, d.datconnlimit, d.datallowconn, d.datistemplate
  FROM pg_catalog.pg_database d WHERE d.datname = current_database()),
acl AS (
  SELECT 'database' AS kind, '-' AS name, d.datdba AS owner, x.grantee, x.privilege_type,
         x.is_grantable
  FROM cur_db d CROSS JOIN LATERAL pg_catalog.aclexplode(d.datacl) x WHERE d.datacl IS NOT NULL
  UNION ALL
  SELECT 'schema', quote_ident(n.nspname), n.nspowner, x.grantee, x.privilege_type, x.is_grantable
  FROM pg_catalog.pg_namespace n JOIN ns ON ns.oid = n.oid
  CROSS JOIN LATERAL pg_catalog.aclexplode(n.nspacl) x
  WHERE n.nspacl IS NOT NULL
    AND NOT (n.nspname = 'public'
             AND n.nspacl::text = '{pg_database_owner=UC/pg_database_owner,=U/pg_database_owner}')
  UNION ALL
  SELECT 'relation', format('%I.%I', r.nspname, r.relname), r.relowner, x.grantee,
         x.privilege_type, x.is_grantable
  FROM rel r CROSS JOIN LATERAL pg_catalog.aclexplode(r.relacl) x WHERE r.relacl IS NOT NULL
  UNION ALL
  SELECT 'column', format('%I.%I.%I', r.nspname, r.relname, a.attname), r.relowner, x.grantee,
         x.privilege_type, x.is_grantable
  FROM rel r
  JOIN pg_catalog.pg_attribute a ON a.attrelid = r.oid AND a.attnum > 0 AND NOT a.attisdropped
  CROSS JOIN LATERAL pg_catalog.aclexplode(a.attacl) x WHERE a.attacl IS NOT NULL
  UNION ALL
  SELECT 'function', p.oid::regprocedure::text, p.proowner, x.grantee,
         x.privilege_type, x.is_grantable
  FROM pg_catalog.pg_proc p JOIN ns n ON n.oid = p.pronamespace
  CROSS JOIN LATERAL pg_catalog.aclexplode(p.proacl) x WHERE p.proacl IS NOT NULL),
other_obj AS (
  SELECT 'pg_catalog.pg_type'::regclass AS classid, t.oid AS objid FROM pg_catalog.pg_type t
  WHERE t.oid >= 16384 AND t.typrelid = 0 AND t.typcategory <> 'A'
  UNION ALL SELECT 'pg_catalog.pg_operator'::regclass, oid FROM pg_catalog.pg_operator WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_cast'::regclass, oid FROM pg_catalog.pg_cast WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_collation'::regclass, oid FROM pg_catalog.pg_collation WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_conversion'::regclass, oid FROM pg_catalog.pg_conversion WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_ts_config'::regclass, oid FROM pg_catalog.pg_ts_config WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_ts_dict'::regclass, oid FROM pg_catalog.pg_ts_dict WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_ts_parser'::regclass, oid FROM pg_catalog.pg_ts_parser WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_ts_template'::regclass, oid FROM pg_catalog.pg_ts_template WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_opclass'::regclass, oid FROM pg_catalog.pg_opclass WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_opfamily'::regclass, oid FROM pg_catalog.pg_opfamily WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_am'::regclass, oid FROM pg_catalog.pg_am WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_language'::regclass, oid FROM pg_catalog.pg_language WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_extension'::regclass, oid FROM pg_catalog.pg_extension WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_transform'::regclass, oid FROM pg_catalog.pg_transform WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_event_trigger'::regclass, oid FROM pg_catalog.pg_event_trigger WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_foreign_data_wrapper'::regclass, oid FROM pg_catalog.pg_foreign_data_wrapper WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_foreign_server'::regclass, oid FROM pg_catalog.pg_foreign_server WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_publication'::regclass, oid FROM pg_catalog.pg_publication WHERE oid >= 16384
  UNION ALL SELECT 'pg_catalog.pg_statistic_ext'::regclass, oid FROM pg_catalog.pg_statistic_ext WHERE oid >= 16384),
obj AS (
  SELECT 'schema ' || quote_ident(nspname) AS x FROM ns
  UNION ALL
  SELECT format('relation %I.%I kind=%s persistence=%s rls=%s/%s', nspname, relname, relkind,
                relpersistence, relrowsecurity, relforcerowsecurity) FROM rel
  UNION ALL
  SELECT format('column %I.%I #%s %I %s notnull=%s default=%s collation=%s', r.nspname, r.relname,
                row_number() OVER (PARTITION BY a.attrelid ORDER BY a.attnum), a.attname,
                format_type(a.atttypid, a.atttypmod), a.attnotnull,
                COALESCE(pg_get_expr(d.adbin, d.adrelid), '-'), COALESCE(co.collname, '-'))
  FROM rel r
  JOIN pg_catalog.pg_attribute a ON a.attrelid = r.oid AND a.attnum > 0 AND NOT a.attisdropped
  LEFT JOIN pg_catalog.pg_attrdef d ON d.adrelid = a.attrelid AND d.adnum = a.attnum
  LEFT JOIN pg_catalog.pg_collation co ON co.oid = a.attcollation
  UNION ALL
  SELECT format('constraint %I.%I %I: %s', n.nspname, COALESCE(r.relname, '-'), con.conname,
                pg_get_constraintdef(con.oid))
  FROM pg_catalog.pg_constraint con JOIN ns n ON n.oid = con.connamespace
  LEFT JOIN pg_catalog.pg_class r ON r.oid = con.conrelid
  UNION ALL
  SELECT format('index %I.%I: %s', schemaname, indexname, indexdef)
  FROM pg_catalog.pg_indexes WHERE schemaname IN (SELECT nspname FROM ns)
  UNION ALL
  SELECT format('trigger %I.%I %I enabled=%s: %s', r.nspname, r.relname, t.tgname, t.tgenabled,
                pg_get_triggerdef(t.oid))
  FROM pg_catalog.pg_trigger t JOIN rel r ON r.oid = t.tgrelid WHERE NOT t.tgisinternal
  UNION ALL
  SELECT format('policy %I.%I %I %s %s roles=%s using=%s check=%s', schemaname, tablename,
                policyname, permissive, cmd, roles::text, COALESCE(qual, '-'),
                COALESCE(with_check, '-'))
  FROM pg_catalog.pg_policies WHERE schemaname IN (SELECT nspname FROM ns)
  UNION ALL
  SELECT format('rule %I.%I %I: %s', schemaname, tablename, rulename, definition)
  FROM pg_catalog.pg_rules WHERE schemaname IN (SELECT nspname FROM ns)
  UNION ALL
  SELECT format('view %I.%I: %s', nspname, relname, pg_get_viewdef(oid)) FROM rel
  WHERE relkind IN ('v', 'm')
  UNION ALL
  SELECT format('function %I.%s: %s', n.nspname, p.oid::regprocedure,
                md5(COALESCE(p.prosrc, '') || '|' || pg_get_function_result(p.oid)))
  FROM pg_catalog.pg_proc p JOIN ns n ON n.oid = p.pronamespace
  UNION ALL
  SELECT format('dbsetting %s %s', CASE WHEN s.setrole = 0 THEN 'all-roles' ELSE 'one-role' END, c)
  FROM pg_catalog.pg_db_role_setting s JOIN cur_db d ON d.oid = s.setdatabase
  CROSS JOIN LATERAL unnest(s.setconfig) c
  UNION ALL
  SELECT format('database connlimit=%s allowconn=%s istemplate=%s', datconnlimit, datallowconn,
                datistemplate)
  FROM cur_db WHERE datconnlimit <> -1 OR NOT datallowconn OR datistemplate
  UNION ALL
  SELECT format('acl %s %s %s %s%s', kind, name,
                CASE WHEN grantee = 0 THEN 'PUBLIC' WHEN grantee = owner THEN 'owner' ELSE 'other' END,
                privilege_type, CASE WHEN is_grantable THEN ' grantable' ELSE '' END)
  FROM acl
  UNION ALL
  SELECT format('comment %s: %s', pg_describe_object(d.classoid, d.objoid, d.objsubid), d.description)
  FROM pg_catalog.pg_description d WHERE d.objoid >= 16384
  UNION ALL
  SELECT format('comment schema %I: %s', n.nspname, d.description)
  FROM pg_catalog.pg_description d JOIN ns n ON n.oid = d.objoid
  WHERE d.classoid = 'pg_catalog.pg_namespace'::regclass AND d.objoid < 16384
    AND NOT (n.nspname = 'public' AND d.description = 'standard public schema')
  UNION ALL
  SELECT format('comment database: %s', s.description)
  FROM pg_catalog.pg_shdescription s JOIN cur_db d ON d.oid = s.objoid
  WHERE s.classoid = 'pg_catalog.pg_database'::regclass
  UNION ALL
  SELECT format('object %s', pg_describe_object(classid, objid, 0)) FROM other_obj)
SELECT md5(COALESCE(string_agg(x, E'\n' ORDER BY x COLLATE "C"), '')), count(*) FROM obj
"""
# for an engine that runs each statement inside a transaction and rolls back
# (grade_v13n.make_engine): the SET LOCAL ends with that transaction
SCHEMA_STMT = "SET LOCAL search_path = pg_catalog; " + SCHEMA_DIGEST_SQL
TABLE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
TEXT_TYPES = {"text", "character varying", "character"}
RULE_TOKEN = "None"
NULLISH = {"none", "null", "n/a", "na", "nil", "-", "--", "?", ""}
CSV_OF = {
    "president": "President.csv",
    "party": "Party.csv",
    "presidentmarriage": "PresidentMarriage.csv",
    "presidentholding": "PresidentHolding.csv",
    "ecommerce": "Ecommerce_Dataset.csv",
}
ID_COLS = {
    "presidentholding": ["presidentname", "yearholding"],
    "presidentmarriage": ["presidentname"],
    "president": ["presidentname"],
}
ICT = dt.timezone(dt.timedelta(hours=7))
NEVER_READ = {"gradestudent.csv"}


def die(msg, code=2):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(code)


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def now_ict():
    return dt.datetime.now(ICT).replace(microsecond=0).isoformat()


# ---------------------------------------------------------------- database access
class DB:
    """one read-only session with fixed output settings"""

    def __init__(self, dsn):
        try:
            import psycopg2
        except ImportError:
            die("psycopg2 is not importable by this python")
        try:
            self.conn = psycopg2.connect(dsn)
        except Exception as e:  # noqa: BLE001
            die(f"cannot connect ({type(e).__name__})")
        self.conn.set_session(readonly=True, autocommit=True)
        self.conn.set_client_encoding("UTF8")
        self.dbname = self.conn.info.dbname
        self.datestyle_server = self.one("SELECT current_setting('DateStyle')")
        secs = int(self.one("SELECT EXTRACT(TIMEZONE FROM now())"))
        sign = "+" if secs >= 0 else "-"
        hh, mm = divmod(abs(secs) // 60, 60)
        # the zone name can name a city: keep only the UTC offset
        self.timezone_server = f"UTC{sign}{hh:02d}:{mm:02d}"
        with self.conn.cursor() as cur:
            for k, v in SESSION_SETTINGS:
                cur.execute("SELECT set_config(%s, %s, false)", (k, v))

    def schema_digest(self):
        """(md5, number of objects) of SCHEMA_DIGEST_SQL with search_path = pg_catalog"""
        with self.conn.cursor() as cur:
            cur.execute("BEGIN READ ONLY")
            try:
                cur.execute(SCHEMA_STMT)
                r = cur.fetchone()
            finally:
                cur.execute("ROLLBACK")
        return r[0], int(r[1])

    def all(self, sql, args=None):
        with self.conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    def one(self, sql, args=None):
        return self.all(sql, args)[0][0]

    def copy_text(self, sql):
        """COPY (sql) TO STDOUT as one str"""
        buf = io.BytesIO()
        with self.conn.cursor() as cur:
            cur.copy_expert(f"COPY ({sql}) TO STDOUT", buf)
        return buf.getvalue().decode("utf-8")

    def copy_md5(self, sql):
        """md5 of the COPY text of (sql) without the final newline (streamed)"""
        w = _Md5Writer()
        with self.conn.cursor() as cur:
            cur.copy_expert(f"COPY ({sql}) TO STDOUT", w)
        return w.hexdigest()

    def close(self):
        self.conn.close()


class _Md5Writer:
    """file-like sink: md5 of all bytes except a final '\\n' (the join of lines)"""

    def __init__(self):
        self.h = hashlib.md5()
        self.pending = b""

    def write(self, data):
        if isinstance(data, str):
            data = data.encode("utf-8")
        if not data:
            return 0
        self.h.update(self.pending)
        self.h.update(data[:-1])
        self.pending = data[-1:]
        return len(data)

    def hexdigest(self):
        if self.pending and self.pending != b"\n":
            self.h.update(self.pending)
        return self.h.hexdigest()


def q_ident(t):
    if not TABLE_RE.match(t):
        die(f"unexpected table name {t!r}")
    return '"' + t + '"'


def list_tables(db):
    names = [r[0] for r in db.all(
        "SELECT table_name FROM information_schema.tables "
        "WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")]
    known = [t for t in TABLE_ORDER if t in names]
    return known + sorted(t for t in names if t not in TABLE_ORDER)


def table_columns(db, t):
    return [(c, ty) for c, ty in db.all(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'public' AND table_name = %s ORDER BY ordinal_position", (t,))]


def mi_md5_sql(t):
    return (f"SELECT md5(COALESCE(string_agg(to_jsonb(r)::text, E'\\n' "
            f"ORDER BY to_jsonb(r)::text COLLATE \"C\"), '')) FROM public.{q_ident(t)} r")


def rowhash_sql(t):
    return (f"SELECT md5(COALESCE(string_agg(h, E'\\n' ORDER BY h COLLATE \"C\"), '')) "
            f"FROM (SELECT md5(to_jsonb(r)::text) AS h FROM public.{q_ident(t)} r) s")


def ctids_sql(t):
    return (f"SELECT md5(COALESCE(string_agg(x.ctid::text, E'\\n' ORDER BY x.ctid), '')) "
            f"FROM public.{q_ident(t)} x")


def copy_lines(text):
    """COPY text output -> list of lines (an empty line is a row, e.g. one '' cell)"""
    if text == "":
        return []
    if not text.endswith("\n"):
        die("unexpected COPY output (no final newline)")
    return text[:-1].split("\n")


def dml_counters(db):
    out = {}
    for rel, ins, upd, dele, hot in db.all(
            "SELECT relname, n_tup_ins, n_tup_upd, n_tup_del, n_tup_hot_upd "
            "FROM pg_stat_user_tables WHERE schemaname = 'public'"):
        out[rel] = f"ins={ins} upd={upd} del={dele} hot={hot}"
    return out


def db_meta(db):
    r = db.all(
        "SELECT pg_encoding_to_char(encoding), datcollate, datctype, datlocprovider, "
        "COALESCE(daticulocale, '') "
        "FROM pg_database WHERE datname = current_database()")[0]
    schema_md5, schema_objects = db.schema_digest()
    meta = {
        "dbname": db.dbname,
        "server_version": db.one("SELECT version()"),
        "server_version_num": db.one("SELECT current_setting('server_version_num')"),
        "encoding": r[0], "datcollate": r[1], "datctype": r[2],
        "datlocprovider": r[3], "daticulocale": r[4],
        "datestyle_server": db.datestyle_server,
        "timezone_server": db.timezone_server,
        "schema_md5": schema_md5,
        "schema_objects": schema_objects,
        "session_datestyle": "ISO, MDY",
        "session_timezone": "UTC",
        "indexes": [x[0] for x in db.all(
            "SELECT tablename || '.' || indexname || ': ' || indexdef FROM pg_indexes "
            "WHERE schemaname = 'public' ORDER BY 1")],
        "constraints": [x[0] for x in db.all(
            "SELECT conrelid::regclass::text || '.' || conname || ': ' || "
            "pg_get_constraintdef(oid) FROM pg_constraint "
            "WHERE connamespace = 'public'::regnamespace ORDER BY 1")],
    }
    return meta


def fingerprint_db(db):
    stats = dml_counters(db)
    rows = {}
    for t in list_tables(db):
        qi = q_ident(t)
        cols = table_columns(db, t)
        n = db.one(f"SELECT count(*) FROM public.{qi}")
        big = t in BIG_TABLES
        if big:
            order_free = "-"
            mi = "-"
        else:
            lines = copy_lines(db.copy_text(f"SELECT x.* FROM public.{qi} x ORDER BY x.ctid"))
            if len(lines) != n:
                die(f"{t}: COPY gave {len(lines)} lines for {n} rows")
            order_free = hashlib.md5("\n".join(sorted(lines)).encode("utf-8")).hexdigest()
            mi = db.one(mi_md5_sql(t))
        rows[t] = {
            "rows": str(n),
            "columns": ",".join(f"{c}:{ty}" for c, ty in cols),
            "md5_order_free": order_free,
            "mi_md5": mi,
            "rowhash_md5": db.one(rowhash_sql(t)),
            "md5_physical_order": db.copy_md5(f"SELECT x.* FROM public.{qi} x ORDER BY x.ctid"),
            "md5_ctids": db.one(ctids_sql(t)),
            "dml_counters": stats.get(t, ""),
        }
    return rows


def load_grader(path):
    spec = importlib.util.spec_from_file_location("grader_for_selfcheck", path)
    if spec is None or spec.loader is None:
        die(f"cannot load grader {os.path.basename(path)}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    for name in ("make_engine", "mi_fingerprint"):
        if not hasattr(mod, name):
            die(f"grader {os.path.basename(path)} has no {name}()")
    return mod


def fp_pair(v):
    """mi_fingerprint value -> (rows, md5); accepts {'rows','md5'} or [rows, md5]"""
    if isinstance(v, dict):
        return int(v["rows"]), v["md5"]
    return int(v[0]), v[1]


def selfcheck(dsn, rows, grader_path):
    g = load_grader(grader_path)
    q = g.make_engine(dsn)
    tables = [t for t in rows if rows[t]["mi_md5"] != "-"]
    got = g.mi_fingerprint(q, tables)
    bad = []
    for t in tables:
        n, h = fp_pair(got[t])
        if n != int(rows[t]["rows"]) or h != rows[t]["mi_md5"]:
            bad.append(t)
    return tables, bad


# ---------------------------------------------------------------- files
def write_fp(path, meta, rows):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        f.write("#meta\t" + json.dumps(meta, sort_keys=True, ensure_ascii=False) + "\n")
        f.write("\t".join(HEADER) + "\n")
        for t, r in rows.items():
            f.write("\t".join([t] + [r[k] for k in HEADER[1:]]) + "\n")


def read_fp(path):
    """-> (meta, rows); rows[table] = {column: value}. Reads the legacy
    diff_k3_k3n.py format too (meta['legacy'] = True, no mi_md5/rowhash_md5)."""
    try:
        with open(path, encoding="utf-8", newline="") as f:
            lines = f.read().split("\n")
    except OSError as e:
        die(f"cannot read {os.path.basename(path)} ({type(e).__name__})")
    lines = [ln for ln in lines if ln != ""]
    if len(lines) < 2:
        die(f"{os.path.basename(path)}: not a fingerprint file")
    if lines[0].startswith("#meta\t"):
        try:
            meta = json.loads(lines[0][len("#meta\t"):])
        except ValueError:
            die(f"{os.path.basename(path)}: meta line is not valid JSON")
        if not isinstance(meta, dict):
            die(f"{os.path.basename(path)}: meta line is not a JSON object")
        meta["legacy"] = False
    elif lines[0].startswith("# "):
        first = next(csv.reader([lines[0]], delimiter="\t"))
        meta = {"legacy": True,
                "settings_legacy": first[first.index("settings") + 1] if "settings" in first else ""}
    else:
        die(f"{os.path.basename(path)}: unknown fingerprint format")
    header = lines[1].split("\t")
    if header != (LEGACY_HEADER if meta["legacy"] else HEADER):
        die(f"{os.path.basename(path)}: bad header (not the db_fingerprint.py "
            f"{'legacy ' if meta['legacy'] else ''}format)")
    rows = {}
    for ln in lines[2:]:
        parts = ln.split("\t")
        if len(parts) != len(header):
            die(f"{os.path.basename(path)}: bad row width")
        if parts[0] in rows:
            die(f"{os.path.basename(path)}: table {parts[0]} listed twice")
        rows[parts[0]] = dict(zip(header[1:], parts[1:]))
    return meta, rows


# ---------------------------------------------------------------- subcommands
def cmd_fingerprint(a):
    db = DB(a.dsn)
    meta = db_meta(db)
    rows = fingerprint_db(db)
    db.close()
    meta["tool_sha256"] = sha256_file(os.path.abspath(__file__))
    meta["taken_at_ict"] = now_ict()
    if a.label:
        meta["label"] = a.label
    status = 0
    note = ""
    if not a.no_selfcheck:
        gpath = a.grader or DEFAULT_GRADER
        if not os.path.isfile(gpath):
            if a.grader:
                die(f"grader not found: {os.path.basename(gpath)}")
            note = "self-check skipped (grade_v13n.py not found next to db/)"
        else:
            tables, bad = selfcheck(a.dsn, rows, gpath)
            if bad:
                note = "SELF-CHECK FAIL: mi_md5 differs from mi_fingerprint() for " + ",".join(bad)
                status = 1
            else:
                note = f"self-check OK: mi_md5 = mi_fingerprint() of the grader ({len(tables)} tables)"
    write_fp(a.out, meta, rows)
    print(f"fingerprint {meta['dbname']}: {len(rows)} tables -> {os.path.basename(a.out)}")
    print(f"  server {meta['server_version_num']}, encoding {meta['encoding']}, "
          f"collate {meta['datcollate']}, ctype {meta['datctype']}, "
          f"provider {meta['datlocprovider']}, DateStyle(server) {meta['datestyle_server']}")
    print(f"  schema_md5 {meta['schema_md5']} ({meta['schema_objects']} objects), "
          f"{len(meta['indexes'])} indexes, {len(meta['constraints'])} constraints")
    for t, r in rows.items():
        print(f"  {t:18s} rows={r['rows']:>8s} md5_order_free={r['md5_order_free'][:12]} "
              f"mi_md5={r['mi_md5'][:12]} rowhash={r['rowhash_md5'][:12]}")
    if note:
        print("  " + note)
    print(f"  sha256 {os.path.basename(a.out)} = {sha256_file(a.out)}")
    sys.exit(status)


def _cmp_settings(ma, mb, out):
    if ma.get("legacy") or mb.get("legacy"):
        sa = ma.get("settings_legacy") or "|".join(
            str(ma.get(k, "")) for k in ("encoding", "datcollate", "datctype"))
        sb = mb.get("settings_legacy") or "|".join(
            str(mb.get(k, "")) for k in ("encoding", "datcollate", "datctype"))
        out.append(("WARN", f"legacy fingerprint file: settings A={sa} B={sb}"))
        return
    for k in SETTINGS_KEYS:
        if ma.get(k) != mb.get(k):
            va, vb = ma.get(k), mb.get(k)
            if isinstance(va, list) or isinstance(vb, list):
                va = f"{len(va or [])} entries"
                vb = f"{len(vb or [])} entries"
            out.append(("WARN", f"setting {k}: A={va} B={vb}"))
    if ma.get("dbname") != mb.get("dbname"):
        out.append(("INFO", f"dbname A={ma.get('dbname')} B={mb.get('dbname')}"))


def crosscheck(pa, pb):
    """-> (ok, messages)"""
    ma, A = read_fp(pa)
    mb, B = read_fp(pb)
    msgs = []
    ok = True
    _cmp_settings(ma, mb, msgs)
    legacy = ma.get("legacy") or mb.get("legacy")
    for t in CORE_TABLES:
        if t not in A or t not in B:
            msgs.append(("FAIL", f"{t}: missing in {'A' if t not in A else 'B'}"))
            ok = False
            continue
        keys = ["rows", "columns", "md5_order_free"] + ([] if legacy else ["mi_md5"])
        for k in keys:
            if A[t].get(k) != B[t].get(k):
                msgs.append(("FAIL", f"{t}: {k} A={A[t].get(k)} B={B[t].get(k)}"))
                ok = False
        if legacy:
            msgs.append(("WARN", f"{t}: mi_md5 not compared (legacy file)"))
        for k in ("md5_physical_order", "md5_ctids", "dml_counters"):
            if A[t].get(k) != B[t].get(k):
                msgs.append(("INFO", f"{t}: {k} differs (not a criterion)"))
    for t in BIG_TABLES:
        if t not in A or t not in B:
            msgs.append(("FAIL", f"{t}: missing in {'A' if t not in A else 'B'}"))
            ok = False
            continue
        if A[t].get("columns") != B[t].get("columns"):
            msgs.append(("FAIL", f"{t}: columns differ"))
            ok = False
        na, nb = int(A[t]["rows"]), int(B[t]["rows"])
        if na > 0 and nb > 0:
            if na != nb:
                msgs.append(("FAIL", f"{t}: rows A={na} B={nb}"))
                ok = False
            if legacy:
                msgs.append(("WARN", f"{t}: rowhash_md5 not compared (legacy file)"))
            elif A[t].get("rowhash_md5") != B[t].get("rowhash_md5"):
                msgs.append(("FAIL", f"{t}: rowhash_md5 A={A[t].get('rowhash_md5')} "
                                     f"B={B[t].get('rowhash_md5')}"))
                ok = False
        elif na != nb:
            msgs.append(("WARN", f"{t}: rows A={na} B={nb}; not compared because one side "
                                 f"has no rows"))
        for k in ("md5_physical_order", "md5_ctids", "dml_counters"):
            if A[t].get(k) != B[t].get(k):
                msgs.append(("INFO", f"{t}: {k} differs (not a criterion)"))
    extra = sorted((set(A) | set(B)) - set(TABLE_ORDER))
    for t in extra:
        if A.get(t) != B.get(t):
            msgs.append(("WARN", f"extra table {t}: present or different on one side only"))
    return ok, msgs


def cmd_crosscheck(a):
    ok, msgs = crosscheck(a.a, a.b)
    print(f"crosscheck {os.path.basename(a.a)} vs {os.path.basename(a.b)}")
    for level, m in msgs:
        print(f"  {level}: {m}")
    print("RESULT: PASS" if ok else "RESULT: FAIL")
    sys.exit(0 if ok else 1)


def samefp(pa, pb):
    ma, A = read_fp(pa)
    mb, B = read_fp(pb)
    diffs = []
    for k in sorted((set(ma) | set(mb)) - {"taken_at_ict"}):
        if ma.get(k) != mb.get(k):
            diffs.append(f"meta {k}: {ma.get(k)} vs {mb.get(k)}")
    for t in sorted(set(A) | set(B)):
        if A.get(t) != B.get(t):
            ra, rb = A.get(t) or {}, B.get(t) or {}
            for k in sorted(set(ra) | set(rb)):
                if ra.get(k) != rb.get(k):
                    diffs.append(f"{t}: {k} {ra.get(k)} vs {rb.get(k)}")
    return diffs


def cmd_samefp(a):
    diffs = samefp(a.a, a.b)
    print(f"fingerprint {os.path.basename(a.a)} vs {os.path.basename(a.b)}: "
          f"{'IDENTICAL' if not diffs else 'DIFFERENT'}")
    for d in diffs:
        print("  " + d)
    sys.exit(0 if not diffs else 1)


def unescape(tok):
    """COPY text format: \\N = NULL; basic backslash escapes"""
    if tok == r"\N":
        return None
    if "\\" not in tok:
        return tok
    m = {"\\": "\\", "t": "\t", "n": "\n", "r": "\r", "b": "\b", "f": "\f", "v": "\v"}
    out, i = [], 0
    while i < len(tok):
        c = tok[i]
        if c == "\\" and i + 1 < len(tok) and tok[i + 1] in m:
            out.append(m[tok[i + 1]])
            i += 2
        else:
            out.append(c)
            i += 1
    return "".join(out)


def rows_with_ctid(db, t):
    raw = db.copy_text(f"SELECT x.ctid::text AS ctid_txt, x.* FROM public.{q_ident(t)} AS x "
                       f"ORDER BY x.ctid")
    res = []
    for line in copy_lines(raw):
        parts = line.split("\t")
        res.append((parts[0], parts[1:]))
    return res


def show(v):
    return "NULL" if v is None else "'" + v + "'"


def csv_lines(path):
    """record index (0-based, header excluded) -> (physical line number, fields)"""
    out = []
    with open(path, newline="", encoding="utf-8-sig") as f:
        rd = csv.reader(f)
        next(rd)
        start = rd.line_num + 1
        for rec in rd:
            out.append((start, rec))
            start = rd.line_num + 1
    return out


def db_settings_line(db):
    r = db.all("SELECT pg_encoding_to_char(encoding), datcollate, datctype, datlocprovider, "
               "COALESCE(daticulocale, '') FROM pg_database WHERE datname = current_database()")[0]
    return "|".join(str(x) for x in r)


def cmd_diff(a):
    lines = []

    def say(s=""):
        print(s)
        lines.append(s)

    R, N = DB(a.ref), DB(a.new)
    control = a.expect_changes == 0
    say(f"# cell-by-cell diff: ref={R.dbname} new={N.dbname} "
        f"(mode: {'control, no rule' if control else 'rule None->NULL'})")
    sr, sn = db_settings_line(R), db_settings_line(N)
    say(f"settings {R.dbname}: {sr}")
    say(f"settings {N.dbname}: {sn}")
    ok = True
    if sr != sn:
        say("FAIL: encoding/collation/provider differ")
        ok = False
    tr, tn = list_tables(R), list_tables(N)
    say(f"tables {R.dbname}: {','.join(tr)}")
    say(f"tables {N.dbname}: {','.join(tn)}")
    if sorted(tr) != sorted(tn):
        say("FAIL: table sets differ")
        ok = False
    expect = {}
    if a.expect_tables:
        for kv in a.expect_tables.split(","):
            k, v = kv.split("=")
            expect[k.strip().lower()] = int(v)

    diffs = []
    none_left_new = 0
    none_total_ref = 0
    nullish_other = []
    order_note = []
    big_note = []
    for t in tr:
        if t not in tn:
            continue
        cr, cn = table_columns(R, t), table_columns(N, t)
        if cr != cn:
            say(f"FAIL {t}: column list/type differ")
            ok = False
            continue
        if t in BIG_TABLES:
            nr = R.one(f"SELECT count(*) FROM public.{q_ident(t)}")
            nn = N.one(f"SELECT count(*) FROM public.{q_ident(t)}")
            hr, hn = R.one(rowhash_sql(t)), N.one(rowhash_sql(t))
            line = f"{t}: rows {R.dbname}={nr} {N.dbname}={nn} (compared by rows + rowhash_md5)"
            if t in expect:
                line += f" expected={expect[t]}"
                if not (nr == nn == expect[t]):
                    ok = False
                    line += "  FAIL"
            if nr != nn or hr != hn:
                ok = False
                line += "  FAIL (rows or rowhash differ)"
            say(line)
            same = R.one(ctids_sql(t)) == N.one(ctids_sql(t))
            big_note.append(f"INFO {t}: ctid sequence identical = {same} (not a criterion; {t} is "
                            f"compared by rows + rowhash_md5, its physical order may differ)")
            continue
        rr, rn = rows_with_ctid(R, t), rows_with_ctid(N, t)
        line = f"{t}: rows {R.dbname}={len(rr)} {N.dbname}={len(rn)}"
        if t in expect:
            line += f" expected={expect[t]}"
            if not (len(rr) == len(rn) == expect[t]):
                ok = False
                line += "  FAIL"
        elif len(rr) != len(rn):
            ok = False
            line += "  FAIL"
        same_ctids = [c for c, _ in rr] == [c for c, _ in rn]
        order_note.append(f"{t}: ctid sequence identical = {same_ctids}")
        say(line)
        if len(rr) != len(rn):
            continue
        textcols = {i for i, (_, ty) in enumerate(cr) if ty in TEXT_TYPES}
        csvmap = None
        if a.csv_dir and t in CSV_OF:
            p = os.path.join(a.csv_dir, CSV_OF[t])
            if os.path.exists(p):
                csvmap = csv_lines(p)
                if len(csvmap) != len(rr):
                    say(f"WARN {t}: CSV records {len(csvmap)} != rows {len(rr)}")
                    csvmap = None
        names = [c for c, _ in cr]
        idc = [names.index(c) for c in ID_COLS.get(t, [names[0]])]
        for i, ((ctr, vr), (ctn, vn)) in enumerate(zip(rr, rn)):
            for j, (tokr, tokn) in enumerate(zip(vr, vn)):
                xr, xn = unescape(tokr), unescape(tokn)
                if j in textcols:
                    if xr == RULE_TOKEN:
                        none_total_ref += 1
                    if xn == RULE_TOKEN:
                        none_left_new += 1
                    if xr is not None and xr != RULE_TOKEN and xr.strip().lower() in NULLISH:
                        nullish_other.append((t, i + 1, names[j], xr))
                if tokr != tokn:
                    ident = " | ".join(show(unescape(vr[k])) for k in idc)
                    csv_line = csvmap[i][0] if csvmap else ""
                    csv_field = (show(csvmap[i][1][j]) if csvmap and j < len(csvmap[i][1])
                                 else "")
                    rule_ok = (j in textcols and xr == RULE_TOKEN and xn is None)
                    diffs.append([t, i + 1, csv_line, ctr, ctn, ident, names[j], cr[j][1],
                                  show(xr), show(xn), csv_field,
                                  "yes" if rule_ok else "NO"])
    R.close()
    N.close()
    say("")
    say(f"cells that differ: {len(diffs)}")
    say(f"'None' text cells in {R.dbname}: {none_total_ref}; "
        f"'None' text cells left in {N.dbname}: {none_left_new}")
    if control:
        if diffs:
            ok = False
            say("FAIL: control mode expects no differing cell")
    else:
        bad = [d for d in diffs if d[-1] != "yes"]
        if bad:
            ok = False
            say(f"FAIL: {len(bad)} differing cells are not explained by the rule")
        if none_left_new:
            ok = False
            say("FAIL: rule not applied to every 'None' cell")
        if len(diffs) != none_total_ref:
            ok = False
            say("FAIL: number of differing cells != number of 'None' cells in ref")
        if a.expect_changes is not None and len(diffs) != a.expect_changes:
            ok = False
            say(f"FAIL: expected {a.expect_changes} changed cells")
    say(f"other null-like text values in {R.dbname} (not touched by the rule): "
        f"{len(nullish_other)}")
    for x in nullish_other[:20]:
        say(f"  {x}")
    say("physical order of the cell-compared tables (the positional compare above already "
        "requires the same row order):")
    for n in order_note:
        say("  " + n)
    for n in big_note:
        say(n)
    say("")
    # column names kept from diff_k3_k3n.py (k3 = --ref, k3n = --new)
    hdr = ["table", "row_ordinal", "csv_line", "ctid_k3", "ctid_k3n", "row_id",
           "column", "type", "k3_value", "k3n_value", "csv_field", "explained_by_rule"]
    say("\t".join(hdr))
    for d in diffs:
        say("\t".join(str(x) for x in d))
    os.makedirs(os.path.dirname(os.path.abspath(a.out_tsv)), exist_ok=True)
    with open(a.out_tsv, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter="\t", lineterminator="\n")
        w.writerow(hdr)
        w.writerows(diffs)
    say("")
    say("RESULT: PASS" if ok else "RESULT: FAIL")
    if a.log:
        os.makedirs(os.path.dirname(os.path.abspath(a.log)), exist_ok=True)
        with open(a.log, "w", encoding="utf-8") as f:
            f.write("\n".join(lines) + "\n")
    sys.exit(0 if ok else 1)


def read_expect(path):
    """k3n_inputs.sha256 -> [(sha256, basename)]"""
    out = []
    with open(path, encoding="utf-8") as f:
        for ln in f:
            ln = ln.strip()
            if not ln or ln.startswith("#"):
                continue
            m = re.match(r"^([0-9a-f]{64})\s+\*?(\S+)$", ln)
            if not m:
                die(f"{os.path.basename(path)}: bad line")
            name = m.group(2)
            if os.path.basename(name) != name:
                die(f"{os.path.basename(path)}: entries must be basenames")
            out.append((m.group(1), name))
    return out


def cmd_csvcheck(a):
    entries = read_expect(a.expect)
    ddl = a.ddl or DEFAULT_DDL
    ok = True
    n_csv = 0
    print(f"csvcheck against {os.path.basename(a.expect)}")
    for want, name in entries:
        if name.lower() in NEVER_READ:
            die(f"{name} must not be listed")
        if name.lower().endswith(".csv"):
            p = os.path.join(a.csv_dir, name)
        elif name == "setup_db.sql":
            p = ddl
        else:
            print(f"  UNKNOWN  {name} (only course CSV files and setup_db.sql may be listed)")
            ok = False
            continue
        if not os.path.isfile(p):
            print(f"  MISSING  {name}" + ("" if a.ddl or name != "setup_db.sql" else
                                         " (expected at ../setup_db.sql next to db/; pass --ddl)"))
            ok = False
            continue
        got = sha256_file(p)
        n_csv += name.lower().endswith(".csv")
        status = "ok" if got == want else "MISMATCH"
        if got != want:
            ok = False
        print(f"  {status:8s} {name}  {got[:16]}... (expected {want[:16]}...)")
    if n_csv == 0:
        ok = False
        print("  FAIL: no CSV entry checked")
    print(f"  {len(entries)} entries listed")
    print("RESULT: PASS" if ok else "RESULT: FAIL")
    sys.exit(0 if ok else 1)


def main():
    ap = argparse.ArgumentParser(description="read-only fingerprint / diff of k3 and k3n")
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("fingerprint")
    f.add_argument("--dsn", required=True, help="libpq DSN, e.g. \"dbname=k3n\"")
    f.add_argument("--out", required=True)
    f.add_argument("--label", help="free text stored in meta (e.g. TEST-ONLY)")
    f.add_argument("--grader", help="grade_v13n.py for the mi_md5 self-check")
    f.add_argument("--no-selfcheck", action="store_true")
    c = sub.add_parser("crosscheck")
    c.add_argument("a")
    c.add_argument("b")
    s = sub.add_parser("samefp")
    s.add_argument("a")
    s.add_argument("b")
    d = sub.add_parser("diff")
    d.add_argument("--ref", required=True, help="DSN of the reference (k3)")
    d.add_argument("--new", required=True, help="DSN of the rebuilt database (k3n)")
    d.add_argument("--out-tsv", required=True)
    d.add_argument("--log")
    d.add_argument("--csv-dir")
    d.add_argument("--expect-tables")
    d.add_argument("--expect-changes", type=int)
    v = sub.add_parser("csvcheck")
    v.add_argument("--csv-dir", required=True)
    v.add_argument("--expect", required=True)
    v.add_argument("--ddl", help="setup_db.sql (default: ../setup_db.sql next to db/)")
    a = ap.parse_args()
    {"fingerprint": cmd_fingerprint, "crosscheck": cmd_crosscheck, "samefp": cmd_samefp,
     "diff": cmd_diff, "csvcheck": cmd_csvcheck}[a.cmd](a)


if __name__ == "__main__":
    main()
