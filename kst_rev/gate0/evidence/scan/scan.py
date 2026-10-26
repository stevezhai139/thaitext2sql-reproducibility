import sys, json, csv, importlib.util, os
from collections import Counter
sys.dont_write_bytecode = True
W, ROOT = sys.argv[1], sys.argv[2]
def load(d):
    sys.path.insert(0, d)
    for m in ("vg_rule", "vg_classifier"):
        sys.modules.pop(m, None)
    spec = importlib.util.spec_from_file_location("vgc_" + os.path.basename(d), os.path.join(d, "vg_classifier.py"))
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    pass
    return mod
old, new = load(os.path.join(W, "old")), load(os.path.join(W, "new"))
suite = {r["id"]: r for r in csv.DictReader(open(os.path.join(ROOT, "kst_rev/wf_null/core/k3n_suite_v1.3n_DRAFT.tsv"), encoding="utf-8"), delimiter="\t")}
suite = {k: v for k, v in suite.items() if v["v13_status"] != "excluded"}
tg_new = new.suite_vg_targets(suite)
tg_old = old.suite_vg_targets(suite)
assert tg_new == tg_old
hints = json.load(open(sys.argv[3], encoding="utf-8"))
voc = new.build_vocab(hints, gold_targets=[t for q in tg_new for t in tg_new[q]])
KEEP = ("qid", "lang", "sql", "parse_ok")
def hook(pairs):
    return {k: v for k, v in pairs if k in KEEP}
n = Counter()
trans = Counter()
with open(os.path.join(ROOT, "results/results.jsonl"), encoding="utf-8") as fh:
    for line in fh:
        if not line.strip():
            continue
        r = json.loads(line, object_pairs_hook=hook)
        q = r.get("qid")
        if q not in tg_new:
            continue
        sql = (r.get("sql") or "") if r.get("parse_ok") else ""
        n["vg_records"] += 1
        co, cn = old.classify_run(sql, tg_new[q], voc), new.classify_run(sql, tg_new[q], voc)
        if co != cn:
            n["class_differs"] += 1
            trans[(r.get("lang"), co, cn)] += 1
        for col, _ in tg_new[q]:
            if col and sorted(old.predicates_on_column(sql, col)) != sorted(new.predicates_on_column(sql, col)):
                n["predicates_differ"] += 1
                break
        if any("''" in x for x in [sql]):
            n["sql_with_doubled_quote"] += 1
        if '"' in sql:
            n["sql_with_double_quote_char"] += 1
print(dict(n))
print({f"{k[0]} {k[1]}->{k[2]}": v for k, v in trans.items()})
