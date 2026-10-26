#!/usr/bin/env python3
"""audit_agreement_rc1.py -- agreement of the author's blind audit with the B2.3
classifier (AMENDMENT-7 A6): % agreement, Cohen's kappa, confusion table; GF of every
audited cell recomputed with the author's classes, and the cells whose GF verdict
differs (both values reported; the classifier stays the primary result).

Inputs: the filled rc1_audit_sheet.xlsx and the sealed rc1_audit_key.csv of
make_audit_sheet_rc1.py. Writes --out (agreement CSV), <out stem>_cells.csv and
<out stem>_confusion.csv. A blank or unknown author_class stops the script (exit 2).
Run with: python3 -B -E -P (openpyxl is in the user site). Reads no jsonl.

Usage: python3 -B -E -P audit_agreement_rc1.py --sheet ../results/rc1/audit/rc1_audit_sheet.xlsx \
         --key ../results/rc1/audit/rc1_audit_key.csv --out ../results/rc1/audit/agreement.csv
"""
import argparse
import csv
import os
import sys
from collections import Counter, defaultdict

sys.dont_write_bytecode = True

CLASSES = ["THAI_COPY", "INVENTED", "NO_PRED", "GROUNDED", "STORED"]
GF_CLASSES = ("THAI_COPY", "INVENTED")
FRONTIER = ["claude-sonnet", "gpt-mini", "gemini-flash"]


def gf_union(classes):
    """AM-7 B2.2: strict majority of THAI_COPY u INVENTED among the failing runs."""
    return bool(classes) and sum(c in GF_CLASSES for c in classes) > len(classes) / 2


def cohen_kappa(pairs):
    n = len(pairs)
    if n == 0:
        return None, None
    po = sum(1 for x, y in pairs if x == y) / n
    ca, cb = Counter(x for x, _ in pairs), Counter(y for _, y in pairs)
    pe = sum(ca[k] * cb[k] for k in set(ca) | set(cb)) / (n * n)
    if pe == 1:
        return po, None
    return po, (po - pe) / (1 - pe)


def read_sheet(path):
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    ws = wb["audit"]
    rows = list(ws.iter_rows(values_only=True))
    head = [str(h) if h is not None else "" for h in rows[0]]
    out = {}
    for r in rows[1:]:
        d = dict(zip(head, r))
        if d.get("audit_id"):
            out[str(d["audit_id"]).strip()] = (str(d.get("author_class") or "").strip().upper())
    return out


def main():
    ap = argparse.ArgumentParser(description="audit agreement (AM-7 A6)")
    ap.add_argument("--sheet", required=True)
    ap.add_argument("--key", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    author = read_sheet(a.sheet)
    with open(a.key, encoding="utf-8", newline="") as fh:
        key = list(csv.DictReader(fh))
    ids = {r["audit_id"] for r in key}
    if set(author) != ids:
        print(f"sheet and key differ: {len(set(author) ^ ids)} audit_ids")
        sys.exit(2)
    blank = sorted(i for i, c in author.items() if not c)
    unknown = sorted(i for i, c in author.items() if c and c not in CLASSES)
    if blank or unknown:
        print(f"author_class blank in {len(blank)} rows {blank[:5]}; unknown in {len(unknown)} "
              f"rows {unknown[:5]}; finish the sheet first")
        sys.exit(2)
    pairs = [(author[r["audit_id"]], r["classifier_class"]) for r in key]
    po, kappa = cohen_kappa(pairs)
    conf = Counter(pairs)

    cells = defaultdict(list)
    for r in key:
        cells[(r["model"], r["arm"], r["qid"])].append(r)
    cell_rows, diff = [], []
    tot = Counter()
    for (m, arm, q), rs in sorted(cells.items()):
        mw = rs[0]["cell_majority_wrong"] == "True"
        n_fail = int(rs[0]["cell_n_fail"])
        if len(rs) != n_fail:
            print(f"cell {(m, arm, q)}: {len(rs)} audit rows but {n_fail} failing runs")
            sys.exit(2)
        g_c = mw and gf_union([r["classifier_class"] for r in rs])
        g_a = mw and gf_union([author[r["audit_id"]] for r in rs])
        row = {"model": m, "arm": arm, "qid": q, "in_vg_cov": rs[0]["in_vg_cov"],
               "in_vg_set": rs[0]["in_vg_set"], "majority_wrong": mw, "n_fail": n_fail,
               "gf_classifier": g_c, "gf_author": g_a, "verdict_differs": g_c != g_a}
        cell_rows.append(row)
        if g_c != g_a:
            diff.append(row)
        if m in FRONTIER:
            for sub in ("in_vg_cov", "in_vg_set"):
                if rs[0][sub] == "True":
                    tot[(sub, arm, "classifier")] += g_c
                    tot[(sub, arm, "author")] += g_a

    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    stem = os.path.splitext(a.out)[0]
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["measure", "value"])
        w.writerow(["runs_audited", len(pairs)])
        w.writerow(["percent_agreement", f"{100 * po:.1f}"])
        w.writerow(["cohen_kappa", "undefined" if kappa is None else f"{kappa:.3f}"])
        w.writerow(["cells_audited", len(cell_rows)])
        w.writerow(["cells_gf_verdict_differs", len(diff)])
        for (sub, arm, who), v in sorted(tot.items()):
            w.writerow([f"frontier_gf_{sub}_{arm}_{who}", v])
    with open(stem + "_cells.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(cell_rows[0]))
        w.writeheader()
        w.writerows(cell_rows)
    with open(stem + "_confusion.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["author \\ classifier"] + CLASSES)
        for x in CLASSES:
            w.writerow([x] + [conf[(x, y)] for y in CLASSES])
    print(f"runs {len(pairs)}; agreement {100 * po:.1f}%; Cohen's kappa "
          f"{'undefined' if kappa is None else f'{kappa:.3f}'}")
    print(f"cells {len(cell_rows)}; GF verdict differs in {len(diff)}: " +
          (", ".join(f"{d['model']}|{d['arm']}|{d['qid']} (classifier {d['gf_classifier']}, "
                     f"author {d['gf_author']})" for d in diff) or "none"))
    for (sub, arm, who), v in sorted(tot.items()):
        print(f"  frontier GF {sub} {arm} by {who}: {v}")


if __name__ == "__main__":
    main()
