# FINAL USER REQUIREMENTS AND DECISIONS — OCTOBER 2026

This file consolidates clarified final decisions. The **full** 145-entry register, preserving the exact user wording, takes precedence over any condensed summary here.

## Project goal, website, privacy, ownership
- An **Indian-market-only**, private, accessible online stock/MF research, portfolio analytics, decision-support, algo-research and later paper/live-broker integration website; functions inspired globally, not restricted to Indian interface ideas.
- Must work in the browser; the owner does not operate Python scripts/spreadsheets. Existing Sheets/Drive are backend inputs, archives or exports, not the sole user interface.
- Publicly resolvable URL, private owner login and private holdings; one owner email/username + password, ideally stronger managed authentication and MFA. Transfer all project files and database to a **different ChatGPT account** without relying on the old account. Existing Vercel project ownership is independently maintained and not transferred by a ChatGPT ZIP.
- Preserve latest **MarketMind UI v3**, clean white/electric blue/violet, responsive, original work inspired by Jimo AI and Awwwards; no copying others' proprietary designs/source code.
- Preserve all 145 distinct recorded requirements and support future additions; user hates lost voice prompts, resets, vague work and claims without working results.

## Market data and automation
- Official/credible permitted data from NSE, BSE, AMFI, company filings, brokers (especially user's Groww), analyst publications and news. Historical corporate-action-adjusted prices, indices, filings, funds, current headlines, valuation/risk inputs.
- Automatic updates **daily**, ready ~09:30–10:00 IST, with **hourly** intraday refresh on relevant trading days, post-close finalisation, source timestamps and failures. This is a requested operating target, **not an implemented cron**.
- Prefer direct provider -> private canonical database -> protected website for high-frequency market data; existing Google Sheet is optional read-only import, reconciliation, report/backup; avoid using Google Sheets as the sole hourly quote bus.
- Use reputable human-expert newspaper research; deliver **conclusions and researched BUY/SELL/HOLD/WAIT cases**, not unfiltered piles of news. Independent verifications against issuer/exchange filings, including analyst disagreements. Human analysts can also be wrong.

## Portfolio and financial modelling
- Preserve all existing dated Groww holdings and the true broker totals and small statement reconciliation differences; no fabricated current holdings/prices. Do not merge repeated mutual-fund folios into one underlying broker position.
- Work toward transparent cash-flow ledger, taxes, actual XIRR/TWR, securities and underlying fund look-through, concentration risk, scenarios, justified position sizing and practical portfolios.
- Final reference stock return-monitoring target **0.033% per CALENDAR DAY** (replacing 0.021%), roughly 0.99% simple 30-day total; compounding convention was not finally determined. Evaluate **after brokerage, fees, levies, spread/slippage and applicable taxes** before suggesting a sell-review. Not promised profit, not a guaranteed daily gain, and NEVER silently execute a broker order.
- Alerts desired when profit target met, with delivery channel to be configured and verified; preserve user input/control over sell decisions. Be realistic and critical, including the downside/loss case and trade cost viability.

## Algo trading and analysis
- Integrated quantitative backtests and stock screening, initial quality/valuation/momentum, earnings event and 200-day trend/ATR algorithms, official and point-in-time adjusted OHLCV, honest India-specific benchmark (TRI), dividend/actions, costs/slippage, no look-ahead/survivorship, scenario risk, walk-forward testing, actual 8–12 **elapsed** weeks paper trading before live usage.
- Preserve safety controls and separate approved real-broker order interface only after proof and owner approval. No live auto trades, leverage, F&O/intraday, or self-improving execution claims as presently implemented.

## Telegram, Google AI Studio, parallel workers
- Integrate appropriately authorised Telegram and publisher financial PDFs, daily reading and verification, temporary storage and cleanup **within 24 hours**, never deleting original Telegram messages. Preserve permitted extracted findings and source/page traceability; alert on cleanup failures. Existing collector currently NOT CONNECTED.
- Google AI Studio/Gemini as **independent auditor** for documents, formulas, business logic and analysis, via documented APIs with separate user-authorised access, transparent cost/quota/privacy, human adjudication of contradictions; Google account connection alone does not grant ChatGPT access to Gemini API.
- Parallel specialised bots/workers for ingestion, expert/news analysis, document extraction, second-model audit, quantitative analysis, QA, scheduled refresh, alerts/cleanup. **No fixed number of bots was specified by the user**; choose a feasible number, do not claim any are deployed without evidence.
- Use relevant connected plugins and identify access blockers. Avoid gratuitous Work-mode token/usage limits. Keep work portable and not dependent on this chat running continuously.

## Delivery requirements
- Short, plain English, British accent in voice, no interruptions while speaking; do not make owner repeat requirements. Provide honest explicit comparison between planned, implemented, verified, unpublished and blocked features.
- Finish as much as actually possible before originally stated 27 Oct 2026 account transfer date, continue long-term as a single project and keep a clean checked ZIP, not multiple conflicting releases.
