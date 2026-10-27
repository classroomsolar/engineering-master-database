# Source data and derived query model

The released master workbook, `dist/data/`, `dist/spreadsheets/`, and archived
`dist/verification/` reports remain the source evidence. The Python tools create
new outputs; they never migrate, correct, or replace these original files.
The browser continues to use the released JavaScript collections offline.
SQLite is an optional local read model, not an additional authoritative database.

## Rebuild and verify

Run these commands from `01_Engineering_Equipment_Database/website`:

```sh
mkdir -p build
python tools/build_collections.py --source-dist dist --output-dir build/rebuilt
python tools/verify_collections.py --source-dist dist \
  --collections-dist build/rebuilt \
  --source-workbook ../../02_Engineering_Master_Database/Engineering_Master_Database_Audited.xlsx \
  --report build/rebuilt-checks.json
python tools/catalog_store.py build --source-dist dist \
  --collections-dist build/rebuilt --output build/catalog.sqlite
python tools/catalog_store.py search --database build/catalog.sqlite \
  --query SunPower --category pv-modules --limit 10
python tools/catalog_store.py profile --database build/catalog.sqlite PV_MODULES:PVM-000001
python -m unittest discover -s tests -v
```

Every output must be new, with an existing parent directory. Use a different
output name for another run. `--output-dir` is required for collection builds.
The isolated result contains `collections/` and
`verification/equipment_unification.json`; its paths remain suitable for the
released browser. Outputs inside the source tree or its ancestors are rejected.
A build is prepared in a sibling temporary directory and published after source
and coverage validation. SQLite is built in a sibling temporary file and
published with an atomic, exclusive link after database integrity validation.
Failed builds remove their temporary files. Existing files are never overwritten.
Input metadata paths cannot escape their input root, including through symlinks.

Verification prints a summary and returns nonzero on failure. It writes no file
unless `--report` names a new path outside both input trees. Without
`--collections-dist`, verification and SQLite import use the collections in
`--source-dist`. `--source-workbook` checks the original master workbook against
the catalog SHA-256; omit it only when that workbook is unavailable. If a Git
checkout exists, verification also compares the actual repository-relative
`data/` and `spreadsheets/` paths against `HEAD`, including staged changes.
The scripts can be imported without executing a build or writing a report.

## SQLite schema

`catalog_store.py` uses Python's standard library and SQLite. It checks source
blob and workbook SHA-256/size, wrappers, sheet identity, column counts, duplicate
row numbers, stored-cell indices, formula locations, headers, and per-sheet and
aggregate counts. Headerless reference sheets retain every row. Foreign keys
reject references to missing source rows. Collection and search payload hashes,
counts, primary source availability, profile shapes, and IDs are checked before
publication. Each metric with a source header must name a header on its primary
source sheet and match that source cell exactly, including lexical precision.
Registry and candidate counts must equal their distinct source-row relationships. Original collection listing-link identities are independently
checked by `verify_collections.py`.

| Table or view | Meaning |
| --- | --- |
| `metadata` | Schema version, source workbook identity, verified import counts. |
| `source_files` | SHA-256, byte length and role for the 235 original catalog/raw/XLSX files. |
| `source_sheets` | Stable sheet ID/name and original catalog metadata, including dependency declarations. |
| `source_fields` | Zero-based column index and exact original header; duplicate header labels remain distinct. |
| `source_rows` | Original Excel row number and header flag, keyed by sheet and row. |
| `source_cells` | Every stored cell, including blank/style-only cells, keyed by sheet/row/column. |
| `categories` | Collection IDs and complete collection metadata. |
| `profiles` | Stable released profile ID, display fields, review status, primary source and complete packed profile. |
| `profile_sources` | Separate source-row relationships, states, listing-link row, scope, and identity basis. |
| `profile_metrics` | Displayed rating/voltage, exact source lexical, declared display unit, source header. |
| `profile_search` | Original deferred full-specification search text for each profile. |
| `profiles_fts` | FTS5 token index, when supported by the local SQLite build. |
| `field_claims` | View joining profile relationships to original field headers, values, formula caches and source coordinates. |

`source_cells.lexical_value` stores the original numeric/text cache as text;
`value_json` also preserves JSON null, empty string and value type distinctly.
`cell_type`, `style_id` and `formula_json` preserve the original raw cell type,
style reference, and formula text/attributes. Formula caches are imported exactly
as recorded. They are never recalculated. The full sheet metadata retains the
catalog's styles/source information through `source_sheets.metadata_json` and
the immutable original catalog; style format definitions remain in that catalog.
All original unit, quality, source, eligibility, scope, and limitation fields
remain source claims. Header labels containing units are preserved verbatim;
no numeric normalization or unit conversion is performed. `profile_metrics`
retains the released display units but does not assert those units describe
other claims or configurations.

The primary provenance indexes are `(sheet_id,row_number,column_index)` on
cells and `(sheet_id,row_number,profile_id)` on relationships. Profile indexes
support category/manufacturer/model browsing and literal manufacturer/model
lookup. No new name matching or merging occurs during import. Distinct profile
IDs stay distinct even when their names are identical. Existing released
candidate links and review flags stay explicit. The original collection builder
still applies its documented existing exact-specification alias and approval
configuration grouping rules; those are not an independent validation of
product identity or project eligibility.

## Read APIs and claim queries

`connect_readonly(path)` returns a SQLite connection opened with `mode=ro` and
`query_only=ON`. Close it after use. `search_profiles(connection, query='',
category=None, limit=50, offset=0)` returns display records ordered by category,
manufacturer, model and ID. Queries are parameterized and converted to literal
FTS tokens; embedded NUL characters become whitespace. User text is not SQL
or FTS syntax. Limits are clamped to 1–500. If
FTS5 is unavailable, search uses literal substring terms over the preserved
search text. Token and substring searches can return different results.
`profile_detail(connection, profile_id)` returns a profile, its metrics and all
source relationships, or `None` if the ID is unknown. The CLI emits JSON for
build summaries, search results, and details. Raw field claims can be queried
without loading unrelated profiles:

```sql
SELECT sheet_name, row_number, header, lexical_value,
       relationship, relationship_state, formula_json
FROM field_claims
WHERE profile_id = 'PV_MODULES:PVM-000001'
ORDER BY sheet_id, row_number, column_index;
```

This separates simultaneous or conflicting source claims instead of picking a
preferred electrical value. Source row positions remain Excel row numbers;
column indices are zero-based. Archived statuses, placeholders, engineering
templates, and unresolved claims retain their original meaning and limits.

## Audit evidence from the complete released data

A complete import produced 117 sheets, 411,286 nonheader data rows, 5,885,829
stored cells, 53,117 formulas, 196,306 profiles and 317,625 profile-source
relationships. The database occupied 1,094,918,144 bytes with FTS5 enabled;
`PRAGMA integrity_check` returned `ok` and `PRAGMA foreign_key_check` returned
no rows. Both the released collections and an isolated rebuild passed 3,617,576
independent verification checks when the master workbook was supplied.
Two isolated builds produced identical bytes for all 60 output files; all 59
collection files also matched the released collection files byte for byte.
These are recorded run results, not fixed assertions that block future releases.

Focused tests cover lexical precision/formulas/styles, distinct same-name IDs,
source corruption, rehashed metric/header inconsistencies and incorrect listing
counts, broken relationships, duplicate source rows, headerless
references, path traversal, read-only/query behavior, output preservation,
failed-build cleanup, required output paths, and import side effects. The
original evidence files remain unchanged. Derived SQLite and rebuild outputs
belong in ignored `build/` directories and can be deleted and rebuilt.
