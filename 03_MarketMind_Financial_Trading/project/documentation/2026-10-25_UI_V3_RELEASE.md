# MarketMind UI v3 · 25 October 2026

## Genuine UI changes
- Replaced prior green visual design with an original Jimo-inspired clean-white, typographically bold, electric blue and violet identity, abstract CSS-only 3D ribbon, light grid, floating source-dated holdings card.
- Light primary sidebar, new minimal header and keyboard-triggered searchable command palette (Ctrl/Cmd+K), with same tested navigation destinations.
- Contextual non-AI product guide drawer and floating help control, which navigate existing research/calculator/risk pages.
- Restyled KPI cards, charts, tables, forms, research cards and mobile bottom navigation.
- Responsive source-date callout, accessible focus and reduced-motion handling, no external fonts, libraries or images.
- Preserved original 6 stock / 18 fund statement model, sizing, XIRR, risk, strategies and all 145 requirements.

## Browser acceptance
Chromium local in-memory tests at 1440x900 and 390x844 both passed navigation, guide-to-risk, search-to-calculator and requirements, 50-share position sizing fixture, holdings stocks/funds 6/18, 145/90 requirement counts, no horizontal viewport overflow, no JS errors. This does not establish independently tested external production sign-in.

## Privacy, data and limitations
The self-contained `website/index.html` embeds private original historical holdings. NEVER serve it anonymously, including GitHub Pages. The existing Vercel project has deployment-wide SSO protection enabled; the portable Node owner-auth wrapper is an alternative for properly configured self-hosting. The interactive guide is a static UI navigator, NOT AI. Live NSE/BSE feeds, broker orders, Google Sheets direct sync, Telegram PDFs and continuous research automation remain disconnected. Market figures are dated 21 and 22 October 2026. No output promises profits.

## Inspiration
Visual reference: https://jimo.ai/product/ai and https://www.awwwards.com/websites/ui-design/. New code is original and does not import another site's copyrighted JS, images, design source, logos or fonts. No site-wide exhaustive Awwwards review was performed.
