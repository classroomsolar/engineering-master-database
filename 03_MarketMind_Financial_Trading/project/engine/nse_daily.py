"""Opt-in best-effort NSE daily EOD ingestion, not a real-time quote server.
Use official public archive if it responds; never fabricate a missing trade day.
"""
from __future__ import annotations
import argparse,datetime as dt,json
from pathlib import Path
from market_engine import IST,save_json
from nse_pipeline import download_udiff,archive_import,archive_name

def update(*,asof:dt.datetime|None=None,root:Path,max_lookback:int=7,fetch:bool=False)->dict:
    now=(asof or dt.datetime.now(IST)).astimezone(IST)
    root=Path(root)
    out=root/'data'/'nse_archives';store=root/'data'/'nse_raw_unadjusted'
    latest=now.date() if now.hour>=19 else now.date()-dt.timedelta(days=1)
    attempts=[];succeeded=None
    for offset in range(max_lookback):
        day=latest-dt.timedelta(days=offset)
        if day.weekday()>4:continue
        file=out/archive_name(day)
        status={'date':day.isoformat(),'source_file':str(file),'attempted_online':fetch}
        try:
            if not file.exists():
                if not fetch:
                    status['status']='ARCHIVE_NOT_PRESENT';attempts.append(status);continue
                receipt=download_udiff(day,file)
                status['retrieved_sha256']=receipt['sha256']
            result=archive_import(file,date=day,store=store)
            succeeded=result
            status.update({'status':'INGESTED_RAW_UNADJUSTED','matched_symbols':result['matched_symbols'],'missing_symbols':result['missing_symbols'],'origin_confirmed':result['origin_confirmed']})
            attempts.append(status)
            break
        except Exception as exc:
            status.update({'status':'FAILED','error':str(exc)[:450]})
            attempts.append(status)
    summary={'run_at_ist':now.isoformat(),'latest_checked_date':latest.isoformat(),
             'success':succeeded is not None,'ingested_asof_date':succeeded['date'] if succeeded else None,
             'matched_symbols':succeeded['matched_symbols'] if succeeded else 0,
             'authoritative_transactional_store':succeeded.get('authoritative_db') if succeeded else None,
             'commit_status':succeeded.get('commit_status') if succeeded else None,
             'valid_for_unadjusted_eod_monitoring':bool(succeeded and succeeded.get('origin_confirmed')),
             'complete_holdings_coverage':bool(succeeded and succeeded.get('matched_symbols')==6),
             'source_quality_warning':('MANUAL OPERATOR ATTESTED, NOT INDEPENDENTLY AUTHENTICATED' if succeeded and succeeded.get('origin_provenance')=='MANUAL_OFFICIAL_EXPORT_ATTESTED' else None),
             'valid_for_corporate_action_adjusted_backtest':False,
             'valid_for_executable_quote':False,
             'action_if_unavailable':'Download the official NSE CM-UDiFF Common Bhavcopy Final ZIP manually, attest provenance, import. Never substitute statement prices.',
             'attempts':attempts}
    save_json(root/'reports'/'nse_eod_pipeline_status.json',summary)
    if succeeded:
        save_json(root/'reports'/'nse_last_successful_ingest.json',{k:v for k,v in succeeded.items() if k!='bars'})
    return summary

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--root',default=str(Path(__file__).resolve().parent));p.add_argument('--fetch',action='store_true',help='Explicitly attempt NSE official archive network fetch')
    p.add_argument('--lookback',type=int,default=7)
    a=p.parse_args(argv)
    if a.lookback<1 or a.lookback>14:raise ValueError('Lookback must be 1..14 calendar days')
    x=update(root=Path(a.root),fetch=a.fetch,max_lookback=a.lookback)
    print(json.dumps(x,indent=2));return 0 if x['success'] else 2
if __name__=='__main__':raise SystemExit(main())
