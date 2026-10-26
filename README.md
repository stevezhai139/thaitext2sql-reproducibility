# ThaiText2SQL: reproducibility artifact for "Silently Wrong"

This repository holds the benchmark suite, harness, generation logs, graded results, preregistration and course database behind the paper

> Arun Reungsilpkolkarn, "Silently Wrong: Auditing Free-Tier LLM Proxies for Thai Database Classrooms with ThaiText2SQL," KST 2027, IEEE. DOI: to be added.

Author: Arun Reungsilpkolkarn, School of Information Technology and Innovation, Bangkok University, Thailand.

Contents: [1. What this is](#1-what-this-is) · [2. Map from the paper to the files](#2-map-from-the-paper-to-the-files) · [3. Quick start](#3-quick-start) · [4. What reproduces and what does not](#4-what-reproduces-and-what-does-not) · [5. Preregistration and deviations](#5-preregistration-and-deviations) · [6. Environment](#6-environment) · [7. Licenses](#7-licenses) · [8. Contact](#8-contact)

## 1. What this is

ThaiText2SQL v1 is a bilingual English/Thai text-to-SQL suite of 60 core items over the two schemas that one undergraduate database course uses: President (four normalized tables) and Ecommerce (one table of 38 columns and 2,390 retail transactions). The core items form four curriculum tiers of 15. An exploratory 40-item extension adds harder query families on the President schema. Common-word data values are written in Thai in the Thai questions, while the values stored in the database stay in English.

The paper uses the suite to audit API models that stand in for the free tiers of ChatGPT, Gemini and Claude, and three local 7–8B models (exploratory), under a preregistered protocol: 9,598 graded generations (core items under a schema-only prompt and under a prompt that also lists stored values; extension items under the schema-only prompt) and a manual check of 84 single-shot chats in the free chat apps. Every query is graded by execution on PostgreSQL 16.9.

This repository is a sanitized snapshot of the author's private working repository, which keeps the full commit history. `PROVENANCE.md` records the source commit, every file that differs from the source with its sha256 before and after, what was left out, and the hashes of the data files. `SNAPSHOT_MANIFEST.tsv` lists the sha256 and status of every file in this snapshot. Commit identifiers quoted in the preregistration refer to the private repository.

**Language.** The preregistration, its amendments and addenda, and many code comments are written in Thai, and some scripts print messages partly in Thai. Script docstrings refer to steps of the author's internal run book (for example "RUNBOOK step 3.23"); the run book is not included, and Section 3 gives the equivalent commands, run from the repository root.

### Citation

```bibtex
@inproceedings{reungsilpkolkarn2027silently,
  author    = {Arun Reungsilpkolkarn},
  title     = {Silently Wrong: Auditing Free-Tier {LLM} Proxies for {Thai} Database Classrooms with {ThaiText2SQL}},
  booktitle = {KST 2027},
  publisher = {IEEE},
  year      = {2027},
  note      = {DOI: to be added}
}
```

### Layout

| Path | Contents |
|---|---|
| `suite/` | Core suites: `k3n_suite_v1.3n_oct.tsv` (October 2026 collection, 60 items, Q27 repaired), `k3n_suite_v1.3n.tsv` (August 2026 collection under the revised key, original Q27 excluded) and `k3_suite_v1.2.tsv` (the key of the submitted version); the extension `k3n_ext_suite_v1.0.tsv` with its reserves and item changes; the stored-value lists `value_hints_v1.json`; the value-grounding item sets; changelogs with errata; `DATA_PROVENANCE.md` on the origin of the course data |
| `harness/` | Generation (`runner.py`, `models.json`), grading (`grade_v13n.py`), analysis and table scripts, database build (`setup_db.sql`, `db/`), chat-check tools (`chatapp/`) |
| `results/` | Logs, graded files and analysis outputs: `rc1/` October core collection, `ext/` October extension, `chat/` chat-app check, `v13n/` and `v13/` the August log re-graded, `db/` database fingerprints; `results.jsonl`, `graded.csv` and `tables/` are the August log and its grading under the original key |
| `prereg/` | `preregistration_FROZEN.md` (frozen on 6 August 2026; amendments and addenda appended with dates) and `preregistration_v0.md` (the text that was frozen; identical to the first 64 lines of the frozen file) |
| `SUPPLEMENT.md` | Full list of limitations, errata for the next suite version, tables and figure that the paper does not print, design details moved out of the paper |
| `paper/generated/` | Tables and figures from `harness/make_tables.py` and `harness/make_figures.py` on the October base arm; inputs of `harness/make_tables_rev.py`. Not printed in the paper |
| `paper/generated_rev/` | Revised tables not printed in the paper (per-tier accuracy, English–Thai contrast, stability). Table I's source `tab_headline_rev.tex` is not included; Section 3.4 regenerates it |
| `paper/generated_v12/` | Tables and figures of the submitted version (original key), kept unchanged |
| `data/course/` | The five course data files `President.csv`, `Party.csv`, `PresidentMarriage.csv`, `PresidentHolding.csv` and `Ecommerce_Dataset.csv`; their sha256 are pinned in `harness/db/k3n_inputs.sha256` |
| `data/ecommerce1m/` | `Ecommerce1M.csv.xz`, the 10^6-row table used for plan quality, exported from the grading database `k3n` (which `harness/db/build_k3n.sh` copied from the study database `k3`, checking rows and row hash) |
| `kst_rev/` | The two freeze manifests, the tools that read them (`freeze_stamp.py`, `prereg_append_check.py`), and the files outside the working repository's git that the manifests pin (the October suite builder and the Q27 repair file, grader and runner diffs, classifier scan evidence, chat-extraction fixtures, extension selection and translation-check inputs), kept at their original paths |
| `hardness/` | Spider-style hardness of the 100 items (60 core, 40 extension) computed from the frozen gold queries, with `hardness/METHOD.md`. Preregistered as an artifact table (AMENDMENT-9, section 8); not used to select items or in any analysis |
| `PROVENANCE.md`, `SNAPSHOT_MANIFEST.tsv` | Provenance of this snapshot and the manifest of its files |
| `LICENSE`, `LICENSE-DATA.md` | Licenses (Section 7) |

**Course data.** The President data were adapted from a long-circulating instructional U.S.-presidents database of untraced origin and extended by the author; the Ecommerce data are synthetic and were generated by the author for classroom use (`suite/DATA_PROVENANCE.md`). The President schema holds 45 presidents, 9 parties, 49 office-holdings and 49 marriage records, one of them a no-spouse placeholder.

### Not included

- The paper's LaTeX source and PDFs (IEEE copyright). Cite the paper by its DOI once published. Table I's source file is printed in the paper and is therefore left out; Section 3.4 regenerates it and checks it against the sha256 pinned in the preregistration.
- An annotation workbook whose file name identified the second rater. The translation-agreement figures come from `results/annotation_sheet_A.xlsx` (second annotator) and `results/annotation_sheet_B.xlsx` (original translator), which are included.
- Internal planning notes, run books and drafts prepared for another venue.
- API keys and model weights.

### Files that differ from the private repository

The exact list, with the sha256 of each file before and after, is in `PROVENANCE.md`.

- `results/results.jsonl` (the August 2026 log): an expired API key that appeared in the `key=` parameter of URLs inside error messages is replaced by `<REDACTED>` (86 places; sha256 `7a68349dcdc7a0c913bfc73ebd93c456fb66ca489fcb32a1f59dd94d79c81365` before, `aa8e122dbd2df7144e6c3beb4973fdea2950468466e2d9d5f552ae8cef75aa9a` after). The six `meta.json` files under `results/v13n/` that cite this log's sha256 refer to the file before redaction. The grader keeps only whether a record is an error, not the error text, so the redaction does not enter grading.
- `suite/AMENDMENT3_VG_RULE.md` (sha256 `256dc532f5ed698e08360c91b56742f629f7010b8e0c922b7a8493e9a21a7d6f` before, `f56de8a13070ee81790a5056e50a8af3acc9a7f164cb29e145675f76ec62995e` after) and several input files under `kst_rev/wf_q100/` (text files, and cell text in two workbooks): a personal name is replaced by "the author" or its Thai equivalent.
- `suite/DATA_PROVENANCE.md`: a third person's name in an internal note is replaced by their role.
- Excel workbooks (`.xlsx`): identity metadata (the document's creator and last-modified-by fields, and the absolute path of the folder it was saved in) is removed. In the rating, coding and suite workbooks under `results/` and `suite/`, cell values are unchanged.
- One selection workbook under `kst_rev/wf_q100/selection/` is renamed; the new name still matches the pattern that `kst_rev/gate0/harness/freeze_manifest_gate1b.tsv` uses for it.

## 2. Map from the paper to the files

| Paper | Content | Files |
|---|---|---|
| I. Introduction | Contribution (iv), the released artifact | this repository; re-grading: Section 3.3 |
| III-A | Schemas and data | `data/course/`, `harness/setup_db.sql`, `harness/db/build_k3n.sh` (missing values `'None'` → NULL), `harness/db/k3n_inputs.sha256`, `suite/DATA_PROVENANCE.md` |
| III-A | 10^6-row scale-up | `data/ecommerce1m/Ecommerce1M.csv.xz`; generator `harness/scale_ecommerce.py` |
| III-A | Core items, tiers | `suite/k3n_suite_v1.3n_oct.tsv` (October), `suite/k3n_suite_v1.3n.tsv` (August), `suite/k3_suite_v1.2.tsv` (submitted key) |
| III-A | Extension (40 items) | `suite/k3n_ext_suite_v1.0.tsv`, `suite/k3n_ext_reserves_v1.0.tsv`, `suite/ITEM_CHANGES_ext_v1.0.tsv`, author decisions `suite/ext_inputs/ext_decisions_2026-10-14.json`, builder `harness/build_ext_suite.py` and its report `results/ext/build/`, selection and translation-check inputs `kst_rev/wf_q100/`; multi-instance items: `harness/db/mi_manifest_k3n.json`, `harness/db/diffs/`, `harness/db/build_instances.py`; hardness: `hardness/` |
| III-B | Bilingual protocol, value-grounding items | `question_en` and `question_th` in the suite files; `suite/vg_set_v13n.txt` (10 items), `suite/vg_set_v13n_VG9.txt` (without Q48), `harness/vg_rule.py`, `harness/make_vg_sets.py`, `suite/AMENDMENT3_VG_RULE.md` |
| III-B | Translation validation | `results/annotation_sheet_A.xlsx`, `results/annotation_sheet_B.xlsx`, `harness/score_annotation.py` (Section 3.6) |
| III-C | Gold validation, revised key, errata | `harness/selftest_v13n.py`, `harness/grade_v13n.py`, `harness/suite_columns.json`, `suite/CHANGELOG_v1.2_to_v1.3.md` (errata section), `suite/CHANGELOG_v1.3_to_v1.3n.md`, Q27 repair `kst_rev/gate0/suite_tools/Q27_REPAIR_2026-10-14.tsv` and `kst_rev/gate0/suite_tools/build_oct_core_suite.py`; SUPPLEMENT.md section 2 |
| III-C | Results under the original key | `results/graded.csv`, `results/tables/`, `paper/generated_v12/`, `results/rc1/rev_numbers/decomposition.csv` |
| III-C | Preregistration, amendments, deviations | `prereg/` (Section 5) |
| IV | Roster, prompts, stored values | `harness/models.json`, `harness/runner.py` (prompt string), `suite/value_hints_v1.json` (from `harness/make_value_hints.py`), `results/rc1/prompts_rc1.jsonl`, `results/ext/prompts_ext.jsonl` |
| IV | Generation logs | October core, both prompts: `results/rc1/results_rc1_api.jsonl`, `results/rc1/results_rc1_local.jsonl`; October extension: `results/ext/results_ext_api.jsonl`, `results/ext/results_ext_local.jsonl`; August: `results/results.jsonl` |
| IV | Provenance of models and runtime | `results/rc1/provenance_gate1a.json`, `results/rc1/provenance_before.json`, `results/rc1/provenance_after.json` |
| IV | Grading and statistics | `harness/grade_v13n.py`, `harness/analyze.py`, `harness/analyze_rc1.py`, `harness/vg_classifier.py`; blind manual re-coding: `results/rc1/audit/` |
| IV | Chat-app consistency check | `harness/chatapp/`; `results/chat/` (cells and prompts, raw replies, screenshots in `shots/`, `log_index.tsv`, `CHAT_LOG.xlsx`, graded files, silence and audit sheets) |
| V, Table I | Headline accuracy, Ext. column | regenerated by `harness/make_tables_rev.py` (Section 3.4) from `paper/generated/tab_headline.tex`, `results/rc1/base60/tables/accuracy.csv`, `results/ext/tables/ext_accuracy.csv` and `results/rc1/rev_numbers/ext_typhoon_descriptive.csv` |
| V-A | RQ1 by tier; matched pair; extension failures | `results/rc1/base60/tables/accuracy.csv`, `paper/generated_rev/tab_tiers_rev.tex`, `paper/generated/fig_tiers.pdf`; `results/rc1/base60/tables/typhoon_analysis.csv`; `results/rc1/rev_numbers/ext_frontier_silent.csv`, `results/rc1/rev_numbers/summary.txt` |
| V-B | RQ2 cross-lingual gap | `results/rc1/base60/tables/cross_lingual.csv`, `paper/generated_rev/tab_crosslingual_rev.tex`, `results/ext/tables/ext_pooled100.csv`; August collection: `results/tables/` (original key), `results/v13n/tables/` (revised key), `results/rc1/consistency/` |
| V-B | Value grounding and the stored-values prompt | `results/rc1/base60/tables/value_translated.csv`, `results/rc1/base60/tables_noQ14/`, `results/rc1/h1h4/`, `results/rc1/values60/`; silent split `results/rc1/base60/partB/` |
| V-B | Chat-app results | `results/chat/report/`, `results/chat/silence_final.tsv`, `results/chat/silence_final_agreement.tsv`, `results/chat/vg_audit_agreement.tsv` |
| V-C | RQ3 plan quality | `results/rc1/base60/plan_indexed.csv`, `results/rc1/base60/plan_noindex.csv`, `paper/generated/tab_plan.tex`, `results/rc1/base60/pg_settings_posthoc_2026-10-22.tsv`; `harness/plan_quality.py`, `harness/indexes.sql`, `harness/db/rq3_drop_indexes.sql` |
| V-D | RQ4 stability, parse rate | `results/rc1/base60/tables/stability_parse.csv`, `paper/generated_rev/tab_stability_rev.tex` |
| VI | Silent failures; Thai adaptation | `results/rc1/paper_numbers_oct.txt`, `results/rc1/base60/partB/partB_summary.txt`; `results/rc1/base60/tables/typhoon_analysis.csv`, `results/rc1/base60/partB/b6_typhoon_llama.csv` |
| VII | Limitations | `SUPPLEMENT.md` section 1 (full list) and section 2 (errata) |
| VIII | Conclusion | this repository |
| artifact only | Sensitivity analyses | column order: `results/rc1/base60_positional/`, `results/rc1/base60_nocolroles/`, `results/rc1/h1h4_positional/`, `results/rc1/h1h4_nocolroles/`; without Q48: `results/rc1/h1h4_vg9/`; concurrent pairs only: `results/rc1/h1h4_concurrent/`; on the original database k3: `results/v13/`, `results/rc1/k3/`, `results/ext/graded_ext_k3_single_instance.csv`, `results/chat/report_k3/` |

## 3. Quick start

Run every command from the repository root. Commands that write create files under `rerun/`, so the released files are never overwritten. Start from an empty `rerun/` folder, and remove it before running the steps again: several scripts refuse to overwrite their outputs.

### 3.0 Requirements

- Python 3.14 was used. Sections 3.1, 3.4 and most of 3.6 need only the standard library. The database steps (3.2, 3.3, 3.5) need `psycopg2`; reading the `.xlsx` sheets needs `openpyxl`; figures need `matplotlib` (3.11.2 in the study). The commands use `python3 -I -B`, which ignores the user site directory, so install these packages where the interpreter's own site-packages are used (for example in a virtual environment).
- PostgreSQL 16.9 with `psql`, `createdb`, `dropdb` and `pg_dump` on the PATH. The harness connects with libpq defaults (`dbname=...` only), so set `PGHOST`, `PGPORT`, `PGUSER` and a password file if your server is not the default local one. The steps create the databases `k3`, `k3n`, `k3n_rq3` and the six instance databases named in `harness/db/mi_manifest_k3n.json`; `build_k3n.sh` and `build_instances.py` drop and recreate their target databases.
- `xz`, `shasum`, `cmp` and `diff`. On Linux, use `sha256sum` where a command says `shasum -a 256`.

```sh
mkdir -p "rerun/db"
```

### 3.1 Check the preregistration

**Append-only history.** The frozen text (lines 1–64, plus its freeze stamp) and Amendments 1–5 (6–7 August 2026) make up the first 115 lines, the earliest state whose sha256 the preregistration records. Every later change was appended, and the preregistration records the sha256 and line count of its own earlier states. Hash the first *n* lines of the current file for each recorded state:

```sh
for n in 115 1914 1970 2013 2089 2146 2207 2349; do printf "%s " "$n"; head -n "$n" "prereg/preregistration_FROZEN.md" | shasum -a 256; done
```

Each line must print the value recorded at the given line of `prereg/preregistration_FROZEN.md`:

| Lines | sha256 | Recorded at line | File state |
|---|---|---|---|
| 115 | `269e5f0996627419154ef9c032e36a92dbecb6f5b7e8f7394f1002b279a375d0` | 1419 | frozen text and Amendments 1–5 (6–7 August 2026) |
| 1914 | `8f891ca1c1c59de3967671f02a240c2c9adecd473a29c13e28512f8ce1c1c118` | 1957 | + Amendments 6–9 (19 October 2026) |
| 1970 | `5176d0c51f39477f1e3b1dc2e726c1d769967deb6cd0ff18a30c0c66cc6b5408` | 1974 | + chat-check item freeze and first addendum (19 October 2026) |
| 2013 | `36aa8d469569e70dba1eec3777350eea50bc0da9b68bf58c94cb4cb2184a3680` | 2016 | + addendum on the October collection (20 October 2026) |
| 2089 | `6c9a2012f6054432ab014ca48ac0034d5ebc3bc1f98e8705163a75de0db4999b` | 2092 | + revision addendum 1 (22 October 2026) |
| 2146 | `60725fe14e4374df6f429d016a2b52954ef46898bee6a25322362ee5228cf708` | 2149 | + revision addendum 2 (22 October 2026) |
| 2207 | `3fde32e50b85e52f603448e8c1b962211c6d586865d99277a6cf0d85bcbd3169` | 2210 | + revision addendum 3 (22 October 2026) |
| 2349 | `258226e16e58a72fc0ac464064e460b24deb4a7914985c97005f2562d7720933` | 2352 | + chat-check addendum (25 October 2026) |

Revision addendum 4 (26 October 2026) follows line 2349; the sha256 of the whole file is in `SNAPSHOT_MANIFEST.tsv`.

**Frozen instruments.** The freeze manifests list the files that each amendment froze; `freeze_stamp.py` hashes them and compares each with its pinned value:

```sh
python3 -I -B "kst_rev/gate0/harness/freeze_stamp.py" --manifest "kst_rev/gate0/harness/freeze_manifest_gate1b.tsv"
python3 -I -B "kst_rev/gate0/harness/freeze_stamp.py" --manifest "kst_rev/gate0/harness/freeze_manifest_gate2.tsv"
```

The tool prints in Thai; its last line is a summary (`สรุป`). For the second manifest the summary should report `FAIL 0`. The first reports FAIL only for files that this snapshot changed (Section 1, `PROVENANCE.md`); for those, the sha256 before the change in `PROVENANCE.md` equals the pinned value. Rows without a pinned value print the current sha256, for comparison with the FREEZE STAMP tables in the preregistration; the tree hash of `kst_rev/wf_q100/translation_check/sql_TESTONLY/` also differs from the value at line 1907, because one file in it changed (`PROVENANCE.md`).

`kst_rev/gate0/harness/prereg_append_check.py` is the checker that was run on the preregistration after each append in the private repository. Its `base` check is the prefix-hash check above. It also runs an identity sweep through a module and a local pattern file that are not part of this snapshot, so it does not run here.

### 3.2 Rebuild the databases

These commands follow the study's run book; the full sequence has not yet been re-run end to end on a fresh server. Use a scratch PostgreSQL cluster (the steps create and drop databases), and please open an issue if a step fails.

The study database `k3` holds the course data as distributed and the 10^6-row table. The grading database `k3n` is built from it by `harness/db/build_k3n.sh`, which applies one rule (every text cell equal to `'None'` becomes NULL; six cells) and copies the 10^6-row table from `k3`, checking its row count and row hash. The study databases used encoding UTF8 with collation and character type `C` (first line of `results/db/k3_fp_before.tsv`).

```sh
python3 -I -B "harness/db/db_fingerprint.py" csvcheck --csv-dir "data/course" --expect "harness/db/k3n_inputs.sha256"
xz -dc "data/ecommerce1m/Ecommerce1M.csv.xz" > "rerun/db/Ecommerce1M.csv"
createdb --template=template0 --encoding=UTF8 --locale=C --locale-provider=libc "k3"
psql -d "k3" -f "harness/setup_db.sql"
psql -d "k3" -c "\copy President FROM 'data/course/President.csv' CSV HEADER"
psql -d "k3" -c "\copy Party FROM 'data/course/Party.csv' CSV HEADER"
psql -d "k3" -c "\copy PresidentMarriage FROM 'data/course/PresidentMarriage.csv' CSV HEADER"
psql -d "k3" -c "\copy PresidentHolding FROM 'data/course/PresidentHolding.csv' CSV HEADER"
psql -d "k3" -c "\copy Ecommerce FROM 'data/course/Ecommerce_Dataset.csv' CSV HEADER"
psql -d "k3" -c "\copy Ecommerce1M FROM 'rerun/db/Ecommerce1M.csv' CSV HEADER"
python3 -I -B "harness/db/db_fingerprint.py" fingerprint --dsn "dbname=k3" --out "rerun/db/k3_fp.tsv"
python3 -I -B "harness/db/db_fingerprint.py" crosscheck "results/db/k3_fp_before.tsv" "rerun/db/k3_fp.tsv"
K3N_CSV_DIR="data/course" K3N_ECOM1M_FROM_REF=1 K3N_FP_OUT="rerun/db/k3n_fp.tsv" bash "harness/db/build_k3n.sh"
python3 -I -B "harness/db/db_fingerprint.py" crosscheck "results/db/k3n_fp_run1.tsv" "rerun/db/k3n_fp.tsv"
```

Expected: `csvcheck` checks six entries (the five data files and `setup_db.sql`) and prints `RESULT: PASS`; `build_k3n.sh` counts 6 `'None'` cells and ends with `== done: k3n ready` (its `INFO` lines on physical row order are information only); both `crosscheck` commands print `RESULT: PASS`, with server-setting differences reported as WARN and physical-order fields as INFO.

Then check every gold query and build the planted instances of the three multi-instance extension items:

```sh
python3 -I -B "harness/selftest_v13n.py" --suite "suite/k3n_suite_v1.3n_oct.tsv" --suite-v12 "suite/k3_suite_v1.2.tsv" --pg "dbname=k3n"
python3 -I -B "harness/db/build_instances.py" --manifest "harness/db/mi_manifest_k3n.json" --pg "dbname=k3n" --grader "harness/grade_v13n.py"
python3 -I -B "harness/db/build_instances.py" --manifest "harness/db/mi_manifest_k3n.json" --pg "dbname=k3n" --grader "harness/grade_v13n.py" --check-gold-only
python3 -I -B "harness/selftest_v13n.py" --suite "suite/k3n_ext_suite_v1.0.tsv" --pg "dbname=k3n" --mi-manifest "harness/db/mi_manifest_k3n.json"
```

Expected: the core self-test prints PASS with `items: 60 (primary 60)`; the instance check ends with `GOLD CHECK OK`; the extension self-test prints PASS.

### 3.3 Re-grade the logs

The grader executes every logged query on `k3n` and refuses to run unless the five course tables match the released fingerprint.

```sh
python3 -I -B "harness/grade_v13n.py" --results "results/rc1/results_rc1_api.jsonl" --results "results/rc1/results_rc1_local.jsonl" --suite "suite/k3n_suite_v1.3n_oct.tsv" --pg "dbname=k3n" --db-fingerprint "results/db/k3n_fp_run1.tsv" --out "rerun/graded_rc1.csv"
cmp "rerun/graded_rc1.csv" "results/rc1/graded_rc1.csv"
python3 -I -B "harness/grade_v13n.py" --results "results/ext/results_ext_api.jsonl" --results "results/ext/results_ext_local.jsonl" --suite "suite/k3n_ext_suite_v1.0.tsv" --pg "dbname=k3n" --db-fingerprint "results/db/k3n_fp_run1.tsv" --mi-manifest "harness/db/mi_manifest_k3n.json" --mi-log "rerun/graded_ext_mi.csv" --arms base --out "rerun/graded_ext.csv"
cmp "rerun/graded_ext.csv" "results/ext/graded_ext.csv"
cmp "rerun/graded_ext_mi.csv" "results/ext/graded_ext_mi.csv"
python3 -I -B "harness/grade_v13n.py" --results "results/results.jsonl" --suite "suite/k3n_suite_v1.3n.tsv" --pg "dbname=k3n" --db-fingerprint "results/db/k3n_fp_run1.tsv" --out "rerun/graded_v13n.csv"
cmp "rerun/graded_v13n.csv" "results/v13n/graded_v13n.csv"
python3 -I -B "harness/grade_v13n.py" --results "results/chat/results_chat.jsonl" --suite "suite/k3n_suite_v1.3n.tsv" --pg "dbname=k3n" --db-fingerprint "results/db/k3n_fp_run1.tsv" --arms chat --out "rerun/graded_chat_k3n.csv"
cmp "rerun/graded_chat_k3n.csv" "results/chat/graded_chat_k3n.csv"
python3 -I -B "harness/empty_split_v13.py" --results "results/rc1/results_rc1_api.jsonl" --results "results/rc1/results_rc1_local.jsonl" --graded "results/rc1/graded_rc1.csv" --suite "suite/k3n_suite_v1.3n_oct.tsv" --pg "dbname=k3n" --arm base --vg-set "suite/vg_set_v13n.txt" --out-rows "rerun/base60/partB/silent_split_rows.csv" --out-summary "rerun/base60/partB/silent_split.csv"
```

Expected: each `cmp` prints nothing (identical files). The four grading commands cover the October core log (both prompts), the extension, the August log under the revised key, and the chat replies.

### 3.4 Regenerate the numbers and tables

These steps read the released graded files and need no database.

```sh
python3 -I -B "harness/analyze.py" --graded "results/rc1/graded_rc1.csv" --suite "suite/k3n_suite_v1.3n_oct.tsv" --arm base --out "rerun/base60/tables"
python3 -I -B "harness/analyze_typhoon.py" --graded "results/rc1/graded_rc1.csv" --suite "suite/k3n_suite_v1.3n_oct.tsv" --arm base --b6 --out "rerun/base60/tables"
python3 -I -B "harness/phi_tableiv.py" --graded "results/rc1/graded_rc1.csv" --suite "suite/k3n_suite_v1.3n_oct.tsv" --arm base --out "rerun/base60/tables/phi_tableiv.csv"
python3 -I -B "harness/analyze_log_v13.py" --graded "results/rc1/graded_rc1.csv" --results "results/rc1/results_rc1_api.jsonl" --results "results/rc1/results_rc1_local.jsonl" --suite "suite/k3n_suite_v1.3n_oct.tsv" --arm base --vg-set "suite/vg_set_v13n.txt" --plan-dir "results/rc1/base60" --out "rerun/base60/partB"
python3 -I -B "harness/paper_numbers_v13n.py" --graded "results/rc1/graded_rc1.csv" --suite "suite/k3n_suite_v1.3n_oct.tsv" --arm base --out "rerun/paper_numbers_oct.txt"
python3 -I -B "harness/consistency_aug_oct.py" --aug "results/v13n/graded_v13n.csv" --oct "results/rc1/graded_rc1.csv" --aug-suite "suite/k3n_suite_v1.3n.tsv" --oct-suite "suite/k3n_suite_v1.3n_oct.tsv" --arm base --out "rerun/consistency"
python3 -I -B "harness/analyze_rc1.py" --mode rc1 --graded "results/rc1/graded_rc1.csv" --results "results/rc1/results_rc1_api.jsonl" --results "results/rc1/results_rc1_local.jsonl" --graded-ror "results/v13n/graded_v13n.csv" --suite "suite/k3n_suite_v1.3n_oct.tsv" --hints "suite/value_hints_v1.json" --hints-sha256 "2ea5efb413182b7929310f30bb312175776e63ea18eec0616ac7bbd0cc38919c" --vg-set "suite/vg_set_v13n.txt" --expect-vg-cov "Q01,Q07,Q09,Q13,Q14,Q15,Q21,Q30,Q42" --out "rerun/h1h4"
python3 -I -B "harness/make_table_rc1.py" --in-dir "rerun/h1h4" --out "rerun/h1h4/tab_values.tex"
python3 -I -B "harness/analyze_ext.py" --graded "results/ext/graded_ext.csv" --mi-log "results/ext/graded_ext_mi.csv" --graded-positional "results/ext/graded_ext_positional.csv" --graded-nocolroles "results/ext/graded_ext_nocolroles.csv" --suite "suite/k3n_ext_suite_v1.0.tsv" --arm base --exclude-models "typhoon2-8b" --core-graded "results/rc1/graded_rc1.csv" --core-suite "suite/k3n_suite_v1.3n_oct.tsv" --results "results/ext/results_ext_api.jsonl" --results "results/ext/results_ext_local.jsonl" --hints "suite/value_hints_v1.json" --hints-sha256 "2ea5efb413182b7929310f30bb312175776e63ea18eec0616ac7bbd0cc38919c" --out "rerun/ext_tables"
python3 -I -B "harness/make_table_ext.py" --in-dir "rerun/ext_tables" --out "rerun/ext_tables/tab_ext.tex"
python3 -I -B "harness/make_tables.py" --results-dir "results/rc1/base60" --out-dir "rerun/generated" --arm base --captions revised --ci-label "results/rc1/base60/tables/phi_tableiv.csv"
python3 -I -B "harness/rev_numbers.py" --graded-rc1 "results/rc1/graded_rc1.csv" --graded-ext "results/ext/graded_ext.csv" --results-ext-api "results/ext/results_ext_api.jsonl" --acc-v12 "results/tables/accuracy.csv" --acc-v13n "results/v13n/tables/accuracy.csv" --acc-oct "results/rc1/base60/tables/accuracy.csv" --out "rerun/rev_numbers"
python3 -I -B "harness/make_tables_rev.py" --generated "paper/generated" --acc-core "results/rc1/base60/tables/accuracy.csv" --ext-acc "results/ext/tables/ext_accuracy.csv" --typhoon-ext "results/rc1/rev_numbers/ext_typhoon_descriptive.csv" --gap "results/rc1/h1h4/rc1_gap.csv" --out "rerun/generated_rev"
```

`--hints-sha256` is the sha256 of `suite/value_hints_v1.json` as pinned in the preregistration (line 1441). The extension analysis leaves out `typhoon2-8b`, as the preregistration's October collection addendum records (line 1986); its extension counts are reported descriptively by `rev_numbers.py`.

Compare with the released files:

```sh
diff -r -x "*meta.json" "rerun/base60/tables" "results/rc1/base60/tables"
diff -r -x "*meta.json" "rerun/base60/partB" "results/rc1/base60/partB"
cmp "rerun/paper_numbers_oct.txt" "results/rc1/paper_numbers_oct.txt"
diff -r -x "*meta.json" "rerun/consistency" "results/rc1/consistency"
diff -r -x "*meta.json" "rerun/h1h4" "results/rc1/h1h4"
diff -r -x "*meta.json" "rerun/ext_tables" "results/ext/tables"
diff -r "rerun/generated" "paper/generated"
diff -r -x "*meta.json" "rerun/rev_numbers" "results/rc1/rev_numbers"
diff -r -x "*meta.json" -x "tab_headline_rev.tex" "rerun/generated_rev" "paper/generated_rev"
shasum -a 256 "rerun/generated_rev/tab_headline_rev.tex"
```

Expected: no differences. The `meta.json` files and `*.meta.json` sidecars record input paths and the PostgreSQL version string, so they can differ on another machine and are left out of the comparison. Without the database steps of Section 3.3, `diff` lists the three `silent_split` files of `results/rc1/base60/partB` as present only in the released folder, and the comparison of `rerun/generated` lists the two figures (`fig_tiers.pdf`, `fig_slope.pdf`), which `harness/make_figures.py` writes. The last command prints the sha256 of Table I, which must equal `95389bc7f63cb96b1468c125196bf2c8b758911e0fadc3d89cf3084a57eb09fc`, the value pinned in the preregistration (lines 2115 and 2582).

### 3.5 Plan quality (RQ3)

Plan quality is measured with `EXPLAIN` on a copy of `k3n` (no query runs), first with the indexes of `harness/indexes.sql`, then without them.

```sh
createdb -T "k3n" "k3n_rq3"
psql -d "k3n_rq3" -f "harness/indexes.sql"
python3 -I -B "harness/plan_quality.py" --graded "results/rc1/graded_rc1.csv" --results "results/rc1/results_rc1_api.jsonl" --results "results/rc1/results_rc1_local.jsonl" --suite "suite/k3_suite_v1.2.tsv" --d11-gold-suite "suite/k3n_suite_v1.3n_oct.tsv" --pg "dbname=k3n_rq3" --arm base --phase indexed --out "rerun/plan_indexed.csv"
psql -d "k3n_rq3" -f "harness/db/rq3_drop_indexes.sql"
python3 -I -B "harness/plan_quality.py" --graded "results/rc1/graded_rc1.csv" --results "results/rc1/results_rc1_api.jsonl" --results "results/rc1/results_rc1_local.jsonl" --suite "suite/k3_suite_v1.2.tsv" --d11-gold-suite "suite/k3n_suite_v1.3n_oct.tsv" --pg "dbname=k3n_rq3" --arm base --phase noindex --out "rerun/plan_noindex.csv"
dropdb "k3n_rq3"
```

`createdb -T` fails while another session is connected to `k3n`. Compare `total_cost`, `scan_types`, `uses_index` and `cost_ratio_vs_gold` with `results/rc1/base60/plan_indexed.csv` and `results/rc1/base60/plan_noindex.csv`. Planner costs are estimates: they depend on server settings and shift slightly with the statistics that `ANALYZE` samples, so expect close but not always identical values. The settings in effect during the October runs, captured afterwards, are in `results/rc1/base60/pg_settings_posthoc_2026-10-22.tsv` (among them `random_page_cost` 1.1, `work_mem`, `shared_buffers` and `effective_cache_size`).

### 3.6 Chat-check reports and rater agreement

The chat-check reports are computed from the graded chat replies, the coding sheets and the October proxy log; no database is needed.

```sh
python3 -I -B "harness/chatapp/vg_outcome.py" --graded "results/chat/graded_chat_k3n.csv" --results "results/chat/results_chat.jsonl" --suite "suite/k3n_suite_v1.3n.tsv" --hints "suite/value_hints_v1.json" --hints-sha256 "2ea5efb413182b7929310f30bb312175776e63ea18eec0616ac7bbd0cc38919c" --out "rerun/chat/vg_codes_chat.tsv"
python3 -I -B "harness/chatapp/chat_report.py" --graded "results/chat/graded_chat_k3n.csv" --graded-turn2 "results/chat/graded_chat_turn2_k3n.csv" --graded-tagsens "results/chat/graded_chat_tagsens_k3n.csv" --vg-codes "results/chat/vg_codes_chat.tsv" --silence "results/chat/silence_final.tsv" --log-index "results/chat/log_index.tsv" --rc1-graded "results/rc1/graded_rc1.csv" --rc1-results "results/rc1/results_rc1_api.jsonl" --suite "suite/k3n_suite_v1.3n.tsv" --hints "suite/value_hints_v1.json" --hints-sha256 "2ea5efb413182b7929310f30bb312175776e63ea18eec0616ac7bbd0cc38919c" --arm base --out "rerun/chat_report"
cmp "rerun/chat/vg_codes_chat.tsv" "results/chat/vg_codes_chat.tsv"
diff -r "rerun/chat_report" "results/chat/report"
```

Expected: no differences. The translation-agreement figures of Section III-B (observed agreement and Cohen's κ) come from the two rating sheets and need `openpyxl`:

```sh
python3 -B -E -P "harness/score_annotation.py" --a "results/annotation_sheet_A.xlsx" --b "results/annotation_sheet_B.xlsx"
```

PABAK is 2 × observed agreement − 1. The `.tsv` files next to the sheets are the blank rating templates.

## 4. What reproduces and what does not

- **Graded counts reproduce exactly.** Re-grading the released logs with the released grader, answer key and database (Section 3.3) reproduces the released graded files under the revised key, from which the paper's counts are computed. The August log's grading under the original key, cited in the paper for the submitted results, is released as `results/graded.csv` and `results/tables/` (grader `harness/grade.py`); Section 3.3 does not re-run it. The graded files also store PostgreSQL's error messages, and the error taxonomy of Section VI counts loud runs by that text, so use PostgreSQL 16.9 with server messages in English (the study server ran with `lc_messages` `C`) to get identical files.
- **Analyses are deterministic given the graded files.** The item-cluster bootstrap in `harness/analyze_rc1.py` uses a fixed seed (20261012).
- **Table I** is regenerated by `harness/make_tables_rev.py`; its sha256 must match the value pinned in the preregistration (Section 3.4).
- **API generations do not re-run identically.** Temperature 0 does not make the API endpoints deterministic, and the `claude-sonnet-5` endpoint runs at the provider's default temperature because it rejects the parameter. Two of the three identifiers, `claude-sonnet-5` and `gemini-3.6-flash`, are undated aliases, so the model behind them may have been updated since the study; their provider metadata was identical before and after the October collection (`results/rc1/provenance_before.json`, `results/rc1/provenance_after.json`), which does not rule out an update. Re-running needs API keys and billed calls; `harness/runner.py` and `harness/models.json` are included for that purpose.
- **Local models.** In October the local models ran under Ollama 0.32.5 at temperature 0 with a fixed seed, and their Ollama digests (and the sha256 of the Thai-adapted model's GGUF file) are recorded in `results/rc1/provenance_gate1a.json`, `results/rc1/provenance_before.json` and `results/rc1/provenance_after.json`. The August collection did not record digests. A re-run is not guaranteed to be identical: the order of calls affects Ollama's prefix-cache state (SUPPLEMENT.md, section 1, item 3). The Thai-adapted weights are a community quantization of a repository that is no longer accessible (SUPPLEMENT.md, section 1, item 8).
- **Planner costs** re-derive only up to `ANALYZE` sampling and depend on server settings (Section 3.5).
- **The 10^6-row table is shipped** because its generator, `harness/scale_ecommerce.py`, does not reproduce it byte for byte: the output also depends on Python's string-hash randomization. The shipped table has the row count and row hash recorded in `results/db/k3n_fp_run1.tsv`.
- **The chat-app check** was a single-shot check on 21 October 2026; the apps can change their models and routing without notice. Its transcripts, screenshots and coding sheets are included, and its grading and reports reproduce from them (Sections 3.3 and 3.6).
- **Human codings** (silence codes, the blind audits, the translation ratings) are recorded in the sheets under `results/`; their agreement statistics recompute from those sheets.

## 5. Preregistration and deviations

- `prereg/preregistration_FROZEN.md` fixes the metrics, tests and exclusions. It was frozen on 6 August 2026; the first commit of the working repository followed the two local-model arms of the August collection.
- Amendments 1–5 are dated 6 and 7 August 2026. Among the later changes, the Thai-adapted model was added during the August collection, plan quality replaced timing after it, and the value-grounding rule, answer key and grader were revised after its results had been seen. Amendments 4–9, with the stored-values condition (Amendment 7), the chat check (Amendment 8) and the extension (Amendment 9), were committed and pushed before the first model call or chat of the October collection. The addendum at line 1955 of the preregistration records that commit at 2026-10-19 12:45:08 (UTC+7), pushed before the official re-grade of the August log; the first October model call is logged at 19:44:40 the same day (line 1976).
- Deviations are logged in Amendment 7, Part D (D-1 to D-11), and in the dated revision addenda (D-12 to D-20). Since 19 October 2026, each appended batch records the sha256 and line count of the file before it; the first record (line 1419) covers lines 1–115 (Section 3.1).
- The extension items were chosen after the August results were known, so extension results are descriptive. All results for the three local models are exploratory.
- The commit identifiers and times in the preregistration refer to the private working repository. This snapshot lets you check that every earlier state recorded in the preregistration is a prefix of the current file and that frozen instruments match their pinned hashes (Section 3.1). Because those records are in the same file, this shows consistency with append-only growth; the commit history of the private repository is the independent record, and this snapshot cannot by itself show when each commit was made.

## 6. Environment

As stated in the paper: the October local inference, grading and analysis ran on a single consumer laptop, a MacBook Pro (Apple M4 Pro, 24 GB unified memory) with macOS 26, Python 3.14, PostgreSQL 16.9 and Ollama 0.32.5; the API models were accessed on 19–20 October 2026. The Python patch version changed from 3.14.7 to 3.14.8 on 18 October 2026, before the official re-grade and the October collection (preregistration, line 1959). The PostgreSQL settings are in `results/rc1/base60/pg_settings_posthoc_2026-10-22.tsv`. The versions of `psycopg2` and `openpyxl` were not recorded.

## 7. Licenses

- Code: MIT License (`LICENSE`).
- Suite, data and results: Creative Commons Attribution 4.0 International (`LICENSE-DATA.md`).
- The paper is under IEEE copyright and is not part of this repository.

## 8. Contact

Corresponding author: Arun Reungsilpkolkarn, arun.r@bu.ac.th. Other courses, in Thai and beyond, are invited to add their own readings with this instrument by pull request, with execution-validated gold queries and run logs (SUPPLEMENT.md, section 5).
