# START HERE — FINAL MARKETMIND OWNER TRANSFER — 25 October 2026

**This is the COMPLETE PRIVATE owner archive. It supersedes previous v0.1–v0.4 individual releases and UI v1/v2 handover ZIPs. Do not combine outdated releases on top of this one.**

## What to do after moving to your new ChatGPT account

1. Upload **this ZIP**, privately, to the new account. Say: "Continue the Indian Market Intelligence MarketMind project from this archive. Extract it, read `prompts/MASTER_PROMPT_FOR_NEXT_ACCOUNT_OR_AI_STUDIO.md`, `requirements/COMPLETE_REQUIREMENTS_USER_MESSAGES.md` and every row in `requirements/COMPLETE_REQUIREMENTS_REGISTER.csv`; audit all files and continue existing website v3, do not restart."
2. The actual latest deployed website source is `website/index.html`, identical to Vercel deployment `dpl_6peWJajnEpf2ktqhKEnTbnjF4fxY` by SHA1. Keep `website/server.mjs`, `website/test_auth.mjs`, `website/package.json` and `website/.env.example` together if using the standalone Node host. Do **not** expose HTML in public static hosting without verified SSO/authentication, because historical real holdings are embedded in the source.
3. Keep the engine folder together for future development: `engine/` contains real algorithms and test fixtures, but **no validated live NSE trading edge**. You do NOT need to run it yourself; the next AI developer can.
4. Use `owner_private/` only in private accounts/storage. Contains original Groww statements plus the fully exported Google Sheets tracker and Google Doc masterplan. No broker access tokens or app login passwords are included.
5. All 145 requirements = O001–O055 + V001–V090 are in `requirements/`. The complete final decisions and gaps are summarised in `01_FINAL_USER_DECISIONS.md` and `02_IMPLEMENTATION_REALITY_CHECK.md`.
6. Use `03_GOOGLE_AI_STUDIO_REVIEW_GUIDE.md` before uploading to Google AI Studio. **Do not casually upload this PRIVATE ZIP to a model or public design service**, because it includes financial holdings and transactions. The separate, optional `MarketMind_AI_Studio_SAFE_CODE_REVIEW_2026-10-25.zip` excludes private files.
7. Credentials, connections, a custom owner login, hosted feeds and notifications require new account/host authorisations. Re-authorise the Google Drive and other plugins in the new ChatGPT account; they do not migrate automatically. Existing ChatGPT automated tasks are account-scoped and should be reviewed before deleting the old account.

## Current website

- Protected owner-controlled Vercel URL: https://indian-market-intelligence-private.vercel.app/
- Latest Vercel project ID: `prj_pTYqqVkee1kC9YeVVUwhOwZ0XZWS`
- Deployment ID: `dpl_6peWJajnEpf2ktqhKEnTbnjF4fxY`; ready / SSO-on at verification; **owner browser login still must be confirmed**.
- Vercel file SHA1 exactly matches `website/index.html`.
- Replit has an unpublished editor project and is NOT the production website.

## Verification

- 64/64 Python engine tests PASS (offline fixture tests).
- Node private wrapper PASS (10 internal checks, 1 Node test file), inline JS syntax verified by the Node test.
- Requirements: 145 unique IDs (O001–O055 and V001–V090).
- Current session Chromium Playwright attempt blocked by administrator at local file URI. Prior v3 release documented its own browser UI test results; do not describe this session as having completed a fresh browser smoke test.
- ZIP CRC and SHA256 content manifest were verified as part of the release. See `verification/`.

**Everything not explicitly verified must remain flagged as INCOMPLETE / NOT CONNECTED.**
