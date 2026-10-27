"""NSE Indices NIFTY 50 Total Return Index (TRI) comparisons, never price-index substitution.

User-supplied official CSV needs an explicit SHA-256 manifest and operator attestation.
This tool does not claim the manifest is cryptographic proof of exchange origin.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import hashlib
import json
import math
from pathlib import Path
from market_engine import performance, save_json

OFFICIAL='https://www.niftyindices.com/reports/historical-data'
DATE_NAMES=('Date','DATE','Trade Date','TradeDate')
INDEX_NAMES=('Index Name','IndexName','Index','INDEX')
TRI_NAMES=('Total Returns Index','Total Return Index','TotalReturnsIndex','TRI','Total Return','Total Returns Index Value')


def _column(fields, names):
    found={x.strip().casefold():x for x in fields if x}
    for n in names:
        if n.casefold() in found:return found[n.casefold()]
    raise ValueError('Missing official TRI CSV column among: '+str(names))


def _date(value):
    for fmt in ('%Y-%m-%d','%d-%b-%Y','%d-%m-%Y','%d/%m/%Y','%Y%m%d'):
        try:return dt.datetime.strptime(value.strip(),fmt).date()
        except ValueError:pass
    raise ValueError('Unrecognized NSE TRI date '+repr(value))


def load_tri(csv_path:Path, *, manifest_path:Path, expected_index='NIFTY 50')->dict:
    csv_path=Path(csv_path)
    manifest=json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    digest=hashlib.sha256(csv_path.read_bytes()).hexdigest()
    if digest != manifest.get('sha256'):raise ValueError('NSE TRI manifest checksum mismatch')
    if manifest.get('attested_source_url')!=OFFICIAL or not manifest.get('reviewed_by'):
        raise ValueError('Source attestation must reference NSE Indices official historical-data page and reviewer')
    if manifest.get('expected_index')!=expected_index:
        raise ValueError('Index label mismatch in manifest')
    with csv_path.open(encoding='utf-8-sig',newline='') as f:
        reader=csv.DictReader(f)
        fields=reader.fieldnames or []
        dc=_column(fields,DATE_NAMES);vc=_column(fields,TRI_NAMES)
        nc=next((k for k in fields if k.strip().casefold() in {v.casefold() for v in INDEX_NAMES}),None)
        points=[]
        for row in reader:
            if not any(row.values()):continue
            if nc and row[nc].strip() and row[nc].strip().upper()!=expected_index.upper():
                raise ValueError('Unexpected index name in NSE TRI CSV')
            d=_date(row[dc]);val=float(row[vc].replace(',','').strip())
            if not math.isfinite(val) or val<=0:raise ValueError('Invalid TRI level')
            points.append({'date':d.isoformat(),'tri_level':val})
    if len(points)<2:raise ValueError('TRI history too short')
    points.sort(key=lambda z:z['date'])
    if len({x['date'] for x in points})!=len(points):raise ValueError('Duplicate TRI dates')
    return {'index':expected_index,'points':points,'source_url':OFFICIAL,'file_sha256':digest,
            'attestation':'HUMAN_SOURCE_ATTESTED_NOT_CRYPTOGRAPHICALLY_VERIFIED',
            'disclaimer':'Reported index TRI history; exchange source and methodology should be independently confirmed.'}


def compare_curve(strategy_curve:list[dict], tri:dict, *, min_coverage=0.95)->dict:
    """Same-date benchmark comparison; refuse different horizons and thin overlaps."""
    if not 0.0<min_coverage<=1.0:raise ValueError('Invalid minimum data coverage')
    if len(strategy_curve)<2:raise ValueError('Strategy test period too short')
    dates=[str(x['date']) for x in strategy_curve]
    if dates!=sorted(set(dates)):raise ValueError('Strategy curve dates must be unique and increasing')
    if any(not math.isfinite(float(x['equity'])) or float(x['equity'])<=0 for x in strategy_curve):
        raise ValueError('Nonpositive / nonfinite equity')
    index_by_day={x['date']:float(x['tri_level']) for x in tri['points']}
    missing=[d for d in dates if d not in index_by_day]
    coverage=(len(dates)-len(missing))/len(dates)
    if coverage<min_coverage or dates[0] not in index_by_day or dates[-1] not in index_by_day:
        raise ValueError(f'Insufficient same-date TRI coverage {coverage:.2%}; refusing benchmark comparison')
    # Percent over identical end-to-end horizon; missing interior dates flagged separately.
    first=index_by_day[dates[0]];last=index_by_day[dates[-1]]
    strategy_ret=100*(float(strategy_curve[-1]['equity'])/float(strategy_curve[0]['equity'])-1)
    benchmark_ret=100*(last/first-1)
    b_dates=[d for d in dates if d in index_by_day]
    levels=[index_by_day[d] for d in b_dates]
    bperf=performance(levels,[{'date':dt.date.fromisoformat(x)} for x in b_dates])
    return {'benchmark_index':tri['index'],'benchmark_source':tri['source_url'],
            'status':'RESEARCH_VALIDATION_REQUIRES_FURTHER_PIT_AND_COST_CHECKS',
            'start_date':dates[0],'end_date':dates[-1],
            'overlap_days':len(b_dates),'expected_strategy_days':len(dates),'coverage_fraction':round(coverage,6),
            'missing_dates':missing[:30],'complete_overlap':not missing,
            'strategy_return_pct':round(strategy_ret,4),'nifty50_tri_return_pct':round(benchmark_ret,4),
            'strategy_minus_tri_percentage_points':round(strategy_ret-benchmark_ret,4),
            'benchmark_cagr_pct':bperf['cagr_pct'],'benchmark_max_drawdown_pct':bperf['max_drawdown_pct'],
            'benchmark_volatility_annual_pct':bperf['volatility_annual_pct'],
            'benchmark_sharpe_zero_rf':bperf['sharpe_zero_rf']}


def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--tri-csv',required=True);p.add_argument('--manifest',required=True)
    p.add_argument('--strategy-report',required=True);p.add_argument('--out',required=True)
    a=p.parse_args(argv)
    tri=load_tri(Path(a.tri_csv),manifest_path=Path(a.manifest))
    strategy=json.loads(Path(a.strategy_report).read_text(encoding='utf-8'))
    if strategy.get('synthetic'):raise ValueError('Synthetic strategy report cannot be represented as real market evidence')
    result=compare_curve(strategy['curve'],tri)
    save_json(Path(a.out),result)
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
