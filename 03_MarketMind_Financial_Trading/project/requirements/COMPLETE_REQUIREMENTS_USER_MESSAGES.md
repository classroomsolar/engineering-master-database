# COMPLETE USER-STATED REQUIREMENTS — INDIAN STOCK MARKET WEBSITE

Prepared 24 October 2026 from the user messages available in this conversation.

**Total: 145 entries = 55 original items + 90 later user requests/clarifications.**

**Source rules:** The first 55 are faithfully transcribed from your numbered master checklist. The later entries are extracted from your subsequent messages, and are not claims that software has been built. Some requirements overlap because they were emphasised repeatedly. Implementation decisions I previously proposed are not silently counted as your instructions.

## PART A — Original 55-point checklist (preserved wording)

**O001.** Complete portfolio database — Import both latest Groww holding statements, accurately record every stock and mutual fund, quantity, purchase price, investment value, profit and loss.  
**O002.** Correct the existing Google Sheets tracker — Eliminate outdated holdings, duplicate entries, incorrect prices and inconsistencies, including the NALCO/Shyam Metalics discrepancy.  
**O003.** Automatic Indian market data — Retrieve daily NSE/BSE prices, Nifty, Sensex, sector indices, volumes and market movements.  
**O004.** Historical stock prices — Maintain reliable historical OHLCV data with corporate-action adjustments.  
**O005.** Integrate online financial analyzers — Evaluate Screener.in, Trendlyne, TradingView, Moneycontrol and other useful Indian market analysis services.  
**O006.** Official financial data integration — Use NSE, BSE, company announcements, RBI, SEBI and AMFI wherever relevant.  
**O007.** Company fundamental analysis — Examine revenue, profits, EPS, ROE, ROCE, margins, cash flow, debt, valuations and financial health.  
**O008.** Bank-specific analysis — Analyze NIM, GNPA, NNPA, ROA, credit growth, provisions and capital adequacy.  
**O009.** Technical analysis — Calculate moving averages, RSI, MACD, ATR, volume trends, support/resistance and market momentum.  
**O010.** Online stock analyst research — Obtain and compare accessible recommendations from Motilal Oswal, HDFC Securities, ICICI Direct, Kotak Securities, Axis Securities and other reputable research firms.  
**O011.** Analyst recommendation comparison — Record BUY/HOLD/SELL opinions, target prices, publication dates, time horizons and disagreements between analysts.  
**O012.** Daily financial newspaper analysis — Read accessible full articles, not merely headlines, from Financial Express, Economic Times, Business Standard, Mint, BusinessLine, Moneycontrol and other relevant publications.  
**O013.** Last-24-hour news research — Find important company, sector, economy and market developments each day.  
**O014.** Financial news verification — Cross-check important information from newspapers against official company disclosures and financial statements.  
**O015.** News impact assessment — Determine which news items genuinely improve or weaken the investment prospects of particular stocks.  
**O016.** Financial recommendation calculator — Develop a working calculator combining market data, fundamentals, technicals, news and analyst research.  
**O017.** Stock selection engine — Identify promising Indian stocks and eliminate unsuitable candidates using transparent screening rules.  
**O018.** BUY / SELL / HOLD / WAIT recommendations — Provide one consolidated, actionable decision list for existing holdings and new investment opportunities.  
**O019.** Entry and exit calculations — Recommend defensible entry prices, review/exit levels, investment horizons and downside scenarios.  
**O020.** Purchase quantity calculator — Calculate how many shares to buy or sell rather than suggesting arbitrary quantities.  
**O021.** Capital allocation calculator — Calculate the INR amount to invest in each opportunity based on available capital, position limits and risk.  
**O022.** Portfolio risk management — Monitor stock concentration, sector exposure, overlapping investments, liquidity and downside risk.  
**O023.** Existing holdings recovery strategy — Review loss-making positions, particularly TCI Express, and determine whether to hold, reduce or average down based on fundamentals rather than purchase cost alone.  
**O024.** Mutual fund analysis — Examine all existing schemes, their performance, expenses, overlap, tax restrictions, risk and suitability.  
**O025.** Mutual fund rebalancing — Identify which schemes to retain, reduce, stop investing in or replace, including concentrated gold/silver exposure.  
**O026.** New investment opportunities — Recommend suitable stocks and mutual funds based on your investment horizon and available capital.  
**O027.** Short-term cash management — Evaluate safe, liquid options for money required within approximately one month, separately from long-term equity investments.  
**O028.** Daily investment dashboard — Display portfolio value, returns, market movements, watchlists, stock rankings and investment recommendations.  
**O029.** Daily 8 AM IST investment review — Maintain the existing scheduled review, incorporate all major analysis components and avoid creating duplicate automations.  
**O030.** Maintain research and decision logs — Save sources, prices, calculations, reasons, proposed trades and subsequent outcomes to measure recommendation quality.  
**O031.** Develop algorithmic trading strategies — Implement initial quality-and-momentum, earnings-event and trend-following strategies.  
**O032.** Algo backtesting — Test strategies against reliable historical data with realistic brokerage costs, slippage, transaction taxes and execution assumptions.  
**O033.** Strategy performance comparison — Compare algorithms against Nifty benchmarks and calculate CAGR, drawdowns, volatility, Sharpe/Sortino ratios and win rates.  
**O034.** Walk-forward validation — Test algorithms on unseen data across different market environments to reduce overfitting.  
**O035.** Algo paper trading — Run validated strategies on a simulated portfolio for at least 8–12 weeks before considering real deployment.  
**O036.** Algo risk controls — Add portfolio limits, position sizing, loss controls, event filters and safeguards against stale or incorrect data.  
**O037.** Groww integration research — Evaluate whether broker holdings, prices and transactions can be securely synchronized, including subscription requirements.  
**O038.** Real trading controls — Keep actual Groww orders subject to your explicit approval; investigate compliant automation only as a later, separate phase. No intraday, F&O, margin or leverage.  
**O039.** Telegram newspaper collection — Develop a permitted method to collect daily financial newspaper PDFs from authorized Telegram channels or publishers.  
**O040.** Telegram collector/bot — Inspect any existing local script and build or improve the automated collector, including scheduling, retries and duplicate detection.  
**O041.** Google Drive newspaper workflow — Organize temporary newspaper intake and research outputs without indefinitely archiving large PDFs.  
**O042.** Gemini PDF extraction — Use Gemini where permitted to extract newspaper articles, company information, financial figures and page-specific evidence.  
**O043.** ChatGPT independent verification — Compare extracted information with official filings and accessible articles, identifying contradictions and missing information.  
**O044.** PDF completeness checks — Verify page counts, extraction coverage, missing pages, duplicates and processing failures before treating a newspaper as analyzed.  
**O045.** Automatic PDF deletion — Delete temporary newspaper PDFs after successful processing, targeting completion within 24 hours.  
**O046.** Verify permanent deletion — Check removal from local storage, temporary Google Drive locations and Gemini uploads rather than assuming moving a file to Trash is sufficient.  
**O047.** Error handling and notifications — Report missing newspapers, failed extraction, stale market data, API problems and unsuccessful file deletion.  
**O048.** Local/cloud automation — Establish a reliable schedule for news collection, financial calculations, research updates and cleanup, accounting for local computer availability.  
**O049.** Use relevant connected plugins — Employ Google Drive, research tools, mathematical tools, document-processing services and other available plugins where useful, without unnecessarily requiring paid services.  
**O050.** Security, privacy and permissions — Protect account credentials, broker data and Telegram sessions, and respect publisher/API access and content-use restrictions.  
**O051.** Comprehensive testing and auditing — Independently validate financial formulas, stock identities, source dates, algo calculations, PDF workflows and portfolio recommendations with realistic test cases.  
**O052.** Build actual working deliverables — Deliver a functional calculator, data pipeline, research dashboard, strategy-testing system and documented automation, not merely conceptual plans.  
**O053.** Clear project completion tracking — Distinguish completed, partially implemented, untested and blocked functionality, explain exact blockers and resolve them wherever possible.  
**O054.** Maintain everything as one integrated project — Use the existing Google Drive masterplan and tracker rather than repeatedly starting disconnected spreadsheets, tools or workflows.  
**O055.** Make the final system dependable and auditable — Every recommendation must be traceable to dated evidence and reproducible calculations; no fabricated prices, untested claims of algorithm profitability or guaranteed returns.  

## PART B — Additional spoken/written instructions and corrections

### Website Delivery And User Experience

**V001.** Create an actual interactive website, not spreadsheets as the main interface.  
**V002.** Use Google Sheets/spreadsheets only as optional data storage or backend input, not something I must operate manually.  
**V003.** The assistant/build system must run the Python, JavaScript, HTML, CSS and tests; I must not have to run Python scripts myself.  
**V004.** The website must have proper working calculators and functionality, not just scripts, mock-ups, plans or screenshots.  
**V005.** Give the site a real reachable web URL; fix the previous content-blocked/page-not-found links.  
**V006.** Website address may be publicly reachable, but actual content and holdings must be private behind sign-in.  
**V007.** Provide one owner login with email address or username and password so only an authorised person can access my data.  
**V008.** Allow me to open the same website on any suitable device/browser, independently of this ChatGPT account.  
**V009.** Maintain polished, easy-to-use UX/UI and keep all financial functions integrated in the same application.  
**V010.** Continue developing the existing website/project instead of abandoning it and generating unrelated replacements.  
**V011.** Allow me to introduce further ideas and features later without discarding what is already complete.  

### Account Migration And Project Ownership

**V012.** Make everything portable before the ChatGPT Plus subscription/account change on 27 October 2026; this is time-critical.  
**V013.** Provide complete frontend source, backend source, UX/UI designs, HTML, CSS, JavaScript, Python scripts and dependencies.  
**V014.** Provide database/data exports, supporting files, configurations, calculator logic, tests and other materials needed to rebuild elsewhere.  
**V015.** Ensure the public URL with private login and hosted files survive deletion of the current ChatGPT account.  
**V016.** Enable continuation in another ChatGPT Plus account using Work/Codex there if I choose.  
**V017.** Keep a reusable master prompt that tells a future ChatGPT account precisely what was requested and what remains.  
**V018.** Preserve the conversation requirements rather than making me repeatedly dictate the same long messages.  
**V019.** Deliver as much functional and verifiable progress as possible before 27 October; do not treat plans as completion.  

### Data Pipeline And Scheduling

**V020.** Automatically update all relevant website data daily without waiting for me to ask in chat.  
**V021.** Aim for data available by roughly 09:30 or 10:00 AM India time on market mornings.  
**V022.** Fetch fresh market information again approximately every hour during the day.  
**V023.** Include current stock prices, historical prices, market movements, company information and relevant news in automated updates.  
**V024.** Use authentic and authoritative NSE, BSE, issuer, regulator and other approved sources; consider Groww, Zerodha/Kite and others as data providers.  
**V025.** Evaluate and choose technically whether providers should feed the website directly or first populate Google Sheets; do not merely follow my suggestion.  
**V026.** Continue using the existing Google Drive/Sheets historical holdings and market research data where useful.  
**V027.** Keep India as the market/security universe, even when borrowing capabilities from global platforms.  
**V028.** Study functional ideas from US, UK, Europe, Australia, New Zealand and other international financial sites/apps.  
**V029.** Study and compare other online/downloadable/spreadsheet financial calculators; incorporate useful lawful functions to make ours more complete.  
**V030.** Use Groww as my actual Demat/broker account; evaluate other broker apps as functional references rather than assuming I hold accounts there.  

### Research, Expert Opinions And Final Advice

**V031.** Collect and study important news on individual stocks daily from many credible publications, experts, interviews and analyst columns.  
**V032.** Read and analyse expert conclusions and price/trend expectations, rather than merely collecting links and article titles.  
**V033.** Do not flood my dashboard with raw newspapers/news reports; show the resulting investment analysis and conclusions.  
**V034.** Compare and synthesise the views of different human analysts and publications.  
**V035.** Treat qualified human expert work seriously; I said I prefer their advice to be followed rather than dismissed.  
**V036.** Provide a clear stock BUY/SELL/HOLD/WAIT recommendation rather than leaving the final interpretation entirely to me.  
**V037.** Provide similarly concrete mutual fund buy/invest, hold, reduce or exit guidance.  
**V038.** Give realistic, persuasive investment cases with reasons, evidence and practical choices.  
**V039.** For each proposed stock buy, give a recommended purchase price, exact quantity and INR outlay.  
**V040.** Specify when I might sell and the conditions or target for doing so.  
**V041.** Focus on financially sensible shorter opportunities; do not automatically require six months or 100% gain on a stock to realise any profit.  
**V042.** Use the disciplined, value-aware research approach associated with Warren Buffett and Charlie Munger as inspiration.  
**V043.** Understand that I intend to use real money based on your analysis; be accountable in your evidence and calculations rather than overconfident.  
**V044.** Challenge my assumptions or bad ideas rather than agree blindly; explain why an idea is technically or financially unsound.  
**V045.** I specifically asked you not to question the experts; this preference must be reconciled with my original insistence on independent filing verification.  

### Stock Profit Objective And Notifications

**V046.** An earlier daily target of 0.021% was discussed, but I subsequently replaced it with the final accepted target of **0.033% per day**.  
**V047.** Use the final 0.033% per-calendar-day target for stock profit monitoring, approximately 1% over 30 days as the planning comparison.  
**V048.** Track the target against actual holding price/cost and elapsed holding time; do not invent realised returns.  
**V049.** When a specific stock meets or exceeds my configured profit objective, tell me that the goal has been met.  
**V050.** Provide a suggested SELL / sell-review prompt when the objective has been reached, including the current price and profit.  
**V051.** The target is a decision threshold, not a requirement that every stock must earn a fixed return each day.  
**V052.** Consider practical platform alert delivery; explain candidly when unattended automatic alerts are not enabled.  
**V053.** Deal carefully with losing positions; I expressed reluctance to sell in loss but did not finish an absolute no-loss-sale rule.  
**V054.** Always tell me honestly when charges, taxes, risk or price movement make a proposed profit target impractical.  

### Algorithmic Trading Expectations

**V055.** Develop algorithmic stock trading/research capabilities as part of this same website, not as an unrelated script.  
**V056.** Combine algos with comprehensive research, technical indicators, market data and portfolio risk assessment.  
**V057.** Analyse positions and target conditions as fresh prices become available so actions can be reviewed promptly.  
**V058.** Give me clear signal/risk/price/quantity proposals; actual orders must still require my explicit approval per the original 55-point checklist.  
**V059.** Use realistic algorithms and tests, not a claim that AI or a 0.033% target automatically creates profits.  

### Telegram Newspaper Ingestion And Retention

**V060.** I am willing to connect authorised Telegram access so the system can collect relevant financial newspaper PDFs automatically.  
**V061.** Collect permitted daily issues again on subsequent days without requiring me to upload every PDF manually.  
**V062.** Read/process newspaper PDFs fully, extracting company, finance and expert-analysis information for the research process.  
**V063.** Use temporary processing storage rather than letting daily downloaded PDFs accumulate indefinitely.  
**V064.** Delete temporary PDF copies from your processing/cloud storage after approximately 24 hours.  
**V065.** Never delete the originals from Telegram itself.  
**V066.** Preserve the extracted research facts and audit information so future calculations can use them after PDF deletion.  
**V067.** If any PDFs are temporarily stored in Drive/Gemini/local files, verify deletion of those copies rather than assuming cleanup.  
**V068.** You referred to approximately 20 GB of cloud storage; this is your assumed capacity, not a verified quota.  

### Google Ai Studio, Parallel Bots And Connected Services

**V069.** Use Google AI Studio/Gemini as an independent auditing partner that checks calculations, extraction and website work.  
**V070.** Research Google AI Studio documentation, its APIs and capabilities before deciding what to integrate.  
**V071.** Research ChatGPT/OpenAI capabilities and documentation to choose the most effective implementation workflows.  
**V072.** Enable cooperation between the two systems, with genuinely independent review rather than declaring both connected automatically.  
**V073.** I may connect my Google account/Gmail/Drive/other Google apps, Telegram and additional plugins to support the project.  
**V074.** Coordinate access to Google AI Studio and Drive under the same Google account where authorised; do not presume connected apps automatically grant API permissions.  
**V075.** Delegate suitable activities to multiple small bots/workers that can work in parallel to accelerate the website.  
**V076.** I did not specify a fixed number of bots; the number and allocation should be chosen for efficiency.  
**V077.** Use relevant already-installed plugins, each for what it does best; do not force irrelevant plugins.  
**V078.** If a genuinely helpful missing plugin, website account, connection or permission is required, tell me specifically so I can provide access.  
**V079.** Minimise use of Work mode because I do not want the project blocked by token/usage resets of around five hours.  
**V080.** Keep ordinary-chat and connected-tool execution productive where possible rather than stopping for avoidable quota reasons.  

### Communication, Reliability And Handover Process

**V081.** Speak English, not Hindi, and do not imitate an Indian accent.  
**V082.** Use a British accent in voice responses as specifically requested.  
**V083.** Do not interrupt when I am speaking; wait until I finish before responding.  
**V084.** Do not drop, truncate or ignore lengthy spoken or written instructions; preserve them in a durable requirements record.  
**V085.** Do not make me repeatedly correct the same mistakes or repeat previous requirements.  
**V086.** Do not claim that an unpublished/broken Replit editor link is a functioning deployed website.  
**V087.** Be straightforward about what is possible, what requires permission and what has not been implemented.  
**V088.** Make proactive technical and financial suggestions rather than requiring me to design every part myself.  
**V089.** Work through the list methodically; no endless replacement plans or misleading statements of completion.  
**V090.** Prepare a complete reusable list and master prompt for this and the successor ChatGPT account.  

## Corrections, superseded values and conflicts that MUST remain visible

- **Final stock profit threshold:** **0.033% per day**. Earlier **0.021%** was explicitly superseded. The user compared this with approximately **1% over 30 days**. Whether the implementation should use a simple threshold or a compound daily threshold for a given holding was **not explicitly settled by the user**; record it as a formula choice requiring transparent display, not as a user instruction. Financial costs and tax can exceed this small objective.
- **Market opening:** The user suggested 09:30 or 10:00 for the first website refresh, not that NSE officially opens at 09:30. Preserve the requested refresh times without incorrectly relabelling them as market opening.
- **Expert opinions:** The user said not to question experts, but also originally instructed us to verify news against issuer and exchange filings and asked the assistant not to agree blindly. Both utterances are preserved. Safety-critical investment recommendations must use independent verification, and expertise is evidence rather than infallibility.
- **Losses:** The user expressed reluctance to sell at a loss but did not finish an absolute mandatory holding rule. Do not translate an incomplete voice sentence into a guaranteed ban on selling losing positions.
- **Bots:** The user asked for parallel bots, not a fixed number. Any previous statement of exactly nine bots is an implementation suggestion, not a requirement they gave.
- **Storage:** The user referred to 20 GB of cloud memory, but no actual cloud quota was established. Do not portray it as confirmed.
- **Privacy vs public reachability:** The user wants a *publicly reachable address* with *private owner-only data after login*, not publicly readable holdings.
- **Advice vs execution:** The user wants serious, specific actionable investment guidance and will use real money; the original checklist requires explicit approval for actual Groww orders. The two requirements are compatible if recommendations do not execute trades.
- **Cross-account transfer:** The website, secrets and data must not depend on the old ChatGPT account; moving source code alone may not move infrastructure ownership or permissions.

## Implementation architecture suggestions — not claimed as user requirements

These are technical recommendations from the assistant and must not be silently inserted as quotes from the user: use a private server-side canonical database with transaction auditing; keep Sheets as optional data ingest/report/export instead of the hourly quote transport; strong session authentication and MFA where available; secure background worker scheduling; freshness and failure gates; source/license checks; independently verified price/fee calculations; no automatic real-money orders.

## Existing project references

- Original masterplan: https://docs.google.com/document/d/1ZXs0YL5FYa0QOXY7FrEGyLJuuciCK59Q2TZvDQ65vuo/edit
- Existing portfolio tracker: https://docs.google.com/spreadsheets/d/1EPUc7rcXpIItu5Nl_w0bRi3FswnEb0tT-uPCT0JOxOo/edit
- Existing Replit project: https://replit.com/@classroomsolar/DeepGiftedFormat (NOT a verified live deployment)
- Broker statements: Stocks_Holdings_Statement_5439142630_2026-10-21.xlsx; Holdings_Statement_2026-10-22.xlsx.

## Limits of extraction

This inventory covers all the user messages exposed in this conversation and the earlier handover text available in the session, including the original 55-point checklist. Some messages appear as skipped/condensed context in the conversation view; this file does not claim to contain verbatim text from anything not actually visible or recoverable. Future instructions should be appended as new dated entries, not overwrite the baseline.
