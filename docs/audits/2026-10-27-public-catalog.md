# Public engineering catalog audit and fixes — 27 October 2026

## Outcome

The engineering catalog now has regression-tested public navigation and recovery, portable preservation/build checks, an indexed lossless SQLite query model, a read-only engineering-only server, and a GitHub Actions validation workflow. The existing design, 29 equipment categories, 196,306 profile identities, original source data, original master workbook, and spreadsheet outputs are retained.

Work used six batches within the user's limit of ten: preservation baseline; data tooling and storage; public UX; source research and safe serving; integrated verification; GitHub delivery. Parallel agents owned independent files, followed by a separate whole-change reviewer. The user's explicit authorization covered implementation and GitHub changes without another access or design-confirmation round.

Baseline: `d7e4a2c359267bb3b550d8ce8472931e7d38ab30`, the restored original package structure. All 395 historical manifested files matched before implementation. The master workbook missing from the earlier flattened upload is now present and matches its original identity.

## Scope and evidence boundaries

Reviewed and exercised the public engineering HTML/CSS/JS, all category/search payloads, original source tables, source/spreadsheet identities, original master identity, collection generator/verifier, transfer verifier, generated SQLite model, HTTP boundary, and current registered source downloads. Original private finance files were checked for byte preservation, not audited as a financial application. No finance feature, holding, or configuration was changed.

Preservation and structural validation do not independently authenticate all electrical specifications or demonstrate equipment suitability. No original cached formula was recalculated or replaced. Existing withheld values, publication scopes, historical/source qualifications and candidate identities remain applicable.

## Fixed defects and improvements

### Public browser

- Late search results and errors no longer overwrite a newer reset, filter, or category action.
- Failed searches no longer leave stale clickable rows, exports, or pagination controls.
- Bootstrap, collection, search, specification and reference failures have working recovery actions.
- Fractional or invalid page input is clamped to valid integer pages instead of indexing an undefined record.
- A reference search entered during source loading is applied after data arrives.
- Malformed URL escaping cannot abort application initialization.
- Record permalinks reload and navigate within the same category, including when a drawer is already open.
- A cold `#equipmentPanel` skip-link fragment initializes the default catalog correctly.
- Drawers isolate background interaction, preserve focus, and coexist correctly with dialogs and keyboard navigation.
- New filters expose original listing states, review notes and candidate relationships without relabeling them as engineering approval.
- Public wording replaces private-workspace language; responsive controls, labels, focus indicators and a skip link improve navigation.
- Original specification/source inspection, formula display, reference tables, Excel downloads, JSON exports, sorting and pagination remain available.

### Data and maintenance

- Generation no longer runs on import or silently writes released collections and historical reports. Explicit new output paths are required.
- Independent verification uses actual source paths, declared hashes and optional explicit master-workbook verification. Current reports are written separately.
- Two isolated builds produced identical bytes across all 60 outputs. All 59 collection/index/search assets match the released versions.
- The derived SQLite schema retains source sheets, fields, rows, stored cells, original lexical/cached values, cell types, style indices, formula metadata, profiles, source relationships, source scope and projected metrics. Indexed queries and FTS5 support maintenance and engineering consumers.
- Atomic no-clobber publication prevents failed imports from leaving a successful-looking database or overwriting existing evidence.
- The importer rejects missing source headers, contradictory or precision-changing projected metrics, missing source links and inconsistent registry/candidate relationship counts.
- Embedded NUL query text is normalized to whitespace, avoiding an internal FTS syntax failure.
- Transfer verification distinguishes six intentionally maintained historical code files from 389 protected original files. It reports original/current source hashes, rather than changing or silently relaxing the archived manifest. Strict original-snapshot mode remains available and intentionally fails on maintained source changes.

### Public serving and CI

- The HTTP server is fixed to the engineering deployment root, supports read-only asset requests, serves original Excel bytes with the proper content type, and supplies CSP and other browser security headers.
- Tests cover hidden files, directory listing, parent traversal, percent-encoded traversal, escaped symlinks, including a symlinked root index, and unsupported write requests.
- The separate private finance application, source archive and derived SQLite files are outside the public web root.
- CI requires browser tests, verifies source preservation, builds and verifies an isolated collection release, and builds the derived SQLite store. Its GitHub token has read-only contents permission.
- Local setup needs Python and a current browser; the public static site has no npm build or writable database service requirement. A managed HTTPS static host supplies production TLS and traffic handling.

## Verification

Run from the repository root:

```bash
python3 -m unittest discover -s 06_Verification/tests -p 'test_*.py' -v
REQUIRE_BROWSER_TESTS=1 python3 -m unittest discover -s 01_Engineering_Equipment_Database/website/tests -p 'test_*.py' -v
python3 06_Verification/verify_transfer.py --mode inputs --allow-output build --allow-output 01_Engineering_Equipment_Database/website/build
python3 01_Engineering_Equipment_Database/website/tools/verify_collections.py --source-workbook 02_Engineering_Master_Database/Engineering_Master_Database_Audited.xlsx
```

Final local regression results are **65 tests passed, no skips**: 25 transfer tests and 40 website/tool tests comprising 19 real Chromium tests, 14 data-pipeline tests, and 7 real HTTP boundary tests. Browser tests run against the public server's CSP, exercise all 29 categories, and include original controls, sorting/export ordering, failures/races, source inspection, record links, dialogs, keyboard and narrow-screen behavior. External fonts are blocked for deterministic local tests; the site uses its documented fallback. No skipped browser cases count as a pass.

Fresh independent collection verification passes **3,617,576 checks** with zero failures, including 235 original source/spreadsheet hashes and the explicit original master SHA-256. The generated build passes the same verification. All original data, original collections/search indexes, workbooks and archived reports remain unchanged. Current source edits are exactly the declared six maintained files, plus new tools/tests/docs/workflow files.

The fresh metric-validated SQLite import contains:

| Item | Count |
|---|---:|
| Source sheets | 117 |
| Data rows excluding headers | 411,286 |
| Stored cells | 5,885,829 |
| Original formulas | 53,117 |
| Catalog profiles | 196,306 |
| Profile/source relationships | 317,625 |
| Source-bound projected metrics validated | 277,938 |
| Original source files represented | 235 |

Its size is 1,094,918,144 bytes. `PRAGMA integrity_check` returns `ok`; `foreign_key_check` has no failures. A formula cache example retains lexical `7.967433714816837` and formula `C4/SQRT(3)`. Representative manufacturer/category search and profile-detail queries return original states and source rows. The disposable database is ignored from Git and is not served publicly.

A separate reviewer reproduced and raised the inconsistent metric and cold skip-link defects, both fixed with regressions before delivery. The reviewer also identified the embedded-NUL query edge, subsequently fixed. No unresolved Critical/Important code finding was reported. Chromium coverage is not a claim of certification in every browser or device; no public load-test or new Excel-native application validation was performed.

## Research and data expansion

See `docs/research/2026-10-27-equipment-sources.md` for URLs, retrieved hashes, dates, exact comparisons and manufacturer/registry scopes.

All 12 registered current CEC downloads were retrieved. Eleven match the existing file hashes. V2G has a changed export-generation date but its 22 listings and 1,232 native cells match exactly. This does not justify new equipment rows.

Southwire SPEC10012 exposes a structured manufacturer export with 20 native configurations, but identity reconciliation against legacy cables is incomplete. Its HTML labels AC resistance at 75°C while the official CSV labels it at 90°C. Both claims and the unresolved condition are documented; no value or equipment row was silently imported. Other checks confirmed conditional Eaton SCCR notes and current Schneider publication metadata. Jimo was reachable; the user-supplied `gmo.ai` spelling returned HTTP503 and was not asserted to be the same website.

No new manufacturer equipment was demonstrated to be safely distinct and fully qualified in this research pass. Review-only candidate comparisons are retained separately. The existing 76 withheld PV electrical records, 15 configuration-identity review states, unit-review backlog and other source qualifications remain an evidence-driven research queue; arithmetic or nearby model names do not justify replacement specifications.

## Reuse and delivery

Root `README.md` documents public serving, current-input verification, strict historical comparison, repeatable isolated build/verify, SQLite generation and browser QA. `website/docs/data-model.md` documents schema and query interfaces. The environment draft was updated to the restored source paths and new server; the obsolete flattened-layout install workaround was removed. Review/save the draft in environment settings and publish the environment to reuse the prepared machine; draft persistence does not publish a website.

GitHub receives the tested source branch and a pull request. The new code has not been deployed to the older hosted Site, and its hosting ownership/access has not been transferred. Only the engineering `website/dist` directory is appropriate for a future public static deployment; the repository as a whole includes private material and is not a public web root.
