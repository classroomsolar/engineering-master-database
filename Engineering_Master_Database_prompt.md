# Engineering_Master_Database_prompt
## Master Engineering Database — the single equipment data source of the website

| Item | Detail |
|---|---|
| Workstream | **Engineering_Master_Database** (shared data service, not a calculator) |
| Status | Existing — continue |
| Website page | `/equipment` (public read-only equipment browser) + data service used by every calculator |
| Master Prompt V5.0 scope | Section 44 (database), Sections 31–33 (sources, overrides, traceability), Section 47 (data contracts) |
| Revision | Final — 14 November 2026 |

## 0. About this file

- This is the **only** project document for this workstream. It replaces every earlier README, prompt, handoff and requirement document; everything still needed from them is written here.
- Governing specification: **Master Prompt V5.0** (Integrated Electrical PV Design Engineering Platform, 9 November 2026). Give the AI both this file and the Master Prompt at the start of every session. If the two ever disagree, the Master Prompt wins.
- This workstream serves **one integrated public website** (Master Prompt Sections 2, 43, 80): every calculator page uses it.
- Reply to the owner in **Hinglish** (simple Hindi–English). Write code, reports and documents in English.
- The owner is an electrical / PV design engineer, not a software developer. The AI does the research, design, coding, testing, debugging and documentation itself (Master Prompt Sections 1–4).

## 1. What this workstream does

One canonical database of approved equipment parameters for the whole website (Section 44): PV modules, inverters, optimizers, microinverters; DC/AC/MV cables and accessories, connectors and terminations; breakers, fuses, disconnects; switchboards and distribution boards; junction, combiner, pull and pole boxes; conduits, raceways, trays and cleats; CTs, PTs/VTs and transformers; reclosers, GOAB switches, switchgear and protective devices; grounding and bonding components; SPDs and surge arresters; meters. Every calculator auto-populates from it; every result stores the database revision used.

**Scope boundary:** only data for in-scope equipment is offered to calculators. Never build, anywhere in this calculator: generator sources or sizing, HV / EHV equipment or studies (above the 35 kV class), substation engineering, field testing / measurement / commissioning, structural / civil / mechanical calculations, and any financial or cost calculation (equipment prices, CAPEX, OPEX, LCOE, tariffs). BESS is deferred (Master Prompt Section 18): do not build it now, but keep data models ready for it. Everything is built on the public website — no spreadsheets, no VBA, no desktop tools.

## 2. Requirements

### 2.1 From Master Prompt V5.0 (Section 44)
- The existing database is the starting canonical source; never create a competing database.
- Keep the original file as the source artifact; build a documented, validated **import pipeline** into structured, versioned datasets; the database is never a calculation engine.
- One source of truth; never hard-code equipment properties or calculated results in calculators.
- Every calculation and saved project stores the database revision and record snapshot.
- Every data change reviewed and versioned; never silently change the basis of saved results.
- Validate schema, duplicates, required fields, units and ranges; never invent missing values; temporary data labelled unverified.
- GitHub versions the source files and reviewed data releases; it is not the runtime database for private projects; a browser cache is never authoritative.
- Each record: canonical ID, manufacturer, model, category, parameters with units, ratings (voltage, current, power, frequency, insulation, short-circuit), dimensions, temperature/environmental limits, standards/certifications, datasheet reference with revision/date, source citation, import version, verification status, applicability and limitations.
- Auto-population: never ask the user to type what a selected record provides; show DATABASE VALUE, USER OVERRIDE and VALUE USED IN CALCULATION with an audit trail.

### 2.2 From the earlier database documents
| # | Requirement | Matches V5.0 |
|---|---|---|
| D01 | Use the master database fully for every calculator | Section 44 |
| D02 | Identify manufacturer first; exact specifications only from official or clearly qualified sources | Sections 30–31 |
| D03 | Never merge records by name alone — compare specifications, revisions, voltages and equipment roles | Section 44 duplicates |
| D04 | Keep withheld or unqualified values flagged when evidence is insufficient (76 withheld electrical records, 15 unqualified configuration claims) | Sections 6, 44 |
| D05 | Use the official CEC equipment lists (active, archived, configurations); CEC membership is provenance inside records, not a separate category | Section 44 |
| D06 | One PV module list and one inverter list | Section 44 |
| D07 | Never alter data when converting; keep original lexical values and cell types; never round-trip numbers through floating point | Section 44 import pipeline |
| D08 | Public, read-only equipment browser with categories, search, manufacturer/type filters, sorting, pagination, record detail, original fields, source links and exports | Section 44, 80 |
| D09 | Responsive layout and keyboard access | Section 73 |

### 2.3 Verification requirements
Schema and unit validation per table; completeness of required fields; range checks; duplicate and near-duplicate detection with identity rules (manufacturer + model + revision + rating variant); provenance per record; import round-trip with zero unexplained differences; licence check before publishing raw manufacturer or research tables.

### 2.4 Connections
| Consumer | Data |
|---|---|
| Production_Calculator, PV_String_MPPT_Calculator | PV modules, inverters, optimizers |
| DC_Cable_Connector, DC_Protection_Combiner, Inverter_LV_AC, MV_Electrical_Design, Cable_Tray, Cable_Thermal, Vault | Cables, conductor properties, ampacity tables, fuses, breakers, disconnects, enclosures, conduits, trays, cleats, terminations |
| Fault_Current_Studio, Transformer_POI, MV_Electrical_Design, LV_Interconnection_Metering | Transformers, switchgear, reclosers, relays, protection curves, CT/PT, NGRs, meters |
| Grounding_Calculator, Lightning_Surge_Protection | Ground electrodes, ground conductors, SPDs, surge arresters |
| Documentation_Schedules_QA | Every record used, with revision |

## 3. Work already done
- Master database **v13**: 117 worksheets, 116 tables, 5,885,829 stored cells, 53,117 formulas, SHA-256 `dcef1fb4a8b00edbfb5e420dc4e76e6f4a8975cd0599e2f3c7902c4ee44f9f52`.
- Public read-only equipment browser (source version 3): 29 equipment categories, 196,306 records/configurations, 39,400 PV primary records, 5,739 inverter records/configurations, 55,018 CEC registry memberships, 117 per-table downloads; 3,617,575 organisation/source checks recorded. Recorded URL: `https://engineering-equipment-master-data.thesocialjay3.chatgpt.site`.
- DB13 compared ten supplied CEC files (nine unique): 845,792 field-value comparisons, zero differences, no missing rows. DB12 qualified/corrected 16 PV records.
- Other copies exist and must be reconciled into v13: a 93-sheet revision used by Cable_Thermal; the older revision inside Fault_Current_Studio (v13 import prepared, not yet published); Production's 26,000-record PV catalogue and CEC inverter library; the earlier tray, grounding and vault equipment lists.

## 4. Functions still to be added
- [ ] Table schemas for every table a calculator uses (types, units, ranges, required fields, identity rules).
- [ ] Import pipeline: source file → validated, versioned datasets with a revision ID.
- [ ] Data service for calculators: lookup by stable ID, filtered selection lists, auto-population, override audit trail, revision returned with every value.
- [ ] Data-quality reports: duplicates, missing fields, unit errors, out-of-range values, withheld values.
- [ ] Equipment browser served from the website domain.

## 5. Earlier work still to be completed
- [ ] **First:** the repository is public and contains a separate private personal project (`03_MarketMind_Financial_Trading/`, `04_Google_AI_Studio_Review/`) with personal holdings files. Move it out to a private repository (Sections 6, 60, 81); treat the git history as exposed. Do not open or quote those files.
- [ ] Reconcile every other copy listed in Section 3 into v13 record by record; import missing records only with source evidence; keep conflicts visible.
- [ ] Production's 26,000 PV records: map IDs, carry provenance flags (24,705 blank source fields, 69 invalid STC rows, 39 power-product anomalies), resolve from manufacturer datasheets where obtainable.
- [ ] Publish v13 to Fault_Current_Studio only after the owner approves the release.

## 6. Checks and audits still to be done
- [ ] Checksum, sheet, row and formula counts of v13 verified.
- [ ] Schema, unit, range and duplicate audit per table; provenance audit.
- [ ] Import round-trip audit (zero unexplained differences).
- [ ] Licence/publication audit of manufacturer and research tables.
- [ ] Security audit: no private data in the repository or the public browser.

## 7. Process to follow to finish everything

This is the Master Prompt V5.0 development process applied to this calculator. Follow it for every task.

### 7.1 Rules that never change (Master Prompt Sections 5, 6, 27, 34)
- Never invent a standard, clause, formula, coefficient, equipment rating, curve, clearing time, test result or repository state. Missing critical input → **INPUT REQUIRED**; never a guessed value.
- Every numerical result comes from a deterministic, tested calculation engine — never from AI text.
- Every result shows a status: PASS, FAIL, REVIEW REQUIRED, INPUT REQUIRED, NOT APPLICABLE, NOT VERIFIED, NOT SUPPORTED or STALE. Never PASS when inputs, sources, methods or validation are missing. Every warning says what is wrong, why it matters, which input to check and how to fix it.
- Never claim "complete", "100 %", "certified" or "compliant" without the evidence of Section 8 of this file.
- Preserve working calculations and verified results; change a validated method only with a documented reason and tests (Sections 52, 58).
- No paid service, subscription or usage-based dependency without the owner's approval (Section 84). No credentials, secrets or private data in code or Git (Sections 6, 60, 82).

### 7.2 Execution cycle for every task (Master Prompt Section 7)
**A Inspect** existing code, data, tests and behaviour → **B Research** primary standards, editions, manufacturer documents, papers and benchmark tools → **C Design** inputs, outputs, units, equations, sequence, error states, tests → **D Implement** the deterministic engine first, then UI, diagrams, data and integration, in small reversible changes → **E Test** (unit, golden, independent, boundary, invalid input, regression, UI, export, security, end-to-end) → **F Audit and fix** (separate engineering and software reviews; repeat until no critical/high defect) → **G Improve** (low-risk improvements; scope expansion only with approval) → **H Report** (files changed, tests run, results, limitations, next step). Do not stop after a plan, a draft or a good-looking screen.

### 7.3 Phases (Master Prompt Section 62)
| Phase | Work | Done when |
|---|---|---|
| 0 Inventory | Verify v13; inventory every table; reconciliation map of all copies; privacy move | Phase 0 report approved |
| 1 Pipeline | Schemas and import pipeline with revision IDs | Round-trip test passes |
| 2–3 Verification | Quality, provenance and duplicate audits | No unexplained differences |
| 4–6 Service and integration | Data service, auto-population, override audit trail; every calculator reads from it | All calculators use the service |
| 7 Release | Reviewed data release, changelog, tag | Owner approves the release |

### 7.4 Engineering rules for every engine (Master Prompt Sections 28–33, 46–48)
- Before coding: master specification (purpose, inputs with units and sources, outputs, standard and edition, equations, assumptions, valid range, warnings, test cases) and data-dictionary entries with stable names (no "Value1", "Factor2").
- Engine: defined inputs/outputs/units, equations with variable definitions, source references (standard, edition, clause/table/equation), assumptions, valid range, input validation, numerical precision/convergence, version ID; identical results for identical inputs; handles zero/negative/huge/tiny/missing values; never shows a failed calculation as a normal result; separate from the UI.
- Units: one central unit service; SI internally; feet/inches and metric display; never mix units silently; full precision internally, round only for display.
- Assumptions classified CONFIRMED / DEFAULT / ENGINEERING ASSUMPTION / NEEDS USER CONFIRMATION / REFERENCE-DERIVED. Show DATABASE VALUE, USER OVERRIDE and VALUE USED IN CALCULATION for every overridable value, with an audit trail.
- Equipment data only from the Master Engineering Database (Section 44), auto-populated from the selected record, with the database revision stored with every result.
- Traceability chain for every important result: user input → database value → intermediate values → correction factors → equation/method → final result, with the limit used, status, warnings, sources and engine version.
- Results passed to other calculators go through typed, versioned contracts; changed upstream inputs mark downstream results **STALE** (Sections 47–50). Never propagate a result whose study case, topology, voltage level or assumptions do not match.

### 7.5 Testing rules (Master Prompt Sections 66–71)
- Golden tests with source of expected values; independent hand calculations or separate scripts (never only against code that shares the implementation); tolerances justified, never chosen to make a test pass.
- Boundary, invalid-input, unit-conversion, unsupported-case and regression tests; end-to-end tests for every applicable project type P1–P5.
- Challenge campaign toward **200 meaningful cases** designed to make the calculator fail; report the real number completed.
- Every reported defect: reproduce → trace UI → validation → lookup → calculation → result → saved state → fix the root cause → add a regression test → rerun all golden tests.

### 7.6 Working method
- GitHub is the home of the code (Section 60): tag the known-good state before work, feature branch, small commits, pull request for engineering/data/security changes, tests run before merge, tagged releases with rollback points.
- Work in controlled batches (Section 61); after each batch give the delivery report of Section 87 (requested, done, requirement IDs, preserved, files changed, sources, tests run with results, remaining gaps, next step).
- Keep these records up to date in the repository (Section 85): REQUIREMENTS.md (traceability for every ID in Section 2), MASTER_SPECIFICATION.md, DATA_DICTIONARY.md, DECISIONS.md, SOURCE_REGISTER.md, TEST_MATRIX.md, ISSUES.md, PROGRESS.md, CHANGELOG.md.
- Ask the owner only when a decision changes safety, correctness, scope, cost, privacy or is irreversible (Section 5). The only open items the Master Prompt leaves to the owner are: jurisdiction and code editions to target first, hosting provider and budget, which calculator becomes the first fully verified reference module, whether 35 kV stays the MV limit (Appendix F) — plus approval of production releases and paid services.

## 8. Final result — what "finished" looks like
- One canonical, versioned equipment database used by every calculator on the website; no parallel copies.
- Every record traceable to its source with revision; unresolved records flagged, never invented.
- Public equipment browser on the website domain; no private data anywhere in the repository.

## 9. Plugins and tools

| Capability (Master Prompt Section 8) | Use it for | Example plugin / tool |
|---|---|---|
| Git repository connector | Branches, commits, pull requests, issues, diffs | GitHub connector |
| Coding agent + execution environment | Write code, run builds and tests, debug | Coding agent with terminal (e.g. Claude Code / similar), Node.js, Python |
| Web research and browser | Official standards information, manufacturer datasheets, benchmark tool documentation | Web search, web fetch, browser |
| PDF / OCR document reader | Read code books, datasheets, manuals, papers page by page | PDF reader with OCR |
| Owner's document storage | The owner's books and reference PDFs (for example the NEC books kept in Dropbox) | Google Drive / Dropbox connector |
| Academic research search | Peer-reviewed papers and DOIs | Semantic Scholar / Google Scholar / IEEE Xplore search |
| Independent maths check | Hand-check equations and reference values | Python (NumPy, SciPy, SymPy), Wolfram |
| Browser / UI automation | End-to-end tests on desktop and mobile, downloads, console errors | Playwright (Chromium, Firefox, WebKit) |
| Accessibility check | WCAG 2.2 AA audit | axe-core / Lighthouse |
| UI / diagram design | Wireframes, screen flows, engineering diagrams | Figma or similar design tool |
| Database connector | Schemas, migrations, records, permissions | Connector for the chosen database |
| Hosting / deployment connector | Deployments, logs, domains, rollback | Connector for the chosen host (Wix connector only for the existing live sites) |
| Security analysis | Dependency, secret and code scanning | Dependabot / npm audit / pip-audit, CodeQL, secret scanning |

Use a tool only when it has a real role, check access/permissions/quota/cost first, never claim a tool ran when it did not (Sections 8–9). Do not use Formula Genius or Coursera. When delegation is available, split work into specialist reviews — standards, independent calculation, equipment data, code/architecture, UX, security, testing — and have an independent checker that never sees the builder's code (Section 9).

**Specific:** Python pandas / openpyxl for import and comparison; official CEC equipment list downloads; manufacturer datasheet websites.

## 10. First task and first reply
1. Reply in Hinglish; confirm Master Prompt V5.0 governs; say what you can access.
2. Report the privacy item of Section 5 first.
3. Phase 0 (read-only): verify v13, inventory tables, reconciliation map, pipeline design, single best next task.
