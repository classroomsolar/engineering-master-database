# Equipment source research — 2026-10-27

## Result and scope

All **12 official CEC downloads in the existing `CEC_IMPORT_INDEX`** were requested successfully on 2026-10-27 between 13:08 and 13:10 IST (07:38–07:40 UTC). Eleven have the **same SHA-256** as the existing 2026-10-24 snapshots. The generated V2G workbook has a different file hash, but **all 22 existing listing rows and all 1,232 native listing cells match exactly**. Its title now says “List generated October 27 2026.” No new CEC equipment was demonstrated, and no CEC import is proposed.

Read the original 117-table catalog and decoded original JavaScript callbacks (gzip/base64 when applicable), including `SOURCE_REGISTER` (2,313 entries), `CEC_IMPORT_INDEX`, `CEC_SOURCE_NOTES`, and `CEC_FILE_RECONCILIATION`. This is a scoped source freshness and candidate-source investigation; it does not independently certify every existing equipment field, every manufacturer publication, or every source-to-profile relationship.

No original data blob, workbook, equipment collection, master workbook, or source ledger was changed by this research. Downloads, detailed comparisons, and candidate proposals are staged outside the repository at `/workspace/scratch/source-research/`. HTTPS requests used inherited proxy settings and normal certificate verification. Macro-enabled workbook contents were inspected as archive/XML data; no workbook macro was executed.

## Current official CEC downloads

The source URL for every row is the existing `CEC_IMPORT_INDEX.Download URL`, retained in the original catalog. The table below records the **current retrieved file**, rather than a guessed publication date.

| Dataset | Existing list state | HTTP | Comparison to registered snapshot | Current SHA-256 |
| --- | --- | --- | --- | --- |
| PVModuleList | ACTIVE | 200 | Exact SHA-256 match | `5701df9b8f9c56bfcdd3fb3fd7cb21a2bfa79a265be1c17dc7a5f2f781987b30` |
| InvertersList | ACTIVE | 200 | Exact SHA-256 match | `0292b8a044f9d7545bae762e75aad06928ede2d898d24ee88a26929b924b319d` |
| BatteryList | ACTIVE | 200 | Exact SHA-256 match | `66077b6c5be5e68cfb87c7db42a54c16af3616abc80a22114dcad6a51a21f3ea` |
| EnergyStorage | ACTIVE | 200 | Exact SHA-256 match | `bebd991435b184d16b09886c89c4971bf27521c72ec3b7354719a2a8a2230e0d` |
| MeterList | ACTIVE | 200 | Exact SHA-256 match | `3d8d151ec644bdf8b406dc20eca5b526f31cae5495d55fdd87cc41b85f5f77dc` |
| PowerControlSystem | LEGACY | 200 | Exact SHA-256 match | `f3bc4326dc6162a29a6ac1cc334fc67ba6198631745833f4a5d519711c6fd9d8` |
| V2G | ACTIVE | 200 | 22 native listing rows unchanged; generated date differs | `60ae5e86225d6c95914c8192bc7d2fcfb8a692b988f3548cb8c2e5bb41c67da3` |
| ArchivedBattery | ARCHIVED | 200 | Exact SHA-256 match | `34f8254a86cb97179104c23c1bd8c02738aab445758460f8ccdaaca423340dc6` |
| ArchivedInverterFull | ARCHIVED | 200 | Exact SHA-256 match | `4e7ab915ec371a6e37627e65945a454071277ddc25473076e4fa532de99d0df3` |
| ArchivedPV | ARCHIVED | 200 | Exact SHA-256 match | `ff2079a2eb3b982ee17c7fd3a7a73f615cd541d15a977ca440d3c9387c6e4da5` |
| CurrentPCS | ACTIVE | 200 | Exact SHA-256 match | `d9aa79471c311d89ffb04377e8a1ee50b3a2c8d2b7c6f3ce4005b6dcd3720de4` |
| PMRS | ACTIVE | 200 | Exact SHA-256 match | `e2862f0281b8882d69ec345941ba6f027a73718a19cdc0cac99f32e10f125735` |

Official index: https://www.energy.ca.gov/programs-and-topics/programs/solar-equipment-lists (HTTP 200, current retrieved SHA-256 `29c4282668db0879ef03abdc7854e0675aed827e9c12bfd6f45096df0659074b`). Active application: https://solarequipment.energy.ca.gov/ (HTTP 200).

The program page explicitly says the lists are generally updated on the 1st, 11th, and 21st, or the next business day. The already registered October 21 updates are therefore consistent with the current download evidence. Existing data update notes differ by dataset and must remain separate from retrieval dates: BatteryList and CurrentPCS say October 21, 2026; MeterList says September 1, 2026; archived and PMRS publications have their own historical dates.

### Native-cell comparison boundary

In addition to the file hashes, four current official worksheets were compared to the corresponding decoded native master tables, by `Source Worksheet`, `Source Excel Row`, and native field position after the five registry metadata columns:

| Master table | Existing listings checked | Native cells checked | Exact lexical differences | Substantive changes |
| --- | ---: | ---: | ---: | ---: |
| CEC_BATTERIES | 999 | 15,984 | 300 numeric serializations | 0 |
| CEC_METERS | 802 | 8,020 | 0 | 0 |
| CEC_POWER_CONTROL | 103 | 2,060 | 53 numeric serializations | 0 |
| CEC_V2G | 22 | 1,232 | 0 | 0 |

Battery and PCS lexical differences are source XML floating-point strings versus the existing rendered numeric strings, for example `8.1999999999999993` versus `8.2`. Both parse to the same binary floating-point value; the official files are also byte-identical to the registered originals. These are **not newly changed manufacturer specifications**. Preserve raw source lexical values in provenance if a future importer needs exact XML reproduction; preserve source types and dates as well. Do not apply numeric normalization to model identifiers.

The V2G worksheet's native data range is rows 6–27. No subsequent nonempty A/B manufacturer/model rows were found. Every one of its 56 native fields per listing matched, including firmware, required devices, power-control modes, communication protocols, connectors, and certification-related claims. A hash change alone would have created a false equipment update.

### Source claims and usage conditions

The program page says CEC staff review submitted information, but “manufacturers’ self-reported information is not confirmed” and CEC “makes no claim or warranty on the equipment and its safety, performance, or durability.” A registry listing is therefore an attributed source claim with a date and configuration scope. It should not become a blanket engineering verification badge or an assertion of CEC endorsement.

Current terms: https://www.energy.ca.gov/conditions-of-use (HTTP 200; SHA-256 `d058eb42add4e66ca395e351b22e3620be15892a72368f2960cb5c1bbed6590c`). The page says most materials generated, compiled, or assembled at public expense are free for public use **provided the Energy Commission is credited**. It also identifies restrictions for third-party material, selected copyrighted content, and commercial/profit-making use of such restricted materials; logos and seals require permission. This is source-specific usage evidence, not an assertion that every linked manufacturer document has an open redistribution license. Preserve attribution and external source links. The initially guessed `/conditions-use` URL returned 404; the corrected URL came from the official page footer.

Configuration details particularly worth retaining:

- PCS notes say text in curly brackets distinguishes configurations and is not part of the manufacturer's model number. Keep the literal listed model and a separately derived base model, without discarding the bracketed distinction.
- Two existing Anker A17E1 PCS rows have different required meters and response/steady-state times (0.5/0.8 seconds versus 2/2.2 seconds). Manufacturer/model equality alone cannot merge these operational configurations.
- Battery capacity is nameplate **kWh**, continuous discharge is **kW**, and JA12 declarations identify applicable code cycles. Keep these measures and applicability fields separate.
- V2G maximum discharge **kW**, nominal **VAC**, tested firmware, required gateway/device, and listed operating mode are distinct claims. A communications flag or a listed certification field is not an unrestricted application approval.

## Manufacturer source refresh and candidate additions

### 1. Southwire SPEC 10012 — authenticated structured source, reconciliation needed

Official page: https://cabletechsupport.southwire.com/en/tile/30/spec/10012/?country=US (HTTP 200; SHA-256 `bd8f196a399c89da0b539f801e4f7c552f55def9511000ca3582319d0e2a7ae9`). Already registered as `CT-SRC-0035`, so this is a source refresh rather than discovery of a previously unknown authority.

The page's “Excel” download link https://cabletechsupport.southwire.com/cablespec/download_excel/10012 redirects to https://cabletechsupport.southwire.com/en/cablespec/download_excel/10012/ and actually returns **text/csv**, 23,455 bytes, SHA-256 `14559987853b9a22434305e139d50385ea88fa084ca2e69fad784eba02026606`. Importers must inspect content and retain the actual MIME type instead of assuming the route name describes an XLSX file.

The current CSV contains two native tables: weights/measurements and electrical/engineering data, each with **179 six-digit stock bases**, covering **18 conductor sizes** and **20 distinct native construction/electrical configurations**. The matching native HTML also identifies stock colors separately. An exact six-digit/optional eight-digit-suffix token comparison across `CABLES`, `CABLE_TYPES`, `PARTS_CATALOG`, `CABLE_NORMALIZATION`, and `SOURCE_REGISTER` found one stock base already referenced and 178 without such a literal token. **This is not evidence for 178 missing physical cables:** color, packaging, order suffixes, and generic existing family records need reconciliation.

Existing master cable records already include `CAB-010609` / exact part `56186702` for 250 kcmil, and `CAB-010610` / family identifier `SPEC10012-AL-2/0`. They establish existing family coverage and must not be duplicated merely because current six-digit stock labels differ. Other legacy generic cable identities were not fully reconciled against the 20 native configurations in this research.

A review-only source diff is staged at `/workspace/scratch/source-research/southwire-proposed-import-diff.json`. It contains all 20 native construction/electrical configurations and their associated stock bases, and explicitly proposes **zero direct equipment additions** pending full identity reconciliation. It does not fabricate an eight-digit ordering suffix, a missing publication date, a color, or installation-specific ampacity.

Proposed field mapping after reconciliation:

| Native source field | Proposed equipment/source field | Scope to retain |
| --- | --- | --- |
| Stock Number | manufacturer stock base / source alias | Six-digit base; retain ordered suffix separately only when published |
| Cond. Size; Cond. Strands; Cond. Number | size; strand count; conductor count | Preserve AWG versus kcmil designation, rather than a unitless sortable number |
| Approx. OD | cable OD | Inches; approximate source value |
| Insulation Thickness; Jacket Thickness | layer thickness | Mils; do not store as inches without explicit conversion metadata |
| Approx. Weight; Aluminum Weight | total and conductor weight | lb/MFT; different measures |
| Min Bending Radius | minimum bend radius | Source inches; cable construction applies |
| Max Pull Tension | maximum pulling tension | Source lb; retain pulling method limits if separately supplied |
| DC Resistance @ 25C | Rdc | Source Ω/1000 ft and 25°C |
| AC Resistance @ 90C (CSV); AC Resistance @ 75°C (HTML) | separate attributed Rac source claims | Ω/1000 ft; **temperature basis conflicts between official source representations and remains unresolved** |
| Inductive Reactance @ 60Hz | reactance | Non-ferrous conduit, one diameter center-to-center spacing, 60 Hz |
| Allowable Ampacity At 75C / At 90C | separate source ampacity claims | 2023 NEC Table 310.16 basis; adjustment, terminal limits, and installation checks remain necessary |

**Observed source conflict:** the current official HTML Table 2 labels “AC Resistance @ 75°C,” while the official CSV labels “AC Resistance @ 90C.” Both artifacts are retained. Do not silently choose a temperature, transform resistance, or mark the Rac temperature verified. Keep the literal field labels and flag the condition for manufacturer clarification before engineering use.

The source page specifies 600 V application, THHN/T90 dry 90°C, THWN-2 wet/dry 90°C, oil-exposed THWN-2 75°C, and TWN75 wet 75°C. Do not collapse these conditions to a universal 90°C cable rating. The page footnote explicitly references NEC 310.15, 110.14(C), and 240.4(D). Source publication/revision date was not identified in the retrieved page/CSV; retrieval is not a substitute. No explicit bulk redistribution license was established from these retrieved materials.

### 2. Eaton shunt-trip safety switches — existing source and conditional ratings confirmed

Official document: https://www.eaton.com/content/dam/eaton/products/low-voltage-power-distribution-controls-systems/swiching-devices/resources/shunttripsafetyswitch-technicaldata-td008003en.pdf (HTTP 200; 693,739 bytes; SHA-256 `6086a53aef7b393510d456792335bfe901f14e2e6bdac85124263d1a53cb575f`). Document title/date: TD008003EN, **effective April 2026**. HTTP Last-Modified: April 27, 2026. Already represented by `C19-EQ-EATON-TD008003EN-202604` and subsequent exact SKU audits.

PDF text inspection confirms Table 5's 200 kA at 480/600 Vac for the 100 A fusible entry, with a footnote restricting the fusible SCCRs to Class R, J/L, or T fusing. Standard Class H clips on 30–600 A devices do not establish those conditional SCCRs. Larger device rows differ between 480 and 600 Vac. Existing `DISCONNECTS` notes already retain this distinction. Preserve it; no new switch model was established by this scoped refresh. The document bears ©2026 Eaton; no open bulk redistribution license was established.

### 3. Schneider Electric Digest — verified current publication metadata

Official landing page: https://www.se.com/us/en/download/document/0100CT2401/ (HTTP 200; SHA-256 `3f8b2b6ada64e0a852f970496e973acfeb6d600a186697df85e0c817b1b4abce`). It identifies **Digest 179 Complete Catalog**, based on the June 2024 printed catalog, release date **April 30, 2026**, version **1.6**. Embedded DigitalDocument metadata reports dateModified **September 25, 2026**. These are separate publication events, not contradictory dates.

The linked full PDF is reported as **55.8 MB** and was not downloaded for this bounded investigation. The source ledger already contains Schneider section-specific Digest references. Landing-page metadata does not establish a missing product or justify refreshing every Schneider equipment specification. Prefer relevant section PDFs and exact SKU sources for future additions. No redistribution license was established from the retrieved landing page.

### 4. ABB library and CPSC — discovery and status sources

https://library.abb.com/ returned HTTP 200 (344,157 bytes; SHA-256 `ce9441985b6408737cce01c8831dc5ae25b0aa1df8d2c7e45363e9a22ba74662`). The original ledger already has many exact ABB documents. The library is useful for authoritative source discovery; its landing page alone provides no equipment specification and no missing-equipment count.

The official public CPSC endpoint https://www.saferproducts.gov/RestWebServices/Recall?format=json&RecallTitle=electrical returned HTTP 200 and **78 recall records**, JSON, 212,790 bytes, SHA-256 `0e522aa1acb63cb79c34c4eae5f54e2120373d14c06596991a53033a953dab07`. Native fields include RecallID, RecallNumber, RecallDate, LastPublishDate, Products, Manufacturers, Hazards, Remedies, and official recall URLs. Sample record 10727 / 26426 concerns Manik and Apex ATX computer power supplies (April 16, 2026), with a blank `Products.Model` field. This query is broad and does not cover every electrical recall. No records were imported or matched to existing equipment. It is a potential future **source-specific recall relationship**, with exact model/date/serial-range review, rather than a source of engineering ratings or automatic equipment rejection. API licensing/redistribution terms were not separately established.

## Current design inspiration evidence

https://jimo.ai/product/ai returned HTTP 200 (779,341 bytes; SHA-256 `62f2b528f8c86abc3969dc7685720c477b12867ae964f7f8b159cac29dde3206`). The retrieved page title is “AI Agent for User Onboarding in SaaS | Jimo.” Visible content includes restrained top-level product/use-case navigation, “Agentic guides,” “Interface knowledge,” and product-led explanation of an agent seeing the user's interface. This confirms a live Jimo source at the URL already documented in the site's `DESIGN.md`.

https://gmo.ai/ returned **HTTP 503**. There is no evidence from this response that it is the same service as Jimo or a corrected spelling. Keep the existing documented Jimo reference as a reference, and retain the user-supplied spelling as unresolved instead of silently asserting equivalence.

This pass inspected downloaded HTML and visible text. It did **not** run a new visual browser comparison or reproduce the prior measured typography from `DESIGN.md`. Existing orbital/black-canvas design observations in that file come from the earlier live-browser inspection; they should not be presented as new current measurements. Adapt general interaction ideas with original content and assets; no Jimo branding, proprietary fonts, or copied product imagery was added.

## Recommended next decisions

1. Retain the original CEC data. Record the current freshness evidence and the generation-only V2G hash change without inflating equipment counts.
2. Resolve the Southwire HTML/CSV AC resistance temperature conflict, and reconcile the 20 staged native configurations against legacy generic cable family identities before proposing actual additions. A source alias can enrich an existing record without producing another electrical equipment profile.
3. Attach field-level condition/unit/provenance to future manufacturer imports. Treat model aliases, configuration claims, manufacturer specifications, and registry statuses as separate source relationships.
4. Keep source usage/attribution evidence near each source. Public download access alone does not prove a redistribution license, and registry participation alone does not prove engineering suitability.

Detailed retrieval log: `/workspace/scratch/source-research/retrievals.json`. Native comparisons: `official-comparison.json`; reproduction scripts: `fetch_sources.py`, `fetch_remaining.py`, `compare_official.py`, `check_southwire.py`. Staging paths are evidence artifacts outside this repository, not production dependencies. Download content hashes above allow subsequent reproduction without treating these temporary paths as durable source URLs.
