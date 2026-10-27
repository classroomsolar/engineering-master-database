# CURRENT PORTABLE v0.4 RESEARCH ENGINE — SOURCE ONLY

See [v0.4 notes](docs/RELEASE_NOTES_v04.md) and [exchange inputs](docs/EXCHANGE_DATA_INPUTS.md). The old generated reports, screenshots, prior release ZIPs and obsolete version notes were intentionally excluded. Recreate output reports if needed; do not treat missing demonstration report JSON as a missing engine dependency.

- Primary historical store: `data/nse_raw_unadjusted/nse_eod_immutable.sqlite3` (only created on actual local import/audit).
- Auditable store CLI: `python cli.py market-store-audit`.
- Genuine-source benchmark helper: `python cli.py nifty-tri-compare --tri-csv ... --manifest ... --strategy-report ... --output ...`.
- Backtest CLI now requires `--history-review` for non-synthetic studies; synthetic fixtures still require `--synthetic-test`.
- Suite count: **50/50 offline synthetic tests**; no real market performance demonstrated.

---

# Indian Market Intelligence — Existing Project Add-on (2026-10-22)

**This extends the existing Google Sheet:** [Indian Investment Review — Portfolio Tracker](https://docs.google.com/spreadsheets/d/1EPUc7rcXpIItu5Nl_w0bRi3FswnEb0tT-uPCT0JOxOo/edit). Do **not** recreate that spreadsheet. Existing 08:00 IST ChatGPT review automation remains active and should not be duplicated.

## What works NOW

- Exact six **stocks** and 18 **mutual-fund folio positions** from the user-supplied Groww 21 and 22 October 2026 statements, respectively. Numbers reconciled to statement summary with transparent **₹4.35 stock invested** and **₹0.02 fund valuation** residuals (broker summaries supersede rounded line items). Individual fund folio numbers have deliberately been removed: internal `MF-01` etc. are pseudonyms, not actual folio numbers.
- Complete offline portfolio audit and concentration by security, category and AMC.
- Standalone HTML dashboard (`dashboard.html`), with explicit historical dates and manual conditional share sizing; opens in your browser without any installation.
- Importer for **already verified, adjusted** OHLCV CSV; validates provenance, OHLC consistency, corporate-action flag, duplicate dates, synthetic vs real.
- Deterministic SMA50/SMA200, RSI14, MACD, ATR14, 20-session support/resistance extrema, volume baseline; no invented historical dataset.
- Cash-only position-size calculator that respects free cash after near-term reserves, risk budget, trade cap and optional portfolio concentration cap; outputs stress-case gap losses, never orders.
- Research input gate for bank-specific financials versus non-bank fundamentals, timestamped quotes, primary evidence and analyst/news checks. **Missing fields => WAIT, not BUY.**
- Offline *prototype* backtest models for (A) quality/valuation/momentum with point-in-time input, (B) earnings-event reaction using availability dates, and (C) 200-day trend with ATR risk exit. Uses close-to-next-open orders, explicit scenario commission/slippage, and conservative stop-gap handling. Includes equity curve, CAGR, drawdowns, zero-risk-free Sharpe/Sortino, volatility and completed-trade metrics. Also supports expanding training / forward date partitions.
- Strictly opt-in local permitted PDF intake: `pypdf` signature/page count + SHA-256/duplicate check + evidence-page coverage validator + facts persisted and read back + local delete receipt. **No Telegram connection, Gemini upload, Drive PDF upload, or simulated remote deletion claims**. Failures retain files and log state.
- A Windows PowerShell launcher for refreshing the LOCAL historical-snapshot output. **It has NOT been scheduled or installed on your computer.**
- `../requirements/COMPLETE_REQUIREMENTS_REGISTER.csv` is the current, user-sourced 145-item definitive requirements tracker; the old 55-row assistant-generated status file is obsolete.
- Automated unit tests (see below) and clearly marked **synthetic** fixtures. **Synthetic percentages must NEVER be cited as NSE backtest performance**.

## Local installation (Windows 10/11 with Python 3.11+)

1. Extract this ZIP to a private, access-controlled local directory. Do not publish `data/portfolio_statement_snapshot.json`, which contains your financial holdings.
2. Run `py -3 -m pip install pypdf` (needed only for PDF workflows). All market and financial arithmetic uses the Python standard library.
3. From the extracted folder run `py -3 cli.py portfolio-audit`; open `reports/portfolio_audit.json`.
4. Open `dashboard.html` in Edge or Chrome. The 21/22 October broker statement prices are **not current market quotes**.
5. Run `py -3 -m unittest discover -s tests -v` and confirm all tests pass. No network or broker accounts are needed.
6. To test indicator and backtesting plumbing **using synthetic data only**, run:

```powershell
py -3 cli.py indicators --csv samples/SYNTHETIC_ONLY_TESTONLY_adjusted.csv --output reports/SYNTHETIC_ONLY_indicators.json --synthetic-test
py -3 cli.py backtest --csv samples/SYNTHETIC_ONLY_TESTONLY_adjusted.csv --strategy trend_200d_atr --output reports/SYNTHETIC_ONLY_trend_200d_atr.json --synthetic-test
py -3 cli.py walk-forward --csv samples/SYNTHETIC_ONLY_TESTONLY_adjusted.csv --strategy trend_200d_atr --output reports/SYNTHETIC_ONLY_walkforward.json --synthetic-test
```

For model A or B use `--strategy quality_valuation_momentum` or `--strategy earnings_event` and pass `--fundamentals ...` or `--events ...`. These bundled files are test fixtures with `example.invalid` URLs — **not** legitimate filing evidence.

## Market-data interface (not connected to NSE/Groww yet)

CSV input, one symbol per file, required fields:

`date,symbol,open,high,low,close,volume,adjusted,corporate_actions_checked,source_url,synthetic`

- `date` YYYY-MM-DD; OHLC positive and internally consistent; `volume` non-negative integer.
- `adjusted=true` and `corporate_actions_checked=true` may be set ONLY after independently reconciling splits, bonuses, dividends as applicable and volume adjustments. **Changing flags without adjusting values corrupts the backtest**.
- `source_url` must resolve to the original permitted data source; synthetic data must set `synthetic=true` and cannot be accepted without the special test switch.
- Use time-stamped, matched NSE/ISIN references for actual stocks. Always retain raw/adjusted histories separately so reconciliation can be repeated.
- No bulk exchange scraping, paywall bypass or Groww token embedded in this package. No automatic download has been claimed.

**Official NSE MCP (information-only):** <https://www.nseindia.com/nse-mcp> supports `https://mcp.nseindia.in/bhavcopy/cm/mcp` for last-five-year daily market data and `https://mcp.nseindia.in/cmmkt/mcp` for delayed near-live market data. Add those directly as permitted ChatGPT custom MCP connectors if supported by your account; *they are not yet connected to this local program*. Raw bhavcopy is **not a certified corporate-action-adjusted historical series**. The NSE explicitly excludes using the MCP as an executable trading feed.

**Groww API (optional, paid):** <https://groww.in/trade-api> currently advertises ₹499 + taxes per month. The historic REST endpoint shown in <https://groww.in/trade-api/docs/curl/historical-data> is deprecated; do not build an adapter against it. Broker token must stay in Windows OS environment/secret store, **never** in ChatGPT, this ZIP, or a shared sheet. Order endpoints are intentionally not implemented.

**AMFI:** <https://www.amfiindia.com/net-asset-value/nav-download> has a new NAV download flow. Folio holdings and scheme category ≠ underlying constituent-level overlap, expense, current tax eligibility or lock-in maturity. Real fund rebalancing requires latest SID/factsheets and dated transaction lots.

## Authorized PDF pipeline: local-only and destructive on success

**Caution:** `pdf-validate-and-purge` actually deletes the exact local file on full validated completion. Use a scratch copy until you understand it. It will not delete if any page is missing, a claim is not verified, a source is unlicensed, or remote-upload ID is recorded.

```powershell
py -3 cli.py pdf-register --file C:\Temp\licensed-paper.pdf --publisher "Licensed Publisher" --source "Approved issue dated YYYY-MM-DD" --rights-approved
```

This returns a SHA-256. Independently generate authorized, compact JSON with exactly one `page_index` 1..N per PDF page, `status` of `EXTRACTED` or `NO_RELEVANT_ARTICLES`, and for material facts `claim`, `source_page`, `source_url`, `verified_status:"VERIFIED"`. This schema is deliberately strict and does NOT mean the program independently verified the claim. This requires actual human and source verification.

```powershell
py -3 cli.py pdf-validate-and-purge --hash <validated-SHA256> --extraction C:\Temp\checked_facts.json --output reports\issue_facts_<date>.json
py -3 cli.py pdf-overdue
```

**Remote cloud deletion is not implemented**: no files are sent to Gemini or Google Drive, so local receipts explicitly state remote deletion **not applicable**. Gemini raw-PDF review, Telegram channel intake, full-page completeness extraction and secure remote lifecycle cannot be claimed to be working. Telegram and publisher permission must be checked before implementing any automated collection.

## Local schedule (NOT installed)

`run_daily.ps1` regenerates local audit/WAIT-recommendations/HTML and checks PDF overdue state without contacting a stock market, uploading anything, or trading. Windows Task Scheduler can invoke `powershell.exe -NoProfile -File "C:\private_path\run_daily.ps1"` at a time of your choice **after you put the project onto your PC**. Do not schedule raw newspaper ingestion until the rights and deletion workflow pass production QA. The existing ChatGPT 8 AM IST automation is separate; this PowerShell script has no link to that task.

## Real-data gates still blocking a production investment engine

1. Appropriate verified source and corporate-action-adjusted **OHLCV** for NSE cash equity plus Nifty benchmark, with exchange ticker/ISIN matching, date/timestamps, and legal reuse.
2. Point-in-time official financial statements, bank ratios, accessible original research, and publication timestamps; historic security universe/delistings for survivorship checks.
3. Current cash and one-month liquid reserve; any proposed trade must still receive the user's separate final approval.
4. Fund SID/TER/exit load/lock-in and underlying constituent overlap; individual tax-lot histories and XIRR for true assessment.
5. Rights-approved newspaper channels, access to the local Windows collector, permitted Gemini API subscription/limits and secure local secret management, verified cloud deletion if uploading is ever enabled.
6. No elapsed 8–12-week real paper-trading period exists. Local strategy results supplied here are **synthetic plumbing tests only, not alpha evidence**.

## Reproducibility/security notes

- Do not transmit local portfolio JSON to public Gemini free-tier APIs or public GitHub. Keep `/data` private.
- No password, phone, PAN, Groww client ID, actual MF folio ID, API token or Telegram credentials are in this deliverable.
- `reports/SYNTHETIC_ONLY_*.json` are demonstration QA artifacts and must not be used to choose actual stocks.
- No guarantees of positive returns, precise sell fills, broker compliance or uninterrupted scheduled execution.

## v0.2 — Official NSE EOD UDiFF integration (22 Oct 2026)

A new guarded NSE market pipeline is included: `nse_pipeline.py` and `nse_daily.py` read NSE's modern CM UDiFF ZIP, validate OHLCV + exact exchange ISIN/series/trade date, calculate a SHA-256 receipt, append immutable raw price history, and log missing/unavailable market days. `corporate_actions.py` back-adjusts SPLIT/BONUS history **only after** an explicit verified-source human review spanning the entire input range. See `docs/NSE_PIPELINE_GUIDE.md` for exact commands and conservative caveats.

- Public NSE ZIP download is **best-effort only**; it could not be exercised against the real NSE website from this tool environment. Offline sample test fixtures verified the converter and filters; no real prices were fetched.
- **Default** local runner remains offline. `run_daily.ps1 -FetchNSE` explicitly opts into attempted official NSE downloads; it preserves failures and never swaps broker snapshots for unverified quotes.
- NSE raw Bhavcopy is not dividend-adjusted, corporate-action-adjusted, guaranteed complete, real-time, or an execution feed. It cannot feed authentic backtest claims without further validation.
- Total automated suite: **30 tests** (20 existing + 10 for UDiFF importing, immutable history and corporate actions). No real historical performance is asserted.

## v0.4 — competitor benchmarking, XIRR/TWR and portfolio stress (23 Oct 2026)

`python cli.py portfolio-risk-v04 --output reports/portfolio_risk_v04.json`

Adds 14 offline tests and first reusable implementations of transaction-based XIRR, period cashflow TWR, consolidated-scheme concentration HHI, illustrative multi-asset shocks and completeness-gated underlying MF overlap. **No actual XIRR/TWR or MF overlap is invented from the holdings snapshot.** This module does NOT fetch live exchange prices, imply actual fund constituent overlap, or send orders. Details and official source references: `docs/COMPETITOR_GAP_AUDIT_v04.md`.
