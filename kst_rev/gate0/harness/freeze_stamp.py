#!/usr/bin/env python3
"""freeze_stamp.py -- hash every file of a freeze manifest and print FREEZE STAMP rows (Gate 0 tool; runs in place).

RUNBOOK_v2: Gate 1a step 74 (freeze_manifest_gate1b.tsv) and Gate 2 step 29 (freeze_manifest_gate2.tsv).
The Markdown tables on stdout are pasted into the FREEZE STAMP of each amendment; the "ผลตรวจ"
block after them is for the chat only.

Manifest format (TSV, UTF-8, one header line, '#' lines are comments; design section 3.12):
  path             relative to ROOT. Forms:
                     a file                       harness/grade_v13n.py
                     a line range of a file       prereg/preregistration_FROZEN.md#L1-115
                     a folder (trailing '/')      results/chat/prompts/
                     a glob matching ONE file     kst_rev/wf_q100/selection/EXTENSION_v2_*_FILLED_2026-10-13_2233.xlsx
  amendment        PREREG | DATA | AM-6 | AM-7 | AM-8 | AM-9 | ADDENDUM
  gate             1b | 2 | 3
  expected_sha256  64 hex, or a prefix of at least 8 hex (optionally ending in '…'), or 'record'
  label            optional; when set, the label is printed instead of the path (inputs outside git
                   whose file names carry a personal name are printed by a neutral label only)
  stage            add          = file is staged by this gate's commit (listed in gate*_paths.txt)
                   add-nostamp  = staged by this gate's commit but never hashed or printed: the
                                  preregistration itself. Its full-file sha256 changes as soon as the
                                  stamp is appended, so a full-file value in the FREEZE STAMP could never
                                  be verified; the frozen part is stamped by the '#La-b' row and the sha256
                                  after the append is recorded in the next gate's addendum (RUNBOOK 1a.77,
                                  2.31b). A whole-file row of the prereg must use this stage.
                   pinned       = file already tracked in git and unchanged; hashed only. A pinned row
                                  needs an expected value: 'record' on a pinned row is a FAIL (drift since
                                  the earlier gate would go unnoticed); copy the value recorded earlier.
                   external     = file outside git (under kst_rev/); hashed only, label required

Hash definitions (so anyone can recompute them):
  file        sha256 of the bytes (same as `shasum -a 256`).
  line range  sha256 of lines a..b including their line endings (same as `head -n b | tail -n +a | shasum -a 256`).
  folder      "tree hash": sha256 of the concatenation, over every file below the folder sorted by its
              POSIX path relative to the folder (skipping __pycache__/ and .DS_Store), of
              "<relative path>\\t<sha256 of the file>\\n". The number of files is printed with it.

Forbidden files: harness/secrets.env, any *.env and results/results.jsonl are never opened. The check
runs on the manifest pattern AND on every concrete file after glob or folder expansion (and on the
target of a symbolic link), before any file is read; a glob whose pattern could match a forbidden name
is rejected. Any of these is a manifest error (exit 2) and nothing is hashed.
Exit: 0 all rows OK, 1 a mismatch, a missing file or a pinned row without a value, 2 manifest or usage error.
Run with: python3 -I -B freeze_stamp.py --manifest <tsv>
"""
import sys

sys.dont_write_bytecode = True

import argparse
import datetime as dt
import fnmatch
import hashlib
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[2]

COLUMNS = ["path", "amendment", "gate", "expected_sha256", "label", "stage"]
AMENDMENT_ORDER = ["PREREG", "DATA", "AM-6", "AM-7", "AM-8", "AM-9", "ADDENDUM"]
GATES = {"1b", "2", "3"}
STAGES = {"add", "add-nostamp", "pinned", "external"}
STAGED = {"add", "add-nostamp"}  # rows listed in gate*_paths.txt
PREREG_PATH = "prereg/preregistration_FROZEN.md"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
HEXPREFIX = re.compile(r"^([0-9a-f]{8,63})(?:…|\.\.\.)?$")
LINE_RANGE = re.compile(r"^(.*)#L(\d+)-(\d+)$")
GLOB_CHARS = set("*?[")
# names a glob pattern must not be able to match (checked with fnmatch on the full pattern and on its
# last component); the concrete matches are checked again after expansion
FORBIDDEN_SAMPLES_FULL = ("results/results.jsonl", "harness/secrets.env")
FORBIDDEN_SAMPLES_BASE = ("secrets.env", ".env", "x.env")
ICT = dt.timezone(dt.timedelta(hours=7))


class ManifestError(Exception):
    pass


def is_forbidden(relpath):
    """True for a path (relative to ROOT, POSIX or Windows separators) this tool must never open."""
    p = relpath.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    base = p.rstrip("/").rsplit("/", 1)[-1]
    return p == "results/results.jsonl" or base == "secrets.env" or base.endswith(".env")


def glob_may_hit_forbidden(pattern):
    last = pattern.rstrip("/").rsplit("/", 1)[-1]
    return (any(fnmatch.fnmatchcase(s, pattern) for s in FORBIDDEN_SAMPLES_FULL)
            or any(fnmatch.fnmatchcase(s, last) for s in FORBIDDEN_SAMPLES_BASE))


def guard_file(root, p):
    """Raise ManifestError when the concrete file p (or the target of a link) is forbidden."""
    rel = os.path.relpath(str(p), str(root)).replace(os.sep, "/")
    if is_forbidden(rel):
        raise ManifestError("ปฏิเสธไฟล์ต้องห้าม (ได้จากการขยาย glob หรือ folder): %s" % rel)
    if os.path.islink(str(p)):
        target = os.path.realpath(str(p))
        trel = os.path.relpath(target, os.path.realpath(str(root))).replace(os.sep, "/")
        if is_forbidden(trel) or is_forbidden(os.path.basename(target)):
            raise ManifestError("ปฏิเสธ link ที่ชี้ไฟล์ต้องห้าม: %s" % rel)


class Row:
    def __init__(self, lineno, path, amendment, gate, expected, label, stage):
        self.lineno, self.path, self.amendment, self.gate = lineno, path, amendment, gate
        self.expected, self.label, self.stage = expected, label, stage
        m = LINE_RANGE.match(path)
        self.line_range = (int(m.group(2)), int(m.group(3))) if m else None
        self.is_dir = path.endswith("/")
        self.is_glob = any(c in GLOB_CHARS for c in path)

    def base_path(self):
        m = LINE_RANGE.match(self.path)
        return m.group(1) if m else self.path

    def display(self):
        if self.label:
            return self.label
        if self.line_range:
            return "`%s` (บรรทัด %d–%d)" % (self.base_path(), self.line_range[0], self.line_range[1])
        return "`%s`" % self.path


def read_manifest(path):
    rows = []
    header = None
    for lineno, raw in enumerate(Path(path).read_text(encoding="utf-8").splitlines(), 1):
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        cells = raw.split("\t")
        if header is None:
            header = cells
            if header != COLUMNS:
                raise ManifestError("header ต้องเป็น %s (บรรทัด %d)" % ("\\t".join(COLUMNS), lineno))
            continue
        if len(cells) != len(COLUMNS):
            raise ManifestError("บรรทัด %d มี %d คอลัมน์ (ต้อง %d)" % (lineno, len(cells), len(COLUMNS)))
        path_, amend, gate, expected, label, stage = [c.strip() for c in cells]
        if not path_ or path_.startswith("/") or ".." in Path(path_).parts:
            raise ManifestError("บรรทัด %d: path ต้องสัมพัทธ์กับ ROOT" % lineno)
        if is_forbidden(LINE_RANGE.sub(r"\1", path_)):
            raise ManifestError("บรรทัด %d: ปฏิเสธไฟล์ต้องห้าม" % lineno)
        if amend not in AMENDMENT_ORDER:
            raise ManifestError("บรรทัด %d: amendment '%s' ไม่รู้จัก" % (lineno, amend))
        if gate not in GATES:
            raise ManifestError("บรรทัด %d: gate '%s' ไม่รู้จัก" % (lineno, gate))
        if stage not in STAGES:
            raise ManifestError("บรรทัด %d: stage '%s' ไม่รู้จัก" % (lineno, stage))
        if expected != "record" and not HEX64.match(expected) and not HEXPREFIX.match(expected):
            raise ManifestError("บรรทัด %d: expected_sha256 ต้องเป็น 64 hex, prefix ≥ 8 hex หรือ record" % lineno)
        under_kst = path_.startswith("kst_rev/")
        if stage == "external" and (not under_kst or not label):
            raise ManifestError("บรรทัด %d: stage external ต้องอยู่ใต้ kst_rev/ และมี label" % lineno)
        if stage != "external" and under_kst:
            raise ManifestError("บรรทัด %d: path ใต้ kst_rev/ ต้องเป็น stage external" % lineno)
        if path_ == PREREG_PATH and stage != "add-nostamp":
            raise ManifestError("บรรทัด %d: แถวทั้งไฟล์ของ prereg ต้องเป็น stage add-nostamp "
                                "(hash ทั้งไฟล์เปลี่ยนเมื่อวาง stamp; ใช้แถว #La-b สำหรับส่วนที่ตรึง)" % lineno)
        if stage == "add-nostamp" and (expected != "record" or label or LINE_RANGE.match(path_)):
            raise ManifestError("บรรทัด %d: stage add-nostamp ใช้ได้กับแถวทั้งไฟล์ที่ไม่มีค่าคาดและไม่มี label" % lineno)
        row = Row(lineno, path_, amend, gate, expected, label, stage)
        if row.is_glob and (row.is_dir or row.line_range):
            raise ManifestError("บรรทัด %d: glob ใช้ได้กับไฟล์เดียวเท่านั้น" % lineno)
        if row.is_glob and glob_may_hit_forbidden(path_):
            raise ManifestError("บรรทัด %d: glob นี้อาจตรงกับไฟล์ต้องห้าม" % lineno)
        rows.append(row)
    if header is None:
        raise ManifestError("manifest ว่าง")
    return rows


def sha256_file(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def sha256_lines(p, a, b):
    with open(p, "rb") as f:
        lines = f.read().splitlines(keepends=True)
    if len(lines) < b or a < 1 or a > b:
        raise FileNotFoundError("ไฟล์มี %d บรรทัด ขอ %d–%d" % (len(lines), a, b))
    return hashlib.sha256(b"".join(lines[a - 1:b])).hexdigest()


def tree_files(folder, root=None):
    """Sorted [(relative POSIX path, Path)] of the files a tree hash covers. Every file (and every link
    target) is checked against the forbidden list BEFORE anything is opened (ManifestError)."""
    root = root if root is not None else folder
    files = []
    for f in sorted(folder.rglob("*"), key=lambda x: x.relative_to(folder).as_posix()):
        rel = f.relative_to(folder)
        if "__pycache__" in rel.parts or f.name == ".DS_Store" or not (f.is_file() or f.is_symlink()):
            continue
        guard_file(root, f)
        if f.is_file():
            files.append((rel.as_posix(), f))
    return files


def tree_hash(folder, root=None):
    entries = ["%s\t%s\n" % (rel, sha256_file(f)) for rel, f in tree_files(folder, root)]
    return hashlib.sha256("".join(entries).encode("utf-8")).hexdigest(), len(entries)


def resolve(root, row):
    """Return the concrete Path of a row or raise FileNotFoundError (ManifestError for a forbidden file)."""
    if row.is_glob:
        matches = sorted(root.glob(row.path))
        for m in matches:
            guard_file(root, m)
        if len(matches) != 1:
            raise FileNotFoundError("glob ได้ %d ไฟล์ (ต้อง 1)" % len(matches))
        return matches[0]
    p = root / row.base_path()
    if row.is_dir:
        if not p.is_dir():
            raise FileNotFoundError("ไม่พบโฟลเดอร์")
        return p
    guard_file(root, p)
    if not p.is_file():
        raise FileNotFoundError("ไม่พบไฟล์")
    return p


def hash_row(root, row):
    """Return (sha256, n_files or None)."""
    p = resolve(root, row)
    if row.is_dir:
        return tree_hash(p, root)
    if row.line_range:
        return sha256_lines(p, *row.line_range), None
    return sha256_file(p), None


def matches_expected(expected, actual):
    if expected == "record":
        return None
    if HEX64.match(expected):
        return expected == actual
    return actual.startswith(HEXPREFIX.match(expected).group(1))


def stamp(root, rows, out=sys.stdout, manifest_name="", manifest_sha=""):
    """Print the tables and the check block; return the exit code. ManifestError propagates (exit 2)
    before anything is printed."""
    # forbidden-file guard for every row first, so that a bad row stops the run before any file is read
    for r in rows:
        if r.stage == "add-nostamp":
            continue
        try:
            if r.is_dir and (root / r.base_path()).is_dir():
                tree_files(root / r.base_path(), root)
            else:
                resolve(root, r)
        except FileNotFoundError:
            pass
    results, nostamp = [], []
    for r in rows:
        if r.stage == "add-nostamp":
            nostamp.append(r)
            continue
        try:
            sha, n = hash_row(root, r)
            ok = matches_expected(r.expected, sha)
            if ok is None and r.stage == "pinned":
                results.append((r, sha, n, False, "แถว pinned ไม่มีค่าคาด (record) จึงตรวจการเปลี่ยนไม่ได้; "
                                                 "คัดลอกค่าที่บันทึกใน gate ก่อนหน้าลง expected_sha256"))
                continue
            results.append((r, sha, n, ok, None))
        except FileNotFoundError as e:
            results.append((r, None, None, False, str(e) or "ไม่พบไฟล์"))
    now = dt.datetime.now(ICT).strftime("%Y-%m-%d %H:%M:%S")
    print("manifest: %s sha256 %s; เวลา (ICT) %s" % (manifest_name, manifest_sha, now), file=out)
    for amend in AMENDMENT_ORDER:
        group = [x for x in results if x[0].amendment == amend]
        if not group:
            continue
        print("", file=out)
        print("#### %s" % amend, file=out)
        print("| ไฟล์ | sha256 |", file=out)
        print("|---|---|", file=out)
        for r, sha, n, ok, err in group:
            name = r.display()
            if r.is_dir and n is not None:
                name += " (%d ไฟล์; tree hash)" % n
            print("| %s | %s |" % (name, ("`%s`" % sha) if sha else "[ไม่พบ]"), file=out)
    print("", file=out)
    print("ผลตรวจ (สำหรับแชตเท่านั้น ไม่ต้องวางใน prereg)", file=out)
    n_ok = n_rec = n_fail = 0
    for r, sha, n, ok, err in results:
        name = r.label or r.path
        if err:
            n_fail += 1
            print("- FAIL %s: %s" % (name, err), file=out)
        elif ok is None:
            n_rec += 1
        elif ok:
            n_ok += 1
            print("- OK %s: ตรงค่าคาด%s" % (name, "" if HEX64.match(r.expected) else " (เทียบ prefix)"), file=out)
        else:
            n_fail += 1
            print("- FAIL %s: ไม่ตรงค่าคาด (คาด %s…, ได้ %s…)" % (name, r.expected[:12], sha[:12]), file=out)
    for r in nostamp:
        print("- ไม่พิมพ์ %s: stage add-nostamp (stage ใน commit นี้; sha256 หลังต่อท้ายบันทึกใน addendum ของ gate ถัดไป)"
              % r.path, file=out)
    print("สรุป: %d แถว; ตรงค่าคาด %d; บันทึกใหม่ %d; FAIL %d; ไม่พิมพ์ (add-nostamp) %d"
          % (len(results), n_ok, n_rec, n_fail, len(nostamp)), file=out)
    return 1 if n_fail else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="hash a freeze manifest and print FREEZE STAMP rows")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--root", default=str(DEFAULT_ROOT), help="project ROOT (default: three levels above this file)")
    ap.add_argument("--gate", choices=sorted(GATES), default=None, help="only rows of this gate")
    a = ap.parse_args(argv)
    mpath = Path(a.manifest)
    try:
        rows = read_manifest(mpath)
    except (ManifestError, OSError) as e:
        print("ERROR manifest: %s" % e)
        return 2
    if a.gate:
        rows = [r for r in rows if r.gate == a.gate]
    try:
        return stamp(Path(a.root).resolve(), rows, manifest_name=mpath.name, manifest_sha=sha256_file(mpath))
    except ManifestError as e:
        print("ERROR manifest: %s" % e)
        return 2


if __name__ == "__main__":
    sys.exit(main())
