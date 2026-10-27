# TECHNICAL DECISIONS AND AUDIT GATES — 24 OCT 2026

## Data flow, chosen for technical rather than convenience reasons
```
NSE / BSE / issuer filings / AMFI / approved Groww exports / authorised journalism
      ↓ independent workers, rights/rate-limit checks
HTTPS collector → raw immutable object/source ledger → validated private SQL DB
      ↓                            ↓                     ↓
corporate-action / timestamp QA    Google Sheets export    news/research queue
      ↓                            (optional only)         ↓
verified API for owner-authenticated website ← deterministic valuations / audited AI facts
      ↓
portfolio and fund analytics / signals / alerts / audit logs
```
**Decision:** direct secure server ingestion -> DB -> website. Do NOT route hourly quotes through `GOOGLEFINANCE` in Sheets; Sheets is useful for review, manual inputs, snapshots, exports and backup, not for timestamped scalable access. If the user only has a sheet export today, ingest that as a dated snapshot, NOT as a live market feed. Use Postgres managed database for hosted system, SQLite offline/testing, object storage with short TTL for PDFs. Users own the repo/database/hosting and can export without ChatGPT.

## Security boundary
A publicly routable URL is compatible with an owner-only app. Public login page is fine, but protect ALL HTML/API private routes server-side; never store private holdings in frontend bundles, public repos, or Replit anonymous app previews. Use managed OAuth/password authentication plus MFA, secure httpOnly sessions, encryption in transit, secret manager, least-privilege Google Sheets scope and backup/recovery. Do not create a single shared password in chat.

## Proposed IST time plan — not currently running
08:00 pre-market research (existing ChatGPT automation only; no duplicate); 09:30 first market snapshot; 10:30 / 11:30 / 12:30 / 13:30 / 14:30 / 15:30 hourly refresh if provider permits. 16:15+ official cash archive ingest after actual official release (not guaranteed exact time). Daily 18:00 portfolio valuation reconciliation; 06:00 next morning news rights-cleared ingestion (only if infrastructure configured). PDFs purge as soon as data validated, with 24-hour enforcement and explicit Gemini API deletion. Exchange regular trading session begins at 09:15 IST and ends 15:30 IST. (NSE official market-timings link in DOCUMENTATION_RESEARCH.md.)

## 0.033 percent daily target mathematics
Daily fraction `d=0.00033`, i.e. 0.033%, selected by user, NOT a minimum guaranteed return. For `n` CALENDAR days, cumulative benchmark compounded: `(1+d)**n-1` (30 days ≈ 0.99475%). Simple alternative `n*d` (30 days 0.99%). For each tax lot / position, compare cost basis + cumulative verified broker and statutory costs against current marked exit proceeds; only eligible recent quotes can trigger sell-review. Quantify gap/liquidity risk. A small position/trade may not recover fees at a 0.033% movement. In-app notification feasible on schedule; email/phone push require app permission, scheduler, and a mail/push provider.

## Research decisions and safety tests
- Date each exchange quote and note whether last-close/delayed/actual execution.
- Source price stale or official adjusted historical series absent → NO EXECUTABLE BUY / NO VERIFIED BACKTEST.
- Brokerage recommendations aren't deterministic evidence; verify report published date, horizon and actual issuer filing.
- News impact: record material facts and independent challenges; present actionable summary, not raw paper republication.
- Banks: NIM/ROA/GNPA/NNPA/CET1; nonbanks: ROIC/FCF/ROCE. Never compare bank debt/EBITDA as manufacturing.
- Benchmark Nifty TRI on exactly matching dates; test no-lookahead, dividends, SEBI rules, Indian friction.
- All trading real orders require explicit user confirmation, separate from AI model recommendations.

## Honest current state (24 October 2026)
- Offline Python v0.4 ZIP exists, 44 files; its 64 `unittest` tests have been run and passed locally today. All are SOFTWARE tests; no licensed real-market backtest validity.
- Offline HTML website exists and embeds a dated portfolio snapshot; not safe to publish that file unmodified.
- Replit project `DeepGiftedFormat` was found in accessible user's account. Replit tool `get_publish_status`: `found=false` at this audit. Not verified live; no public domain was returned.
- Connected Google Sheets tracker and Drive masterplan exist. No proof of website OAuth sync, Gemini API, Telegram API, authentic latest market feed, verified audit bot orchestration, background cron or live notifications.
- User has 6 NSE equity holdings, 18 mutual fund folio lines (14 distinct funds); 21/22 Oct statements. Portfolio summary mixes two dates.
- Existing daily ChatGPT 08:00 IST automation was previously verified; confirm that it remains enabled, don't create a duplicate.

## User authorisation dependencies (ask only when executing each gate)
1. Owner account for deployment with verified login and optional MFA (user sets password directly with provider).
2. Authorised read-only access to Google Sheets / Drive and, if wanted, Gmail newsletters. A Gmail login does NOT grant Gemini API access.
3. Developer Gemini AI Studio project eligibility/billing/quota and API secret stored in host secret manager; never paste into chat.
4. Licensed NSE/BSE quote/historical source agreement or permitted NSE archive import; paid subscription only on explicit approval.
5. Authorized Telegram channel list and rights-cleared PDFs; separate Telegram API/session locally or secure bot permission.
6. Groww dated transaction history (safely redacted) for true XIRR/fees/tax lots, current deployable cash and near-term reserve.
7. Owner-controlled private Git repository/backup destination, independent of ChatGPT login.

## Task priorities prior to 27 Oct
P0: verified login/hosting, portable repo + migration handover, SQL schema, safe authenticated upload of currently held statements, site calculations and source gates; independent tests and live reachability test.
P1: scheduled exchange import with genuine source, quote timestamps/corporate actions, AMFI MF NAVs, portfolio daily readout and after-cost target alert; structured source logging.
P2: licensed news+Gemini ingestion and deletion receipts, fundamental and broker research, non-synthetic backtests, comparison charts and extended fund overlap.
P3: 8–12 real weeks of paper trade validation before ANY question of real order integration. This necessarily cannot be completed by 27 Oct.
