# Transfer acceptance and QA evidence — 24 October 2026

## Executed checks

- v0.4 Python engine: `python -m unittest discover -s tests -v` from the engine directory => **64 tests, ALL PASSED**. These cover software/fixture quality gates, not live exchange market results.
- Website private HTTP server: owner credentials required at startup; anonymous root and `/index.html` HTTP 401; public `/health` HTTP 200 (no portfolio data); invalid credentials 401; valid owner credentials establish session and show dashboard; source files return 404; tampered cookies return 401; log out revokes current cookie. Node test suite => **10 checks passed**.
- JavaScript syntax: `node:vm` compiled the inline dashboard JavaScript without syntax errors.
- 145 requirement IDs verified contiguous O001–O055 and V001–V090, with unique IDs.
- SHA-256 manifest generated for each included deliverable file except the manifest and validation metadata themselves; ZIP entries checked via CRC.
- Original XLSX and DOCX files are valid Office ZIP containers, and copies preserve original SHA-256 hashes.

## Tests NOT passed or NOT executed

- Browser UI automation was attempted with Playwright + Chromium but both localhost and local-file navigation were blocked with `net::ERR_BLOCKED_BY_ADMINISTRATOR`. This is an execution-environment restriction, not proof of website correctness. Interactive page/visual functionality must be smoke-tested by the next hosting/AI Studio agent.
- No actual **Replit source export** was retrievable through the available connector. The Replit app was unpublished (`get_publish_status` returned `found:false`). No working public URL is claimed.
- Auth has only local HTTP smoke tests, not a penetration test or external HTTPS security audit. Owner private hosting must use HTTPS, managed secrets, backups and ideally MFA before exposure.
- Google Sheets OAuth, actual Groww API sync, real-time NSE/BSE/AMFI feeds, hourly cron, Gemini PDF/Telegram, email/push alerts, broker orders and actual paper-trading returns have not been shown to function here.
- The 0.033% profit goal has been correctly documented in the revised master prompt; the included offline HTML predates that user clarification and DOES NOT yet provide a fully integrated live after-cost 0.033% alert. Do not imply the UI does.

## Operational requirement

The user does not run Python. The v0.4 Python files are provided for developers/new AI Studio/ChatGPT agents to deploy as needed. The website HTML runs in the browser; the optional Node server is for private hosting and includes no third-party runtime dependencies. All market data shown in this version are the 21/22 October Groww historical statements, not current values.
