# Existing project references and portability boundaries

- Original Google masterplan (live owner file): https://docs.google.com/document/d/1ZXs0YL5FYa0QOXY7FrEGyLJuuciCK59Q2TZvDQ65vuo/edit
- Google investment tracker (live owner file): https://docs.google.com/spreadsheets/d/1EPUc7rcXpIItu5Nl_w0bRi3FswnEb0tT-uPCT0JOxOo/edit
- Replit app/editor identifier: `dd5313d2-19c9-4684-8506-86f85936841d` — https://replit.com/@classroomsolar/DeepGiftedFormat
- Replit **publish status at handover: not published** (`found:false` from connected service). Live frontend source remains inaccessible via connector; no deployment URL has been validated. Existing Replit owner account and source should be exported manually in Replit if it contains code newer than the local HTML.
- Portable Google masterplan export: `owner_private/Original_Masterplan_2026-10-22.docx`.
- Portable Google Sheets tracker export: `owner_private/Portfolio_Tracker_2026-10-24.xlsx`.
- Original Groww stock statement: `owner_private/Stocks_Holdings_Statement_5439142630_2026-10-21.xlsx`.
- Original Groww mutual-fund statement: `owner_private/Holdings_Statement_2026-10-22.xlsx`.
- Private broker statement-derived snapshot used in source engine: `engine/data/portfolio_statement_snapshot.json`.

A Google Drive connector installed in the old ChatGPT account does not transfer to a new ChatGPT account or Gemini session. Explicitly reauthorise only the minimum needed app scopes.

**Hosting**: The transfer ZIP does not contain the Replit hosted source bundle because current Replit tools cannot fetch its file tree. Do not claim it does. The separately tested local HTML is authoritative *only for that HTML version*, not all later agent edits. No hosted production deployment is included.

## Latest verified v3 website hosting (25 Oct 2026)
- Vercel project: `indian-market-intelligence-private` (ID `prj_pTYqqVkee1kC9YeVVUwhOwZ0XZWS`)
- URL: https://indian-market-intelligence-private.vercel.app/
- Deployment ID: `dpl_6peWJajnEpf2ktqhKEnTbnjF4fxY` (READY at check)
- SSO enabled for **all** deployments; owner login experience not independently confirmed.
- Vercel deployment source contains `src/index.html` with SHA1 `2b3e02656fcff5c9b445d50c5fd69a55d36a9cbe`, exactly matching `website/index.html` in this archive.
- Replit editor project is NOT the live production website. No Replit hosted code is asserted to be in this ZIP.
