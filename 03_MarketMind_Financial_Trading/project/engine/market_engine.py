"""Indian Market Intelligence - reproducible research utilities. Stdlib only.

DISCLAIMER: This is NOT an exchange feed, financial adviser or order execution engine.
All market data must be supplied from sources you are licensed to use.
"""
from __future__ import annotations

import csv
import datetime as dt
import json
import math
import statistics
from collections import defaultdict
from pathlib import Path
from zoneinfo import ZoneInfo

IST = ZoneInfo("Asia/Kolkata")
KNOWN_ISINS = {
    "BAJAJ-AUTO": "INE917I01010", "CANBK": "INE476A01022",
    "LT": "INE018A01030", "NATIONALUM": "INE139A01034",
    "PGIL": "INE940H01022", "TCIEXP": "INE586V01016",
}


def money(x):
    return round(float(x), 2)


def read_json(path):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, data):
    dest = Path(path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False, allow_nan=False)
        handle.flush()
    tmp.replace(dest)


def portfolio_audit(portfolio):
    stocks = portfolio["stocks"]
    funds = portfolio["mutual_funds"]
    if len({s["isin"] for s in stocks}) != len(stocks):
        raise ValueError("Duplicate stock ISIN - reconcile lots rather than double-count")
    if len({f["position_key"] for f in funds}) != len(funds):
        raise ValueError("Duplicate internal fund position_key")
    for s in stocks:
        if KNOWN_ISINS.get(s["symbol"]) != s["isin"]:
            raise ValueError(f"ISIN mismatch for {s['symbol']}")
        if s["quantity"] <= 0 or s["avg_buy"] <= 0:
            raise ValueError("Invalid stock quantity or average cost")
        if abs(money(s["quantity"] * s["price_close"]) - s["closing_value"]) > 0.01:
            raise ValueError(f"Broker closing value mismatch for {s['symbol']}")
    observed = {"stock_invested": money(sum(s["invested"] for s in stocks)),
                "stock_value": money(sum(s["closing_value"] for s in stocks)),
                "mf_invested": money(sum(f["invested"] for f in funds)),
                "mf_value": money(sum(f["closing_value"] for f in funds))}
    st = portfolio["stock_statement_totals"]
    mf = portfolio["mutual_fund_statement_totals"]
    differences = {
        "stock_invested_rupees": money(st["invested"] - observed["stock_invested"]),
        "stock_value_rupees": money(st["value"] - observed["stock_value"]),
        "mf_invested_rupees": money(mf["invested"] - observed["mf_invested"]),
        "mf_value_rupees": money(mf["value"] - observed["mf_value"]),
    }
    combined = st["value"] + mf["value"]
    exposure = defaultdict(float)
    amc_exposure = defaultdict(float)
    for fund in funds:
        exposure[fund["category"]] += fund["closing_value"]
        amc_exposure[fund["amc"]] += fund["closing_value"]
    tci = next(s["closing_value"] for s in stocks if s["symbol"] == "TCIEXP")
    fund_schemes = defaultdict(list)
    for fund in funds:
        fund_schemes[(fund["amc"], fund["scheme_name"])].append(fund["position_key"])
    return {
        "stocks_count": len(stocks), "mutual_fund_folio_count": len(funds),
        "distinct_mutual_fund_schemes": len(fund_schemes),
        "note_on_same_scheme_folios": "Repeated scheme names across different broker folio rows are not erroneous duplicates.",
        "row_totals": observed, "statement_minus_row_totals": differences,
        "summary_statement_rupees": {
            "invested": money(st["invested"]+mf["invested"]),
            "market_value": money(combined),
            "unrealized_pnl": money(st["unrealized_pnl"]+mf["unrealized_pnl"]),
        },
        "risk_exposures": {
            "tciexp_pct_of_stock_portfolio": round(tci/st["value"]*100, 2),
            "tciexp_pct_of_total_portfolio": round(tci/combined*100, 2),
            "gold_funds_rupees": money(exposure["Gold"]),
            "silver_funds_rupees": money(exposure["Silver"]),
            "gold_silver_pct_of_total_portfolio": round((exposure["Gold"]+exposure["Silver"])/combined*100, 2),
            "mf_categories_rupees": {k:money(v) for k,v in sorted(exposure.items())},
            "mf_amcs_rupees": {k:money(v) for k,v in sorted(amc_exposure.items())},
        },
        "statement_dates": {"stocks":stocks[0]["asof_date"], "mutual_funds":funds[0]["asof_date"]},
        "valuation_date_warning": "Statement dates differ. Not a single-date or executable portfolio valuation.",
        "identity_redaction": "No PAN, phone, client code or true folio numbers in this research export."
    }


def parse_quotes_csv(path, *, require_adjusted=True, permit_synthetic=False):
    """Read one equity CSV. Columns: date,symbol,open,high,low,close,volume,
    adjusted,corporate_actions_checked,source_url,synthetic.
    Prices must already be adjusted (including prices/volume consistency).
    """
    records=[]
    with open(path, encoding="utf-8-sig", newline="") as handle:
        r=csv.DictReader(handle)
        needed={"date","symbol","open","high","low","close","volume","adjusted","corporate_actions_checked","source_url","synthetic"}
        if not needed.issubset(r.fieldnames or []):
            raise ValueError(f"Missing historical columns: {sorted(needed-set(r.fieldnames or []))}")
        for row in r:
            if not row["source_url"]:
                raise ValueError("Source URL required for every historical bar")
            if row["synthetic"].lower()=="true" and not permit_synthetic:
                raise ValueError("Synthetic data cannot be used as market evidence")
            if require_adjusted and (row["adjusted"].lower()!="true" or row["corporate_actions_checked"].lower()!="true"):
                raise ValueError("Adjusted OHLCV and checked corporate actions required for backtesting")
            x={"date":dt.date.fromisoformat(row["date"]),"symbol":row["symbol"],
               "volume":int(row["volume"]),"source_url":row["source_url"],
               "synthetic":row["synthetic"].lower()=="true"}
            for field in ("open","high","low","close"):
                x[field]=float(row[field])
            if any(not math.isfinite(x[f]) or x[f]<=0 for f in ("open","high","low","close")):
                raise ValueError(f"Invalid nonpositive price at {x['date']}")
            if not x["low"] <= min(x["open"],x["close"]) <= max(x["open"],x["close"]) <= x["high"]:
                raise ValueError(f"OHLC inconsistency at {x['date']}")
            if x["volume"]<0:
                raise ValueError("Negative volume")
            records.append(x)
    if not records:
        raise ValueError("No historical bars")
    if any(x["symbol"]!=records[0]["symbol"] for x in records):
        raise ValueError("One symbol per OHLCV file")
    records.sort(key=lambda x:x["date"])
    if len({x["date"] for x in records}) != len(records):
        raise ValueError("Duplicate trading date")
    return records


def sma(v, n):
    return [None if i+1<n else sum(v[i-n+1:i+1])/n for i in range(len(v))]


def ema(v, n):
    if n < 1: raise ValueError("EMA n must be positive")
    out=[]; state=None; k=2/(n+1)
    for i,p in enumerate(v):
        if p is None:
            out.append(None); continue
        if state is None:
            prefix=[q for q in v[:i+1] if q is not None]
            if len(prefix)<n:
                out.append(None); continue
            state=sum(prefix[-n:])/n
        else:
            state=(p-state)*k+state
        out.append(state)
    return out


def rsi(close, n=14):
    out=[None]*len(close)
    if len(close)<n+1:return out
    gains=[max(close[i]-close[i-1],0) for i in range(1,len(close))]
    losses=[max(close[i-1]-close[i],0) for i in range(1,len(close))]
    ag=sum(gains[:n])/n;al=sum(losses[:n])/n
    def calc(g,l):
        if l==0: return 100.0 if g>0 else 50.0
        return 100-100/(1+g/l)
    out[n]=calc(ag,al)
    for i in range(n+1,len(close)):
        ag=(ag*(n-1)+gains[i-1])/n;al=(al*(n-1)+losses[i-1])/n
        out[i]=calc(ag,al)
    return out


def atr(bars,n=14):
    tr=[]
    for i,b in enumerate(bars):
        prev=bars[i-1]["close"] if i else None
        tr.append(max(b["high"]-b["low"],abs(b["high"]-prev),abs(b["low"]-prev)) if prev else b["high"]-b["low"])
    out=[None]*len(bars)
    if len(bars)<n:return out
    state=sum(tr[:n])/n;out[n-1]=state
    for i in range(n,len(bars)):
        state=(state*(n-1)+tr[i])/n;out[i]=state
    return out


def macd(close):
    a,b=ema(close,12),ema(close,26)
    line=[x-y if x is not None and y is not None else None for x,y in zip(a,b)]
    signal=ema(line,9)
    hist=[x-y if x is not None and y is not None else None for x,y in zip(line,signal)]
    return line,signal,hist


def indicators(bars):
    c=[b["close"] for b in bars]
    ma50,ma200=sma(c,50),sma(c,200)
    v20=sma([b["volume"] for b in bars],20)
    line,signal,hist=macd(c)
    a=rsi(c); b=atr(bars)
    return [{"date":x["date"].isoformat(),"close":c[i],"sma50":ma50[i],"sma200":ma200[i],
             "rsi14":a[i],"atr14":b[i],"macd":line[i],"macd_signal":signal[i],
             "macd_hist":hist[i],"avg_volume20":v20[i],"volume":x["volume"],
             "high20": max(z["high"] for z in bars[max(0,i-19):i+1]) if i>=19 else None,
             "low20": min(z["low"] for z in bars[max(0,i-19):i+1]) if i>=19 else None}
            for i,x in enumerate(bars)]


def verify_fundamentals(row, *, is_bank, asof):
    """Missing data remains WAIT, never assumed zero or a fabricated score."""
    required=["symbol","period_end","filed_at_ist","filing_url","financials","analyst_reports"]
    missing=[k for k in required if k not in row or not row[k]]
    if missing: return {"ok":False,"missing":missing}
    if not str(row["filing_url"]).startswith("https://"):
        return {"ok":False,"missing":["valid_primary_filing_url"]}
    filed=dt.datetime.fromisoformat(row["filed_at_ist"])
    if filed.tzinfo is None or filed.astimezone(IST)>asof:
        return {"ok":False,"missing":["source_published_by_asof_with_timezone"]}
    fields=(["roa","nim","gnpa","nnpa","cet1","deposit_growth","credit_growth","provisions"] if is_bank
            else ["revenue_growth_3y","eps_growth_3y","roce","roe","operating_cashflow","free_cashflow","net_debt_to_ebitda","pe"])
    missing_fields=[k for k in fields if not isinstance(row["financials"].get(k), (int,float))]
    if missing_fields:return {"ok":False,"missing":missing_fields}
    return {"ok":True,"missing":[]}


def valid_quote(quote, asof, max_age_minutes=30):
    if not quote or not all(k in quote for k in ("price","time_ist","exchange","source_url","symbol")):
        return False,"QUOTE_FIELDS_MISSING"
    qtime=dt.datetime.fromisoformat(quote["time_ist"])
    if qtime.tzinfo is None:return False,"QUOTE_TIMEZONE_MISSING"
    lag=(asof-qtime.astimezone(IST)).total_seconds()/60
    if lag<0 or lag>max_age_minutes:return False,"QUOTE_STALE_OR_FUTURE"
    if quote["exchange"] not in ("NSE","BSE") or not quote["source_url"]:
        return False,"EXCHANGE_PROVENANCE_MISSING"
    if not isinstance(quote["price"],(int,float)) or quote["price"]<=0:return False,"QUOTE_INVALID"
    if quote.get("synthetic",False):return False,"SYNTHETIC_PRICE"
    return True,"QUOTE_CURRENT_FOR_RESEARCH_ONLY"


def position_size(*, entry, review_exit, free_cash, cap_fraction, risk_fraction,
                  existing_exposure=0.0, portfolio_total=None, max_weight_after=0.15):
    """All quantities whole shares, non-leveraged. REVIEW EXIT IS NOT A GUARANTEED FILL."""
    args=[entry,review_exit,free_cash,cap_fraction,risk_fraction]
    if any(not isinstance(x,(int,float)) or not math.isfinite(x) for x in args):
        raise ValueError("All sizing inputs must be finite numerical values")
    if not (0<review_exit<entry) or free_cash<0 or not (0<cap_fraction<=1) or not (0<risk_fraction<=1):
        raise ValueError("Invalid entry/exit/capital/assumptions")
    if portfolio_total is not None and portfolio_total<=0:raise ValueError("Invalid portfolio total")
    per_share_risk=entry-review_exit
    limits={"cash_shares":math.floor(free_cash/entry),
            "position_cap_shares":math.floor(free_cash*cap_fraction/entry),
            "risk_budget_shares":math.floor(free_cash*risk_fraction/per_share_risk)}
    if portfolio_total is not None:
        remaining=max(0,(portfolio_total+free_cash)*max_weight_after-existing_exposure)
        limits["max_portfolio_weight_shares"]=math.floor(remaining/entry)
    q=max(0,min(limits.values()))
    return {"candidate_shares":q,"candidate_notional_rupees":money(q*entry),
            "planned_exit_risk_rupees":money(q*per_share_risk),
            "loss_if_15pct_gap_below_review_exit_rupees":money(q*(entry-review_exit*0.85)),
            "risk_budget_rupees":money(free_cash*risk_fraction),"binding_limits_shares":limits,
            "requires_manual_review":True}


def evaluate_candidate(*, quote=None, fundamental=None, technical=None, news_verified=False,
                       analyst_verified=False, available_cash=None, one_month_reserve=None,
                       planned_entry=None, review_exit=None, is_bank=False, asof=None):
    asof=asof or dt.datetime.now(IST)
    fail=[]
    ok,why=valid_quote(quote,asof)
    if not ok:fail.append(why)
    if fundamental is None:fail.append("FUNDAMENTALS_MISSING")
    else:
        v=verify_fundamentals(fundamental,is_bank=is_bank,asof=asof)
        if not v["ok"]:fail.append("FUNDAMENTALS_INCOMPLETE:"+",".join(v["missing"]))
    if not technical or technical.get("sma200") is None or technical.get("atr14") is None:
        fail.append("TECHNICAL_HISTORY_INCOMPLETE")
    if not news_verified:fail.append("NEWS_NOT_INDEPENDENTLY_VERIFIED")
    if not analyst_verified:fail.append("DATED_ANALYST_VIEWS_NOT_VERIFIED")
    if any(not isinstance(v,(int,float)) for v in (available_cash,one_month_reserve)):
        fail.append("FREE_CASH_AND_ONE_MONTH_RESERVE_UNKNOWN")
    if planned_entry is None or review_exit is None:fail.append("ENTRY_EXIT_NOT_DEFINED")
    if fail:return {"decision":"WAIT","candidate_shares":0,"reasons":fail,"real_trading_authorized":False}
    free=max(0,available_cash-one_month_reserve)
    sized=position_size(entry=planned_entry,review_exit=review_exit,free_cash=free,
                        cap_fraction=0.10,risk_fraction=0.01)
    if sized["candidate_shares"]<=0:return {"decision":"WAIT","candidate_shares":0,"reasons":["SIZING_ZERO"],"real_trading_authorized":False}
    return {"decision":"RESEARCH CANDIDATE - HUMAN REVIEW","reasons":[],
            **sized,"real_trading_authorized":False}


def performance(equity, bars=None):
    if len(equity)<2 or equity[0]<=0:raise ValueError("Insufficient equity")
    returns=[equity[i]/equity[i-1]-1 for i in range(1,len(equity))]
    years=(bars[-1]["date"]-bars[0]["date"]).days/365.25 if bars else len(equity)/252
    cagr=(equity[-1]/equity[0])**(1/years)-1 if years>0 else None
    peak=equity[0];mdd=0
    for x in equity:
        peak=max(peak,x);mdd=min(mdd,x/peak-1)
    sd=statistics.stdev(returns) if len(returns)>1 else 0
    down=[min(x,0) for x in returns]
    downside=math.sqrt(sum(x*x for x in down)/len(down))
    return {"total_return_pct":round((equity[-1]/equity[0]-1)*100,3),
            "cagr_pct":round(cagr*100,3) if cagr is not None else None,
            "max_drawdown_pct":round(mdd*100,3),
            "volatility_annual_pct":round(sd*math.sqrt(252)*100,3),
            "sharpe_zero_rf":round(statistics.mean(returns)/sd*math.sqrt(252),3) if sd else None,
            "sortino_zero_target":round(statistics.mean(returns)/downside*math.sqrt(252),3) if downside else None,
            "note":"zero-risk-free-rate comparison; cannot infer investment suitability"}


def report(portfolio,asof=None):
    audit=portfolio_audit(portfolio)
    return {"generated_at_ist":(asof or dt.datetime.now(IST)).isoformat(),
            "portfolio":audit,"system_status": "HOLDINGS VERIFIED TO STATEMENT DATES; LIVE RESEARCH DATA NOT CONNECTED",
            "holding_decisions":[{"symbol":x["symbol"],"status":"WAIT - CURRENT EVIDENCE REQUIRED","new_buy_quantity":0} for x in portfolio["stocks"]],
            "disclaimer":"Informational research system, not an execution service. No trade placement capability."}


def signal_for_strategy(strategy, bars, ind, idx, *, fundamental_snapshots=None, earnings_events=None):
    """Point-in-time signal at CLOSE of idx. Execution not before NEXT session open.

    Strategy A: quality+valuation+momentum snapshot, with explicit PIT filing time.
    Strategy B: verified earnings surprise event AFTER market's awareness of event.
    Strategy C: 200d rising trend / 50d moving average.
    No guess on missing point-in-time data.
    """
    b=bars[idx]; v=ind[idx]
    if strategy == "trend_200d_atr":
        if idx<204 or v["sma200"] is None or ind[idx-5]["sma200"] is None:return None
        if b["close"]>v["sma200"] and v["sma200"]>ind[idx-5]["sma200"] and b["close"]>v["sma50"]:
            return "BUY"
        return "SELL" if b["close"]<v["sma200"] or b["close"]<v["sma50"] else None
    elif strategy=="quality_valuation_momentum":
        snaps=fundamental_snapshots or []
        d=b["date"].isoformat()
        candidates=[s for s in snaps if s.get("published_date", "9999")<=d]
        if not candidates:return None
        snap=max(candidates,key=lambda s:s["published_date"])
        if not snap.get("source_url") or not snap.get("point_in_time_confirmed"):
            return None
        if any(k not in snap for k in ("quality_score","valuation_score")):return None
        if idx<200 or v["sma200"] is None:return None
        if snap["quality_score"]>=70 and snap["valuation_score"]>=55 and b["close"]>v["sma200"]:
            return "BUY"
        if snap["quality_score"]<45 or b["close"]<v["sma200"]:return "SELL"
        return None
    elif strategy=="earnings_event":
        events=earnings_events or []
        d=b["date"].isoformat()
        # Must use verified filing availability as-of close, not subsequent revisions.
        e=[x for x in events if x.get("available_to_trade_date")==d and x.get("filing_url") and x.get("verified")]
        if not e:return None
        event=e[-1]
        if event.get("profit_surprise_pct",0)>=10 and event.get("revenue_surprise_pct",0)>=5:
            return "BUY"
        if event.get("profit_surprise_pct",0)<-10:return "SELL"
        return None
    raise ValueError("Unknown strategy")


def backtest_strategy(bars, *, strategy, fundamental_snapshots=None, earnings_events=None,
                      initial_cash=100000, round_trip_fee_fraction=0.002,
                      slippage_fraction=0.001, max_deployed_fraction=0.5,
                      max_holding_days=20, start_date=None, end_date=None,
                      allow_synthetic=False):
    """Three strategies with no same-close execution, cash-only, deterministic fills.
    Fees are explicit model assumptions, not broker verified charges.
    Includes a gap-aware trailing ATR risk exit and timed event exit.
    """
    if any(b.get("synthetic") for b in bars) and not allow_synthetic:
        raise ValueError("Synthetic price data cannot produce historical trading evidence")
    if len(bars)<205:raise ValueError("Insufficient history / warm-up")
    if not 0<=round_trip_fee_fraction<0.1 or not 0<=slippage_fraction<0.1:
        raise ValueError("Invalid cost assumptions")
    if not 0<max_deployed_fraction<=1:raise ValueError("Invalid deployment cap")
    prices=indicators(bars)
    cash=float(initial_cash);position=0;stop=None;pending=None;last_buy_idx=None
    trade_records=[];equity_rows=[];completed=[];entry_spend=0;turnover=0;fee=round_trip_fee_fraction/2
    for i,b in enumerate(bars):
        date=b["date"]
        can_enter=start_date is None or date>=start_date
        should_track=end_date is None or date<=end_date
        if not should_track:break
        if pending=="BUY" and position==0 and can_enter:
            price=b["open"]*(1+slippage_fraction)
            n=math.floor((cash*max_deployed_fraction)/(price*(1+fee)))
            if n:
                spend=n*price*(1+fee)
                cash-=spend;position=n;entry_spend=spend;last_buy_idx=i;turnover+=n*price
                a=prices[i-1]["atr14"] if i else None
                stop=price-2.5*a if a is not None else None
                trade_records.append({"date":date.isoformat(),"action":"BUY","shares":n,"fill":money(price),"fee_rupees":money(n*price*fee)})
        elif pending=="SELL" and position:
            p=b["open"]*(1-slippage_fraction)
            net=position*p*(1-fee);cash+=net;turnover+=position*p
            completed.append(money(net-entry_spend))
            trade_records.append({"date":date.isoformat(),"action":"SELL_SIGNAL","shares":position,"fill":money(p),"fee_rupees":money(position*p*fee)})
            position=0;stop=None;last_buy_idx=None
        pending=None
        if position and stop is not None and b["low"]<=stop:
            p=min(b["open"],stop)*(1-slippage_fraction)
            net=position*p*(1-fee);cash+=net;turnover+=position*p
            completed.append(money(net-entry_spend))
            trade_records.append({"date":date.isoformat(),"action":"SELL_STOP_GAP_AWARE","shares":position,"fill":money(p),"fee_rupees":money(position*p*fee)})
            position=0;stop=None;last_buy_idx=None
        equity=cash+position*b["close"]
        if can_enter:equity_rows.append({"date":date.isoformat(),"equity":equity})
        if i+1>=len(bars) or not should_track:continue
        if position:
            aa=prices[i]["atr14"]
            if aa is not None:stop=max(stop or 0,b["close"]-2.5*aa)
            exit_signal=signal_for_strategy(strategy,bars,prices,i,fundamental_snapshots=fundamental_snapshots,earnings_events=earnings_events)
            if exit_signal=="SELL" or (strategy=="earnings_event" and last_buy_idx is not None and i-last_buy_idx>=max_holding_days):
                pending="SELL"
        else:
            enter_signal=signal_for_strategy(strategy,bars,prices,i,fundamental_snapshots=fundamental_snapshots,earnings_events=earnings_events)
            if enter_signal=="BUY":pending="BUY"
    if not equity_rows:raise ValueError("No scored trading days")
    e=[x["equity"] for x in equity_rows]
    if len(e)<2:raise ValueError("Need at least two test dates")
    span=[{"date":dt.date.fromisoformat(x["date"])} for x in equity_rows]
    perf=performance(e,span)
    perf.update({"completed_round_trips":len(completed),
                 "win_rate_pct":round(sum(p>0 for p in completed)/len(completed)*100,2) if completed else None,
                 "profit_factor":(round(sum(p for p in completed if p>0)/(-sum(p for p in completed if p<0)),3) if sum(p for p in completed if p<0)<0 else None),
                 "traded_notional_rupees":money(turnover),
                 "open_position_at_end":position})
    return {"strategy":strategy,"assumptions":{"initial_cash":initial_cash,"round_trip_fee_fraction":round_trip_fee_fraction,"slippage_fraction":slippage_fraction,"portfolio_deployment_cap":max_deployed_fraction},"synthetic":any(b.get("synthetic") for b in bars),"trades":trade_records,"curve":equity_rows,"performance":perf,"execution":"signals at close; fills at next open; stop gaps priced at open if worse"}


def walk_forward(bars, *, strategy, fundamental_snapshots=None, earnings_events=None,
                 train_days=300,test_days=65,step_days=65,allow_synthetic=False, **cost_args):
    """Holdout windows do not choose parameters on holdout data.
    The strategy/rules are fixed BEFORE test. Train fold is reported for transparency.
    Supports 5-yr data only when actual data present; no survivorship-bias claim.
    """
    if train_days<205 or test_days<10 or step_days<=0:raise ValueError("Insufficient fold length")
    folds=[]
    for cut in range(train_days,len(bars)-test_days+1,step_days):
        train=bars[:cut]
        future_end=cut+test_days
        prior=bars[max(0,cut-205):future_end]
        train_result=backtest_strategy(train,strategy=strategy,fundamental_snapshots=fundamental_snapshots,
            earnings_events=earnings_events,allow_synthetic=allow_synthetic,**cost_args)
        # Forward segment gets prior close+indicator warmup but no past positions carried in.
        # Earliest signal may execute within forward test period only.
        test_result=backtest_strategy(bars[:future_end],strategy=strategy,
            fundamental_snapshots=fundamental_snapshots,earnings_events=earnings_events,
            start_date=bars[cut]["date"],allow_synthetic=allow_synthetic,**cost_args)
        # Starting simulation at future start cannot carry hypothetical prior holdings;
        # equity returns are measured only on post-cut dates.
        folds.append({"train_end":bars[cut-1]["date"].isoformat(),
                      "test_start":bars[cut]["date"].isoformat(),
                      "test_end":bars[future_end-1]["date"].isoformat(),
                      "train_cagr_pct":train_result["performance"]["cagr_pct"],
                      "test_cagr_pct":test_result["performance"]["cagr_pct"],
                      "test_max_drawdown_pct":test_result["performance"]["max_drawdown_pct"],
                      "test_completed_round_trips":test_result["performance"]["completed_round_trips"]})
    return {"strategy":strategy,"method":"fixed-rule expanding training / unseen forward windows","folds":folds,
            "status":"SYNTHETIC QA ONLY" if allow_synthetic else "RESEARCH - REQUIRES SURVIVORSHIP/POINT-IN-TIME AUDIT"}


def benchmark_buyhold(bars, *, initial_cash=100000, buy_fee=0.001, sell_fee=0.001):
    p0=bars[0]["open"]*(1+buy_fee)
    q=math.floor(initial_cash/p0)
    cash=initial_cash-q*p0
    final=cash+q*bars[-1]["close"]*(1-sell_fee)
    return {"total_return_pct":round((final/initial_cash-1)*100,3),
            "shares":q,"start_date":bars[0]["date"].isoformat(),"end_date":bars[-1]["date"].isoformat(),
            "warning":"Compare only matching dates, consistent corporate-action adjustments and identical costs."}
