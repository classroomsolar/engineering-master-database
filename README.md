# Engineering Equipment Database

Read-only, single-unit-normalized engineering equipment catalog and reference workspace covering 195,478 verified equipment records across 29 categories and 34 curated engineering reference tables.

## Quick Start

```bash
npm install
npm start
```

Open `http://localhost:3000` in your browser.

## Verification & Tests

```bash
node --test tests/*.mjs
python3 01_Engineering_Equipment_Database/website/tools/audit_security_and_governance.py
```

## Structure

- `server.js` — Read-only Express server serving the static catalog on port `3000` (with `/verification`, `/spreadsheets`, `/exports`, and `*.xlsx` blocked).
- `01_Engineering_Equipment_Database/website/dist/` — Frontend application (`index.html`, `assets/`) and normalized gzip-compressed JS datasets (`collections/`, `data/`).
- `01_Engineering_Equipment_Database/website/tools/` — Deterministic cleaning and audit scripts.
- `tests/` — Deterministic Node unit and catalog integrity tests.
