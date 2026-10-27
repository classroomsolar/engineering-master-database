# Version 0.4: Best-of-market audit and portfolio math — 23 October 2026

**Not a best-in-class claim. Not execution-ready.** The v0.3 predecessor passed 50 synthetic/offline software tests but lacked reliable market integrations and transaction-based returns. This incremental v0.4 extends the **existing** research project, retaining all prior code and historical broker inputs.

## New working software

- `portfolio_analytics_v04.py` implements XIRR using dated signed flows (365-day convention), linked subperiod TWR with dated portfolio values and end-of-period flows, fund-vehicle HHI including scheme consolidation, hypothetical asset-class stress tests, and MF underlying-stock overlap using full, dated constituent ISIN weights.
- `python cli.py portfolio-risk-v04 --output reports/portfolio_risk_v04.json`: reproducible audit of the statement holdings and a hypothetical shock. The sample stress test is NOT a prediction, investment recommendation, Value-at-Risk measure or real trade result.
- Four new Google Sheets tabs in the existing connected portfolio tracker: Competitor Benchmark, Upgrade Roadmap, Risk Lab v2, Cashflow XIRR. The source-owned broker snapshots have not been overwritten.
- 14 new unit tests; 64/64 offline tests passed. None are validated production-market returns.

## Limits that cannot be bypassed by adding formulas

- **XIRR needs dated cash flows**: original purchases/SIPs, withdrawals, realized sales, distributions/fees and final value date. A single holdings export contains only current holdings and cost/valuation, not sufficient transaction timing. The tool correctly returns `NOT CALCULABLE` until valid inputs arrive.
- **TWR needs portfolio valuations on cash-flow boundaries**, not one reported P&L snapshot.
- **MF overlap needs verified complete, dated underlying holdings**, not just fund names. Existing multiple folios of the same underlying scheme are preserved but aggregated for scheme-level concentration; FoF holdings need cascading look-through.
- **No real NSE/backtest alpha:** v0.4 retains v0.3 transactional raw store, TRI parser, and strict history audit gates; no actual verified date-adjusted NSE bars have been loaded.
- **Current working profile**: research-only, no Groww order integration, no live data subscription, no automated Telegram/Gemini ingestion or remote deletion, 8AM IST existing daily task untouched.

## Independent competitor audit and feature priorities

See `docs/COMPETITOR_GAP_AUDIT_v04.md`. It lists official product sources, their known strengths, what can be implemented without copying proprietary data/methods, blockers, and explicit P0/P1/P2 priorities.

## Validation commands

```bash
python -m unittest discover -s tests -q
python cli.py portfolio-risk-v04 --output reports/portfolio_risk_v04.json
```

Portfolio scenario reports are intentionally calculated using **sum of row-level values** ₹2,349,296.90 rather than broker statement summary ₹2,349,296.92; the ₹0.02 difference is documented. Stock statement is dated 21 October and fund statement 22 October 2026. Portfolio values are not executable quotes.
