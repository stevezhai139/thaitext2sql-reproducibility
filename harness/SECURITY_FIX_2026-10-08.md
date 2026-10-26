# Harness security fix — 8 Oct 2026 (not a protocol amendment)

**Problem.** `runner.py` sent the Google API key as a URL query parameter (`?key=…`). When a request failed, the HTTP error text contained the full URL, and `runner.py` wrote that text into the `error` field of `results/results.jsonl`. The run-of-record file committed on 12 Aug 2026 (commit 2b81d9c) therefore holds the key in 86 error records. The repository is private, with one collaborator and no forks.

**Actions taken (8 Oct 2026).**
1. The author created a new key in Google AI Studio, put it in `harness/secrets.env`, and deleted the two old keys: the leaked key and a key exposed in a chat transcript. AI Studio now lists one key. `secrets.env` is git-ignored. None of the three provider keys appears in any tracked file.
2. `runner.py` changes:
   - The Google key is now sent in the `x-goog-api-key` header, not in the URL.
   - New `redact()` removes the values of `OPENAI_API_KEY`, `ANTHROPIC_API_KEY` and `GOOGLE_API_KEY`, and any `key=` URL parameter, from error text before it is written to the log.
   - Tested offline with a fake key; no real API call was made.

**Effect on results.** None. The change touches only how the key is sent and how errors are logged. Prompts, models, parameters, grading and every number in the paper are unchanged. The run-of-record file is not modified.

**Before any public release of the artifact.** Build the release from a snapshot in which the old key in the `error` fields of `results/results.jsonl` is masked (`<REDACTED>`). Leave all result columns unchanged, and state the masking in the release README. The old key no longer works, so the private history does not need rewriting.
