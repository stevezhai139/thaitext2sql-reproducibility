#!/usr/bin/env python3
"""prereg_append_check.py -- check prereg/preregistration_FROZEN.md after amendments are appended (Gate 0 tool; runs in place).

RUNBOOK_v2: Gate 1a step 76 (base = 115 lines, 269e5f09…), Gate 2 step 31 and Gate 3 step 62 (base = the
prereg of the previous commit). Checks, each printed as PASS/FAIL:
  1. base      lines 1..--base-lines have sha256 --base-sha (the frozen part is byte-identical).
  2. order     '## AMENDMENT-N' headings appended after the base are numbered above every amendment of
               the base and strictly increasing; --expect-amendments fixes the exact list (Gate 1b: 6,7,8,9).
               Inside AMENDMENT-7 the sections of AM7_REQUIRED_ORDER appear in that order (OQ1 default:
               Part 0 (D10) first, then the data rule 'None' → NULL, then Part C).
  3. slots     no unfilled slot remains: [กรอก…], [ผู้เขียนยืนยัน…], [ผู้เขียนเลือก…], [ยืนยัน…], [เลข],
               [วันที่ commit], '[ ]', any bracket token with Thai text, ASCII choice slots such as
               [VG9/VG10] or [n=59 primary], angle placeholders with Thai text such as
               <sha256 จากขั้น 1a.55>, and the words TODO, TBD and XXX. A9 sentence templates
               (A9_TEMPLATE_TOKENS, e.g. [GF_B]) and --allow-token values are allowed. Tokens may span lines.
  0. eol       the file ends with a newline, so `wc -l` (RUNBOOK 1a.78, 2.31c, 3.62c) counts every line and
               the next gate's --base-lines/--base-sha pair describes the whole file.
  4. markers   no author-note block, append markers, '(ร่าง)' heading, PENDING-AUTHOR marker, or internal
               question code (OQ…; those codes belong to the Gate 0 documents, not to the preregistration).
  5. identity  no identity pattern (anon_sweep.py) in the appended text.
  6. hashes    every sha256 written in an appended FREEZE STAMP table row (| file | sha256 |) or in an
               inline "`path` sha256: `hex`" equals the file on disk (full value or prefix). Labels are
               resolved through --manifest (the freeze manifests).
               - A whole-file value of the preregistration itself can only describe the file BEFORE this
                 append (a file cannot hold its own hash): it must equal the sha256 of lines
                 1..--base-lines (= --base-sha), e.g. the value of step 1a.77 written in the Gate 2 addendum.
                 A row whose name is not a path but mentions 'prereg' is read the same way.
               - Names that are neither a path nor a label FAIL ("unverified"), unless they are known
                 non-file values (NONFILE_NAMES: commit hashes, the pre-shuffle and item-list sha256 of the
                 chat check, hint blocks, model digests, GGUF) or are named with --allow-unverified.
               - A path must be relative to ROOT and stay inside it; harness/secrets.env, any *.env and
                 results/results.jsonl are never opened, also not inside a folder (tree hash) or glob:
                 such a row FAILs as 'ไฟล์ต้องห้ามใน FREEZE STAMP'.
Exit 0 all PASS, 1 any FAIL, 2 usage error. Run with: python3 -I -B prereg_append_check.py ...
"""
import sys

sys.dont_write_bytecode = True

import argparse
import hashlib
import importlib.util
import os
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
DEFAULT_ROOT = HERE.parents[2]

# Order of sections inside AMENDMENT-7 (OQ1/OQ1.2 defaults; change here only).
AM7_REQUIRED_ORDER = [
    ("Part 0", re.compile(r"^###\s+Part 0\b")),
    ("กฎข้อมูล 'None' → NULL", re.compile(r"^###\s+.*(กฎข้อมูล|'None'\s*→\s*NULL)")),
    ("Part C", re.compile(r"^###\s+Part C\b")),
]
# Sentence templates of AMENDMENT-7 A9 / B3-B5 that stay in brackets in the preregistration.
A9_TEMPLATE_TOKENS = {
    "GF_B", "GF_V", "VI", "x", "y", "z", "a", "N", "s", "lo, hi", "9", "10", "k", "<schema>", "RESULT",
    "most | all", "a1", "a2", "a3", "N1", "N2", "N3", "g1", "g2", "g3", "x1", "x2", "x3", "model",
    "100 − (c)", "app", "date",
}
ASCII_SLOTS = re.compile(r"^(n=\d+ primary|[A-Za-z0-9.+ -]+/[A-Za-z0-9.+ /-]+)$")
SLOT_PREFIXES = ("กรอก", "ผู้เขียนยืนยัน", "ผู้เขียนเลือก", "ผู้เขียนตรวจ", "ผู้เขียนตัดสิน", "ยืนยัน", "เลข", "วันที่ commit")
THAI = re.compile(r"[฀-๿]")
TOKEN = re.compile(r"\[([^\[\]]*)\](?!\()", re.S)
ANGLE_SLOT = re.compile(r"<[^<>\n]*[฀-๿][^<>\n]*>")
WORD_SLOT = re.compile(r"\b(TODO|TBD|XXX)\b")
MARKERS = ["หมายเหตุถึงผู้เขียน", "ข้อความที่ต่อท้าย prereg เริ่มที่นี่", "ข้อความที่ต่อท้าย prereg จบที่นี่", "PENDING-AUTHOR"]
OQ_CODE = re.compile(r"\bOQ\d+(?:\.\d+)?\b")
AMEND_HEAD = re.compile(r"^##\s+AMENDMENT-(\d+)\b")
HEXTOK = re.compile(r"\b([0-9a-f]{8,64})(?:…|\.\.\.)?")
INLINE_HASH = re.compile(r"`([^`]+)`\s*sha256:?\s*`?([0-9a-f]{8,64})")
RANGE_TH = re.compile(r"\(บรรทัด\s*(\d+)\s*[–-]\s*(\d+)\)")
# Hash values that do not describe a file in the repository; reported, never opened, never failed.
NONFILE_NAMES = re.compile(r"commit|pre-shuffle|pre_shuffle|items_sha256|รายการ 18 ข้อ|ลำดับก่อนสลับ|block|digest|GGUF",
                           re.IGNORECASE)


def _load_sibling(name):
    spec = importlib.util.spec_from_file_location("g0_" + name, HERE / (name + ".py"))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def find_slots(text, allow=()):
    """Return [(line_no, token)] of unfilled slots in text (line_no relative to text), in text order."""
    allowed = set(A9_TEMPLATE_TOKENS) | set(allow)
    out = []
    for m in TOKEN.finditer(text):
        tok = m.group(1)
        if tok in allowed:
            continue
        flat = " ".join(tok.split())
        is_slot = (tok.strip() == "" or THAI.search(tok) or flat.startswith(SLOT_PREFIXES) or ASCII_SLOTS.match(flat))
        if is_slot and not flat.startswith("http"):
            out.append((m.start(), flat[:60]))
    for rx in (ANGLE_SLOT, WORD_SLOT):
        for m in rx.finditer(text):
            if m.group(0) in allowed or m.group(0).strip("<>") in allowed:
                continue
            out.append((m.start(), " ".join(m.group(0).split())[:60]))
    out.sort()
    return [(text.count("\n", 0, pos) + 1, tok) for pos, tok in out]


def check_order(base_lines, app_lines, expect):
    msgs = []
    base_max = max([int(m.group(1)) for m in (AMEND_HEAD.match(l) for l in base_lines) if m] or [0])
    nums = []
    for l in app_lines:
        m = AMEND_HEAD.match(l)
        if m:
            nums.append(int(m.group(1)))
    if nums and nums[0] <= base_max:
        msgs.append("AMENDMENT-%d ไม่มากกว่า AMENDMENT สูงสุดของส่วนเดิม (%d)" % (nums[0], base_max))
    if any(b <= a for a, b in zip(nums, nums[1:])):
        msgs.append("ลำดับ AMENDMENT ไม่เพิ่มขึ้นอย่างเคร่ง: %s" % ", ".join(map(str, nums)))
    if expect is not None and nums != expect:
        msgs.append("AMENDMENT ที่ต่อท้าย %s ไม่ตรงกับที่คาด %s" % (nums or "ไม่มี", expect))
    # sections inside AMENDMENT-7
    in7, seen = False, []
    for l in app_lines:
        m = AMEND_HEAD.match(l)
        if m:
            in7 = int(m.group(1)) == 7
            continue
        if in7:
            for name, rx in AM7_REQUIRED_ORDER:
                if rx.match(l) and name not in seen:
                    seen.append(name)
    if 7 in nums:
        want = [n for n, _ in AM7_REQUIRED_ORDER]
        missing = [n for n in want if n not in seen]
        if missing:
            msgs.append("AMENDMENT-7 ไม่มีหัวข้อ: %s" % ", ".join(missing))
        elif seen != want:
            msgs.append("หัวข้อใน AMENDMENT-7 ไม่เรียงตามมติ: %s" % " → ".join(seen))
    return msgs


def parse_names(cell):
    """Split a FREEZE STAMP file cell into [(name, line_range or None)]."""
    cell = cell.strip()
    rng = RANGE_TH.search(cell)
    lr = (int(rng.group(1)), int(rng.group(2))) if rng else None
    cell = RANGE_TH.sub("", cell)
    cell = re.sub(r"\(\d+ ไฟล์; tree hash\)", "", cell)
    names = []
    first_dir = ""
    for part in [p.strip().strip("`").strip() for p in cell.split(" / ")]:
        if not part:
            continue
        m = re.match(r"^(.*)#L(\d+)-(\d+)$", part)
        plr = lr
        if m:
            part, plr = m.group(1), (int(m.group(2)), int(m.group(3)))
        if "/" in part and not first_dir:
            first_dir = part.rsplit("/", 1)[0] if not part.endswith("/") else ""
        elif "/" not in part and first_dir and "." in part:
            part = first_dir + "/" + part
        names.append((part, plr))
    return names


def collect_claims(app_lines):
    """[(appended line no, name, line_range, hex)] of every hash claim in the appended text."""
    claims = []
    for no, line in enumerate(app_lines, 1):
        s = line.strip()
        if s.startswith("|") and s.endswith("|") and not re.match(r"^\|[\s|:-]+\|$", s):
            cells = [c.strip() for c in s.strip("|").split("|")]
            if len(cells) >= 2:
                hexes = [h for h in HEXTOK.findall(cells[1])]
                if hexes:
                    names = parse_names(cells[0])
                    if len(names) == len(hexes):
                        claims += [(no, n, lr, h) for (n, lr), h in zip(names, hexes)]
                    elif names:
                        claims.append((no, names[0][0], names[0][1], hexes[0]))
        for m in INLINE_HASH.finditer(line):
            claims.append((no, m.group(1), None, m.group(2)))
    return claims


class Forbidden(Exception):
    pass


def safe_target(root, path):
    """Path inside root for a claim path, or raise Forbidden / FileNotFoundError without opening anything."""
    if path.startswith("/") or path.startswith("~") or ".." in Path(path.rstrip("/") or ".").parts:
        raise Forbidden("path ต้องสัมพัทธ์กับ ROOT และไม่ออกนอก ROOT")
    if is_forbidden_claim(path):
        raise Forbidden("ไฟล์ต้องห้ามใน FREEZE STAMP")
    return path


def is_forbidden_claim(path):
    p = path.replace("\\", "/")
    while p.startswith("./"):
        p = p[2:]
    base = p.rstrip("/").rsplit("/", 1)[-1]
    return p == "results/results.jsonl" or base == "secrets.env" or base.endswith(".env")


def verify_hashes(app_lines, root, labels, fs, prereg_path=None, base_sha=None, allow_unverified=()):
    """Return (n_checked, notes, [fail messages])."""
    checked, nonfile, fails = 0, [], []
    prereg_real = os.path.realpath(str(prereg_path)) if prereg_path else None
    for no, name, lr, hexv in collect_claims(app_lines):
        path, rng = None, lr
        if name in labels:
            path = labels[name]
        elif "/" in name or re.search(r"\.[A-Za-z0-9]{1,5}$", name):
            path = name
        if path is None and re.search(r"prereg", name, re.IGNORECASE):
            path, rng = fs.PREREG_PATH, None
        if path is None:
            if NONFILE_NAMES.search(name):
                nonfile.append(name)
            elif name in allow_unverified:
                nonfile.append(name + " (--allow-unverified)")
            else:
                fails.append("บรรทัดต่อท้าย %d: '%s' ไม่ใช่ path หรือ label ที่รู้จัก จึงตรวจค่าไม่ได้ "
                             "(พิมพ์ label ผิด? ส่ง --manifest ของ gate นั้น หรือ --allow-unverified \"%s\" ถ้าตั้งใจ)"
                             % (no, name[:60], name[:60]))
            continue
        try:
            safe_target(root, path)
            is_prereg = rng is None and not path.endswith("/") and (
                path == fs.PREREG_PATH or (prereg_real and os.path.realpath(str(root / path)) == prereg_real))
            if is_prereg:
                checked += 1
                if base_sha and base_sha.startswith(hexv):
                    continue
                fails.append("บรรทัดต่อท้าย %d: %s — ค่า sha256 ทั้งไฟล์ของ prereg ใน FREEZE STAMP ต้องเป็นค่าก่อนต่อท้าย "
                             "(= --base-sha %s…) เพราะไฟล์มี hash ของตัวเองไม่ได้; ใช้แถว (บรรทัด 1–N) แทน และบันทึก "
                             "ค่าหลังต่อท้ายใน addendum ของ gate ถัดไป (ได้ %s…)" % (no, name, (base_sha or "")[:12], hexv[:12]))
                continue
            if any(c in path for c in "*?["):
                if fs.glob_may_hit_forbidden(path):
                    raise Forbidden("glob อาจตรงกับไฟล์ต้องห้าม")
                hits = sorted(root.glob(path))
                for h in hits:
                    fs.guard_file(root, h)
                if len(hits) != 1:
                    raise FileNotFoundError("glob ได้ %d ไฟล์" % len(hits))
                p = hits[0]
            else:
                p = root / path.rstrip("/")
            if os.path.realpath(str(p)) != os.path.realpath(str(root)) and \
                    not os.path.realpath(str(p)).startswith(os.path.realpath(str(root)) + os.sep):
                raise Forbidden("path ออกนอก ROOT")
            if path.endswith("/") or p.is_dir():
                actual, _ = fs.tree_hash(p, root)
            else:
                fs.guard_file(root, p)
                if rng:
                    actual = fs.sha256_lines(p, *rng)
                else:
                    if not p.is_file():
                        raise FileNotFoundError("ไม่พบไฟล์")
                    actual = fs.sha256_file(p)
        except (Forbidden, fs.ManifestError) as e:
            fails.append("บรรทัดต่อท้าย %d: %s — ไฟล์ต้องห้ามใน FREEZE STAMP หรือ path ไม่ปลอดภัย (%s); ไม่ได้เปิดไฟล์"
                         % (no, name[:60], str(e)[:80]))
            continue
        except FileNotFoundError as e:
            fails.append("บรรทัดต่อท้าย %d: %s — %s" % (no, name, e))
            continue
        checked += 1
        if not actual.startswith(hexv):
            fails.append("บรรทัดต่อท้าย %d: %s — sha256 ใน FREEZE STAMP (%s…) ไม่ตรงกับไฟล์ (%s…)" % (no, name, hexv[:12], actual[:12]))
    return checked, nonfile, fails


def main(argv=None):
    ap = argparse.ArgumentParser(description="check the preregistration after appending amendments")
    ap.add_argument("--prereg", required=True)
    ap.add_argument("--base-sha", required=True)
    ap.add_argument("--base-lines", required=True, type=int)
    ap.add_argument("--expect-amendments", default=None, help='e.g. "6,7,8,9" (Gate 1b)')
    ap.add_argument("--manifest", action="append", default=[], help="freeze manifest(s) for label lookup")
    ap.add_argument("--allow-token", action="append", default=[], help="extra bracket token that is not a slot")
    ap.add_argument("--allow-unverified", action="append", default=[],
                    help="exact name of a hash claim that is not a file (repeatable); otherwise such a name FAILs")
    ap.add_argument("--root", default=str(DEFAULT_ROOT))
    ap.add_argument("--extra-patterns", default="", help="passed to the identity sweep")
    ap.add_argument("--no-runtime", action="store_true", help="identity sweep without user/host patterns")
    a = ap.parse_args(argv)
    if not re.fullmatch(r"[0-9a-f]{64}", a.base_sha):
        ap.error("--base-sha ต้องเป็น sha256 64 hex")
    root = Path(a.root).resolve()
    fs = _load_sibling("freeze_stamp")
    sw = _load_sibling("anon_sweep")

    data = Path(a.prereg).read_bytes()
    lines_b = data.splitlines(keepends=True)
    results = []

    base_ok = len(lines_b) >= a.base_lines and hashlib.sha256(b"".join(lines_b[:a.base_lines])).hexdigest() == a.base_sha
    results.append(("base", base_ok, [] if base_ok else ["บรรทัด 1–%d ไม่ตรงกับ sha256 ที่ให้" % a.base_lines]))

    text = data.decode("utf-8")
    all_lines = text.split("\n")
    base_lines, app_lines = all_lines[:a.base_lines], all_lines[a.base_lines:]
    app_text = "\n".join(app_lines)
    if not app_text.strip():
        results.append(("appended", False, ["ไม่มีข้อความต่อท้ายหลังบรรทัด %d" % a.base_lines]))
    eol_ok = data.endswith(b"\n")
    results.append(("eol", eol_ok, [] if eol_ok else ["ไฟล์ไม่จบด้วยการขึ้นบรรทัดใหม่: เพิ่มบรรทัดว่างท้ายไฟล์ "
                                                     "(wc -l ของ gate ถัดไปจะนับบรรทัดสุดท้ายไม่ได้)"]))

    expect = [int(x) for x in a.expect_amendments.split(",")] if a.expect_amendments else None
    msgs = check_order(base_lines, app_lines, expect)
    results.append(("order", not msgs, msgs))

    slots = find_slots(app_text, a.allow_token)
    results.append(("slots", not slots, ["บรรทัดต่อท้าย %d: [%s]" % s for s in slots]))

    mk = []
    for no, l in enumerate(app_lines, 1):
        for m in MARKERS:
            if m in l:
                mk.append("บรรทัดต่อท้าย %d: พบ '%s'" % (no, m))
        if l.startswith("#") and "(ร่าง)" in l:
            mk.append("บรรทัดต่อท้าย %d: หัวข้อยังมี '(ร่าง)'" % no)
        for m in OQ_CODE.finditer(l):
            mk.append("บรรทัดต่อท้าย %d: รหัสคำถามภายใน '%s' (ลบออกจากข้อความที่ต่อท้าย)" % (no, m.group(0)))
    results.append(("markers", not mk, mk))

    ps = sw.build_patterns(root, a.extra_patterns, not a.no_runtime)
    idh = ["บรรทัดต่อท้าย %d [%s]" % (no, ",".join(ids)) for no, ids in ps.scan_text(app_text)]
    results.append(("identity", not idh, idh))

    labels = {}
    for mf in a.manifest:
        try:
            rows = fs.read_manifest(Path(mf))
        except (fs.ManifestError, OSError) as e:
            print("ERROR manifest %s: %s" % (Path(mf).name, e))
            return 2
        for r in rows:
            if r.label:
                labels[r.label] = r.path
    checked, nonfile, fails = verify_hashes(app_lines, root, labels, fs, prereg_path=Path(a.prereg),
                                            base_sha=a.base_sha, allow_unverified=set(a.allow_unverified))
    notes = ["ตรวจ %d ค่า; ค่าที่ไม่ใช่ไฟล์ (ไม่ตรวจ) %d ค่า%s" % (checked, len(nonfile),
             (": " + ", ".join(n[:40] for n in nonfile[:8])) if nonfile else "")]
    results.append(("hashes", not fails, fails + notes))

    bad = 0
    for name, ok, details in results:
        print("%s %s" % ("PASS" if ok else "FAIL", name))
        for d in details:
            print("  - %s" % d)
        bad += 0 if ok else 1
    print("สรุป: %s (%d จาก %d หัวข้อไม่ผ่าน)" % ("PASS" if not bad else "FAIL", bad, len(results)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
