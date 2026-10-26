"""parity gate for grade_v13.py: its --legacy output must equal results/graded.csv
(exec_ok, correct, fail_reason) on every (model_key, lang, qid, run). Exit 1 otherwise.
Usage: python3 -I parity_check_v13.py "<results/graded.csv>" "<graded_legacy_parity.csv>"
"""
import csv
import sys

key = lambda r: (r["model_key"], r["lang"], r["qid"], r["run"])
A = {key(r): r for r in csv.DictReader(open(sys.argv[1], encoding="utf-8"))}
B = {key(r): r for r in csv.DictReader(open(sys.argv[2], encoding="utf-8"))}
cols = ("exec_ok", "correct", "fail_reason")
bad = [k for k in A if k not in B or any(A[k][c] != B[k][c] for c in cols)]
extra = [k for k in B if k not in A]
print(f"record rows {len(A)} | legacy rows {len(B)} | mismatches {len(bad)} | extra {len(extra)}")
for k in bad[:10]:
    print("  mismatch", k)
if bad or extra or len(A) != len(B):
    sys.exit("PARITY FAILED: do not use grade_v13.py until this is resolved")
print("PARITY PASS: grade_v13.py --legacy reproduces graded.csv exactly")
