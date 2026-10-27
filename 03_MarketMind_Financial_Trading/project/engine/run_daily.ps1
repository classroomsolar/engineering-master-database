# Indian Market Intelligence v0.2 - SAFE local scheduled job
# OFFLINE by default. Optional -FetchNSE attempts public official NSE EOD Bhavcopy.
# Does not call Groww, Gemini, Telegram, ChatGPT or any broker trading endpoint.
param([switch]$FetchNSE)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
if (-not (Test-Path '.\reports')) { New-Item -ItemType Directory -Path '.\reports' | Out-Null }
"$(Get-Date -Format o) Daily local refresh start FetchNSE=$FetchNSE" | Out-File .\reports\local_job_log.txt -Append -Encoding utf8
try {
    py -3 .\cli.py portfolio-audit --output '.\reports\portfolio_audit.json'
    if ($LASTEXITCODE -ne 0) { throw 'Broker snapshot audit failed' }
    if ($FetchNSE) {
        py -3 .\nse_daily.py --fetch
        $nseExit=$LASTEXITCODE
        if ($nseExit -ne 0) {
           # Maintain the verified older snapshot and continue independent local work.
           "$(Get-Date -Format o) WARNING NSE EOD unavailable; see nse_eod_pipeline_status.json" | Out-File .\reports\local_job_log.txt -Append -Encoding utf8
        }
    } else {
        py -3 .\nse_daily.py
        if ($LASTEXITCODE -ne 0) {
           "$(Get-Date -Format o) INFO no local NSE archive; optional -FetchNSE disabled" | Out-File .\reports\local_job_log.txt -Append -Encoding utf8
        }
    }
    py -3 .\cli.py market-store-audit --output '.\reports\market_store_quality.json'
    if ($LASTEXITCODE -ne 0) { throw 'NSE transactional market-data quality audit failed' }
    py -3 .\cli.py daily-report --output '.\reports\daily_research_gate.json'
    if ($LASTEXITCODE -ne 0) { throw 'Research WAIT gate failed' }
    py -3 .\make_dashboard.py
    if ($LASTEXITCODE -ne 0) { throw 'Dashboard refresh failed' }
    py -3 .\cli.py pdf-overdue | Out-File .\reports\pdf_overdue_log.txt -Append -Encoding utf8
    if ($LASTEXITCODE -ne 0) { throw 'PDF overdue audit failed' }
    "$(Get-Date -Format o) Daily local refresh complete; NO REAL ORDERS" | Out-File .\reports\local_job_log.txt -Append -Encoding utf8
} catch {
    "$(Get-Date -Format o) ERROR $($_.Exception.Message)" | Out-File .\reports\local_job_log.txt -Append -Encoding utf8
    exit 1
}
