# NSE EOD UDiFF integration — v0.2

**Existing master project**: <https://docs.google.com/spreadsheets/d/1EPUc7rcXpIItu5Nl_w0bRi3FswnEb0tT-uPCT0JOxOo/edit>.

## Verified public references

- NSE official reports and CM-UDiFF ZIP: <https://www.nseindia.com/all-reports>
- NSE MCP docs and use restrictions: <https://www.nseindia.com/nse-mcp>
- NSE historical archives: <https://www.nseindia.com/static/resources/historical-reports-capital-market-daily-monthly-archives>

The archived format is `BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`. The NSE public page confirms the old CM Bhavcopy CSV formats were discontinued July 2024. NSE may change access controls without notice. The script **does not bypass access controls or invent quotes**.

## User-tested, manual NSE workflow (works without network fetch)

1. From the [NSE All Reports](https://www.nseindia.com/all-reports), save the CM-UDiFF Common Bhavcopy Final ZIP for the desired trading date into a private directory. Keep the original filename.
2. Only after checking the NSE source/file date and identity, attest the local exact original ZIP and its SHA-256:

```powershell
py -3 nse_pipeline.py attest --file "C:\private\BhavCopy_NSE_CM_0_0_0_20261021_F_0000.csv.zip" --date 2026-10-21 --source-url "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20261021_F_0000.csv.zip" --reviewed-by "local-human-review"
py -3 nse_pipeline.py import --file "C:\private\BhavCopy_NSE_CM_0_0_0_20261021_F_0000.csv.zip" --date 2026-10-21 --store data/nse_raw_unadjusted
```

Or attempt **best-effort official network download** and then import:

```powershell
py -3 nse_pipeline.py download --date 2026-10-21 --out "data/nse_archives/BhavCopy_NSE_CM_0_0_0_20261021_F_0000.csv.zip"
py -3 nse_pipeline.py import --file "data/nse_archives/BhavCopy_NSE_CM_0_0_0_20261021_F_0000.csv.zip" --date 2026-10-21 --store data/nse_raw_unadjusted
```

`nse_pipeline.py import` rejects wrong ISIN, duplicate EQ rows, bad OHLC, wrong dates, ZIP bomb risk, mutated archive receipts, and later contradictory same-date bars. Every file is tagged raw/unadjusted **even with a provenance receipt**. External/manual files without a receipt show `USER_SUPPLIED_UNVERIFIED_ORIGIN`.

## Conservative corporate action gate

Source history remains **unadjusted** until independently reviewing issuer/NSE split/bonus history for the **entire range**, and signing an explicit JSON review. An empty approved event list means someone actually checked the full period, **not** that software proved no events.

Example for a *hypothetical* zero-split review (DO NOT sign until checked):

```json
{
  "symbol": "NATIONALUM", "isin": "INE139A01034",
  "status": "HUMAN_REVIEWED_APPROVED",
  "covered_from_date": "2024-01-01", "reviewed_through_date": "2026-10-21",
  "official_source_url": "https://www.nseindia.com/companies-listing/corporate-filings-actions",
  "events": []
}
```

For stock split or bonus events, each event must include `type` SPLIT or BONUS, `ex_date`, `shares_after_per_share_before`, and `official_source_url`. Do **not** include real events or claim none happened without verification. For a share ratio of 2 after:1 before, pre-ex-date prices divide by 2 and volumes multiply by 2. This is a *price/volume* split adjustment, not a complete total-return series.

```powershell
py -3 corporate_actions.py --raw data/nse_raw_unadjusted/NATIONALUM.csv --review "C:\private\checked_nalco_actions.json" --out data/adjusted_reviewed/NATIONALUM.csv
py -3 cli.py indicators --csv data/adjusted_reviewed/NATIONALUM.csv --output reports/NALCO_indicators.json
```

Dividends, demergers, rights issues, mergers, delistings, historical security membership, survivorship and index-total-return benchmarks require separate handling before serious comparative strategy validation. Price-only split/bonus adjustments do not silently become 'total returns'.

## Daily optional research job

```powershell
py -3 nse_daily.py                         # Offline/import known local NSE archives only
py -3 nse_daily.py --fetch                 # Opt-in NSE official archive, 7-calendar-day bounded fallback
powershell.exe -NoProfile -File .\run_daily.ps1 -FetchNSE
```

The script checks candidate trading weekdays only; NSE holidays are detected by failed official data availability rather than a guessed market calendar. It records date, checksum, matched symbols and warnings in `reports/nse_eod_pipeline_status.json`. It never reports a fresh price without an actual parsed archive. It leaves last successful ingest metadata separate on failures and never issues trades. It does not connect to the existing 8 AM ChatGPT task.

### Verification scope

30 automated unit tests include 10 new offline synthetic NSE-format fixtures for correct ID/date, reproducibility, source receipts, split maths and strict rejection. An **actual NSE network fetch was not available** in this execution environment; neither live prices nor genuine historical strategy results were generated. The user's existing historical holdings snapshot remains the only valuation in the bundled dashboard.
