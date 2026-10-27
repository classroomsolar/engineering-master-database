# Authorized data inputs — production dependencies

## NSE cash-market archive

Source: https://www.nseindia.com/all-reports — download **CM-UDiFF Common Bhavcopy Final (zip)** for relevant trading days. Official archive pattern: `BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`.

The user may manually download it through the official page. To register a manual source declaration:

```bash
python nse_pipeline.py attest --file FILE.zip --date YYYY-MM-DD --reviewed-by "operator" --source-url "https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip"
```

**Attestation means the operator asserts it came from NSE. A SHA-256 fingerprint only detects later changes; it cannot authenticate the origin by itself.** Any file that cannot be tied to the original exchange source should stay `USER_SUPPLIED_UNVERIFIED_ORIGIN`.

`python nse_pipeline.py import --file FILE.zip --date YYYY-MM-DD --store data/nse_raw_unadjusted` creates an authoritative SQLite data store and regenerates stock CSVs.

## Official benchmark

Source: https://www.niftyindices.com/reports/historical-data — use the Total Returns Index data, not the ordinary NIFTY 50 price index. Export CSV under authorized access. Save a manifest alongside it, for example:

```json
{
  "sha256": "<SHA256 OF EXACT CSV FILE>",
  "attested_source_url": "https://www.niftyindices.com/reports/historical-data",
  "reviewed_by": "<HUMAN_REVIEWER>",
  "expected_index": "NIFTY 50"
}
```

The benchmark CSV needs a Date column, Total Returns Index numeric column, and optionally Index Name (strictly NIFTY 50). The user should confirm official export format and actual data permissions. A CSV may be used in research only if the output is transparent about review status.

## Price adjustments and research qualification

Price split/bonus ratios may be applied only from issuer/exchange-reviewed action data. Full financial research and after-cost backtesting also require dividends, rights/mergers, delistings, a point-in-time stock universe, cash flows, and a properly sourced NIFTY 50 TRI comparison. No review JSON should falsely certify full coverage.

**Costs:** hard-coded example fees, slippage and tax defaults are NOT verified current Groww charges. Before any credible realistic backtest, confirm dates, price adjustments, cost schedules and tax applicability, including DP fees and STT.

## Operational security

No Groww login or API secrets or Telegram session files should be placed in the ZIP or Google Sheets. The Windows scheduling script is opt-in and off by default for network access. No live order functionality is included.
