#!/usr/bin/env python3
"""score_annotation.py — C-2 kit (part 2): Cohen's kappa + agreement report
from two filled sheets (A = second annotator, B = original translator).

Usage: python3 score_annotation.py --a ../results/annotation_sheet_A.tsv \
                                   --b ../results/annotation_sheet_B.tsv
"""
import argparse
import csv

ap = argparse.ArgumentParser()
ap.add_argument("--a", required=True)
ap.add_argument("--b", required=True)
p = ap.parse_args()


def _norm(v):
    """xlsx cells come back as int/float/None; TSV as str. Normalize to str."""
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)
    return str(v).strip()


def load(path):
    if path.lower().endswith(".xlsx"):
        from openpyxl import load_workbook
        ws = load_workbook(path, data_only=True)["annotation"]
        rows = list(ws.iter_rows(values_only=True))
        hdr = [_norm(h) for h in rows[0]]
        return {_norm(r[0]): dict(zip(hdr, map(_norm, r)))
                for r in rows[1:] if _norm(r[0])}
    return {r["id"]: r for r in csv.DictReader(open(path, encoding="utf-8"),
                                               delimiter="\t")}


A, B = load(p.a), load(p.b)
ids = sorted(A)
pairs = [(int(A[i]["clarity"]), int(B[i]["clarity"])) for i in ids
         if A[i]["clarity"] != "" and B[i]["clarity"] != ""]
n = len(pairs)
po = sum(1 for x, y in pairs if x == y) / n
pa1 = sum(x for x, _ in pairs) / n
pb1 = sum(y for _, y in pairs) / n
pe = pa1 * pb1 + (1 - pa1) * (1 - pb1)
kappa = (po - pe) / (1 - pe) if pe < 1 else 1.0

vg_ids = [i for i in ids if A[i]["vg_check"] in ("0", "1")]
vg_conf = sum(1 for i in vg_ids if A[i]["vg_check"] == "1")
flagged = [i for i in ids if A[i].get("clarity") == "0" or B[i].get("clarity") == "0"]

print(f"n rated by both = {n}")
print(f"observed agreement = {po:.3f} | Cohen's kappa = {kappa:.3f}")
print(f"value-grounding confirmed: {vg_conf}/{len(vg_ids)}")
print(f"items flagged unclear by either rater: {flagged or 'none'}")
print("\nประโยคสำหรับ paper (เติมอัตโนมัติจากเลขจริง):")
print(f'  "A second bilingual annotator independently reviewed all 60 Thai items '
      f'for clarity and verified the value-grounding subset; inter-annotator '
      f'agreement on clarity was kappa = {kappa:.2f} '
      f'({vg_conf}/{len(vg_ids)} value-grounding items confirmed)."')
