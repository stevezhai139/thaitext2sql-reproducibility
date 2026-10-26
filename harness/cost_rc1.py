#!/usr/bin/env python3
"""cost_rc1.py -- token usage and list-price cost estimate of the October session
(AMENDMENT-7 A6 item 9), per log x model x arm (core and extension logs are kept apart
by file). Prices come from a JSON the author fills (source and access date; OQ31).

Prices file (per 1M tokens; 'thinking_billed_as': "out" adds tok_think to output):
  {"source": "...", "accessed": "YYYY-MM-DD", "currency": "USD", "unit": "per_1M_tokens",
   "label": "list-price estimate",
   "models": {"gpt-mini": {"in": 0.75, "out": 4.50}, ...,
              "gemini-flash": {"in": 0.75, "out": 3.75, "thinking_billed_as": "out"},
              "llama31-8b": {"in": 0, "out": 0}}}
--write-template PATH writes such a file with the OQ31 default values (triage
14 Oct 2026: provider pricing pages read on 13 Oct 2026) for the author to check.

Records are read through a hook that keeps model_key, arm, tok_in, tok_out, tok_think
and turns 'error' into a boolean. Error records count as calls; their tokens are
usually absent and are reported as such.

Usage (Gate 3 step 60):
  python3 -I -B cost_rc1.py --results ../results/rc1/results_rc1_api.jsonl \
    --results ../results/ext/results_ext_api.jsonl --prices "<prices json>" --out ../results/rc1/cost.csv
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict

sys.dont_write_bytecode = True

_KEEP = ("model_key", "arm", "tok_in", "tok_out", "tok_think")
TEMPLATE = {
    "source": "provider pricing page", "accessed": "2026-10-13", "currency": "USD",
    "unit": "per_1M_tokens", "label": "list-price estimate",
    "models": {"gpt-mini": {"in": 0.75, "out": 4.50},
               "claude-sonnet": {"in": 2.0, "out": 10.0},
               "gemini-flash": {"in": 0.75, "out": 3.75, "thinking_billed_as": "out"},
               "llama31-8b": {"in": 0, "out": 0},
               "qwen25-coder-7b": {"in": 0, "out": 0},
               "typhoon2-8b": {"in": 0, "out": 0}}}


def _hook(pairs):
    d = {}
    for k, v in pairs:
        if k == "error":
            d["error"] = v is not None
        elif k in _KEEP:
            d[k] = v
    return d


def num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) else None


def main():
    ap = argparse.ArgumentParser(description="token usage and list-price cost")
    ap.add_argument("--results", action="append", default=[])
    ap.add_argument("--prices")
    ap.add_argument("--out")
    ap.add_argument("--write-template", help="write a prices template (OQ31 defaults) and stop")
    a = ap.parse_args()
    if a.write_template:
        if os.path.exists(a.write_template):
            sys.exit(f"{a.write_template} exists")
        with open(a.write_template, "w", encoding="utf-8") as fh:
            json.dump(TEMPLATE, fh, indent=1, ensure_ascii=False)
            fh.write("\n")
        print(f"wrote {a.write_template}; check every price, source and date before use")
        return
    if not (a.results and a.prices and a.out):
        ap.error("--results, --prices and --out are required (or --write-template)")
    prices = json.load(open(a.prices, encoding="utf-8"))
    for k in ("source", "accessed", "models"):
        if not prices.get(k):
            sys.exit(f"prices file lacks '{k}'")
    agg = defaultdict(lambda: defaultdict(float))
    for path in a.results:
        label = os.path.splitext(os.path.basename(path))[0]
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if not line.strip():
                    continue
                try:
                    r = json.loads(line, object_pairs_hook=_hook)
                except json.JSONDecodeError:
                    sys.exit(f"{label} line {n}: not JSON")
                k = (label, r.get("model_key"), r.get("arm") or "base")
                g = agg[k]
                g["calls"] += 1
                g["errors"] += bool(r.get("error"))
                ti, to, tt = num(r.get("tok_in")), num(r.get("tok_out")), num(r.get("tok_think"))
                if ti is None and to is None:
                    g["calls_without_usage"] += 1
                g["tok_in"] += ti or 0
                g["tok_out"] += to or 0
                g["tok_think"] += tt or 0
    rows, total = [], 0.0
    for (label, m, arm), g in sorted(agg.items(), key=lambda kv: tuple(map(str, kv[0]))):
        p = prices["models"].get(m)
        if p is None:
            sys.exit(f"no price for model {m}")
        billed_out = g["tok_out"] + (g["tok_think"] if p.get("thinking_billed_as") == "out" else 0)
        cost = (g["tok_in"] * float(p["in"]) + billed_out * float(p["out"])) / 1e6
        total += cost
        rows.append({"log": label, "model": m, "arm": arm, "calls": int(g["calls"]),
                     "error_calls": int(g["errors"]), "calls_without_usage": int(g["calls_without_usage"]),
                     "tok_in": int(g["tok_in"]), "tok_out": int(g["tok_out"]),
                     "tok_think": int(g["tok_think"]), "billed_out": int(billed_out),
                     "price_in": p["in"], "price_out": p["out"],
                     "cost": f"{cost:.4f}", "currency": prices.get("currency", "USD")})
    os.makedirs(os.path.dirname(os.path.abspath(a.out)), exist_ok=True)
    with open(a.out, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]) if rows else ["log"])
        w.writeheader()
        w.writerows(rows)
        fh.write(f"# {prices.get('label', 'list-price estimate')}; source: {prices['source']}; "
                 f"accessed {prices['accessed']}; total {total:.4f} {prices.get('currency', 'USD')}\n")
    for r in rows:
        print(f"  {r['log']:22} {r['model']:16} {r['arm']:6} calls {r['calls']:5} "
              f"(errors {r['error_calls']}) in {r['tok_in']} out {r['billed_out']} -> "
              f"{r['cost']} {r['currency']}")
    print(f"total {total:.4f} {prices.get('currency', 'USD')} ({prices.get('label', 'list-price estimate')})")


if __name__ == "__main__":
    main()
