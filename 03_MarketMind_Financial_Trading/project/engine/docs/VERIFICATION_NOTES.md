# QA Notes · 22 October 2026

## Statement verification

Directly parsed Groww spreadsheets, not older memory or screenshots. 6 stock positions, 18 MF position records, 14 distinct MF scheme-and-AMC names, 1 unique ISIN per stock. First report as of 2026-10-21; second as of 2026-10-22. User identity and account/folio identifiers removed from generated project JSON.

- Stock statement: investment ₹591,709.57; closing value ₹363,453.40; unrealized loss ₹228,256.17. Sum of individual invested stock rows ₹591,705.22 => difference ₹4.35; closing value matches exactly.
- Mutual fund statement: investment ₹1,744,913.39; reported value ₹1,985,843.52; P&L ₹240,930.13. Sum of displayed 18-row values ₹1,985,843.50 => difference ₹0.02; invested matches exactly.
- TCIEXP statement share count 592; average cost ₹849.17, not previously saved ₹849.18. This statement includes NATIONALUM 30 shares and omits SHYAMMETL.
- Investment statement summaries combined: market value ₹2,349,296.92, invested ₹2,336,622.96, unrealized P&L +₹12,673.96. *Mixed statement dates; not live valuation.*
- TCIEXP 75.67% of individual stock closing value; 11.71% of combined mixed-date portfolio. Fund category gold ₹784,285.92 and silver ₹299,126.04, combined 46.12% of mixed-date portfolio.

## Model tests

`python -m unittest discover -s tests -v` passed 20 tests. These cover portfolio totals, stock ISIN uniqueness, non-arbitrary integer share counts, concentration caps, input rejection, SMA/EMA/RSI/ATR/MACD generation, quote freshness gating, incomplete-research WAIT, adjusted OHLCV history rejection, refusal to treat synthetic test data as real, next-open scenario trading, three strategy paths, expanding walk-forward date separation, benchmark calculation, rights rejection, local deletion after validated page coverage, and blocked deletion on missing pages.

**No historical performance claim is established by any test.** Sample prices are fabricated from deterministic mathematical functions and marked `SYNTHETIC_ONLY`. Brokerage/tax/slippage fractions in the example are scenario assumptions, not verified Groww charges. True Nifty total-return benchmark and delisting-survivorship universe are not loaded.

## PDF deletion safety

Successful two-page synthetic test generated a local purge receipt with `local_path_absent=true` and explicitly stated no Gemini or Drive copy existed. A separate missing-page test verified the PDF is not deleted and processing fails. This proves only a *local program flow in the test environment*, not 24-hour cloud cleanup or actual Telegram/Gemini integration.

## Known model limitations

1. Historical CSV importer requires its caller to have truly adjusted OHLCV; a `true` CSV flag cannot prove source actions were adjusted. No provider integration or nightly update running yet.
2. The quality and event strategy prototype `quality_score` and `valuation_score` thresholds are hypotheses, not empirically validated. No point-in-time fundamentals source loaded for actual users.
3. An earnings-event test fixture uses an explicit tradable availability date; actual earnings-publication time must be reconciled with local exchange sessions to avoid lookahead. Current event script does not process timestamps itself.
4. Commission, DP charge, STT, stamp duty, GST and capital-gains taxes are approximated by configurable round-trip fractions, not a complete Groww statutory cost model. No capacity/market-impact analysis.
5. Cash-position test uses one symbol. Portfolio-level multi-security execution, partial fills, delistings, corporate actions, market holidays, benchmark TR and intraday order restrictions require a proper feed and further tests before the model is production fit.
6. No local Windows task has been installed by ChatGPT. The PowerShell launcher is a file ready for user-directed setup, not ongoing cloud/background execution.
