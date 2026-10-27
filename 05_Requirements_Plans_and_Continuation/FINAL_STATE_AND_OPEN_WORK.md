# Current state and remaining work

## Engineering equipment database

The engineering Site is a completed public, read-only equipment browser at its existing URL. Source version 3 is current. It has 29 functional equipment categories and 196,306 catalogue records/configurations. CEC membership is attached provenance, not a separate catalogue. The original 39,400 PV primary records and 5,603 inverter primary records remain; inverter configuration profiles bring that category to 5,739. All 55,018 registry memberships remain, including monitoring-provider references.

Master version 13 has 117 worksheets and 116 native tables, 5,885,829 stored cells and 53,117 formulas. All 117 original single-sheet outputs are in `01_Engineering_Equipment_Database/website/dist/spreadsheets`. CABLE_NORMALIZATION's original hidden CABLES dependency is intentionally retained inside that one workbook. No value or formula was recalculated for this transfer.

DB13 compared the ten supplied CEC files (nine unique contents) against the existing database. 32,295 unique source memberships already existed, 313 native fields were checked, and 845,792 unique native field-value comparisons found zero differences. The duplicated Grid Support input adds comparisons, not unique equipment. Two swapped PCS source-file mappings were corrected in the audit ledger only. The raw source/primary data did not need additions from these uploads.

Source authentication remains a continuing research task. The retained DB12 audit qualified/corrected 16 publication-scoped PV records and preserved 33 prior claims in history. It leaves 76 electrical records with values withheld and 15 repeated-name configuration claims across five groups unqualified. Zero repeated IDs or identical typed-specification groups in 41 scanned tables is a scoped result, not proof of no semantic duplicate globally. Do not overwrite primary data with a different suffix/revision or a source's conflicting raw claim. BYD390MIK-36 is an explicit example: primary publication 390 W and raw registry 420 W remain separately visible with applicability notes.

The current website exposes original data. It does not prove that a separate engineering calculator consumes 100% of the database. No new engineering calculations or VBA were added. Further equipment expansion and source verification may continue under the same identity, provenance and duplicate rules when requested.

## Financial / MarketMind

The current recovered source is UI v3 plus the portable Node authentication wrapper and the offline v0.4 Python research engine. All 145 recorded requirements are present. Preserve the actual requirement text and statuses; 145 requirements do not mean 145 finished features.

Final plans include:

- A private browser application focused on Indian equities and mutual funds, using a publicly reachable domain and owner authentication.
- Authoritative/licensed NSE, BSE, AMFI, issuer and Groww data feeding a private database and protected API. Sheets is optional for import/reconciliation/export, not a mandatory quote-feed intermediary.
- Daily morning readiness about 09:30-10:00 IST, hourly relevant-market refresh, post-close official ingestion, timestamps, failures and holiday awareness. These are operating requirements, not proof of deployed schedules.
- A 0.033% per calendar-day reference stock goal, after costs and taxes for review/alerts. The earlier 0.021% is superseded. Simple versus compound convention remains unresolved. No profit guarantee or automatic sell.
- Deterministic trend/ATR, quality/valuation/momentum and earnings-event research; point-in-time/corporate-action/benchmark/cost/bias validation; walk-forward testing; then 8-12 real elapsed weeks of paper trading; separately authorised compliant broker execution only later.
- Gemini/Google AI Studio for permitted PDF/structured extraction and independent audit, deterministic Python for maths, ChatGPT for verification/reporting and independent numeric checks. Gemini is not an assumed free entitlement from a ChatGPT/Google login.
- Authorised daily newspaper/Telegram processing, page/source evidence, duplication handling, temporary-copy purge after extraction with a 24-hour upper target and deletion receipts; do not delete original Telegram messages.
- Specialised auditable hosted workers for ingestion, filings/news, extraction, independent review, quant work, QA, alerts and cleanup. No fixed bot count was specified. Chat cannot claim continuous unattended work without actual jobs.

The latest financial handover records 64 passing offline engine tests and ten local Node authentication/JS checks. These are historical evidence; this export does not relabel them fresh live tests. It records a READY Vercel deployment with SSO, but owner browser access still needed independent verification. The bundled Node wrapper was not the Vercel production backend.

Live licensed feeds, hourly hosted price ingestion, Google Sheets OAuth production sync, Gemini reviewer, Telegram collector, verified temporary-PDF cleanup, real after-cost notifications and Groww execution are not connected in the recovered evidence. No verified trading alpha or completed elapsed paper-trading journal is provided. Real trading remains disabled.

Next financial work is the existing P0 sequence: recover owner host access; verify authenticated end-to-end access; reconcile the dated original portfolio; establish canonical database/source timestamps and genuine inputs; verify after-cost calculations; implement and monitor authorised source imports; then proceed through the full unchanged requirement register. Do not fabricate missing transaction history, live quotes, credentials or completion evidence.
