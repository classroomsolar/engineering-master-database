# START HERE — MarketMind UI v3 · 25 October 2026

This ZIP supersedes all earlier project handover archives. It includes only the latest self-contained browser dashboard (`website/index.html`), its owner-auth Node wrapper (`website/server.mjs` and package files), offline engine, tests, 145 requirements, prompts, private original input files and essential documentation.

1. Read `prompts/MASTER_PROMPT_FOR_NEXT_ACCOUNT_OR_AI_STUDIO.md` and `requirements/COMPLETE_REQUIREMENTS_REGISTER.csv` before editing.
2. Latest website source: `website/index.html` (UI v3, responsive, interactive, no external front-end dependencies). It contains private broker holdings inline and **must NOT be deployed without strong server/deployment-level authentication**.
3. The current owner Vercel project `indian-market-intelligence-private` has SSO protection enabled for all deployments, and the existing production domain is `https://indian-market-intelligence-private.vercel.app/`. A new ChatGPT account does not transfer the Vercel project automatically.
4. For self-hosting with Node, use `website/server.mjs`, run private-access tests and set owner authentication secrets from `website/.env.example`. Never put passwords, PAN, live brokerage tokens or any secrets in frontend code.
5. All 145 requirements include 55 original + 90 later specifications. Progress statuses are truthful, not 145 completions.
6. `engine/` contains offline calculation code and 64 synthetic/offline unit tests; no verified live NSE/BSE history, automatic trading or current analyst claims.
7. `owner_private/` contains Groww statements and offline Google Drive data exports; do not share this ZIP with public services without review.
8. Run `node --test test_auth.mjs` in `website/` and `python -m unittest discover -s tests -q` in `engine/`. Local site smoke tests and SHA-256 checks are documented in `verification/`.

Jimo / Awwwards visual references informed an ORIGINAL design; their proprietary source, logos and assets are not copied.
