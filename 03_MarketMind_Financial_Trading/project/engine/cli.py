"""Command-line entry points: offline by default; never place trades."""
import argparse
import datetime as dt
import json
from pathlib import Path
from market_engine import (IST,read_json,save_json,portfolio_audit,report,parse_quotes_csv,
                           indicators,backtest_strategy,walk_forward,benchmark_buyhold)
from pdf_pipeline import register,validate_and_purge,overdue_jobs

ROOT=Path(__file__).resolve().parent
DEFAULT=ROOT/'data'/'portfolio_statement_snapshot.json'

def main(argv=None):
    p=argparse.ArgumentParser(description="India-only auditable stock research. NEVER sends broker orders.")
    sub=p.add_subparsers(dest="command",required=True)
    a=sub.add_parser("portfolio-risk-v04");a.add_argument("--portfolio",default=str(DEFAULT));a.add_argument("--output",default=str(ROOT/"reports"/"portfolio_risk_v04.json"))
    a=sub.add_parser("portfolio-audit");a.add_argument("--portfolio",default=str(DEFAULT));a.add_argument("--output",default=str(ROOT/'reports'/'portfolio_audit.json'))
    a=sub.add_parser("daily-report");a.add_argument("--portfolio",default=str(DEFAULT));a.add_argument("--output",default=str(ROOT/'reports'/'daily_research_gate.json'))
    a=sub.add_parser("indicators");a.add_argument("--csv",required=True);a.add_argument("--output",required=True);a.add_argument("--synthetic-test",action="store_true")
    a=sub.add_parser("backtest");a.add_argument("--csv",required=True);a.add_argument("--strategy",required=True,choices=["trend_200d_atr","quality_valuation_momentum","earnings_event"]);a.add_argument("--output",required=True);a.add_argument("--events",default=None);a.add_argument("--fundamentals",default=None);a.add_argument("--synthetic-test",action="store_true");a.add_argument("--history-review",default=None)
    a=sub.add_parser("walk-forward");a.add_argument("--csv",required=True);a.add_argument("--strategy",required=True,choices=["trend_200d_atr","quality_valuation_momentum","earnings_event"]);a.add_argument("--output",required=True);a.add_argument("--events",default=None);a.add_argument("--fundamentals",default=None);a.add_argument("--synthetic-test",action="store_true");a.add_argument("--history-review",default=None)
    a=sub.add_parser("pdf-register");a.add_argument("--file",required=True);a.add_argument("--db",default=str(ROOT/'data'/'pdf_jobs.sqlite'));a.add_argument("--publisher",required=True);a.add_argument("--source",required=True);a.add_argument("--rights-approved",action="store_true")
    a=sub.add_parser("pdf-validate-and-purge");a.add_argument("--hash",required=True);a.add_argument("--extraction",required=True);a.add_argument("--db",default=str(ROOT/'data'/'pdf_jobs.sqlite'));a.add_argument("--output",required=True)
    a=sub.add_parser("pdf-overdue");a.add_argument("--db",default=str(ROOT/'data'/'pdf_jobs.sqlite'))
    a=sub.add_parser("market-store-audit");a.add_argument("--db",default=str(ROOT/'data'/'nse_raw_unadjusted'/'nse_eod_immutable.sqlite3'));a.add_argument("--output",default=str(ROOT/'reports'/'market_store_quality.json'))
    a=sub.add_parser("nifty-tri-compare");a.add_argument("--tri-csv",required=True);a.add_argument("--manifest",required=True);a.add_argument("--strategy-report",required=True);a.add_argument("--output",required=True)
    args=p.parse_args(argv)
    if args.command=="market-store-audit":
        from market_store import audit_store
        result=audit_store(Path(args.db))
    elif args.command=="nifty-tri-compare":
        from benchmark_pipeline import load_tri,compare_curve
        tri=load_tri(Path(args.tri_csv),manifest_path=Path(args.manifest))
        strategy=read_json(args.strategy_report)
        if strategy.get('synthetic') or not strategy.get('curve'):
            raise ValueError('Synthetic/empty backtest report cannot be called real historical evidence')
        result=compare_curve(strategy['curve'],tri)
    elif args.command=="portfolio-risk-v04":
        from portfolio_analytics_v04 import portfolio_enhancement_report
        result=portfolio_enhancement_report(read_json(args.portfolio))
    elif args.command=="portfolio-audit":result=portfolio_audit(read_json(args.portfolio))
    elif args.command=="daily-report":result=report(read_json(args.portfolio))
    elif args.command=="indicators":
        bars=parse_quotes_csv(args.csv,permit_synthetic=args.synthetic_test)
        result={"symbol":bars[0]["symbol"],"history_count":len(bars),"latest":indicators(bars)[-1],"synthetic":bars[0]["synthetic"]}
    elif args.command in ("backtest","walk-forward"):
        if not args.synthetic_test:
            from backtest_quality_gate import verify_backtest_input
            if not args.history_review:
                raise ValueError('Real-data backtest blocked: --history-review JSON is required; split-only adjustments are not production ready')
            verify_backtest_input(Path(args.csv),Path(args.history_review))
        bars=parse_quotes_csv(args.csv,permit_synthetic=args.synthetic_test)
        extra={"earnings_events":read_json(args.events) if args.events else None,
               "fundamental_snapshots":read_json(args.fundamentals) if args.fundamentals else None}
        if args.command=="backtest":
            result=backtest_strategy(bars,strategy=args.strategy,allow_synthetic=args.synthetic_test,**extra)
            result["buy_and_hold_same_symbol"]=benchmark_buyhold(bars)
        else:result=walk_forward(bars,strategy=args.strategy,allow_synthetic=args.synthetic_test,**extra)
    elif args.command=="pdf-register":result=register(args.file,db=args.db,publisher=args.publisher,source_reference=args.source,usage_permitted=args.rights_approved)
    elif args.command=="pdf-validate-and-purge":result=validate_and_purge(db=args.db,sha256=args.hash,extracted_json_file=args.extraction,durable_output=args.output)
    else:result={"overdue_jobs":overdue_jobs(args.db)}
    if hasattr(args,"output"):
        save_json(args.output,result)
        print("SAVED",args.output)
    print(json.dumps(result if args.command not in ("backtest",) else {k:v for k,v in result.items() if k not in ("curve","trades")},indent=2,default=str)[:8000])

if __name__=="__main__":main()
