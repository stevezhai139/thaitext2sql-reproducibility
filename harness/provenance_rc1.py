#!/usr/bin/env python3
"""provenance_rc1.py — model metadata of the October session (AMENDMENT-7; brief 1.0, 1.4).

Records, before and after the runs, the metadata that identifies each model.
Together with the runner's Ollama digest lock this is the only Ollama evidence of
the October session (no Ollama parity gate, brief 1.0).

  API (GET metadata only, never a generate call):
    OpenAI    GET /v1/models/{id}                     -> id, created
    Anthropic GET /v1/models/{id}                     -> id, display_name, created_at
    Gemini    GET /v1beta/models/{id} (key in header) -> name, version, token limits
  Ollama (local): /api/version, /api/tags (digest, size, quantization),
    /api/show (sha256 of template, parameters, modelfile), sha256 of the manifest
    file under <models>/manifests and its layer digests; optional --gguf sha256.

Keys come from os.environ only (run `source "secrets.env"` as a separate step
first); this script never opens secrets.env and never prints a key. A failed
request is recorded as {target, status, type} only: never the provider message.
Privacy (double-blind): stores python version, platform.platform() and the macOS
version only — no host name, no user name, no absolute path (GGUF -> basename,
manifest -> path relative to the Ollama models folder, runner/models -> path
relative to ROOT).

The file is written only when every target succeeded, so a transient failure
(Ollama not started, keys not sourced in this terminal) leaves no file behind:
fix the cause and run the same command again. --allow-errors writes the file
with the failures recorded as {target, status, type}; use it only when the author
decides to keep a failure on record (for example an endpoint that no longer exists).

Usage (RUNBOOK_v2 Gate 1a step 70, Gate 3 steps 5 and 20; one command each, run from harness/):
  python3 -I -B "provenance_rc1.py" --phase gate1a --models "models.json" --gguf "<path of the Typhoon GGUF>" --out "../results/rc1/provenance_gate1a.json"
  python3 -I -B "provenance_rc1.py" --phase before --models "models.json" --gguf "<path of the Typhoon GGUF>" --out "../results/rc1/provenance_before.json" --compare "../results/rc1/provenance_gate1a.json"
Exit: 0 all targets ok and file written; 1 some target failed (file not written,
or written with the failures when --allow-errors is given), or an unexpected
error (exception name only); 2 usage error, checked before any request or write:
--out exists or its folder is missing, --models or --compare missing or not a
JSON object, --gguf path missing. Messages name files by basename only.
"""
import argparse
import datetime
import hashlib
import json
import os
import platform
import re
import sys
import urllib.error
import urllib.request

sys.dont_write_bytecode = True

HERE = os.path.dirname(os.path.abspath(__file__))
OLLAMA_BASE = "http://localhost:11434"
ICT = datetime.timezone(datetime.timedelta(hours=7))
TIMEOUT = 30
_TOKEN = re.compile(r"[A-Za-z0-9_.\-]{1,64}")

API = {
    "openai": {"url": "https://api.openai.com/v1/models/{model}", "env": "OPENAI_API_KEY",
               "headers": lambda k: {"Authorization": f"Bearer {k}"},
               "fields": (("id", "id"), ("created", "created"))},
    "anthropic": {"url": "https://api.anthropic.com/v1/models/{model}", "env": "ANTHROPIC_API_KEY",
                  "headers": lambda k: {"x-api-key": k, "anthropic-version": "2023-06-01"},
                  "fields": (("id", "id"), ("display_name", "display_name"), ("created_at", "created_at"))},
    "google": {"url": "https://generativelanguage.googleapis.com/v1beta/models/{model}", "env": "GOOGLE_API_KEY",
               "headers": lambda k: {"x-goog-api-key": k},
               "fields": (("name", "name"), ("version", "version"),
                          ("input_token_limit", "inputTokenLimit"), ("output_token_limit", "outputTokenLimit"))},
}

_SECRETS = []


def redact(text):
    text = str(text)
    for s in _SECRETS:
        if s:
            text = text.replace(s, "<REDACTED>")
    return text


def say(msg):
    print(redact(msg), flush=True)


def die(code, msg):
    print(redact(msg), file=sys.stderr, flush=True)
    raise SystemExit(code)


def load_json_arg(flag, path):
    """อ่าน JSON object ของ flag ก่อน request หรือการเขียนใดๆ; ข้อความมีเฉพาะ basename (ไม่มี path เต็ม)"""
    if not os.path.isfile(path):
        die(2, f"{flag} {os.path.basename(path)} not found; nothing was requested or written")
    try:
        with open(path, encoding="utf-8") as fh:
            d = json.load(fh)
    except (OSError, ValueError) as e:
        die(2, f"{flag} {os.path.basename(path)} cannot be read as JSON ({type(e).__name__}); "
               f"nothing was requested or written")
    if not isinstance(d, dict):
        die(2, f"{flag} {os.path.basename(path)} is not a JSON object; nothing was requested or written")
    return d


# ---------------------------------------------------------------------------
# transport (tests replace http_request; nothing else opens sockets)
# ---------------------------------------------------------------------------
def http_request(method, url, headers=None, body=None, timeout=TIMEOUT):
    data = None if body is None else json.dumps(body).encode()
    hdr = dict(headers or {})
    if data is not None:
        hdr["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=hdr, method=method)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read())


def classify(e):
    """(status, type) only — the provider message and body are never kept"""
    if isinstance(e, urllib.error.HTTPError):
        etype = None
        try:
            d = json.loads(e.read().decode(errors="replace"))
            if isinstance(d, list) and d:
                d = d[0]
            err = d.get("error") if isinstance(d, dict) else None
            if isinstance(err, dict):
                etype = err.get("type") or err.get("status") or err.get("code")
        except Exception:
            etype = None
        if not (isinstance(etype, (str, int)) and _TOKEN.fullmatch(str(etype))):
            etype = "HTTPError"
        return e.code, str(etype)
    return None, type(e).__name__


def sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha256_text(s):
    return None if s is None else sha256_bytes(s.encode("utf-8"))


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def root_relpath(path):
    root = os.path.dirname(HERE)
    rel = os.path.relpath(os.path.abspath(path), root)
    return "<outside-root>/" + os.path.basename(path) if rel.startswith("..") else rel.replace(os.sep, "/")


def manifest_relpath(name):
    """Ollama model name -> manifest path relative to the models folder"""
    model, tag = (name.rsplit(":", 1) + ["latest"])[:2] if ":" in name.split("/")[-1] else (name, "latest")
    parts = model.split("/")
    if len(parts) == 1:
        host, ns, base = "registry.ollama.ai", "library", parts[0]
    elif len(parts) == 2:
        host, ns, base = "registry.ollama.ai", parts[0], parts[1]
    else:
        host, ns, base = parts[0], "/".join(parts[1:-1]), parts[-1]
    return "/".join(["manifests", host, ns, base, tag])


def _norm(name):
    return name if ":" in name.split("/")[-1] else name + ":latest"


def api_metadata(models, errors):
    out = {}
    for mkey, m in models.items():
        spec = API.get(m.get("provider"))
        if spec is None:
            continue
        ent = {"status": None}
        for dst, _ in spec["fields"]:
            ent[dst] = None
        key = os.environ.get(spec["env"])
        if not key:
            errors.append({"target": f"api:{mkey}", "status": None, "type": "missing_env"})
            out[mkey] = ent
            continue
        _SECRETS.append(key)
        try:
            r = http_request("GET", spec["url"].format(model=m["model"]), spec["headers"](key))
            ent["status"] = 200
            for dst, src in spec["fields"]:
                ent[dst] = r.get(src)
        except Exception as e:
            st, ty = classify(e)
            ent["status"] = st
            errors.append({"target": f"api:{mkey}", "status": st, "type": ty})
        out[mkey] = ent
    return out


def ollama_metadata(models, models_dir, errors):
    names = [m["model"] for m in models.values() if m.get("provider") == "ollama"]
    res = {"version": None, "models": {}}
    if not names:
        return res
    try:
        res["version"] = (http_request("GET", OLLAMA_BASE + "/api/version") or {}).get("version")
    except Exception as e:
        st, ty = classify(e)
        errors.append({"target": "ollama:/api/version", "status": st, "type": ty})
    tags = {}
    try:
        for t in (http_request("GET", OLLAMA_BASE + "/api/tags") or {}).get("models") or []:
            for nm in (t.get("name"), t.get("model")):
                if nm:
                    tags[_norm(nm)] = t
    except Exception as e:
        st, ty = classify(e)
        errors.append({"target": "ollama:/api/tags", "status": st, "type": ty})
    for name in names:
        ent = {"digest": None, "size": None, "quantization": None, "manifest_relpath": manifest_relpath(name),
               "manifest_sha256": None, "list_id": None, "config_digest": None, "layers": [],
               "template_sha256": None, "params_sha256": None, "modelfile_sha256": None}
        t = tags.get(_norm(name))
        if t is None:
            errors.append({"target": f"ollama:{name}:/api/tags", "status": None, "type": "not_listed"})
        else:
            ent["digest"] = t.get("digest")
            ent["size"] = t.get("size")
            ent["quantization"] = (t.get("details") or {}).get("quantization_level")
        try:
            show = http_request("POST", OLLAMA_BASE + "/api/show", body={"model": name}) or {}
            ent["template_sha256"] = sha256_text(show.get("template"))
            ent["params_sha256"] = sha256_text(show.get("parameters"))
            ent["modelfile_sha256"] = sha256_text(show.get("modelfile"))
        except Exception as e:
            st, ty = classify(e)
            errors.append({"target": f"ollama:{name}:/api/show", "status": st, "type": ty})
        mpath = os.path.join(models_dir, *ent["manifest_relpath"].split("/"))
        try:
            raw = open(mpath, "rb").read()
            ent["manifest_sha256"] = sha256_bytes(raw)
            ent["list_id"] = ent["manifest_sha256"][:12]   # รูปแบบ ID ของ `ollama list`
            man = json.loads(raw)
            ent["config_digest"] = (man.get("config") or {}).get("digest")
            ent["layers"] = [{"mediaType": l.get("mediaType"), "digest": l.get("digest"), "size": l.get("size")}
                             for l in man.get("layers") or []]
        except Exception as e:
            errors.append({"target": f"manifest:{name}", "status": None, "type": type(e).__name__})
        res["models"][name] = ent
    return res


def gguf_metadata(path, errors):
    if not path:
        return None
    try:
        return {"basename": os.path.basename(path), "sha256": sha256_file(path), "size": os.path.getsize(path)}
    except Exception as e:
        errors.append({"target": "gguf", "status": None, "type": type(e).__name__})
        return {"basename": os.path.basename(path), "sha256": None, "size": None}


def flatten(d, prefix=""):
    out = {}
    if isinstance(d, dict):
        for k, v in d.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(d, list):
        out[prefix] = json.dumps(d, sort_keys=True)
    else:
        out[prefix] = d
    return out


def compare(prev, cur):
    ignore = {"phase", "taken_at_ict"}
    a, b = flatten(prev), flatten(cur)
    changed = []
    for k in sorted(set(a) | set(b)):
        if k in ignore:
            continue
        if a.get(k, "<absent>") != b.get(k, "<absent>"):
            changed.append((k, a.get(k, "<absent>"), b.get(k, "<absent>")))
    return changed


def short(v):
    s = v if isinstance(v, str) else json.dumps(v)
    return s if len(s) <= 80 else s[:77] + "..."


def main():
    """error ที่ไม่คาดไว้: พิมพ์เฉพาะชื่อ exception (ข้อความของ OSError มี path เต็ม จึงไม่พิมพ์)"""
    try:
        _main()
    except Exception as e:
        die(1, f"UNEXPECTED ERROR {type(e).__name__} (message not printed: it may hold a full path)")


def _main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=("gate1a", "before", "after"))
    ap.add_argument("--models", required=True)
    ap.add_argument("--gguf", help="path of the Typhoon GGUF (only the basename and sha256 are stored)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--compare", help="earlier provenance JSON; print only the fields that changed")
    ap.add_argument("--runner", default=os.path.join(HERE, "runner.py"))
    ap.add_argument("--ollama-models", default=None,
                    help="Ollama models folder (default $OLLAMA_MODELS or ~/.ollama/models; never stored)")
    ap.add_argument("--allow-errors", action="store_true",
                    help="write the file even when some target failed (failures recorded as target/status/type)")
    a = ap.parse_args()
    # ---- usage checks (exit 2) before any request or write, so a wrong argument never
    # leaves a file behind and the same command can be run again once it is fixed
    if os.path.exists(a.out):
        die(2, f"{os.path.basename(a.out)} exists — provenance files are never overwritten")
    if not os.path.isdir(os.path.dirname(os.path.abspath(a.out))):
        die(2, f"the folder of --out {os.path.basename(a.out)} does not exist; nothing was requested or written")
    models = load_json_arg("--models", a.models)
    if not all(isinstance(v, dict) for v in models.values()):
        die(2, f"--models {os.path.basename(a.models)}: expected an object of model_key -> settings")
    prev = load_json_arg("--compare", a.compare) if a.compare else None
    if a.gguf and not os.path.isfile(a.gguf):
        die(2, f"--gguf {os.path.basename(a.gguf)} not found (check the path); nothing was requested or written")
    models_dir = a.ollama_models or os.environ.get("OLLAMA_MODELS") or os.path.join(
        os.path.expanduser("~"), ".ollama", "models")

    errors = []
    rec = {"phase": a.phase,
           "taken_at_ict": datetime.datetime.now(ICT).strftime("%Y-%m-%dT%H:%M:%S+07:00"),
           "python": platform.python_version(),
           "platform": platform.platform(),
           "macos": platform.mac_ver()[0],
           "runner_path": root_relpath(a.runner),
           "runner_sha256": sha256_file(a.runner) if os.path.exists(a.runner) else None,
           "models_path": root_relpath(a.models),
           "models_sha256": sha256_file(a.models)}
    rec["api"] = api_metadata(models, errors)
    rec["ollama"] = ollama_metadata(models, models_dir, errors)
    rec["gguf"] = gguf_metadata(a.gguf, errors)
    rec["errors"] = errors

    data = (json.dumps(rec, ensure_ascii=False, indent=1) + "\n").encode("utf-8")
    written = not errors or a.allow_errors
    if written:
        fd = os.open(a.out, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
        with os.fdopen(fd, "wb") as fh:
            fh.write(data)

    for mkey, ent in rec["api"].items():
        ident = ent.get("version") or ent.get("id") or ent.get("name")
        say(f"api {mkey}: status {ent['status']} | {ident}")
    if rec["ollama"]["models"]:
        say(f"ollama version: {rec['ollama']['version']}")
    for name, ent in rec["ollama"]["models"].items():
        dig = (ent["digest"] or "")[:12] or None
        say(f"ollama {name}: tags digest {dig} | manifest id {ent['list_id']} | quant {ent['quantization']}")
    if rec["gguf"]:
        say(f"gguf {rec['gguf']['basename']}: sha256 {rec['gguf']['sha256']}")
    say(f"runner sha256 {rec['runner_sha256']} | models sha256 {rec['models_sha256']}")
    for e in errors:
        say(f"ERROR {e['target']}: status {e['status']} type {e['type']}")
    if written:
        say(f"file sha256: {sha256_bytes(data)} ({len(errors)} error(s)) -> {os.path.basename(a.out)}")
    else:
        say(f"NOT WRITTEN: {len(errors)} target(s) failed, so {os.path.basename(a.out)} was not created. "
            f"Fix the cause (start Ollama, source the keys in this terminal) and run the same command again; "
            f"--allow-errors records the failures instead.")

    if prev is not None:
        changed = compare(prev, rec)
        if not changed:
            say("compare: no field changed (phase and taken_at_ict ignored)")
        for k, old, new in changed:
            say(f"CHANGED {k}: {short(old)} -> {short(new)}")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
