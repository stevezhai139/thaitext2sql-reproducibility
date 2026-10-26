#!/usr/bin/env python3
"""chat_log_export.py -- check the filled CHAT_LOG.xlsx and the raw reply files, then
write log_index.tsv and raw_manifest.tsv (prereg AMENDMENT-8 sec.6-7).

Checks (any failure -> exit 1, nothing written):
  prompts   every prompts/<prompt_id>.txt still has the sha256 recorded in cells.tsv;
            prompts/TURN2.txt equals the AMENDMENT-8 sec.6 text; cells_meta.json (beside
            cells.tsv) exists and records the sha256 of cells.tsv
  rows      app in {chatgpt, gemini, claude}; order 1..28 with the prompt_id of
            cells.tsv; attempt >= 1 and unique per (app, prompt_id); status done|void
            (blank = row not filled); void needs a note; a void row without ts_sent_ict
            needs a note that starts with 'not sent' (or 'ไม่ได้ส่ง'), so a sent void chat
            cannot escape the time checks; turn2_sent Y|N|blank
  coverage  exactly one done row per (app, prompt_id) for all 28 x 3 = 84 pairs, and it
            is the highest attempt of that pair
  times     ICT, YYYY-MM-DD HH:MM:SS (or Excel datetime); done rows need ts_sent and
            ts_done with ts_sent <= ts_done; ts_done needs ts_sent; --not-before is not
            earlier than created_at_ict of cells_meta.json (the prompt build), so the
            NOT_BEFORE of Gate 1b passed by mistake is refused; every ts_sent (done and
            void rows) >= --not-before; attempts of a pair are sent in attempt order; per app the
            first attempts are sent in order 1..28; all sent rows (done and void) fall
            within 3 consecutive calendar days (OQ33.9 default: max date - min date <= 2
            days); the cross-app cell-major order of AMENDMENT-8 sec.5 is a NOTE or a FAIL
            per the DEFAULT switch CELL_MAJOR_BREACH in make_chat_cells.py (chat_report.py
            recomputes the count from log_index.tsv and records it)
  files     done rows: raw_file exists under --raw-dir, is non-empty UTF-8; turn2_sent Y:
            raw2_file likewise; a row's raw2_file that exists on disk while its
            turn2_sent is not Y is a FAIL (a saved turn-2 reply would otherwise be dropped);
            raw_file, raw2_file and screenshot (required on done rows) must be exactly the
            names make_chat_cells.raw_name / shot_name build from the row's app, prompt_id
            and attempt, so a row cannot point at another app's or cell's reply
  setup     every SETUP_FIELDS value is filled (Y fields must be Y)
Outputs under --out-dir (refuses to overwrite either file):
  log_index.tsv     LOG_COLUMNS, one row per filled log row (done and void), sorted
                    cell-major (order, app, attempt); times as YYYY-MM-DDTHH:MM:SS; raw
                    paths relative to --out-dir; raw2_file blank unless turn2_sent = Y
  raw_manifest.tsv  path (relative to --out-dir), bytes, sha256 of every referenced raw file
--verify: run every check again, rebuild both files in memory and compare them with the
files on disk byte for byte, and re-hash every file listed in raw_manifest.tsv
(append-only evidence); writes nothing; exit 1 on any difference.
--not-before is CHAT_NOT_BEFORE: the commit time (ICT, RUNBOOK_v2 step 2.38b: git log -1
--format=%cd --date=format:%Y-%m-%dT%H:%M:%S) of the Gate 2 commit that froze the item
list and the AMENDMENT-8 FREEZE STAMP and was pushed before the first chat (GATES_CHECKLIST
sec.10; RUNBOOK_v2 C.2 and C.10). It is not the Gate 1b NOT_BEFORE: the draw and the prompt
build come after Gate 1b, so that value is earlier than the prompt build and is refused.

Run with openpyxl available: python3 -B -E -P. Never reads results*.jsonl.

Usage (from harness/):
  python3 -B -E -P "chatapp/chat_log_export.py" --xlsx "../results/chat/CHAT_LOG.xlsx"
      --raw-dir "../results/chat/raw" --prompts-dir "../results/chat/prompts"
      --not-before "<CHAT_NOT_BEFORE>" --out-dir "../results/chat" [--verify]
"""
import sys

sys.dont_write_bytecode = True

import argparse  # noqa: E402
import csv  # noqa: E402
import datetime as dt  # noqa: E402
import io  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import re  # noqa: E402
from collections import defaultdict  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from draw_chat_items_v13 import die, sha256_file  # noqa: E402
from make_chat_cells import (APPS, CELLS_PER_APP, CELL_MAJOR_BREACH, CHAT_SPAN_MAX_DAYS,  # noqa: E402
                             LOG_COLUMNS, TS_FMT, TURN2_FILE, TURN2_TEXT, cell_major_breaches,
                             check_switches, raw_name, read_cells, sha256_text, shot_name)
from make_chat_log_xlsx import SETUP_FIELDS, STATUS_VALUES  # noqa: E402

NOT_BEFORE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")
TS_FORMATS = ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M")
MANIFEST_COLUMNS = ["path", "bytes", "sha256"]
NOT_SENT_NOTE = ("not sent", "ไม่ได้ส่ง")


def parse_ts(v):
    """Excel datetime or text -> naive ICT datetime; None when blank; raises ValueError."""
    if v is None or (isinstance(v, str) and not v.strip()):
        return None
    if isinstance(v, dt.datetime):
        return v.replace(microsecond=0, tzinfo=None)
    if isinstance(v, dt.date):
        return dt.datetime(v.year, v.month, v.day)
    s = str(v).strip()
    for f in TS_FORMATS:
        try:
            return dt.datetime.strptime(s, f)
        except ValueError:
            pass
    raise ValueError(s)


def fmt_ts(t):
    return t.strftime("%Y-%m-%dT%H:%M:%S") if t else ""


def text(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def as_int(v):
    s = text(v)
    if not re.fullmatch(r"\d+", s):
        raise ValueError(s)
    return int(s)


def tsv_bytes(header, rows):
    buf = io.StringIO()
    w = csv.writer(buf, delimiter="\t", lineterminator="\n")
    w.writerow(header)
    w.writerows(rows)
    return buf.getvalue().encode("utf-8")


def check_prompts(cells_path, prompts_dir, errors):
    cells = read_cells(cells_path)
    if len(cells) != CELLS_PER_APP:
        errors.append(f"cells.tsv has {len(cells)} cells, expected {CELLS_PER_APP}")
    meta_path = os.path.join(os.path.dirname(cells_path), "cells_meta.json")
    meta = {}
    if not os.path.isfile(meta_path):
        errors.append("cells_meta.json (written by make_chat_cells.py beside cells.tsv) is missing")
    else:
        with open(meta_path, encoding="utf-8") as fh:
            meta = json.load(fh)
        if meta.get("cells_tsv_sha256") != sha256_file(cells_path):
            errors.append("cells.tsv sha256 differs from cells_meta.json")
    for c in cells:
        p = os.path.join(prompts_dir, os.path.basename(c["prompt_file"]))
        if not os.path.isfile(p):
            errors.append(f"prompt file missing: {c['prompt_id']}")
        elif sha256_file(p) != c["prompt_sha256"]:
            errors.append(f"prompt file changed: {c['prompt_id']}")
    t2 = os.path.join(prompts_dir, TURN2_FILE)
    if not os.path.isfile(t2) or sha256_file(t2) != sha256_text(TURN2_TEXT):
        errors.append(f"{TURN2_FILE} missing or changed")
    return {c["order"]: c for c in cells}, meta


def read_log(xlsx, errors):
    from openpyxl import load_workbook
    wb = load_workbook(xlsx, data_only=True)
    for name in ("log", "setup"):
        if name not in wb.sheetnames:
            errors.append(f"sheet '{name}' missing")
            return [], {}
    ws = wb["log"]
    rows = list(ws.iter_rows(values_only=True))
    header = [text(x) for x in rows[0]] if rows else []
    if header[:len(LOG_COLUMNS)] != LOG_COLUMNS:
        errors.append(f"log header is not {LOG_COLUMNS}")
        return [], {}
    out = []
    for i, r in enumerate(rows[1:], 2):
        vals = dict(zip(LOG_COLUMNS, r[:len(LOG_COLUMNS)]))
        if all(text(v) == "" for v in vals.values()):
            continue
        vals["_row"] = i
        out.append(vals)
    setup = {}
    for r in wb["setup"].iter_rows(min_row=2, values_only=True):
        if r and text(r[0]):
            setup[text(r[0])] = text(r[2] if len(r) > 2 else None)
    return out, setup


def validate(a, errors, warnings):
    cells_path = a.cells or os.path.join(os.path.dirname(os.path.abspath(a.prompts_dir)), "cells.tsv")
    by_order, meta = check_prompts(cells_path, a.prompts_dir, errors)
    rows, setup = read_log(a.xlsx, errors)
    nb = dt.datetime.strptime(a.not_before, "%Y-%m-%dT%H:%M:%S")
    built = meta.get("created_at_ict")
    built_t = dt.datetime.strptime(built, TS_FMT) if built else None
    if meta and not built:
        errors.append("cells_meta.json has no created_at_ict (rebuild the cells with the current make_chat_cells.py)")
    elif built_t and nb < built_t:
        errors.append(f"--not-before {a.not_before} is earlier than the prompt build ({built}, cells_meta.json); "
                      "pass CHAT_NOT_BEFORE, the Gate 2 commit time of RUNBOOK step 2.38b (the NOT_BEFORE of "
                      "Gate 1b is earlier)")
    bound, bound_name = nb, "--not-before"
    a.bound_text = f"{fmt_ts(bound)} (--not-before; prompt build {built or 'unknown'})"

    for key, _label, kind in SETUP_FIELDS:
        v = setup.get(key, "")
        if kind == "Y" and v.upper() != "Y":
            errors.append(f"setup: {key} must be Y")
        elif kind == "text" and not v:
            errors.append(f"setup: {key} is blank")

    recs = []
    names_seen = {}
    for v in rows:
        rn = v["_row"]
        r = {"_row": rn}
        try:
            r["app"] = text(v["app"])
            if r["app"] not in APPS:
                raise ValueError("app")
            r["order"] = as_int(v["order"])
            cell = by_order.get(r["order"])
            if cell is None:
                raise ValueError("order")
            r["prompt_id"] = text(v["prompt_id"])
            if r["prompt_id"] != cell["prompt_id"]:
                raise ValueError("prompt_id does not match order")
            r["attempt"] = as_int(v["attempt"])
            if r["attempt"] < 1:
                raise ValueError("attempt")
        except (ValueError, KeyError) as e:
            errors.append(f"log row {rn}: bad key columns ({e})")
            continue
        r["status"] = text(v["status"]).lower()
        if r["status"] not in STATUS_VALUES:
            errors.append(f"log row {rn}: status must be done or void (blank = not filled)")
            continue
        r["note"] = text(v["note"])
        if r["status"] == "void" and not r["note"]:
            errors.append(f"log row {rn}: void row needs a note")
        expect = {"raw_file": raw_name(r["app"], r["prompt_id"], r["attempt"]),
                  "raw2_file": raw_name(r["app"], r["prompt_id"], r["attempt"], 2),
                  "screenshot": shot_name(r["app"], r["prompt_id"], r["attempt"])}
        r["turn2_sent"] = text(v["turn2_sent"]).upper() or "N"
        if r["turn2_sent"] not in ("Y", "N"):
            errors.append(f"log row {rn}: turn2_sent must be Y or N")
        try:
            r["ts_sent"] = parse_ts(v["ts_sent_ict"])
            r["ts_done"] = parse_ts(v["ts_done_ict"])
        except ValueError:
            errors.append(f"log row {rn}: time not in YYYY-MM-DD HH:MM:SS")
            continue
        if r["status"] == "done" and (r["ts_sent"] is None or r["ts_done"] is None):
            errors.append(f"log row {rn}: done row needs ts_sent_ict and ts_done_ict")
        if r["ts_done"] and r["ts_sent"] is None:
            errors.append(f"log row {rn}: ts_done_ict without ts_sent_ict")
        if (r["status"] == "void" and r["ts_sent"] is None
                and not r["note"].lower().startswith(NOT_SENT_NOTE)):
            errors.append(f"log row {rn}: void row without ts_sent_ict needs a note that starts with "
                          f"'not sent' (a sent void chat must carry its times)")
        if r["ts_sent"] and r["ts_done"] and r["ts_done"] < r["ts_sent"]:
            errors.append(f"log row {rn}: ts_done_ict is before ts_sent_ict")
        if r["ts_sent"] and r["ts_sent"] < bound:
            errors.append(f"log row {rn}: ts_sent_ict is before {bound_name} ({fmt_ts(bound)})")
        for k in ("ui_model_label", "limit_banner", "tools_visible", "screenshot"):
            r[k] = text(v[k])
        if r["screenshot"] and r["screenshot"] != expect["screenshot"]:
            errors.append(f"log row {rn}: screenshot must be {expect['screenshot']} (app, prompt_id and attempt "
                          f"of the row)")
        elif r["status"] == "done" and not r["screenshot"]:
            errors.append(f"log row {rn}: screenshot is blank")
        for k, needed in (("raw_file", r["status"] == "done"),
                          ("raw2_file", r["status"] == "done" and r["turn2_sent"] == "Y")):
            name = text(v[k])
            r[k] = name
            if not name:
                if needed:
                    errors.append(f"log row {rn}: {k} is blank")
                continue
            if os.path.basename(name) != name:
                errors.append(f"log row {rn}: {k} must be a file name without folders")
                continue
            if name != expect[k]:
                errors.append(f"log row {rn}: {k} must be {expect[k]} (app, prompt_id and attempt of the row)")
                continue
            if name in names_seen:
                errors.append(f"log row {rn}: {k} {name} is also used by row {names_seen[name]}")
            names_seen[name] = rn
            p = os.path.join(a.raw_dir, name)
            r[k + "_exists"] = os.path.isfile(p)
            if k == "raw2_file" and r[k + "_exists"] and r["turn2_sent"] != "Y":
                errors.append(f"log row {rn}: {name} exists in --raw-dir but turn2_sent is not Y "
                              f"(set turn2_sent = Y if turn 2 was sent; otherwise the file does not "
                              f"belong to this row)")
            if needed:
                if not os.path.isfile(p) or os.path.getsize(p) == 0:
                    errors.append(f"log row {rn}: {k} missing or empty")
                else:
                    try:
                        with open(p, encoding="utf-8") as fh:
                            fh.read()
                    except UnicodeDecodeError:
                        errors.append(f"log row {rn}: {k} is not UTF-8")
        recs.append(r)

    groups = defaultdict(list)
    for r in recs:
        groups[(r["app"], r["prompt_id"])].append(r)
    for app in APPS:
        for order in sorted(by_order):
            pid = by_order[order]["prompt_id"]
            g = groups.get((app, pid), [])
            done = [r for r in g if r["status"] == "done"]
            if len(done) != 1:
                errors.append(f"{app} {pid}: {len(done)} done rows (need exactly 1)")
            atts = [r["attempt"] for r in g]
            if len(set(atts)) != len(atts):
                errors.append(f"{app} {pid}: repeated attempt number")
            if len(done) == 1 and done[0]["attempt"] != max(atts):
                errors.append(f"{app} {pid}: the done row is not the last attempt")
            sent = sorted((r["attempt"], r["ts_sent"]) for r in g if r["ts_sent"])
            if any(sent[i][1] > sent[i + 1][1] for i in range(len(sent) - 1)):
                errors.append(f"{app} {pid}: attempts are not in time order")
    for app in APPS:
        first = sorted((r["order"], r["ts_sent"]) for r in recs
                       if r["app"] == app and r["attempt"] == 1 and r["ts_sent"])
        bad = [first[i][0] for i in range(len(first) - 1) if first[i][1] >= first[i + 1][1]]
        if bad:
            errors.append(f"{app}: first attempts are not sent in order 1..28 (after order {bad[0]})")
    sent_dates = [r["ts_sent"].date() for r in recs if r["ts_sent"]]
    if sent_dates:
        span = (max(sent_dates) - min(sent_dates)).days
        if span > CHAT_SPAN_MAX_DAYS:
            errors.append(f"chats span {span + 1} calendar days ({min(sent_dates)} to {max(sent_dates)}); "
                          f"the limit is 3")
    # cell-major plan: cell i done in all apps before cell i+1 starts (shared rule)
    breach = cell_major_breaches(recs)
    if breach:
        msg = (f"{len(breach)} cells started before the previous cell was done in all three apps "
               f"(after orders {', '.join(str(o) for o in breach[:10])}; AMENDMENT-8 sec.5 cell-major order; "
               f"CELL_MAJOR_BREACH = {CELL_MAJOR_BREACH}; chat_report.py records the count as a deviation)")
        (errors if CELL_MAJOR_BREACH == "fail" else warnings).append(msg)
    on_disk = set(os.listdir(a.raw_dir)) if os.path.isdir(a.raw_dir) else set()
    stray = sorted(n for n in on_disk if not n.startswith(".") and n not in names_seen)
    if stray:
        warnings.append(f"{len(stray)} files in --raw-dir are not referenced by the log")
    return recs, sent_dates


def build_outputs(a, recs):
    out_dir = os.path.abspath(a.out_dir)
    app_rank = {x: i for i, x in enumerate(APPS)}
    idx_rows, manifest = [], {}
    for r in sorted(recs, key=lambda x: (x["order"], app_rank[x["app"]], x["attempt"])):
        rel = {}
        for k in ("raw_file", "raw2_file"):
            name = r.get(k, "")
            keep = name and (k == "raw_file" or r["turn2_sent"] == "Y")
            if keep and r.get(k + "_exists"):
                p = os.path.abspath(os.path.join(a.raw_dir, name))
                rel[k] = os.path.relpath(p, out_dir).replace(os.sep, "/")
                manifest[rel[k]] = (os.path.getsize(p), sha256_file(p))
            else:
                rel[k] = ""
        row = {"app": r["app"], "order": r["order"], "prompt_id": r["prompt_id"], "attempt": r["attempt"],
               "status": r["status"], "ts_sent_ict": fmt_ts(r["ts_sent"]), "ts_done_ict": fmt_ts(r["ts_done"]),
               "ui_model_label": r["ui_model_label"], "limit_banner": r["limit_banner"],
               "tools_visible": r["tools_visible"], "turn2_sent": r["turn2_sent"],
               "raw_file": rel["raw_file"], "raw2_file": rel["raw2_file"], "screenshot": r["screenshot"],
               "note": r["note"]}
        idx_rows.append([row[k] for k in LOG_COLUMNS])
    man_rows = [[p, b, s] for p, (b, s) in sorted(manifest.items())]
    return tsv_bytes(LOG_COLUMNS, idx_rows), tsv_bytes(MANIFEST_COLUMNS, man_rows), len(idx_rows), len(man_rows)


def verify_manifest(out_dir, errors):
    path = os.path.join(out_dir, "raw_manifest.tsv")
    with open(path, encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh, delimiter="\t"):
            p = os.path.join(out_dir, r["path"])
            if not os.path.isfile(p):
                errors.append(f"raw file listed in raw_manifest.tsv is missing: {r['path']}")
            elif str(os.path.getsize(p)) != r["bytes"] or sha256_file(p) != r["sha256"]:
                errors.append(f"raw file changed after export: {r['path']}")


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--xlsx", required=True)
    ap.add_argument("--raw-dir", required=True)
    ap.add_argument("--prompts-dir", required=True)
    ap.add_argument("--not-before", required=True,
                    help="CHAT_NOT_BEFORE: Gate 2 commit time (RUNBOOK 2.38b), YYYY-MM-DDTHH:MM:SS (ICT, no zone)")
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--cells", help="cells.tsv (default: next to --prompts-dir)")
    ap.add_argument("--verify", action="store_true")
    a = ap.parse_args()
    check_switches()
    if not NOT_BEFORE_RE.match(a.not_before):
        die("--not-before must look like YYYY-MM-DDTHH:MM:SS (no zone)")
    out_dir = os.path.abspath(a.out_dir)
    idx_path = os.path.join(out_dir, "log_index.tsv")
    man_path = os.path.join(out_dir, "raw_manifest.tsv")
    if not a.verify and (os.path.exists(idx_path) or os.path.exists(man_path)):
        die("log_index.tsv or raw_manifest.tsv exists; use --verify to re-check, never overwrite")
    if a.verify and not (os.path.exists(idx_path) and os.path.exists(man_path)):
        die("--verify needs log_index.tsv and raw_manifest.tsv under --out-dir")

    errors, warnings = [], []
    recs, dates = validate(a, errors, warnings)
    if a.verify and not errors:
        verify_manifest(out_dir, errors)
    idx_b, man_b, n_idx, n_man = build_outputs(a, recs) if not errors else (b"", b"", 0, 0)
    if a.verify and not errors:
        if open(idx_path, "rb").read() != idx_b:
            errors.append("log_index.tsv differs from the workbook (workbook changed after export)")
        if open(man_path, "rb").read() != man_b:
            errors.append("raw_manifest.tsv differs from the raw files on disk")
    for w in warnings:
        print("NOTE: " + w)
    if errors:
        for e in errors[:60]:
            print("FAIL: " + e)
        if len(errors) > 60:
            print(f"FAIL: ... {len(errors) - 60} more")
        print(f"RESULT: FAIL ({len(errors)} problems)")
        sys.exit(1)
    n_done = sum(1 for r in recs if r["status"] == "done")
    n_void = sum(1 for r in recs if r["status"] == "void")
    n_t2 = sum(1 for r in recs if r["status"] == "done" and r["turn2_sent"] == "Y")
    print(f"rows: done {n_done}, void {n_void}; turn 2 sent in {n_t2} done rows")
    print(f"chat dates: {min(dates)} to {max(dates)}; lower bound for ts_sent_ict: {a.bound_text}")
    if a.verify:
        print("RESULT: PASS (verify; nothing written)")
        return
    with open(idx_path, "xb") as fh:
        fh.write(idx_b)
    with open(man_path, "xb") as fh:
        fh.write(man_b)
    print(f"[out] log_index.tsv rows={n_idx} sha256={sha256_file(idx_path)}")
    print(f"[out] raw_manifest.tsv files={n_man} sha256={sha256_file(man_path)}")
    print("RESULT: PASS")


if __name__ == "__main__":
    main()
