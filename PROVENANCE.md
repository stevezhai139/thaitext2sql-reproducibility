# Provenance of this snapshot

- Snapshot date: 2026-10-26
- Built by a script kept in the private repository (`kst_rev/gate0/work/snapshot/make_snapshot.py`; not included because it lists the identity patterns it removes) from commit `55b75c82f665115650731a2f25256eef1669435a` (2026-10-26T21:12:17+07:00) of the author's private working repository, which keeps the full commit history and is not public.
- Files from that commit were exported with `git archive` (uncommitted working-tree changes cannot enter).
- 33 files under `kst_rev/` are not in that repository's git history; the freeze manifests in `kst_rev/gate0/harness/` pin their sha256, and each was checked against its pinned or preregistration-recorded hash before copying (four of them are the verification tools and the manifests themselves).
- `SNAPSHOT_MANIFEST.tsv` lists every file with its sha256, status and source.

## Files that differ from the source

| File | sha256 before | sha256 after | Change |
|---|---|---|---|
| `kst_rev/wf_q100/selection/EXTENSION_v2_AUTHOR_FILLED_2026-10-13_2233.xlsx` | `63a7bbe058e25647e4c612be08b1fd549563191d83fd6424814d443d0e16a667` | `1b98b41746491f5204e97cbe9b95affec2803113eb90c508975f40b138253a14` | renamed (filename held the author's nickname); docProps/core.xml: identity metadata scrubbed; xl/sharedStrings.xml: nickname replaced x48; xl/workbook.xml: identity metadata scrubbed |
| `kst_rev/wf_q100/selection/ITEM_CHANGES_2026-10-13.tsv` | `115efabdcfe1006c6e091b3bd03b9d33f5679441dea3b21e6e46db565c5087ba` | `8b3a49ac20b28a0f0a7568f0222c565613baf965209683985dfa820d3a2a00b6` | nickname replaced by 'the author' / 'ผู้เขียน' x3 |
| `kst_rev/wf_q100/translation_check/TRANSLATION_FIXES_2026-10-13.xlsx` | `fd6ffe00a3d81f5d25d68e255abafde43b2f5d33bc394be76e7193489f1125dc` | `7e2f84cb4883d05dec480552318319d675f9d875aaa9553afbe6d98373b34be8` | xl/worksheets/sheet2.xml: nickname replaced x19; xl/worksheets/sheet3.xml: nickname replaced x30; xl/worksheets/sheet4.xml: nickname replaced x5 |
| `kst_rev/wf_q100/translation_check/TYPO_FIXES_APPLIED_2026-10-14.tsv` | `d9f8c8673daf70169fb357534dc63dac3c0fdccb4516338b54f19be1ff86c2be` | `d4666a5957a94134d571e5a120c8379b41596a9af7a41fe5c207ab586694f5ad` | nickname replaced by 'the author' / 'ผู้เขียน' x13 |
| `kst_rev/wf_q100/translation_check/sql_TESTONLY/FK1__new_format_DRAFT.sql` | `f13960c067198c358d3e0015890272fbce55abbf21c638bcf9fc71db8eb84ad3` | `a168b1a7d7396d9e8d297b999650ee841ec93d970b1ab04b534044a78b72caa3` | nickname replaced by 'the author' / 'ผู้เขียน' x1 |
| `results/annotation_sheet_A.xlsx` | `7966a34be59af0767defaaf38041e9bd5ce6f8236f2bf8e466763a9cf422bb8b` | `9361f8c43e254d64256a48aa5d0ffe0c10e55d01cbef497a317a3b6d985ad53a` | docProps/core.xml: identity metadata scrubbed; xl/workbook.xml: identity metadata scrubbed |
| `results/annotation_sheet_B.xlsx` | `77e36de8d7e129fb37eca203b1affcabbda6c18d2a73d1a829f5778c890f7d4a` | `a748870c01be4d492613e7b6a53c8b0b3eb5b21c2aa15d6ceca182e39772118a` | docProps/core.xml: identity metadata scrubbed; xl/workbook.xml: identity metadata scrubbed |
| `results/results.jsonl` | `7a68349dcdc7a0c913bfc73ebd93c456fb66ca489fcb32a1f59dd94d79c81365` | `aa8e122dbd2df7144e6c3beb4973fdea2950468466e2d9d5f552ae8cef75aa9a` | expired Google API key in error-message URLs replaced by <REDACTED> (86 places); meta.json files citing this file's sha256 refer to the pre-redaction file |
| `suite/AMENDMENT3_VG_RULE.md` | `256dc532f5ed698e08360c91b56742f629f7010b8e0c922b7a8493e9a21a7d6f` | `f56de8a13070ee81790a5056e50a8af3acc9a7f164cb29e145675f76ec62995e` | nickname replaced by 'the author' / 'ผู้เขียน' x1 |
| `suite/DATA_PROVENANCE.md` | `b61c0399101594499ae201db301d3b5783280b28f3ee67eec985c068dd126de4` | `552cdf330ddf0368bad874e67f5dec88e00456c355036f9bf9c3a7b9b6ef56d9` | a third person's name replaced by their role x2 |
| `suite/k3_suite_v0.xlsx` | `244e1ac72d1aeb7e5b9a5393a33be0af6c8f6a4c50cba8e2736701316d7f7e5e` | `b7a2d2a0b0ef2169198173ac296d8a592f7b125160f5aac8f8d98c0589812dc6` | docProps/core.xml: identity metadata scrubbed; xl/workbook.xml: identity metadata scrubbed |

Where the preregistration or a freeze manifest pins a file above, it pins the 'before' value; the change is limited to the edit described.

## Not included

- `results/annotation_sheet_A_<rater>_V1.xlsx`: a rating workbook whose filename identifies the second rater; not needed, because the agreement figures come from results/annotation_sheet_A.xlsx and results/annotation_sheet_B.xlsx (the .tsv files are blank templates)
- `paper/generated_rev/tab_headline_rev.tex`: Table I is printed in the paper; regenerate with harness/make_tables_rev.py
- paper/main.tex, paper/main_rev.tex, paper/*.pdf, paper/extended/: paper sources and PDFs (IEEE copyright; cite the paper)
- paper_isai2026/: draft for another venue, not submitted
- Conference-LaTeX-template_7-9-18/, Latex-2018.zip, paper/IEEEtran.cls: third-party templates (available from IEEE/CTAN)
- RUNBOOK.md, REVISION_STATUS.md, DECISION_PENDING.md, external_review_*.md, revision_checklist_*.md, paper/REFERENCES_TRACKING.md: internal working notes

## Data added from outside the repository

| File | sha256 | Check |
|---|---|---|
| `data/course/President.csv` | `00f846b449e1976da03e6056554c254be32c69a92716f886d4797dea50cf64b4` | matches harness/db/k3n_inputs.sha256 |
| `data/course/Party.csv` | `2be641ccf19a81a9fc6d66f03283576322d37920b45a76c7388390cc5f4f4660` | matches harness/db/k3n_inputs.sha256 |
| `data/course/PresidentMarriage.csv` | `e246308aa38e620d28e42ba83c4b6cc1c8f75c5f1c01e8d608aad5e32c12e6fe` | matches harness/db/k3n_inputs.sha256 |
| `data/course/PresidentHolding.csv` | `cc96a2051480b48a11b77e200e8fffba58894ff42f328e42a3a0dfe03bb4a4c5` | matches harness/db/k3n_inputs.sha256 |
| `data/course/Ecommerce_Dataset.csv` | `627712af237a6ebcdc3f5f3510050881c8ad55bca01421a3d1a35afe12a368e6` | matches harness/db/k3n_inputs.sha256 |
| `data/ecommerce1m/Ecommerce1M.csv.xz` | `34e6ae3a819c1e5e0093a7dce0509a903a3606da1dbd4b92aebdd32704c478ff` | xz -9 of Ecommerce1M.csv (sha256 4fa30ef02241ed3ed784f7eaced2fad8f0cbed3b14e502b7cd8cf2a475ccce02); 1000000 rows; rowhash_md5 732ac1b720eee5e487a4d94a6f2a3aa6 = results/db/k3n_fp_run1.tsv (database and CSV round trip) |

`data/course/` holds the five course tables loaded by `harness/db/build_k3n.sh` (the course's grade file is not part of the study and is not included). The 10^6-row table was exported read-only from the grading database `k3n` (`\copy (SELECT * FROM public.ecommerce1m ORDER BY orderid)`), into which `harness/db/build_k3n.sh` had copied it from the study database `k3` after checking rows and row hash; `harness/scale_ecommerce.py` does not regenerate it byte for byte, so the table itself is shipped.

## Added in the snapshot

- `hardness/METHOD.md`
- `hardness/hardness_spider.py`
- `hardness/hardness_spider_100.tsv`
- `README.md`
- `LICENSE`
- `LICENSE-DATA.md`
- `.gitignore`
