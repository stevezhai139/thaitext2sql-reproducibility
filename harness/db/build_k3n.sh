#!/usr/bin/env bash
# build_k3n.sh — สร้างฐาน k3n = k3 + กฎข้อเดียว ('None' ใน text column -> NULL)
#
# ที่มา: มติของผู้เขียน 13 ต.ค. 2026 (brief 1.1) — ใน PresidentMarriage แถว James Buchanan
# เก็บ SpouseName เป็น string 'None' ไม่ใช่ NULL; ให้เปลี่ยนเป็น NULL ตามนิยามของ NULL value
# กฎที่ใช้ (uniform, ข้อเดียว): ทุก cell ใน column ชนิด text ของทุกตาราง ที่มีค่าเท่ากับ 'None'
# ทุกตัวอักษร (case-sensitive, ไม่ trim) กลายเป็น NULL — ไม่เลือกเฉพาะ SpouseName
# บน CSV ชุดปัจจุบันคาดว่าเปลี่ยน 6 cells: PresidentMarriage.SpouseName 1,
# PresidentHolding.VicePresidentName 4, PresidentHolding.RunnerUp 1
#
# ตำแหน่งใน repo: harness/db/build_k3n.sh (DDL = harness/setup_db.sql)
#
# สิ่งที่สคริปต์ทำ (idempotent: drop + create ใหม่ทุกครั้ง ผลเหมือนเดิมทุกรอบ)
#   0) ตรวจก่อนแตะฐานใด: ชื่อฐาน, เครื่องมือ (psql, pg_dump) และ major version ของ pg_dump
#      ต้องเท่ากับ server, sha256 ของ CSV 5 ไฟล์และ setup_db.sql เทียบ k3n_inputs.sha256
#      (พิมพ์เฉพาะ basename), ฐานอ้างอิง (k3) ต้องมีอยู่, และถ้า k3 มีแถวใน Ecommerce1M
#      ต้องขอคัดลอก (K3N_ECOM1M_FROM_REF=1) มิฉะนั้นหยุดก่อนแตะ k3n
#   1) DROP DATABASE IF EXISTS k3n WITH (FORCE) แล้ว CREATE DATABASE k3n
#      คัด encoding/collation/ctype/provider (libc หรือ ICU) จาก k3 (TEMPLATE template0)
#      ให้ ORDER BY ข้อความเรียงเหมือนกัน
#   2) รัน setup_db.sql (DDL เดียวกับ k3 ไม่แก้ไฟล์)
#   3) สแกน CSV ทุกไฟล์ผ่าน temp table นับ cell 'None' ราย text column ก่อนโหลดจริง
#      ถ้ารวมไม่เท่ากับ K3N_EXPECT_CHANGES -> ลบ k3n ที่ยังว่างแล้วหยุด
#   4) โหลดข้อมูล
#      - ตารางที่ไม่มี 'None': \copy <table> FROM <csv> CSV HEADER ตรงตาม RUNBOOK 0.3
#        (กฎไม่มีผลกับตารางนี้ จึงโหลดด้วยวิธีเดียวกับ k3 ทุกประการ)
#      - ตารางที่มี 'None': \copy ลง temp table ที่มีเลขลำดับบรรทัด แล้ว
#        INSERT ... SELECT NULLIF(text_col,'None') ... ORDER BY ลำดับบรรทัด ใน transaction เดียว
#      เหตุผลที่ไม่โหลดตรงแล้วค่อย UPDATE: UPDATE สร้าง tuple version ใหม่ที่ตำแหน่งอื่น
#      ลำดับแถวของ query ที่ไม่มี ORDER BY และลำดับ tie จะต่างจาก k3 โดยไม่เกี่ยวกับ NULL
#      และเพิ่มตัวนับ n_mod_since_analyze ซึ่งอาจทำให้ autovacuum analyze ตารางเล็กต่างจาก k3
#      เหตุผลที่ไม่โหลดทุกตารางผ่าน temp table: บน cluster ทดสอบ (PostgreSQL 16.9) ลำดับ
#      physical ของ Ecommerce ใน k3 หลัง \copy ไม่ตรงกับลำดับใน CSV อยู่แล้ว (81 จาก 2390
#      ตำแหน่ง; สาเหตุน่าจะเป็นการนำ free space ของ page เดิมกลับมาใช้) และการทดลองโหลดผ่าน
#      temp table + INSERT ทำให้ layout ต่างจาก k3 — จึงใช้ \copy ตรงกับทุกตารางที่กฎไม่แตะ
#      การตรวจ ctid ใน db_fingerprint.py diff ยืนยันว่าทุกตารางมีลำดับ physical เดียวกับ k3
#   4b) (K3N_ECOM1M_FROM_REF=1) คัดลอกแถวของ Ecommerce1M จาก k3 ด้วย
#      pg_dump --data-only --table=public.ecommerce1m ต่อเข้า psql ของ k3n แล้วตรวจว่าได้
#      แถวชุดเดียวกับ k3 ณ เวลาที่รัน (จำนวนแถว + rowhash ต้องตรง มิฉะนั้นหยุด)
#      ลำดับ physical ไม่รับประกัน: COPY FROM อาจวางแถวลง free space ของ page ก่อนหน้า
#      (ผ่าน FSM) เมื่อขนาดแถวต่างกัน และ heap ของ k3 ที่ไม่ได้เติมด้วย COPY ล้วน (เช่นผ่าน INSERT
#      หรือ UPDATE) ก็มีลำดับต่างได้ สคริปต์จึงพิมพ์ผลตรวจสองบรรทัดเป็น INFO (ค่า "no" ไม่ใช่เงื่อนไขหยุด):
#      "row sequence in ctid order identical to <ref>: yes/no" และ "ctid values identical: yes/no"
#      amendment ข้อมูลให้อ้างค่าที่พิมพ์ ไม่อ้างว่าเหมือนข้อมูล ส.ค. ทุก byte
#      เหตุผล: harness/scale_ecommerce.py สร้างข้อมูลเดิมซ้ำไม่ได้ (ผลขึ้นกับ PYTHONHASHSEED)
#      และห้ามรัน phase0_setup.py หรือ scale_ecommerce.py บนเครื่อง run-of-record
#   5) ตรวจ: ไม่เหลือ 'None' ใน text column ใด และจำนวนแถวทุกตารางเท่ากับ k3 (อ่านอย่างเดียว)
#   6) (K3N_FP_OUT) บันทึก fingerprint ด้วย db_fingerprint.py แล้วพิมพ์ sha256 ของสคริปต์นี้,
#      setup_db.sql และ k3n_inputs.sha256 (ข้อมูลของ FREEZE STAMP)
#   ไม่แก้ CSV, ไม่แก้ setup_db.sql, ไม่เขียนอะไรลง k3
#   ถ้าขั้นใดหลังขั้น 1 ล้มเหลว (psql error, การตรวจไม่ผ่าน, fingerprint ล้มเหลว หรือถูกขัดจังหวะ)
#   trap ลบ target ที่สร้างไม่เสร็จทิ้ง (DROP DATABASE ... WITH (FORCE)) จึงไม่มี k3n ค้างครึ่งทาง
#   การหยุดก่อนขั้น 1 (guard ทั้งหมดของขั้น 0) ไม่แตะ target เลย
#
# ตรวจละเอียด cell-by-cell ด้วย db_fingerprint.py diff (โฟลเดอร์เดียวกัน)
# K3N_APPLY_RULE=0 สร้างฐานแบบไม่ใช้กฎ (ใช้เป็น control: ต้องได้ diff 0 cell กับ k3)
#
# การเชื่อมต่อใช้ค่า default ของ libpq (แบบเดียวกับ DSN "dbname=k3" ของ harness)
# เปลี่ยนได้ด้วย environment variable:
#   K3N_CSV_DIR          โฟลเดอร์ CSV ของรายวิชา (บังคับ ไม่มีค่า default; ผู้รันพิมพ์เอง)
#   K3N_DB (k3n)  K3N_REF_DB (k3)
#   K3N_HOST K3N_PORT K3N_USER  ค่า default ว่าง = ไม่ส่ง -h/-p/-U
#   K3N_PSQL K3N_PG_DUMP K3N_PYTHON  ค่า default = psql, pg_dump, python3 บน PATH
#   K3N_EXPECT_CHANGES (6)  K3N_APPLY_RULE (1)
#   K3N_ECOM1M_FROM_REF=1   คัดลอกแถว Ecommerce1M จาก K3N_REF_DB (ขั้น 4b)
#   K3N_ECOM1M_CSV + K3N_ECOM1M_SHA256  โหลด Ecommerce1M จาก CSV ด้วยกฎเดียวกัน
#                           (ใช้ได้เฉพาะเมื่อ sha256 ของไฟล์ตรงกับ K3N_ECOM1M_SHA256)
#   K3N_FP_OUT              ไฟล์ fingerprint ที่จะเขียนหลังสร้างเสร็จ
#   K3N_ALLOW_NO_REF=1      (สำหรับ test เท่านั้น) ยอมให้ไม่มีฐานอ้างอิง
#   K3N_DDL K3N_INPUTS      (สำหรับ test เท่านั้น) path ของ setup_db.sql และ k3n_inputs.sha256
#
# ใช้ (จากโฟลเดอร์ harness/):
#   K3N_CSV_DIR="<โฟลเดอร์ CSV ของรายวิชา>" K3N_ECOM1M_FROM_REF=1 K3N_FP_OUT="../results/db/k3n_fp_run1.tsv" bash "db/build_k3n.sh"

set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SELF="$HERE/$(basename "${BASH_SOURCE[0]}")"
PSQL_BIN="${K3N_PSQL:-$(command -v psql || true)}"
PG_DUMP_BIN="${K3N_PG_DUMP:-$(command -v pg_dump || true)}"
PY_BIN="${K3N_PYTHON:-$(command -v python3 || true)}"
HOST="${K3N_HOST:-}"
PORT="${K3N_PORT:-}"
DBUSER="${K3N_USER:-}"
TARGET_DB="${K3N_DB:-k3n}"
REF_DB="${K3N_REF_DB:-k3}"
DDL="${K3N_DDL:-$HERE/../setup_db.sql}"
INPUTS="${K3N_INPUTS:-$HERE/k3n_inputs.sha256}"
CSV_DIR="${K3N_CSV_DIR:-}"
EXPECT_CHANGES="${K3N_EXPECT_CHANGES:-6}"
APPLY_RULE="${K3N_APPLY_RULE:-1}"
ECOM1M_FROM_REF="${K3N_ECOM1M_FROM_REF:-0}"
ECOM1M_CSV="${K3N_ECOM1M_CSV:-}"
ECOM1M_SHA256="${K3N_ECOM1M_SHA256:-}"
FP_OUT="${K3N_FP_OUT:-}"
ALLOW_NO_REF="${K3N_ALLOW_NO_REF:-0}"

die() { echo "ERROR: $*" >&2; exit 1; }

sha256_of() {
  if command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "$1" | awk '{print $1}'
  else
    sha256sum "$1" | awk '{print $1}'
  fi
}

# ---- 0) ตรวจก่อนแตะฐานใด ----------------------------------------------------
case "$TARGET_DB" in
  k3|k3_*|postgres|template0|template1|"") die "target database '$TARGET_DB' ไม่อนุญาต (ห้าม k3, k3_* และฐานระบบ)" ;;
  *[!a-z0-9_]*) die "ชื่อ target ต้องเป็น a-z0-9_ เท่านั้น" ;;
esac
case "$REF_DB" in
  ""|*[!a-z0-9_]*) die "ชื่อฐานอ้างอิงต้องเป็น a-z0-9_ เท่านั้น" ;;
esac
[ "$TARGET_DB" != "$REF_DB" ] || die "target ต้องไม่ใช่ฐานอ้างอิง ($REF_DB)"
case "$EXPECT_CHANGES" in ''|*[!0-9]*) die "K3N_EXPECT_CHANGES ต้องเป็นจำนวนเต็ม" ;; esac
case "$APPLY_RULE" in 0|1) ;; *) die "K3N_APPLY_RULE ต้องเป็น 0 หรือ 1" ;; esac
case "$ECOM1M_FROM_REF" in 0|1) ;; *) die "K3N_ECOM1M_FROM_REF ต้องเป็น 0 หรือ 1" ;; esac
case "$ALLOW_NO_REF" in 0|1) ;; *) die "K3N_ALLOW_NO_REF ต้องเป็น 0 หรือ 1" ;; esac
for v in "$HOST" "$PORT" "$DBUSER"; do
  case "$v" in *[\ \'\"\\]*) die "K3N_HOST/K3N_PORT/K3N_USER ต้องไม่มีช่องว่างหรือเครื่องหมายคำพูด" ;; esac
done
[ -n "$CSV_DIR" ] || die "ต้องกำหนด K3N_CSV_DIR (โฟลเดอร์ CSV ของรายวิชา; ไม่มีค่า default)"
[ -d "$CSV_DIR" ] || die "ไม่พบโฟลเดอร์ที่ K3N_CSV_DIR ชี้"
[ -n "$PSQL_BIN" ] && [ -x "$PSQL_BIN" ] || die "ไม่พบ psql (ตั้ง K3N_PSQL)"
[ -f "$DDL" ] || die "ไม่พบ setup_db.sql (คาดที่ ../setup_db.sql ของโฟลเดอร์ db/)"
[ -f "$INPUTS" ] || die "ไม่พบ k3n_inputs.sha256 (คาดในโฟลเดอร์เดียวกับสคริปต์)"
if [ "$ECOM1M_FROM_REF" = "1" ] && [ -n "$ECOM1M_CSV" ]; then
  die "K3N_ECOM1M_FROM_REF=1 และ K3N_ECOM1M_CSV ใช้พร้อมกันไม่ได้"
fi

CONN=()
[ -z "$HOST" ] || CONN+=(-h "$HOST")
[ -z "$PORT" ] || CONN+=(-p "$PORT")
[ -z "$DBUSER" ] || CONN+=(-U "$DBUSER")
q() { "$PSQL_BIN" -X -q ${CONN[@]+"${CONN[@]}"} -v ON_ERROR_STOP=1 "$@"; }

echo "== build $TARGET_DB, reference $REF_DB, apply rule = $APPLY_RULE"
echo "   psql:    $("$PSQL_BIN" --version)"
server_num="$(q -d postgres -At -c "SHOW server_version_num")"
echo "   server:  $(q -d postgres -At -c "SELECT version()")"
server_major=$((server_num / 10000))
if [ -n "$PG_DUMP_BIN" ] && [ -x "$PG_DUMP_BIN" ]; then
  dump_ver="$("$PG_DUMP_BIN" --version)"
  echo "   pg_dump: $dump_ver"
  dump_major="$(echo "$dump_ver" | sed -n 's/.*PostgreSQL) \([0-9][0-9]*\).*/\1/p')"
  [ "$dump_major" = "$server_major" ] || die "major version ของ pg_dump ($dump_major) ไม่เท่ากับ server ($server_major)"
else
  [ "$ECOM1M_FROM_REF" = "0" ] || die "ไม่พบ pg_dump (ตั้ง K3N_PG_DUMP) แต่ขอคัดลอก Ecommerce1M"
  echo "   pg_dump: not found (ใช้เฉพาะเมื่อคัดลอก Ecommerce1M)"
fi

TABLES="President Party PresidentMarriage PresidentHolding Ecommerce"
csv_of() {
  case "$1" in
    President) echo "$CSV_DIR/President.csv" ;;
    Party) echo "$CSV_DIR/Party.csv" ;;
    PresidentMarriage) echo "$CSV_DIR/PresidentMarriage.csv" ;;
    PresidentHolding) echo "$CSV_DIR/PresidentHolding.csv" ;;
    Ecommerce) echo "$CSV_DIR/Ecommerce_Dataset.csv" ;;
    Ecommerce1M) echo "$ECOM1M_CSV" ;;
  esac
}

echo "== 0) input sha256 vs $(basename "$INPUTS")"
need="President.csv Party.csv PresidentMarriage.csv PresidentHolding.csv Ecommerce_Dataset.csv setup_db.sql"
checked=""
bad=0
while read -r want name rest; do
  case "$want" in ""|\#*) continue ;; esac
  case "$want" in *[!0-9a-f]*) die "บรรทัดผิดรูปแบบใน $(basename "$INPUTS")" ;; esac
  [ "${#want}" = "64" ] || die "บรรทัดผิดรูปแบบใน $(basename "$INPUTS")"
  name="${name#\*}"
  case "$name" in
    */*) die "k3n_inputs.sha256 ต้องมีเฉพาะ basename" ;;
    GradeStudent.csv) die "GradeStudent.csv ต้องไม่อยู่ใน k3n_inputs.sha256" ;;
    setup_db.sql) f="$DDL" ;;
    *.csv) f="$CSV_DIR/$name" ;;
    *) die "รายการที่ไม่รู้จักใน k3n_inputs.sha256: $name" ;;
  esac
  [ -f "$f" ] || { echo "   MISSING   $name"; bad=1; continue; }
  got="$(sha256_of "$f")"
  if [ "$got" = "$want" ]; then
    echo "   ok        $name  ${got:0:16}..."
  else
    echo "   MISMATCH  $name  ${got:0:16}... (expected ${want:0:16}...)"
    bad=1
  fi
  checked="$checked $name"
done < "$INPUTS"
for n in $need; do
  case " $checked " in *" $n "*) ;; *) die "k3n_inputs.sha256 ไม่มีรายการ $n" ;; esac
done
[ "$bad" = "0" ] || die "sha256 ของ input ไม่ตรงกับ k3n_inputs.sha256 — ไม่ได้แตะฐานใด"

if [ -n "$ECOM1M_CSV" ]; then
  [ -n "$ECOM1M_SHA256" ] || die "K3N_ECOM1M_CSV ต้องมาพร้อม K3N_ECOM1M_SHA256"
  [ -f "$ECOM1M_CSV" ] || die "ไม่พบไฟล์ที่ K3N_ECOM1M_CSV ชี้"
  got="$(sha256_of "$ECOM1M_CSV")"
  [ "$got" = "$ECOM1M_SHA256" ] || die "sha256 ของ $(basename "$ECOM1M_CSV") ไม่ตรงกับ K3N_ECOM1M_SHA256"
  echo "   ok        $(basename "$ECOM1M_CSV")  ${got:0:16}... (Ecommerce1M)"
  TABLES="$TABLES Ecommerce1M"
fi
for t in $TABLES; do
  f="$(csv_of "$t")"
  [ -f "$f" ] || die "ไม่พบ CSV ของ $t"
  case "$f" in *"'"*) die "path ของ CSV มี single quote ใช้กับ \\copy ไม่ได้" ;; esac
done

TEXT_TYPES="('text', 'character varying', 'character')"
WORK="$(mktemp -d "${TMPDIR:-/tmp}/build_k3n.XXXXXX")"
TARGET_TOUCHED=0
BUILD_DONE=0
cleanup() {
  rc=$?
  trap - EXIT INT TERM
  if [ "$TARGET_TOUCHED" = "1" ] && [ "$BUILD_DONE" != "1" ]; then
    if q -d postgres -c "DROP DATABASE IF EXISTS \"$TARGET_DB\" WITH (FORCE)" > /dev/null 2>&1; then
      echo "ERROR: build ไม่สำเร็จ — ลบ $TARGET_DB ที่สร้างไม่เสร็จทิ้งแล้ว" >&2
    else
      echo "ERROR: build ไม่สำเร็จ และลบ $TARGET_DB ไม่ได้ — ห้ามใช้ $TARGET_DB จนกว่าจะสร้างใหม่สำเร็จ" >&2
    fi
    [ "$rc" != "0" ] || rc=1
  fi
  rm -rf "$WORK"
  exit "$rc"
}
trap cleanup EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

ref_exists="$(q -d postgres -At -c "SELECT count(*) FROM pg_database WHERE datname = '$REF_DB'")"
LOCALE_OPTS="ENCODING 'UTF8'"
ref_e1m=0
if [ "$ref_exists" = "1" ]; then
  q -d postgres -At -F '|' -c "SELECT pg_encoding_to_char(encoding), datcollate, datctype, datlocprovider, coalesce(daticulocale, '') FROM pg_database WHERE datname = '$REF_DB'" > "$WORK/locale.txt"
  IFS='|' read -r r_enc r_coll r_ctype r_prov r_icu < "$WORK/locale.txt"
  LOCALE_OPTS="ENCODING '$r_enc' LC_COLLATE '$r_coll' LC_CTYPE '$r_ctype'"
  if [ "$r_prov" = "i" ]; then
    LOCALE_OPTS="$LOCALE_OPTS LOCALE_PROVIDER icu ICU_LOCALE '$r_icu'"
  else
    LOCALE_OPTS="$LOCALE_OPTS LOCALE_PROVIDER libc"
  fi
  echo "   locale copied from $REF_DB: $LOCALE_OPTS"
  has_e1m="$(q -d "$REF_DB" -At -c "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name = 'ecommerce1m'")"
  if [ "$has_e1m" = "1" ]; then
    ref_e1m="$(q -d "$REF_DB" -At -c "SELECT count(*) FROM public.ecommerce1m")"
  fi
  echo "   $REF_DB.ecommerce1m rows = $ref_e1m"
  if [ "$ref_e1m" != "0" ] && [ "$ECOM1M_FROM_REF" = "0" ] && [ -z "$ECOM1M_CSV" ]; then
    die "$REF_DB มี $ref_e1m แถวใน Ecommerce1M แต่ไม่ได้ขอคัดลอก — รันใหม่โดยเพิ่ม K3N_ECOM1M_FROM_REF=1 (ไม่ได้แตะ $TARGET_DB)"
  fi
  if [ "$ECOM1M_FROM_REF" = "1" ] && [ "$has_e1m" != "1" ]; then
    die "$REF_DB ไม่มีตาราง ecommerce1m ให้คัดลอก"
  fi
else
  [ "$ALLOW_NO_REF" = "1" ] || die "ไม่พบฐานอ้างอิง $REF_DB (K3N_ALLOW_NO_REF=1 ใช้ได้เฉพาะ test)"
  [ "$ECOM1M_FROM_REF" = "0" ] || die "ขอคัดลอก Ecommerce1M แต่ไม่พบฐานอ้างอิง $REF_DB"
  echo "   WARN: ไม่พบ $REF_DB ใช้ locale ค่าเริ่มของ cluster (test เท่านั้น)"
fi

echo "== 1) drop + create $TARGET_DB"
TARGET_TOUCHED=1
q -d postgres -c "DROP DATABASE IF EXISTS \"$TARGET_DB\" WITH (FORCE)"
q -d postgres -c "CREATE DATABASE \"$TARGET_DB\" TEMPLATE template0 $LOCALE_OPTS"

echo "== 2) DDL ($(basename "$DDL"))"
q -d "$TARGET_DB" -f "$DDL"

col_sql() {
  q -d "$TARGET_DB" -At -c "SELECT $2 FROM information_schema.columns WHERE table_schema = 'public' AND table_name = lower('$1')"
}

echo "== 3) scan CSVs for 'None' in text columns (temp tables only, nothing loaded yet)"
total=0
: > "$WORK/affected.txt"
for t in $TABLES; do
  f="$(csv_of "$t")"
  scan="$(col_sql "$t" "coalesce(string_agg(format('SELECT %L, count(*) FROM pg_temp.k3n_scan WHERE %I = %L', column_name, column_name, 'None'), ' UNION ALL ' ORDER BY ordinal_position) FILTER (WHERE data_type IN $TEXT_TYPES), 'SELECT NULL, 0')")"
  q -d "$TARGET_DB" -At -F '|' \
    -c "CREATE TEMP TABLE k3n_scan (LIKE public.$t)" \
    -c "\\copy pg_temp.k3n_scan FROM '$f' CSV HEADER" \
    -c "$scan" > "$WORK/scan_$t.txt"
  tcount=0
  while IFS='|' read -r col n; do
    [ -n "$col" ] || continue
    if [ "$n" -gt 0 ]; then
      printf "   %-18s %-18s 'None' cells = %s\n" "$t" "$col" "$n"
      tcount=$((tcount + n))
    fi
  done < "$WORK/scan_$t.txt"
  [ "$tcount" -eq 0 ] || echo "$t" >> "$WORK/affected.txt"
  total=$((total + tcount))
done
echo "   total 'None' cells = $total (expected $EXPECT_CHANGES)"
if [ "$APPLY_RULE" = "1" ] && [ "$total" -ne "$EXPECT_CHANGES" ]; then
  die "จำนวน 'None' ไม่ตรงกับที่คาด ($total vs $EXPECT_CHANGES)"
fi

echo "== 4) load"
for t in $TABLES; do
  f="$(csv_of "$t")"
  if [ "$APPLY_RULE" = "1" ] && grep -qx "$t" "$WORK/affected.txt"; then
    cols="$(col_sql "$t" "string_agg(format('%I', column_name), ', ' ORDER BY ordinal_position)")"
    sel="$(col_sql "$t" "string_agg(CASE WHEN data_type IN $TEXT_TYPES THEN format('NULLIF(%I, %L)', column_name, 'None') ELSE format('%I', column_name) END, ', ' ORDER BY ordinal_position)")"
    echo "   $t: staging + INSERT with rule (order = CSV line order)"
    q -d "$TARGET_DB" -1 \
      -c "CREATE TEMP TABLE k3n_stage (LIKE public.$t)" \
      -c "ALTER TABLE pg_temp.k3n_stage ADD COLUMN k3n_line bigserial" \
      -c "\\copy pg_temp.k3n_stage ($cols) FROM '$f' CSV HEADER" \
      -c "INSERT INTO public.$t ($cols) SELECT $sel FROM pg_temp.k3n_stage ORDER BY k3n_line"
  else
    echo "   $t: \\copy (identical to RUNBOOK 0.3)"
    q -d "$TARGET_DB" -c "\\copy $t FROM '$f' CSV HEADER"
  fi
done

if [ "$ECOM1M_FROM_REF" = "1" ]; then
  echo "== 4b) copy Ecommerce1M rows from $REF_DB (pg_dump --data-only)"
  [ "$(q -d "$TARGET_DB" -At -c "SELECT count(*) FROM public.ecommerce1m")" = "0" ] || die "ecommerce1m ของ $TARGET_DB ไม่ว่างก่อนคัดลอก"
  PGOPTIONS="-c synchronize_seqscans=off" "$PG_DUMP_BIN" ${CONN[@]+"${CONN[@]}"} --data-only --no-owner --no-privileges --table=public.ecommerce1m -d "$REF_DB" \
    | q -d "$TARGET_DB" > /dev/null
  rh_sql="SELECT count(*) || ' ' || md5(COALESCE(string_agg(h, E'\\n' ORDER BY h COLLATE \"C\"), '')) FROM (SELECT md5(to_jsonb(r)::text) AS h FROM public.ecommerce1m r) s"
  rh_ref="$(q -d "$REF_DB" -At -c "$rh_sql")"
  rh_new="$(q -d "$TARGET_DB" -At -c "$rh_sql")"
  echo "   ecommerce1m rows + rowhash: $REF_DB=$rh_ref $TARGET_DB=$rh_new"
  [ "$rh_ref" = "$rh_new" ] || die "ecommerce1m ที่คัดลอกไม่ตรงกับ $REF_DB"
  echo "   ecommerce1m: same rows as $REF_DB (rows + rowhash)"
  phys_sql="SELECT md5(COALESCE(string_agg(md5(to_jsonb(r)::text), E'\\n' ORDER BY r.ctid), '')) || ' ' || md5(COALESCE(string_agg(r.ctid::text, E'\\n' ORDER BY r.ctid), '')) FROM public.ecommerce1m r"
  read -r seq_ref ctid_ref <<< "$(q -d "$REF_DB" -At -c "$phys_sql")"
  read -r seq_new ctid_new <<< "$(q -d "$TARGET_DB" -At -c "$phys_sql")"
  if [ "$seq_ref" = "$seq_new" ]; then
    echo "   INFO ecommerce1m: row sequence in ctid order identical to $REF_DB: yes (physical order kept)"
  else
    echo "   INFO ecommerce1m: row sequence in ctid order identical to $REF_DB: no (same rows, other physical order; not a stop condition)"
  fi
  if [ "$ctid_ref" = "$ctid_new" ]; then
    echo "   INFO ecommerce1m: ctid values identical to $REF_DB: yes"
  else
    echo "   INFO ecommerce1m: ctid values identical to $REF_DB: no"
  fi
fi

echo "== 5) checks"
left="$(q -d "$TARGET_DB" -At -c "SELECT coalesce(string_agg(format('SELECT %L AS t, %L AS c, count(*) AS n FROM public.%I WHERE %I = %L', table_name, column_name, table_name, column_name, 'None'), ' UNION ALL '), 'SELECT NULL AS t, NULL AS c, 0 AS n') FROM information_schema.columns WHERE table_schema = 'public' AND data_type IN $TEXT_TYPES")"
remaining="$(q -d "$TARGET_DB" -At -c "SELECT coalesce(sum(n), 0) FROM ($left) s")"
echo "   'None' cells remaining in $TARGET_DB = $remaining"
if [ "$APPLY_RULE" = "1" ] && [ "$remaining" != "0" ]; then
  die "ยังเหลือ 'None' ใน $TARGET_DB"
fi
ALL_TABLES="$(q -d "$TARGET_DB" -At -c "SELECT string_agg(table_name, ' ' ORDER BY table_name) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE'")"
fail=0
for t in $ALL_TABLES; do
  n_new="$(q -d "$TARGET_DB" -At -c "SELECT count(*) FROM public.$t")"
  if [ "$ref_exists" = "1" ]; then
    n_ref="$(q -d "$REF_DB" -At -c "SELECT count(*) FROM public.$t")"
    status="ok"
    [ "$n_new" = "$n_ref" ] || { status="MISMATCH"; fail=1; }
    printf "   %-18s %s=%-8s %s=%-8s %s\n" "$t" "$TARGET_DB" "$n_new" "$REF_DB" "$n_ref" "$status"
  else
    printf "   %-18s %s=%s\n" "$t" "$TARGET_DB" "$n_new"
  fi
done
if [ "$fail" != "0" ]; then
  if [ "$ref_e1m" != "0" ] && [ "$ECOM1M_FROM_REF" = "0" ]; then
    die "row counts ไม่ตรงกับ $REF_DB — Ecommerce1M ของ $REF_DB มีแถว ให้รันใหม่ด้วย K3N_ECOM1M_FROM_REF=1"
  fi
  die "row counts ไม่ตรงกับ $REF_DB"
fi

if [ -n "$FP_OUT" ]; then
  echo "== 6) fingerprint -> $(basename "$FP_OUT")"
  [ -n "$PY_BIN" ] && [ -x "$PY_BIN" ] || die "ไม่พบ python3 (ตั้ง K3N_PYTHON)"
  DSN="dbname=$TARGET_DB"
  [ -z "$HOST" ] || DSN="$DSN host=$HOST"
  [ -z "$PORT" ] || DSN="$DSN port=$PORT"
  [ -z "$DBUSER" ] || DSN="$DSN user=$DBUSER"
  "$PY_BIN" -I -B "$HERE/db_fingerprint.py" fingerprint --dsn "$DSN" --out "$FP_OUT"
fi

echo "== sha256 (FREEZE STAMP)"
echo "   build_k3n.sh       $(sha256_of "$SELF")"
echo "   setup_db.sql       $(sha256_of "$DDL")"
echo "   k3n_inputs.sha256  $(sha256_of "$INPUTS")"
BUILD_DONE=1
echo "== done: $TARGET_DB ready"
