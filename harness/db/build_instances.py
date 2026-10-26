"""
build_instances.py -- build, verify and record the planted grading instances of
the multi-instance manifest (format kst-mi-2, rule MI-1b) from k3n.

Every planted instance = its parent database + one explicit SQL diff
(diffs/<name>.sql). The parent is the base (k3n) or an instance that comes
earlier in the manifest (parent chain, e.g. k3_pk_n_dup <- k3_pk_n_named).
Instances are built in manifest order. For each planted instance:

  1  preflight (before any database is touched): manifest format and rule;
     manifest status (below); names (^k3_(pk|fk)_[a-z0-9_]+$, never the base,
     k3 or k3n); parents come earlier; deltas are well formed; sha256 of every
     diff equals the registered one (when registered); a diff whose code
     (comments and quoted literals left out) holds ALTER DATABASE/ROLE/USER/
     GROUP/SYSTEM/DEFAULT PRIVILEGES, GRANT, REVOKE, COMMENT ON, SECURITY
     LABEL, REASSIGN/DROP OWNED or CREATE/DROP ROLE/USER/GROUP/DATABASE is
     refused; --record refuses a diff that still carries the PENDING-AUTHOR
     marker (literal values not approved yet, OQ4)
  2  parent check: the parent's fingerprint (every table except
     clone_exclude_data) and its schema digest are taken again right before
     the clone and must equal the values verified when the parent was built
     (base: registered values; base fingerprint file, see below)
  3  DROP DATABASE IF EXISTS <name> WITH (FORCE); CREATE DATABASE <name>
     TEMPLATE template0 with the parent's encoding, collate, ctype and
     provider (libc, or ICU with ICU_LOCALE and ICU_RULES)
  4  clone: pg_dump --no-owner --no-privileges --exclude-table-data for the
     clone_exclude_data tables (default ecommerce1m) | psql
  5  clone check: same tables and same schema digest as the parent; every
     non-excluded table has the parent's fingerprint; excluded tables exist
     and are empty; the fingerprint tables keep the parent's row sequence in
     ctid order
  6  diff: one transaction (psql -1, ON_ERROR_STOP); the diff carries its own
     guards before and after
  7  delta check against the parent: diffs change data only, so the table
     set and the schema digest (constraints, indexes, columns, triggers,
     policies, views, functions, database settings, privileges, comments,
     other objects ...) must still equal the parent's; undeclared tables keep
     their fingerprint (and, for fingerprint_tables, their row sequence in
     ctid order); each declared table matches its position
       in_place          same length, exactly <changed> positions differ
       append            parent sequence is a prefix, <added> rows appended
       in_place+append   <changed> positions differ, then <added> rows appended
  8  fingerprint (fingerprint_tables) and schema_md5 equal the registered
     ones; when the manifest is not recorded yet they are compared with
     expected_TESTONLY and expected_schema_md5_TESTONLY (a difference is fatal
     with --test-prefix, a WARN otherwise)
A failed instance is dropped again, so no half-built database is left; the
same holds when the run is stopped by Ctrl-C (SIGINT), SIGTERM or SIGHUP:
the instance being built is dropped, one line is printed (no traceback) and
the exit status is 130. Instances finished before the failure or the signal
are complete; rerunning the same command drops and rebuilds every instance.
Nothing is written to the base or to any parent.

Schema digest: SCHEMA_STMT of db_fingerprint.py (same folder; the single
definition), run through the grader's engine. Every instance must have the
schema digest of the base: a planted instance differs from the base in data
only, so a diff (or a later ALTER) that adds a PRIMARY KEY, a constraint, an
index, a table, a database setting (e.g. search_path), a privilege, a comment
or any other object is refused. The registered schema_md5 is checked here
(every mode, and --check-gold-only); the grader re-checks the data
fingerprints only, so --check-gold-only is the step that shows a schema change
made after Gate 1a (run it again right before the MI items are graded).

Manifest status (without --test-prefix): "DRAFT" without registered values,
or "RECORDED on run-of-record server (not frozen)" with every registered
value present (fingerprint and schema_md5 of every instance, diff_sha256 of
every planted instance, provenance). Any other status is refused, in
particular a TEST-ONLY dry-record manifest. With --test-prefix every status is
accepted.

Base fingerprint file: --base-fp, or by default base_build.k3n_fingerprint_file
(results/db/k3n_fp_run1.tsv, written by build_k3n.sh K3N_FP_OUT) resolved from
the project folder (two levels above this file). When the file exists the base
must equal it (rows + mi_md5 of fingerprint_tables, and schema_md5 when the
file has one) and, on a recorded manifest, the file must have the registered
sha256. --record requires the file and stores its path and sha256 in
base_build (k3n_fingerprint_file, k3n_fingerprint_sha256).

Modes
  (default)          build and verify
  --record           build, then write fingerprint and schema_md5 (every
                     instance), diff_sha256 (every planted instance), base_build
                     and provenance into the manifest and set status to
                     "RECORDED on run-of-record server (not frozen)"; nothing
                     else changes (diff -u of the DRAFT and the recorded
                     manifest shows only these keys); the file is replaced
                     atomically (temporary file + rename); refused with
                     --test-prefix, on a manifest that is already recorded,
                     while a diff carries PENDING-AUTHOR and without the base
                     fingerprint file
  --check-gold-only  check every instance (fingerprint and schema digest as in
                     step 8; schema digest equal to the base's), then run
                     items.<id>.gold_sql read-only on every instance of the
                     item and compare with expected_gold through match_v13 of
                     the grader; empty gold on the base only where the item
                     says empty_gold_on_base_ok; a missing instance database is
                     reported in one line
  --test-prefix g0_  (TEST-ONLY) every planted instance is built as
                     <prefix><name>; the prefix is g0_ or g0_<tag>_ (several
                     tags allowed, e.g. g0_dbm_icu_), so parallel test runs
                     do not share databases
  --dry-record-out F (TEST-ONLY, needs --test-prefix) what --record would
                     write, written to F instead of the manifest

The grader supplies make_engine() and mi_fingerprint() (and match_v13() for
--check-gold-only); it is imported from an explicit path (--grader, default
../grade_v13n.py next to this folder) without writing bytecode.

Usage (from harness/):
  python3 -I -B "db/build_instances.py" --manifest "db/mi_manifest_k3n.json" --pg "dbname=k3n" --grader "grade_v13n.py"
  python3 -I -B "db/build_instances.py" --manifest "db/mi_manifest_k3n.json" --pg "dbname=k3n" --grader "grade_v13n.py" --record
  python3 -I -B "db/build_instances.py" --manifest "db/mi_manifest_k3n.json" --pg "dbname=k3n" --grader "grade_v13n.py" --check-gold-only
"""
import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import tempfile

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
DEFAULT_GRADER = os.path.join(HERE, "..", "grade_v13n.py")
DB_FINGERPRINT = os.path.join(HERE, "db_fingerprint.py")
PENDING_MARK = "PENDING-AUTHOR"
FORMAT = "kst-mi-2"
RULE = "MI-1b"
RAW_NAME_RE = re.compile(r"^k3_(pk|fk)_[a-z0-9_]+$")
NAME_RE = re.compile(r"^(g0_([a-z0-9]+_)*)?k3_(pk|fk)_[a-z0-9_]+$")
PREFIX_RE = re.compile(r"^g0_([a-z0-9]+_)*$")
TABLE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
FORBIDDEN = {"k3", "k3n", "postgres", "template0", "template1"}
POSITIONS = {"in_place", "append", "in_place+append"}
DRAFT_STATUS = "DRAFT"
RECORDED_STATUS = "RECORDED on run-of-record server (not frozen)"
DRY_STATUS = "TEST-ONLY dry record (not for pre-registration)"
ICT = dt.timezone(dt.timedelta(hours=7))
# statements a diff may not hold (they change settings, privileges, comments or
# roles, not table data); matched on the code only (sql_code_only)
FORBIDDEN_SQL_RE = re.compile(
    r"\b(ALTER\s+(DATABASE|ROLE|USER|GROUP|SYSTEM|DEFAULT\s+PRIVILEGES)|GRANT|REVOKE|COMMENT\s+ON|"
    r"SECURITY\s+LABEL|REASSIGN\s+OWNED|DROP\s+OWNED|(CREATE|DROP)\s+(ROLE|USER|GROUP|DATABASE))\b",
    re.IGNORECASE)
INTERRUPT_EXIT = 130


class BuildError(Exception):
    pass


def die(msg):
    print("ERROR: " + msg, file=sys.stderr)
    sys.exit(1)


def interrupted(msg):
    """one line on stderr (no traceback, no path), exit status 130"""
    print("INTERRUPTED: " + msg, file=sys.stderr)
    sys.exit(INTERRUPT_EXIT)


def _raise_interrupt(signum, frame):
    raise KeyboardInterrupt


def install_signal_handlers():
    """SIGTERM and SIGHUP stop the run like Ctrl-C (SIGINT -> KeyboardInterrupt)"""
    for name in ("SIGTERM", "SIGHUP"):
        sig = getattr(signal, name, None)
        if sig is not None:
            signal.signal(sig, _raise_interrupt)


def sql_code_only(text):
    """SQL text without -- and /* */ comments and without single-quoted literals
    (dollar-quoted bodies such as DO $$ ... $$ stay: they are code)"""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("--", i):
            j = text.find("\n", i)
            i = n if j < 0 else j
        elif text.startswith("/*", i):
            j = text.find("*/", i + 2)
            i = n if j < 0 else j + 2
            out.append(" ")
        elif text[i] == "'":
            j = i + 1
            while j < n:
                if text[j] == "'":
                    if j + 1 < n and text[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            i = j + 1
            out.append("''")
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def write_json_atomic(path, obj):
    """write JSON to a temporary file in the same folder, then rename it over
    path: the file is either the old or the new version, never half-written"""
    folder = os.path.dirname(os.path.abspath(path))
    fd, tmp = tempfile.mkstemp(prefix=".tmp_", suffix=".json", dir=folder)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(obj, f, indent=1, ensure_ascii=False)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        mode = os.stat(path).st_mode & 0o7777 if os.path.exists(path) else 0o644
        os.chmod(tmp, mode)
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canon(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False)


def load_module(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        die(f"cannot load {os.path.basename(path)}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def norm_fp(fp):
    """grader mi_fingerprint value -> {table: [rows, md5]}"""
    out = {}
    for t, v in fp.items():
        if isinstance(v, dict):
            out[t] = [int(v["rows"]), v["md5"]]
        else:
            out[t] = [int(v[0]), v[1]]
    return out


def short(fp):
    return ", ".join(f"{t}={v[0]}/{v[1][:8]}" for t, v in fp.items())


# ---------------------------------------------------------------- manifest checks
def preflight(man, mdir, a, base_db):
    if man.get("format") != FORMAT:
        die(f"manifest format must be {FORMAT} (got {man.get('format')!r})")
    if man.get("rule") != RULE:
        die(f"manifest rule must be {RULE}")
    base = man.get("base")
    insts = man.get("instances")
    if not isinstance(insts, list) or not insts:
        die("manifest: instances must be a non-empty list")
    tables_fp = man.get("fingerprint_tables") or []
    excl = man.get("clone_exclude_data", ["ecommerce1m"])
    for t in tables_fp + excl:
        if not TABLE_RE.match(t):
            die(f"manifest: bad table name {t!r}")
    if set(tables_fp) & set(excl):
        die("manifest: a fingerprint table cannot be in clone_exclude_data")
    first = insts[0]
    if first.get("dbname") != base or first.get("role") != "base":
        die("manifest: the first instance must be the base (role base)")
    if a.test_prefix is not None:
        if not PREFIX_RE.match(a.test_prefix):
            die("--test-prefix must be g0_ or g0_<tag>_ (lower-case letters, digits and _)")
        if a.record:
            die("--record is not allowed with --test-prefix (g0_ databases are test copies)")
    else:
        if a.dry_record_out:
            die("--dry-record-out needs --test-prefix")
        if base_db != base:
            die(f"--pg must name the manifest base {base!r} (got {base_db!r})")
    if a.record and str(man.get("status", "")).startswith("RECORDED"):
        die("manifest is already recorded; copy the DRAFT manifest again to re-record")
    if a.record and any(s.get("fingerprint") is not None or s.get("schema_md5") is not None
                        for s in insts):
        die("manifest already holds fingerprints; copy the DRAFT manifest again to re-record")
    check_status(man, a)
    names = [s.get("dbname") for s in insts]
    if len(set(names)) != len(names):
        die("manifest: duplicate instance names")
    seen = {base}
    plan = []
    pending = []
    for s in insts[1:]:
        name = s.get("dbname", "")
        if not RAW_NAME_RE.match(name) or name in FORBIDDEN or name == base:
            die(f"instance name {name!r} not allowed (must match k3_(pk|fk)_..., never the base, k3 or k3n)")
        target = (a.test_prefix or "") + name
        if not NAME_RE.match(target) or target in FORBIDDEN or target == base_db:
            die(f"target database {target!r} not allowed")
        parent = s.get("derived_from")
        if parent not in seen:
            die(f"{name}: derived_from {parent!r} must be the base or an earlier instance")
        diff = s.get("diff") or ""
        if not diff or os.path.isabs(diff) or ".." in diff.split("/"):
            die(f"{name}: diff must be a relative path inside the manifest folder")
        dpath = os.path.join(mdir, diff)
        if not os.path.isfile(dpath):
            die(f"{name}: diff file {diff} not found")
        h = sha256_file(dpath)
        if s.get("diff_sha256") is not None and s["diff_sha256"] != h:
            die(f"{name}: {diff} sha256 {h} differs from the registered one; nothing was built")
        with open(dpath, encoding="utf-8") as f:
            text = f.read()
        if PENDING_MARK in text:
            pending.append(diff)
        bad_stmt = FORBIDDEN_SQL_RE.search(sql_code_only(text))
        if bad_stmt:
            die(f"{name}: {diff} contains {' '.join(bad_stmt.group(0).split()).upper()}: diffs may "
                f"change table data only (no database setting, privilege, comment or role); "
                f"nothing was built")
        delta = s.get("delta")
        if not isinstance(delta, dict) or not delta:
            die(f"{name}: delta must be a non-empty object")
        for t, d in delta.items():
            if not TABLE_RE.match(t) or t in excl:
                die(f"{name}: bad delta table {t!r}")
            pos = d.get("position")
            ch, ad = d.get("changed", 0), d.get("added", 0)
            if pos not in POSITIONS or not isinstance(ch, int) or not isinstance(ad, int) \
                    or ch < 0 or ad < 0 or d.get("removed", 0) != 0:
                die(f"{name}: bad delta for {t}")
            if (pos == "in_place" and (ch < 1 or ad != 0)) or \
                    (pos == "append" and (ch != 0 or ad < 1)) or \
                    (pos == "in_place+append" and (ch < 1 or ad < 1)):
                die(f"{name}: delta of {t} does not fit position {pos}")
        seen.add(name)
        plan.append((s, target, dpath, h))
    for iid, item in (man.get("items") or {}).items():
        for inst in item.get("instances", []):
            if inst not in seen:
                die(f"item {iid}: unknown instance {inst!r}")
            if inst not in (item.get("expected_gold") or {}):
                die(f"item {iid}: no expected_gold for {inst}")
        if not (item.get("gold_sql") or "").strip():
            die(f"item {iid}: gold_sql missing")
        if item.get("instances", [None])[0] != base:
            die(f"item {iid}: the first instance must be the base")
    if pending:
        msg = (f"{', '.join(pending)} still carr{'y' if len(pending) > 1 else 'ies'} the "
               f"{PENDING_MARK} marker: the literal values are not approved yet (OQ4)")
        if a.record:
            die(msg + "; after the author's approval (RUNBOOK 0.4) the marker lines are replaced in "
                      "the Gate 0 copy of the diffs before the copy at Gate 1a step 1a.19; stop here "
                      "and paste this output; nothing was built")
        if a.dry_record_out:
            print("WARN " + msg + " (--record would refuse)")
    return plan


def check_status(man, a):
    """manifest status rule (see the module docstring); test runs accept every status"""
    status = str(man.get("status", ""))
    if a.test_prefix is not None:
        return
    insts = man.get("instances") or []
    registered = [s.get("dbname") for s in insts
                  if s.get("fingerprint") is not None or s.get("schema_md5") is not None]
    if status.startswith("TEST-ONLY"):
        die(f"manifest status {status!r} is a TEST-ONLY manifest; use the DRAFT manifest of the "
            f"repo or the one recorded on this server")
    if status == DRAFT_STATUS:
        if registered:
            die(f"DRAFT manifest holds registered values ({', '.join(registered)}); "
                f"copy the DRAFT manifest again")
        return
    if status == RECORDED_STATUS:
        missing = [f"{s.get('dbname')}.{k}" for s in insts for k in ("fingerprint", "schema_md5")
                   if s.get(k) is None]
        missing += [f"{s.get('dbname')}.diff_sha256" for s in insts[1:] if s.get("diff_sha256") is None]
        if not (man.get("provenance") or {}).get("recorded_at_ict"):
            missing.append("provenance.recorded_at_ict")
        if missing:
            die(f"manifest says RECORDED but registered values are missing: {', '.join(missing)}")
        return
    die(f"manifest status {status!r} is not allowed (only {DRAFT_STATUS!r} or {RECORDED_STATUS!r})")


# ---------------------------------------------------------------- database helpers
def dsn_for(base_dsn, dbname):
    from psycopg2.extensions import make_dsn
    return make_dsn(base_dsn, dbname=dbname)


def admin_conn(base_dsn):
    import psycopg2
    try:
        c = psycopg2.connect(dsn_for(base_dsn, "postgres"))
    except psycopg2.Error as e:
        die(f"cannot connect to the server (database postgres) ({type(e).__name__}); check --pg")
    c.autocommit = True
    return c


def err_line(e):
    """exception -> one line without traceback or paths (type, SQLSTATE, first message line)"""
    msg = (getattr(e, "pgerror", None) or "").strip().splitlines()
    code = getattr(e, "pgcode", None)
    return type(e).__name__ + (f" {code}" if code else "") + (f": {msg[0]}" if msg else "")


def db_row(admin, dbname):
    with admin.cursor() as cur:
        cur.execute("SELECT to_jsonb(d) FROM pg_database d WHERE datname = %s", (dbname,))
        r = cur.fetchone()
    return r[0] if r else None


def drop_db(admin, dbname):
    from psycopg2 import sql
    with admin.cursor() as cur:
        cur.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(dbname)))


def create_db_like(admin, dbname, parent_row):
    from psycopg2 import sql
    prov = parent_row.get("datlocprovider")
    parts = [sql.SQL("CREATE DATABASE {} TEMPLATE template0 ENCODING {} LC_COLLATE {} LC_CTYPE {}")
             .format(sql.Identifier(dbname),
                     sql.Literal(_encoding_name(admin, parent_row["encoding"])),
                     sql.Literal(parent_row["datcollate"]), sql.Literal(parent_row["datctype"]))]
    if prov == "i":
        parts.append(sql.SQL(" LOCALE_PROVIDER icu ICU_LOCALE {}").format(
            sql.Literal(parent_row.get("daticulocale") or parent_row.get("datlocale"))))
        if parent_row.get("daticurules"):
            parts.append(sql.SQL(" ICU_RULES {}").format(sql.Literal(parent_row["daticurules"])))
    elif prov == "c":
        parts.append(sql.SQL(" LOCALE_PROVIDER libc"))
    else:
        raise BuildError(f"locale provider {prov!r} of the parent is not supported")
    with admin.cursor() as cur:
        cur.execute(sql.Composed(parts))


def _encoding_name(admin, enc):
    with admin.cursor() as cur:
        cur.execute("SELECT pg_encoding_to_char(%s)", (enc,))
        return cur.fetchone()[0]


def all_tables(q):
    return [r[0] for r in q("SELECT table_name FROM information_schema.tables "
                            "WHERE table_schema = 'public' AND table_type = 'BASE TABLE' "
                            "ORDER BY 1")]


def sequence(q, table):
    """rows of a table in physical (ctid) order, as canonical JSON strings"""
    if not TABLE_RE.match(table):
        raise BuildError(f"bad table name {table!r}")
    return [canon(r[0]) for r in q(f'SELECT to_jsonb(r) FROM public."{table}" r ORDER BY r.ctid')]


def count_rows(q, table):
    if not TABLE_RE.match(table):
        raise BuildError(f"bad table name {table!r}")
    return q(f'SELECT count(*) FROM public."{table}"')[0][0]


class Ctx:
    def __init__(self, a, man, grader, base_dsn, dbf):
        self.a = a
        self.man = man
        self.g = grader
        self.dbf = dbf
        self.base_dsn = base_dsn
        self.tables_fp = man["fingerprint_tables"]
        self.excl = man.get("clone_exclude_data", ["ecommerce1m"])
        self.engines = {}
        self.dsns = {}
        self.state = {}
        self.base_fp_used = None

    def engine(self, logical, actual):
        if logical not in self.engines:
            dsn = dsn_for(self.base_dsn, actual)
            try:
                self.engines[logical] = self.g.make_engine(dsn)
            except Exception as e:  # noqa: BLE001 -- connection errors: type only (no role names)
                if logical == self.man["base"]:
                    raise BuildError(f"base {logical} (database {actual}) cannot be opened "
                                     f"({type(e).__name__}); check --pg")
                raise BuildError(f"instance {logical} (database {actual}) not found or cannot be "
                                 f"opened ({type(e).__name__}); run build_instances.py (without "
                                 f"--check-gold-only) first")
            self.dsns[logical] = dsn
        return self.engines[logical]

    def fp(self, q, tables):
        return norm_fp(self.g.mi_fingerprint(q, tables))

    def schema(self, q):
        """schema digest (md5) through SCHEMA_STMT of db_fingerprint.py"""
        return q(self.dbf.SCHEMA_STMT)[0][0]


def compare_schema(label, spec, got, test_mode, record_mode, notes):
    """registered schema_md5 -> strict; else expected_schema_md5_TESTONLY (fatal in test mode)"""
    reg = spec.get("schema_md5")
    if reg is not None:
        if reg != got:
            raise BuildError(f"{label}: schema digest {got} differs from the registered schema_md5 "
                             f"{reg} (a constraint, index, column or other object was added, "
                             f"removed or changed)")
        return "schema matches registered"
    exp = spec.get("expected_schema_md5_TESTONLY")
    if exp:
        if exp != got:
            msg = f"{label}: schema digest {got} differs from expected_schema_md5_TESTONLY {exp}"
            if test_mode:
                raise BuildError(msg)
            notes.append("WARN " + msg + " (paste this output; not a failure of the decision)")
            return "schema DIFFERS from expected_TESTONLY (WARN)"
        return "schema matches expected_TESTONLY"
    return "schema unrecorded" if not record_mode else "schema recorded now"


def compare_registered(label, spec, got, test_mode, record_mode, notes):
    """registered fingerprint -> strict; else expected_TESTONLY (fatal in test mode)"""
    reg = spec.get("fingerprint")
    if reg is not None:
        if norm_fp(reg) != got:
            raise BuildError(f"{label}: fingerprint {canon(got)} differs from the registered one")
        return "matches registered fingerprint"
    exp = spec.get("expected_TESTONLY") or {}
    if exp:
        expn = norm_fp(exp)
        diff = [t for t in expn if got.get(t) != expn[t]]
        if diff:
            msg = f"{label}: differs from expected_TESTONLY in {','.join(diff)}"
            if test_mode:
                raise BuildError(msg)
            notes.append("WARN " + msg + " (paste this output; not a failure of the decision)")
            return "DIFFERS from expected_TESTONLY (WARN)"
        return "matches expected_TESTONLY"
    if test_mode:
        notes.append(f"WARN {label}: no registered or expected fingerprint to compare")
    return "unrecorded (no expectation)" if not record_mode else "recorded now"


# ---------------------------------------------------------------- build
def tool_paths(a):
    bindir = a.bindir
    if not bindir:
        p = shutil.which("psql")
        if not p:
            die("psql not found on PATH (pass --bindir)")
        bindir = os.path.dirname(p)
    psql = os.path.join(bindir, "psql")
    pg_dump = os.path.join(bindir, "pg_dump")
    for p in (psql, pg_dump):
        if not os.access(p, os.X_OK):
            die(f"{os.path.basename(p)} not found in --bindir")
    return psql, pg_dump


def major_of(text):
    m = re.search(r"PostgreSQL\)\s+(\d+)", text)
    return int(m.group(1)) if m else None


def base_fp_file(a, man):
    """(path, explicit) of the base fingerprint file: --base-fp, else
    base_build.k3n_fingerprint_file resolved from the project folder"""
    if a.base_fp:
        return os.path.abspath(a.base_fp), True
    rel = (man.get("base_build") or {}).get("k3n_fingerprint_file")
    if isinstance(rel, str) and rel and not os.path.isabs(rel) \
            and ".." not in rel.replace("\\", "/").split("/"):
        return os.path.normpath(os.path.join(PROJECT_ROOT, rel)), False
    return None, False


def rel_to_root(path):
    r = os.path.relpath(path, PROJECT_ROOT)
    return None if r == ".." or r.startswith(".." + os.sep) else r.replace(os.sep, "/")


def check_base_fp(ctx, fp_b, schema_b):
    """compare the base with its fingerprint file (db_fingerprint.py); die on a difference"""
    a, man = ctx.a, ctx.man
    path, explicit = base_fp_file(a, man)
    shown = os.path.basename(path) if path else "-"
    if not path or not os.path.isfile(path):
        if explicit:
            die(f"--base-fp file {shown} not found")
        if a.record:
            die("--record needs the fingerprint file of the base "
                f"({(man.get('base_build') or {}).get('k3n_fingerprint_file')}, written by build_k3n.sh "
                f"with K3N_FP_OUT) or --base-fp; nothing was built")
        print(f"base fingerprint file {shown} not found: not checked")
        return
    if a.record and rel_to_root(path) is None:
        die(f"--base-fp {shown} must be inside the project folder for --record; nothing was built")
    meta, rows = ctx.dbf.read_fp(path)
    bad = [t for t in ctx.tables_fp
           if t not in rows or [int(rows[t]["rows"]), rows[t].get("mi_md5")] != fp_b[t]]
    if bad:
        die(f"base differs from {shown} in {','.join(bad)}; nothing was built")
    if meta.get("schema_md5") is not None and meta["schema_md5"] != schema_b:
        die(f"base schema digest differs from the schema_md5 of {shown}; nothing was built")
    h = sha256_file(path)
    reg = (man.get("base_build") or {}).get("k3n_fingerprint_sha256")
    if reg and reg != h:
        die(f"{shown} sha256 {h} differs from the registered base_build.k3n_fingerprint_sha256")
    ctx.base_fp_used = (path, h)
    print(f"base matches {shown} (rows + mi_md5 of {len(ctx.tables_fp)} tables"
          + (", schema_md5" if meta.get("schema_md5") is not None else "; file has no schema_md5")
          + f"); sha256 {h[:12]}..." + (" = registered" if reg else ""))


def drop_half_built(ctx, admin, target, dump):
    """drop the target of a failed or stopped instance; SIGINT, SIGTERM and SIGHUP
    are ignored meanwhile. -> True when a database was dropped"""
    sigs = [x for x in (getattr(signal, n, None) for n in ("SIGINT", "SIGTERM", "SIGHUP"))
            if x is not None]
    old = {x: signal.signal(x, signal.SIG_IGN) for x in sigs}
    try:
        if dump is not None:
            if dump.poll() is None:
                dump.kill()
            try:
                dump.wait(timeout=30)
            except subprocess.TimeoutExpired:
                pass
        try:
            existed = db_row(admin, target) is not None
            drop_db(admin, target)
            return existed
        except Exception:  # noqa: BLE001 -- the admin session may be broken: use a new one
            import psycopg2
            c = psycopg2.connect(dsn_for(ctx.base_dsn, "postgres"))
            c.autocommit = True
            try:
                existed = db_row(c, target) is not None
                drop_db(c, target)
                return existed
            finally:
                c.close()
    finally:
        for x, h in old.items():
            signal.signal(x, h)


def first_error(files):
    """first error line written by pg_dump / psql into the temporary files (one line)"""
    lines = []
    for f in files:
        f.seek(0)
        lines += [x.strip() for x in f.read().decode("utf-8", "replace").splitlines() if x.strip()]
    errs = [x for x in lines if "error" in x.lower() or "fatal" in x.lower()]
    return ((errs or lines or ["no message"])[0])[:300]


def cleanup_note(ctx, admin, target, dump):
    """drop the half-built target and say what happened (one clause, no path)"""
    try:
        dropped = drop_half_built(ctx, admin, target, dump)
    except Exception as e:  # noqa: BLE001
        return (f"the half-built database {target} could NOT be dropped ({type(e).__name__}); "
                f"rerunning the same command drops and rebuilds it")
    return (f"the half-built database {target} was dropped" if dropped
            else f"database {target} was not created")


def build(ctx, plan, psql, pg_dump, admin, base_db, notes):
    a, man = ctx.a, ctx.man
    test_mode = a.test_prefix is not None
    record_mode = a.record or bool(a.dry_record_out)
    base_spec = man["instances"][0]
    qb = ctx.engine(man["base"], base_db)
    base_tables = all_tables(qb)
    for t in ctx.tables_fp + ctx.excl:
        if t not in base_tables:
            die(f"base {base_db} has no table {t}")
    cmp_tables = [t for t in base_tables if t not in ctx.excl]
    fp_b = ctx.fp(qb, ctx.tables_fp)
    schema_b = ctx.schema(qb)
    try:
        st = compare_registered(f"base {man['base']}", base_spec, fp_b, test_mode, record_mode, notes)
        st_s = compare_schema(f"base {man['base']}", base_spec, schema_b, test_mode, record_mode, notes)
    except BuildError as e:
        die(str(e))
    print(f"base {man['base']} (db {base_db}) fingerprint {st}; {st_s} ({schema_b[:12]}...): {short(fp_b)}")
    check_base_fp(ctx, fp_b, schema_b)
    ctx.state[man["base"]] = {"fp_all": ctx.fp(qb, cmp_tables), "fp": fp_b, "tables": base_tables,
                              "seq": {t: sequence(qb, t) for t in ctx.tables_fp},
                              "q": qb, "actual": base_db, "schema": schema_b}
    built = {man["base"]: fp_b}
    schemas = {man["base"]: schema_b}
    for spec, target, dpath, h in plan:
        name = spec["dbname"]
        parent = spec["derived_from"]
        ps = ctx.state[parent]
        touched = False
        dump = None
        errf = []
        try:
            now = ctx.fp(ps["q"], cmp_tables)
            if now != ps["fp_all"]:
                raise BuildError(f"{name}: parent {parent} changed since it was verified")
            if ctx.schema(ps["q"]) != ps["schema"]:
                raise BuildError(f"{name}: the schema of parent {parent} changed since it was verified")
            prow = db_row(admin, ps["actual"])
            if prow is None:
                raise BuildError(f"{name}: parent database {ps['actual']} not found")
            touched = True
            drop_db(admin, target)
            create_db_like(admin, target, prow)
            env = dict(os.environ, PGOPTIONS="-c synchronize_seqscans=off")
            # stderr of pg_dump and psql goes to anonymous temporary files: only the first
            # error line is reported (one line, as for the diff)
            errf = [tempfile.TemporaryFile(), tempfile.TemporaryFile()]
            dump = subprocess.Popen(
                [pg_dump, "--no-owner", "--no-privileges"]
                + [f"--exclude-table-data=public.{t}" for t in ctx.excl]
                + ["-d", dsn_for(ctx.base_dsn, ps["actual"])],
                stdout=subprocess.PIPE, stderr=errf[0], env=env)
            load = subprocess.run([psql, "-X", "-q", "-v", "ON_ERROR_STOP=1",
                                   "-d", dsn_for(ctx.base_dsn, target)],
                                  stdin=dump.stdout, stdout=subprocess.DEVNULL, stderr=errf[1])
            dump.stdout.close()
            if dump.wait() != 0 or load.returncode != 0:
                raise BuildError(f"{name}: clone of {parent} failed: {first_error(errf)}")
            qi = ctx.engine(name, target)
            # 5 clone check
            if all_tables(qi) != ps["tables"]:
                raise BuildError(f"{name}: clone has other tables than {parent}")
            if ctx.schema(qi) != ps["schema"]:
                raise BuildError(f"{name}: clone schema differs from {parent}")
            if ctx.fp(qi, cmp_tables) != ps["fp_all"]:
                raise BuildError(f"{name}: clone differs from {parent} before the diff")
            for t in ctx.excl:
                if count_rows(qi, t) != 0:
                    raise BuildError(f"{name}: excluded table {t} is not empty in the clone")
            for t in ctx.tables_fp:
                if sequence(qi, t) != ps["seq"][t]:
                    raise BuildError(f"{name}: clone row order of {t} differs from {parent}")
            # 6 diff
            r = subprocess.run([psql, "-X", "-q", "-v", "ON_ERROR_STOP=1", "-1",
                                "-d", dsn_for(ctx.base_dsn, target), "-f", dpath],
                               stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
            if r.returncode != 0:
                err = r.stderr.decode("utf-8", "replace").strip().splitlines()
                errs = [x.split("ERROR:", 1)[1].strip() for x in err if "ERROR:" in x]
                raise BuildError(f"{name}: diff {spec['diff']} failed: "
                                 + (errs[0] if errs else (err[-1] if err else
                                                          f"psql exit {r.returncode}")))
            # 7 delta check: data only (same tables, same schema), then the declared delta
            tables_i = all_tables(qi)
            if tables_i != ps["tables"]:
                extra = sorted(set(tables_i) - set(ps["tables"]))
                gone = sorted(set(ps["tables"]) - set(tables_i))
                raise BuildError(f"{name}: diff {spec['diff']} changed the table set (added "
                                 f"{extra or '-'}, removed {gone or '-'}); diffs may change data only")
            schema_i = ctx.schema(qi)
            if schema_i != ps["schema"]:
                raise BuildError(f"{name}: diff {spec['diff']} changed the schema (constraint, index, "
                                 f"column, trigger, view or other object); diffs may change data only")
            fp_all_i = ctx.fp(qi, cmp_tables)
            delta = spec["delta"]
            seq_i = {}
            for t in cmp_tables:
                if t not in delta:
                    if fp_all_i[t] != ps["fp_all"][t]:
                        raise BuildError(f"{name}: table {t} changed but is not in the declared delta")
                    if t in ps["seq"] and sequence(qi, t) != ps["seq"][t]:
                        raise BuildError(f"{name}: the row order of {t} changed but {t} is not in "
                                         f"the declared delta")
                    continue
                d = delta[t]
                p_seq = ps["seq"][t] if t in ps["seq"] else sequence(ps["q"], t)
                c_seq = sequence(qi, t)
                seq_i[t] = c_seq
                pos, ch, ad = d["position"], d.get("changed", 0), d.get("added", 0)
                n_add = len(c_seq) - len(p_seq)
                n_chg = sum(1 for x, y in zip(p_seq, c_seq) if x != y)
                if pos == "in_place":
                    ok = n_add == 0 and n_chg == ch
                elif pos == "append":
                    ok = c_seq[:len(p_seq)] == p_seq and n_add == ad
                else:
                    ok = n_add == ad and n_chg == ch
                if not ok:
                    raise BuildError(f"{name}: delta of {t} is changed={n_chg} added={n_add}, "
                                     f"declared {pos} changed={ch} added={ad}")
            for t in delta:
                if t not in cmp_tables:
                    raise BuildError(f"{name}: delta table {t} not in the database")
            for t in ctx.excl:
                if count_rows(qi, t) != 0:
                    raise BuildError(f"{name}: the diff wrote into excluded table {t}")
            # 8 fingerprint and schema digest
            fp_i = ctx.fp(qi, ctx.tables_fp)
            st = compare_registered(name, spec, fp_i, test_mode, record_mode, notes)
            st_s = compare_schema(name, spec, schema_i, test_mode, record_mode, notes)
        except KeyboardInterrupt:
            interrupted(f"{name}: stopped by a signal; "
                        + (cleanup_note(ctx, admin, target, dump) if touched else
                           "no database of this instance was touched")
                        + "; instances finished before it are complete; rerun the same command")
        except BuildError as e:
            die(str(e) + ("; " + cleanup_note(ctx, admin, target, dump) if touched else ""))
        except Exception as e:  # noqa: BLE001 -- one line, no traceback (paths)
            die(f"{name}: unexpected {err_line(e)}"
                + ("; " + cleanup_note(ctx, admin, target, dump) if touched else ""))
        finally:
            for f in errf:
                f.close()
        seq_all = dict(ps["seq"])
        seq_all.update(seq_i)
        for t in ctx.tables_fp:
            if t not in seq_i:
                seq_all[t] = sequence(qi, t)
        ctx.state[name] = {"fp_all": fp_all_i, "fp": fp_i, "tables": ps["tables"], "seq": seq_all,
                           "q": qi, "actual": target, "schema": schema_i}
        built[name] = fp_i
        schemas[name] = schema_i
        changed = [t for t in ctx.tables_fp if fp_i[t] != ctx.state[parent]["fp"][t]]
        print(f"{name} (db {target}) <- {parent}: diff {spec['diff']} sha256 {h[:12]}...; "
              f"delta {canon(spec['delta'])} as declared; tables and schema = parent; "
              f"fingerprint {st}; {st_s}; "
              + ", ".join(f"{t}={fp_i[t][0]}/{fp_i[t][1][:8]}" for t in changed))
    return built, schemas


def record(ctx, plan, built, schemas, admin, base_db, mpath, out_path, dry):
    man = ctx.man
    before = sha256_file(mpath)
    for s in man["instances"]:
        s["fingerprint"] = built[s["dbname"]]
        s["schema_md5"] = schemas[s["dbname"]]
    for spec, _target, _dpath, h in plan:
        spec["diff_sha256"] = h
    bb = man.setdefault("base_build", {})

    def maybe(path):
        return sha256_file(path) if os.path.isfile(path) else None
    bb["build_k3n_sh_sha256"] = maybe(os.path.join(HERE, "build_k3n.sh"))
    bb["setup_db_sql_sha256"] = maybe(os.path.join(HERE, "..", "setup_db.sql"))
    bb["inputs_sha256_file_sha256"] = maybe(os.path.join(HERE, "k3n_inputs.sha256"))
    bb.setdefault("k3n_fingerprint_file", "results/db/k3n_fp_run1.tsv")
    if ctx.base_fp_used:
        path, h = ctx.base_fp_used
        bb["k3n_fingerprint_file"] = rel_to_root(path) or os.path.basename(path)
        bb["k3n_fingerprint_sha256"] = h
    else:
        bb["k3n_fingerprint_sha256"] = None
    row = db_row(admin, base_db)
    man["provenance"] = {
        "recorded_at_ict": dt.datetime.now(ICT).replace(microsecond=0).isoformat(),
        "server_version": ctx.engines[man["base"]]("SELECT current_setting('server_version')")[0][0],
        "datcollate": row["datcollate"], "datctype": row["datctype"],
        "provider": {"c": "libc", "i": "icu"}.get(row["datlocprovider"], row["datlocprovider"]),
        "builder_sha256": sha256_file(os.path.abspath(__file__)),
        "db_fingerprint_sha256": sha256_file(DB_FINGERPRINT),
        "grader_sha256": sha256_file(ctx.a.grader),
        "manifest_before_sha256": before,
    }
    man["status"] = DRY_STATUS if dry else RECORDED_STATUS
    write_json_atomic(out_path, man)
    print(f"recorded into {os.path.basename(out_path)}: fingerprint and schema_md5 of "
          f"{len(man['instances'])} instances, diff_sha256 of {len(plan)} planted instances, "
          f"base_build, provenance and status ({man['status']}); no other key changed")


# ---------------------------------------------------------------- gold check
def fmt_rows(rows):
    return "[" + "; ".join("|".join("NULL" if v is None else str(v) for v in r) for r in rows) + "]"


def check_gold(ctx, base_db, notes):
    man = ctx.man
    a = ctx.a
    test_mode = a.test_prefix is not None
    specs = {s["dbname"]: s for s in man["instances"]}
    actual = {man["base"]: base_db}
    for s in man["instances"][1:]:
        actual[s["dbname"]] = (a.test_prefix or "") + s["dbname"]
    # every instance first: fingerprint and schema (schema = the base's), then the gold
    names = [man["base"]] + sorted({i for item in man["items"].values() for i in item["instances"]}
                                   - {man["base"]}, key=lambda n: list(specs).index(n))
    checked = {}
    base_schema = None
    for inst in names:
        q = ctx.engine(inst, actual[inst])
        fp = ctx.fp(q, ctx.tables_fp)
        schema = ctx.schema(q)
        if inst == man["base"]:
            base_schema = schema
        elif schema != base_schema:
            raise BuildError(f"instance {inst} (database {actual[inst]}): schema digest {schema} differs "
                             f"from the base {man['base']} ({base_schema}); instances may differ from "
                             f"the base in data only (rebuild with build_instances.py)")
        st = compare_registered(inst, specs[inst], fp, test_mode, False, notes)
        st_s = compare_schema(inst, specs[inst], schema, test_mode, False, notes)
        checked[inst] = f"{st}; {st_s}"
    ok = True
    for iid, item in man["items"].items():
        sql = item["gold_sql"].strip()
        while sql.endswith(";"):
            sql = sql[:-1].rstrip()
        results = []
        for inst in item["instances"]:
            q = ctx.engine(inst, actual[inst])
            exp = item["expected_gold"][inst]
            try:
                rows = q(sql)
            except Exception as e:  # noqa: BLE001
                ok = False
                print(f"{iid:4s} {inst:16s} gold_sql failed: {err_line(e)}  FAIL")
                results.append("error")
                continue
            good = bool(ctx.g.match_v13(rows, exp, False, None, {}, colperm=False))
            if not rows and inst == man["base"] and not item.get("empty_gold_on_base_ok"):
                good = False
                notes.append(f"FAIL {iid}: gold is empty on the base and empty_gold_on_base_ok is not set")
            ok = ok and good
            results.append(canon(sorted([[None if v is None else str(v) for v in r] for r in rows],
                                        key=lambda r: [str(x) for x in r])))
            print(f"{iid:4s} {inst:16s} {fmt_rows(rows):60s} expected {fmt_rows(exp)}  "
                  f"{'ok' if good else 'FAIL'}  (instance {checked[inst]})")
        varies = len(set(results)) > 1
        if "gold_varies" in item and bool(item["gold_varies"]) != varies:
            ok = False
            notes.append(f"FAIL {iid}: gold_varies={item['gold_varies']} but the results "
                         f"{'differ' if varies else 'are equal'} across instances")
    for iid in man.get("single_instance_items", []):
        print(f"{iid}: single-instance item, graded on the base only (not checked here)")
    for iid in man.get("reserve_items", []):
        print(f"{iid}: reserve item (not run unless the AM-9 replacement rule applies)")
    return ok


# ---------------------------------------------------------------- main
def main():
    install_signal_handlers()
    try:
        run()
    except KeyboardInterrupt:
        interrupted("stopped by a signal outside the build of an instance; no half-built database "
                    "and no half-written manifest were left; rerun the same command")


def run():
    ap = argparse.ArgumentParser(description="build / verify / record MI instances (kst-mi-2)")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--pg", required=True, help="libpq DSN of the base, e.g. \"dbname=k3n\"")
    ap.add_argument("--bindir", help="folder of psql and pg_dump (default: psql on PATH)")
    ap.add_argument("--grader", default=DEFAULT_GRADER,
                    help="grade_v13n.py (make_engine, mi_fingerprint, match_v13)")
    ap.add_argument("--test-prefix", help="TEST-ONLY: build planted instances as <prefix><name>")
    ap.add_argument("--record", action="store_true")
    ap.add_argument("--dry-record-out", help="TEST-ONLY: write what --record would write to this file")
    ap.add_argument("--check-gold-only", action="store_true")
    ap.add_argument("--base-fp", help="fingerprint file of the base (db_fingerprint.py); default: "
                                      "base_build.k3n_fingerprint_file of the manifest from the project folder")
    a = ap.parse_args()
    if a.record and a.check_gold_only:
        die("--record and --check-gold-only cannot be combined")
    if a.dry_record_out and (a.record or a.check_gold_only):
        die("--dry-record-out cannot be combined with --record or --check-gold-only")

    mpath = os.path.abspath(a.manifest)
    mdir = os.path.dirname(mpath)
    try:
        with open(mpath, encoding="utf-8") as f:
            man = json.load(f)
    except (OSError, ValueError) as e:
        die(f"cannot read the manifest ({type(e).__name__})")
    if a.dry_record_out and os.path.abspath(a.dry_record_out) == mpath:
        die("--dry-record-out must differ from --manifest")
    from psycopg2.extensions import parse_dsn
    try:
        base_db = parse_dsn(a.pg).get("dbname")
    except Exception as e:  # noqa: BLE001
        die(f"--pg is not a valid libpq DSN ({type(e).__name__})")
    if not base_db:
        die("--pg must contain dbname=")
    plan = preflight(man, mdir, a, base_db)
    if not os.path.isfile(DB_FINGERPRINT):
        die("db_fingerprint.py not found next to build_instances.py (it defines the schema digest)")
    dbf = load_module(DB_FINGERPRINT, "db_fingerprint_for_instances")
    a.grader = os.path.abspath(a.grader)
    if not os.path.isfile(a.grader):
        die(f"grader not found: {os.path.basename(a.grader)}")
    g = load_module(a.grader, "grader_for_instances")
    for fn in ("make_engine", "mi_fingerprint") + (("match_v13",) if a.check_gold_only else ()):
        if not hasattr(g, fn):
            die(f"grader has no {fn}()")
    ctx = Ctx(a, man, g, a.pg, dbf)
    notes = []
    print(f"manifest {os.path.basename(mpath)}: format {man['format']}, rule {man['rule']}, "
          f"status {man.get('status')}, base {man['base']} (db {base_db}), "
          f"{len(plan)} planted instances" + (f", TEST prefix {a.test_prefix}" if a.test_prefix else ""))

    try:
        if a.check_gold_only:
            ok = check_gold(ctx, base_db, notes)
            for n in notes:
                print(n)
            print("GOLD CHECK OK" if ok else "GOLD CHECK FAIL")
            sys.exit(0 if ok else 1)

        psql, pg_dump = tool_paths(a)
        admin = admin_conn(a.pg)
        with admin.cursor() as cur:
            cur.execute("SELECT current_setting('server_version_num')::int")
            server_major = cur.fetchone()[0] // 10000
        vd = subprocess.run([pg_dump, "--version"], capture_output=True, text=True).stdout.strip()
        vp = subprocess.run([psql, "--version"], capture_output=True, text=True).stdout.strip()
        print(f"tools: {vp}; {vd}; server major {server_major}")
        if major_of(vd) != server_major:
            die(f"pg_dump major version {major_of(vd)} differs from the server ({server_major})")
        built, schemas = build(ctx, plan, psql, pg_dump, admin, base_db, notes)
        if a.record:
            record(ctx, plan, built, schemas, admin, base_db, mpath, mpath, dry=False)
        elif a.dry_record_out:
            record(ctx, plan, built, schemas, admin, base_db, mpath,
                   os.path.abspath(a.dry_record_out), dry=True)
    except BuildError as e:
        for n in notes:
            print(n)
        die(str(e))
    except Exception as e:  # noqa: BLE001 -- one line, no traceback (paths)
        die(f"unexpected {err_line(e)}")
    for n in notes:
        print(n)
    print("BUILD OK")


if __name__ == "__main__":
    main()
