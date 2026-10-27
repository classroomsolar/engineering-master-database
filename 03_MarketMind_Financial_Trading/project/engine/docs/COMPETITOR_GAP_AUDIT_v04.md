# Indian Market Intelligence v0.4 — Verified Competitor and Feature Gap Audit

**Audit date:** 23 October 2026. **Assessment:** v0.3 was not the best or most complete calculator, standalone application, or spreadsheet. v0.4 adds discrete capabilities but remains a **research-only local prototype**. This audit benchmarks identifiable functionality; it is **not** a measured accuracy or investment-profitability ranking. It does not imply rights to copy proprietary scoring algorithms, reports, subscription feeds, or UI.

## Real-world comparators

| Tool | What is publicly documented | Feature we should adopt independently | Data/subscription caveat |
|---|---|---|---|
| [Screener.in](https://www.screener.in/features/) | 10–15-year financial statements, consolidated/standalone, custom ratios, Excel exports and screen alerts | Long financial timelines; bank and non-bank peer-relative screens; watchlist event triggers | Export subject to the site's access and use terms; no blanket scraping licence |
| [Trendlyne](https://trendlyne.com/features/matrix/) | DVM style scores, portfolio analysis, screening, analyst forecasts, reports, corporate action calendar | *Original* transparent quality/valuation/momentum score, analyst dispersion and portfolio event monitor | Proprietary DVM formula/report content cannot simply be copied; paid tiers vary |
| [TradingView](https://in.tradingview.com/features/) | Pine Script, multi-indicator scanner, charts, strategy tester, trade CSV report | Custom signals, indicator visualizations, strategy equity/order diagnostics | Deep Backtesting, bar magnifier and other functions are paid-tier features |
| [StockEdge](https://web.stockedge.com/plans) | Combination scans, sector rotation, sector analytics, momentum/fundamental scoring | Sector-relative ranks, liquidity/market breadth monitors | Publicly advertised paid plans; no unlimited export assumption |
| [PrimeInvestor](https://primeinvestor.in/reports/whats-changing-at-primeinvestor-faq/) | MF/stock review, MF overlap, rolling returns, screeners and calculators | Dated MF look-through and rolling-return distributions | Availability/review cadence and member features must be verified individually |
| [Portfolio Performance](https://www.portfolio-performance.info/en/) | Desktop offline transaction history, taxes/fees, IRR, true time-weighted returns, rebalancing | Full event-ledger accounting, XIRR/TWR, income attribution, privacy-first storage | Not an India-exchange-specific guaranteed data feed |
| [Zerodha Console](https://zerodha.com/products/console) | Trade/tax P&L, corporate actions, trade/fee breakdown, performance tracking | Groww statement import plus transaction-lot reconciliation and tax reports | Zerodha's dashboard does not give access to user's Groww account |
| [Ghostfolio](https://github.com/ghostfolio/ghostfolio) | Open-source multi-account transaction imports, asset allocations, charts, privacy options | Portable multi-account transaction schema and snapshot export | Stock/fund coverage depends on external data sources |
| [Portfolio Visualizer](https://legacy.portfoliovisualizer.com/) | Factor models, Monte Carlo, asset correlation, optimized portfolios | Correlations, factor controls, regime scenario and parameter sensitivity | Assets/datasets are not necessarily suitable for Indian securities |
| [Portfolio Charts](https://portfoliocharts.com/charts/) | Rolling returns, start-date sensitivity, drawdowns, retirement withdrawal rates | Multiple-start-date stress and downside-percentile summaries | Its bundled global assets are not a direct substitute for NSE shares |
| [Backtrader](https://www.backtrader.com/docu/slippage/slippage/) | Flexible orders, commissions, slippage and analyzers | More accurate next-open fills, stop gaps, broker cost models | Data licensing and Indian execution realism remain our responsibility |
| [QuantConnect LEAN](https://www.quantconnect.com/docs/v2/lean-engine/getting-started) | Open-source event-driven backtesting engine with modular data/fee models | Point-in-time event simulation, unit-tested order fills and walk-forward research | Do not assume India data/brokers are available without licensed integration |
| [VectorBT](https://vectorbt.dev/) | Vectorized parameter sweeps, multi-strategy simulations and interactive analytics | Multi-parameter robustness tests and broad strategy comparisons | Some advanced features are paid PRO |
| [AMFI](https://www.amfiindia.com/net-asset-value/nav-download) | Official mutual-fund NAVs and historical NAV downloads | Scheme-code/ISIN validation and dated NAV snapshots | Old NAV download format discontinued; history often fetched in bounded periods |
| [NSE](https://www.nseindia.com/all-reports) | Official CM-UDiFF Bhavcopy, delivery positions, volatility, announcements | Exchange identity and provenance, delivery-data filters, company events | Raw UDiFF prices not automatically corporate-action adjusted |
| [Groww API](https://groww.in/trade-api) | Broker portfolio/quote/history and order APIs | Optional *read-only* account synchronization | Paid; no broker order API to be connected in research phase |

## Missing capabilities and implementation order

### P0 — Data integrity and investor accounting (must-have before real recommendations)
1. Import *dated Groww trade book*, contract notes, dividends, MF SIP/redemption and cash flows. Distinguish cost-basis from actual execution settlement and realized gains.
2. Daily point-in-time market source with timestamps, provenance, adjustments, actual end-of-day price and exception reports. Official share ISIN identity for additions/delistings.
3. Build back-adjusted total return series after proper shares, bonuses, dividends, demergers, merger and rights treatment. Benchmark against corresponding NSE TRI.
4. Fund scheme ISIN/AMFI code, dated NAV, TER, direct/regular classification, scheme factsheet and monthly holdings. Aggregate *the same scheme across multiple folios* but preserve lot identity.
5. XIRR and TWR from dated ledger/valuation intervals; quarterly/yearly snapshots must not be silently substituted.
6. India charges & tax engine: brokerage, exchange fees, STT, stamp, GST, DP, exit load, lock-ins, holding periods and prevailing tax year. Amounts/rules timestamped and validated by original authority; never hardcode unverified future rules.
7. Enforce 'WAIT' whenever input quality, investable capital, near-term cash reserves, market liquidity or authority is not verified.

### P1 — Core research & portfolio decision intelligence
8. Equity & bank-specific fundamental scorecards with explicit ratios, sector peer comparisons and filing-linked facts.
9. Reproducible valuation: DCF/multi-stage reverse DCF/EV multiples for nonbanks; P/B/ROA/ROE/earnings normalisation for banks; base/bear/bull stress.
10. Ownership/concentration by underlying security, AMC and sector, not merely fund category. Require dated MF holdings and comparable identifiers.
11. Stock/fund overlap, top issuer concentration, HHI, correlation, beta, expected shortfall, shock scenarios and downside allocation budgets.
12. Transparent, *internally defined* multi-factor screen; missing data => no score, not median guesses. Outlier winsorisation and sector ranking tracked.
13. Dated analyst views, target revisions, source documents, horizon normalization and confidence/dispersion.
14. Quality news research, peer/sector market context, original filing check and contradiction log; rights-approved extraction only.
15. Entry/exit quantity/INR, liquidity-adjusted participation, order price bands, stop gaps, multiple horizon cases, human-only final order approval.

### P2 — Advanced backtesting, intelligence and user experience
16. Event-driven backtests with next-open fills, taxes/charges, slippage, market impact, delisting/survivorship, no look-ahead and PIT earnings timestamps.
17. Statistical robustness: rolling out-of-sample tests, different economic regimes, nested parameter search, bootstrap uncertainty and multiple-hypothesis controls.
18. India benchmark comparison: Nifty 50 / Nifty 500 / sector TRI and cash, on identical observation dates with source IDs.
19. 8–12+ week paper-trade journal with fill assumptions, partial fills, operational failure alerts and opportunity costs.
20. Dashboards: current-value timestamp, portfolio return waterfall, drawdowns, sector heatmap, change logs, holdings/watchlist research.
21. Authorized publisher/PDF/news extraction, page completeness and rights controls, verified local/cloud cleanup and auditable failure receipts.
22. Portable CSV/Excel exports and automatic integrity tests; no hard-coded external subscription or vendor scoring dependency.

## v0.4 changes made now
- `portfolio_analytics_v04.py`: standard-library XIRR with dated cash flows, chain-linked TWR for end-period external flows, concentration HHI (folio-line and scheme-consolidated), illustrative scenario shocks and official-holdings-gated MF underlying overlap.
- `tests/test_portfolio_analytics_v04.py`: 14 new checks; **64/64 offline tests** passing.
- `cli.py portfolio-risk-v04`: reads the preserved Groww broker statement snapshot and outputs a research-only risk report.
- All lack-of-evidence conditions report **NOT CALCULABLE**, not synthetic profits or target prices. Funds with repeated scheme names are not discarded as fake duplicates.

## Specific risk findings from the 21/22 October 2026 Groww snapshots
- Combined statement-level value ₹2,349,296.92. Sum of the visible individual position values ₹2,349,296.90, owing to a ₹0.02 MF statement rounding difference. Both dates differ and are not a live valuation.
- Gold funds about 33.38% and silver funds about 12.73% of the position-value total; direct equities about 15.47%. Underlying exposures may overlap; the listed weights are category-level, not security look-through.
- **20** distinct vehicles after consolidating six stocks plus fourteen distinct fund scheme names, but the effective scheme/vehicle position count (HHI) is not a measure of genuine company-level diversification.
- One fully hypothetical simultaneous shock (direct equity −18%, equity MFs −22%, gold −10%, silver −25%) produces approximately −₹417,167 (−17.76%) against the dated row-value base. The shocks are **illustrations, not predictions**, and ignore fees, taxes, intra-fund overlap and change in valuations.

## Acceptance boundary
Do not call this product best-in-class, production ready, or profitable until: licensed real market data are ingested; the accounting engine reconciles all lots and distributions; genuine source-verified historical strategies pass after-cost walk-forward tests; paper trading has happened; and the daily automation is deployed, monitored and independently audited.
