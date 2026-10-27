# Account migration and technical guide

## New-account procedure

Upload the complete ZIP privately and paste the root continuation prompt. Keep a downloaded backup outside ChatGPT. The receiving AI should verify the package, preserve current source, read every requirements row and recover authorised host access before editing production. Files are portable; account ownership and connected-provider authorisations are separate.

## Engineering website

The existing Sites project ID, version, commit and public URL are in PROJECT_SNAPSHOT.json and the retained `.openai/hosting.json`. If the new account is authorised to manage that project, use the Sites existing-project workflow and preserve that ID. Public viewing does not grant editor/owner permissions. Use the hosting service's supported sharing or transfer controls as applicable. Do not claim this ZIP has transferred the old account's hosting ownership or connector sessions.

The engineering website is buildless HTML/CSS/JS. Its deployment root is `website/dist/`; there is no npm install or build step. Runtime dependencies are a current JavaScript browser supporting DecompressionStream and optional Google Fonts, with system fallbacks. All catalogue/source data and Excel files are local static assets. A host must serve JS and XLSX correctly and retain all relative paths. The new AI developer can serve it with a static HTTP server for local QA; the user does not need to run Python personally.

`tools/build_collections.py` builds the catalogue views from the retained raw exports. `tools/verify_collections.py` performs the full source/organisation audit; its original Git working-tree comparison requires a Git checkout and is intentionally preserved unchanged. In a source export without `.git`, use the root portable verifier for file preservation. Do not treat initialising a new Git repository as independent historical proof. The immutable sourceBlobHashes in equipment_unification.json still identify the 235 original data/Excel files.

Raw browser rows store original lexical values, native cell types, style indices, formula text/attributes, cell-presence information and original row coordinates. Do not parse numbers through floating point and overwrite stored source strings. Source and configuration profiles are not an installed-equipment count. Every primary/candidate/history role and original selection gate remains applicable.

The original master workbook is unchanged. All split XLSX outputs and extraction/hash/native-opening evidence are present. The original temporary workbook-splitting authoring scripts are not part of the retained Sites repository; the delivered original outputs and manifests are sufficient to run the current website. A future fresh master-to-browser import must be checked against these native data, formula and dependency preservation rules. Do not claim those temporary scripts were recovered.

Older engineering README wording saying private is historical source text retained byte-for-byte. The current native Site access snapshot is PUBLIC. This export does not alter that UI text or deploy a new version.

## MarketMind

Preserve `03_MarketMind_Financial_Trading/project` as one existing application. Its original README, .env.example, Node server and tests provide the portable Node >=20 wrapper instructions. The Python engine and test fixtures stay together under engine. The financial runtime needs genuine separately configured data/auth/database/job providers for planned integrations. Do not invent a deployed backend from local code.

Keep original Vercel ownership with the appropriate provider login or use its supported transfer/access flow. Reconnect Google Drive, Gmail, Gemini, Telegram and any licensed data/broker service only when needed through secure provider authorisation. No secret values are in this transfer. Review old account ChatGPT schedules before disabling the old account; do not duplicate or assume transfer of the earlier 08:00 IST review task. Backend schedules, API quotas and billing are also provider-specific.

`04_Google_AI_Studio_Review` contains the already prepared limited review bundles. Their contents exclude actual website HTML, owner_private statements and the real portfolio snapshot. They are code-audit inputs, not full runnable websites. Their own documentation defines scope. The full main ZIP is the private owner transfer, not the default external-model upload.

## Evidence precedence and what was not transferred

The latest explicit user correction and PROJECT_SNAPSHOT take precedence for current state; then current project final-decision/reality files and full requirements registers; then older audit history. Preserve historical reports as evidence rather than silently rewriting them. DB13 supersedes DB12's pending-user-CEC-upload text. Financial final decisions retain the unresolved simple/compound convention even though an older architecture note describes a compounded example.

This is not a verbatim export of every ChatGPT message or an automatic memory/connector migration. It preserves the visible engineering requirements, recovered full financial requirements and final plans, latest actual source/data and available audit evidence. Full third-party manufacturer PDFs and paywalled research are not redistributed; source URLs, publication identities, hashes, extracted facts and original audit decisions provide the traceability. Live host secrets, cookies and repository write credentials are excluded. The unavailable earlier Replit source is not represented as recovered; it is not a dependency of the packaged current Vercel UI. Other separate calculator projects are outside this archive.
