MASTER DATABASE — SEPARATE EXCEL FILES

Open the spreadsheets folder and choose the equipment or reference sheet you need.
The 117 Excel files correspond to all 117 original worksheets, in their original order in Inventory.csv.

DATA PRESERVATION
Original master: Engineering_Master_Database_Audited.xlsx, version 13.
Original SHA-256: dcef1fb4a8b00edbfb5e420dc4e76e6f4a8975cd0599e2f3c7902c4ee44f9f52

The original worksheet XML has been copied byte-for-byte. All original cell contents, cell types, formulas, saved formula results, tables, column widths, row heights, formatting, freeze panes, blank cells and source notes are retained. No equipment rows were added, removed, merged, cleaned, corrected or deduplicated. The original master was not changed.

Only the workbook container, the selected sheet's navigation, and the workbook's sheet-count metadata were regenerated to make smaller individual files.

FORMULA DEPENDENCY
CABLE_NORMALIZATION.xlsx includes its original primary sheet and an unchanged hidden CABLES sheet. Its 53,105 formulas refer to CABLES. Keeping that dependency inside the same workbook preserves those original references without changing formulas or introducing external-file links.
The other 116 Excel files each contain one original sheet.

CHECKS AND INVENTORY
Inventory.csv maps every original worksheet to its Excel file and records its row count, stored-cell count, formula count, dependencies and hashes.
verification/verification_report.json records the comparison of every worksheet and every stored cell against the original v13 master.
verification/native_open_checks.json records native spreadsheet-application opening checks and their stated limitations.
verification/extraction_manifest.json records the original XML-part hashes and output-file hashes.

The 5,885,829 stored cells and 53,117 original formulas are counted once for each primary sheet. The hidden CABLES dependency copy is not counted again in those totals.
Row counts include equipment, registry memberships, reference data and audit records. They are not a count of unique equipment.
The underlying specifications and existing review flags have not been reclassified by this file-splitting task.

PRIVATE DATA WEBSITE
Equipment is organized into 29 equipment-type collections. Manufacturer, registry and historical source records are attached to their equipment record. Existing IDs and source-link identities are retained. Candidate identity and control-configuration relationships remain explicitly qualified.

There is one PV modules list and one inverters list. Similar equipment is kept in the same collection with type filters. Source origin is provenance within each record.

The original 117 data exports and 117 Excel downloads are unchanged. The equipment browsing index and full-source search index are separate for loading performance. Specifications and source values are displayed as stored, with original qualification notes and applicability scopes.

New organization checks: verification/unified_catalog_checks.json
Source mapping details: verification/equipment_unification.json
Interface checks: verification/interface_checks.json
