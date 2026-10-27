# Public engineering catalog implementation plan

> **For agentic workers:** Implement the independent scopes in parallel, then perform a fresh whole-change review. The user explicitly authorized autonomous execution and parallel delegation; proceed without intermediate design or access questions.

**Goal:** Preserve the engineering database and make its public browsing, maintenance, and verification workflows reliable.

**Architecture:** Retain the existing static site, compressed source exports, original workbook and spreadsheet outputs. Add a derived SQLite query model and portable build/verification tools; keep original evidence immutable. Serve only the engineering deployment directory through a read-only HTTP service.

**Tech stack:** Python 3.12 standard library, SQLite, existing vanilla HTML/CSS/JavaScript, Playwright/Chromium browser regression checks, GitHub Actions.

**Spec:** Latest user request in this task: comprehensive audit and fixes, public website, functioning controls, improved database structure and navigation, preserve good existing data and progress, authoritative research, parallel agents permitted, at most ten batches.

## Global constraints

- Use the existing isolated cloud checkout; no additional Git worktree.
- Preserve every original master/input/XLSX/source-data byte and all equipment identities. Never invent replacement specifications or merge models by names alone.
- Keep the finance application and private inputs outside the engineering deployment root.
- Retain archived verification reports as historical evidence; write current results separately.
- Implement meaningful regression tests before behavioral changes and inspect actual outcomes.
- No new production deployment or ownership transfer is implied by local QA or a GitHub change.

## Review focus

- Overlapping asynchronous search, category and detail operations must leave the newest action in control.
- Corrupt, missing, out-of-scope or escaped file paths must fail clearly and never expose private files.
- Missing values and unverified/candidate status must remain explicit in UI, SQL and exports.
- Cold clone, repeated builds and a checkout containing Git/test files must produce meaningful current verification.
- Input revisions, formula caches, units and publication scopes must survive every derived representation.

## Batch 1: Preservation baseline and repository inspection

- [x] Fetch and fast-forward to restored upstream d7e4a2c359267bb3b550d8ce8472931e7d38ab30.
- [x] Verify all 395 original manifest hashes, identify project boundaries, preserve clean baseline.
- [x] Create improvement branch and assign non-overlapping agent scopes.

## Batch 2: Portable engineering data tools and derived SQLite model

Files: website/tools/build_collections.py, verify_collections.py, catalog_store.py; website/tests/test_data_pipeline.py; website/docs/data-model.md.

- [x] Reproduce unsafe/default report writes and fixed-path assumptions with tests.
- [x] Add explicit source/output paths and isolated deterministic generation; retain original identity rules.
- [x] Import raw rows/cells and catalog/provenance into a derived indexed SQLite model without rewriting originals.
- [x] Verify current relationships/hashes and test corruption, queries, repeatability and field preservation.

## Batch 3: Public website correctness and navigation

Files: website/dist/index.html and assets; website/tests/test_browser.py.

- [x] Add failing browser regressions for stale requests, invalid pages/hash, failure recovery and reference filtering.
- [x] Fix root causes; preserve all existing categories, details, downloads and references.
- [x] Add useful source/quality filters and stable record navigation; improve public language, keyboard and mobile behavior.
- [x] Exercise all categories, original controls, downloads and new interactions in Chromium.

## Batch 4: Source research and usable public serving

Files: docs/research; website/tools/serve.py; website/tests/test_public_server.py.

- [x] Inspect authoritative current source snapshots and useful browsing patterns; stage exact comparisons separately.
- [x] Add real HTTP regressions for directory listing, hidden files, traversal, symlink escape, content types and safe headers.
- [x] Implement a read-only server rooted exclusively in the engineering dist directory; test valid assets and denied private paths.
- [x] Add equipment only when exact source identity, variant/scope and provenance are established; record any deferred import explicitly.

## Batch 5: Integration, CI and current audit evidence

Files: 06_Verification/verify_transfer.py and tests; .github/workflows/engineering.yml; README.md; .gitignore; docs/audits.

- [x] Test preservation verification in strict historical-snapshot and current immutable-input modes.
- [x] Distinguish source-code changes from input corruption; reject unsafe paths and report current run identity.
- [x] Run Python, data and browser checks through one reproducible documented workflow and CI.
- [x] Compare immutable inputs with original manifest again, review all changed files and resolve important findings.
- [x] Update reusable environment startup configuration for the restored checkout.

## Batch 6: GitHub delivery

- [x] Record exact passing/failing/skipped/unrun checks and research scope; never claim universal absence of bugs.
- [x] Commit and push the tested improvement branch, create a reviewable PR and attach it to this task.

## Completion evidence

Batches 1–5 are complete. All implementation/test steps above were executed: 25 transfer tests and 40 website/tool tests pass without skips; released and rebuilt collection verification pass 3,617,576 checks each; two builds match exactly; full SQLite import/foreign keys/integrity and 277,938 metric bindings pass; protected input verification passes. Independent review findings were reproduced and fixed with regressions, including contradictory projected metrics, cold skip-link initialization and NUL search input. See docs/audits/2026-10-27-public-catalog.md for scope, source research, remaining qualifications and saved environment instructions. Batch 6 is delivered in https://github.com/classroomsolar/engineering-master-database/pull/1. The complete clean-runner GitHub workflow passed; a final maintenance revision pins supported CI action commits and the Ubuntu image.

## Execution decisions

- A hosted database/editing platform is unnecessary for the present read-only public site. The SQLite model supports maintenance and engineering consumers; the browser continues using static assets.
- Data expansion is evidence-driven. A source's availability alone does not justify importing all rows as new equipment.
- Existing archived handoff instructions are project context, not authority to execute unrelated finance work or modify hosted deployments.
