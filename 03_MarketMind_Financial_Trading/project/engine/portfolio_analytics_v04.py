"""Portfolio analytics v0.4: evidence-aware calculations; no prices fetched or orders placed.

Missing cash flow history must never be inferred from unrealized profit or a current snapshot.
Underlying mutual fund holdings are not known from a category/AMC label.
"""
from __future__ import annotations
import csv
import datetime as dt
import math
from collections import defaultdict
from pathlib import Path


def _finite(v, name):
    if isinstance(v, bool) or not isinstance(v, (int,float)) or not math.isfinite(v):
        raise ValueError(f"{name} must be a finite number")
    return float(v)


def xirr(flows:list[tuple[str, float]], *, tol=1e-10) -> float:
    """Money-weighted annual return as decimal. Negative investments, positive distributions/terminal value.

    Excel-style ACT/365 date convention; needs dated genuine transactions and terminal valuation.
    Rejects multiple sign changes (potential multiple IRRs) rather than selecting an arbitrary root.
    """
    if len(flows)<2: raise ValueError("XIRR needs dated investment(s) and value distribution(s)")
    agg=defaultdict(float)
    for date_str,amount in flows:
        d=dt.date.fromisoformat(date_str)
        agg[d]+=_finite(amount,'flow amount')
    seq=sorted((d,v) for d,v in agg.items() if abs(v)>1e-10)
    if len(seq)<2 or seq[0][0]==seq[-1][0]:raise ValueError('XIRR needs multiple distinct cash-flow dates')
    amounts=[x[1] for x in seq]
    if not (min(amounts)<0<max(amounts)): raise ValueError('XIRR requires both investment and distribution/terminal value')
    signs=[1 if v>0 else -1 for v in amounts]
    if sum(a!=b for a,b in zip(signs,signs[1:]))!=1:
        raise ValueError('Ambiguous nonconventional cash flows: multiple IRR roots possible')
    start=seq[0][0]; times=[(d-start).days/365.0 for d,v in seq]
    def f(rate):
        return math.fsum(v/math.exp(t*math.log1p(rate)) for v,t in zip(amounts,times))
    low=-0.999999; high=1.0
    fl=f(low); fh=f(high)
    while (fl>0)==(fh>0) and high<1e8:
        high=high*2+1;fh=f(high)
    if (fl>0)==(fh>0): raise ValueError('XIRR root not bracketed within defensible range')
    for _ in range(240):
        mid=(low+high)/2;fm=f(mid)
        if abs(fm)<tol or high-low<1e-12:return mid
        if (fm>0)==(fl>0):low=mid;fl=fm
        else:high=mid
    return (low+high)/2


def time_weighted_return(periods:list[dict]) -> dict:
    """Returns of successive intervals: all contributions/withdrawals occur at interval END.

    `end_value` is after the end-of-period flow; `flow_end` positive for deposit.
    Accurate TWR requires valuations at every actual contribution/withdrawal boundary.
    """
    if not periods:raise ValueError('TWR needs valuation intervals')
    growth=1.0;details=[];previous_end=None
    for idx,p in enumerate(periods):
        start=_finite(p['start_value'],'start_value');end=_finite(p['end_value'],'end_value')
        flow=_finite(p.get('flow_end',0),'flow_end')
        if start<=0 or end<0 or end-flow<0:raise ValueError('Invalid TWR valuation/withdrawal')
        if previous_end is not None and abs(start-previous_end)>0.01:raise ValueError('TWR intervals are discontinuous')
        period_return=(end-flow)/start-1
        if period_return < -1:raise ValueError('Impossible period loss below -100%')
        growth*=(1+period_return)
        details.append({'period':idx+1,'simple_return':period_return})
        previous_end=end
    return {'twr_total_return':growth-1,'periods':details,
            'assumption':'External cash flows at period end; rebalance/valuations needed on every cash-flow date'}


def concentration(portfolio:dict)->dict:
    """Holding-vehicle HHI, NOT the portfolio's underlying company diversification."""
    stocks=portfolio['stocks'];funds=portfolio['mutual_funds'];
    values=[_finite(x['closing_value'],'stock') for x in stocks]+[_finite(x['closing_value'],'fund') for x in funds]
    if not values or min(values)<0 or sum(values)<=0:raise ValueError('Portfolio values must be nonnegative and nonzero')
    total=sum(values); weights=[v/total for v in values]
    scheme_values=defaultdict(float)
    for s in stocks: scheme_values[('DIRECT',s['isin'])]+=s['closing_value']
    for f in funds:scheme_values[(f['amc'],f['scheme_name'])]+=f['closing_value']
    scheme_hhi=sum((x/total)**2 for x in scheme_values.values())
    cats=defaultdict(float)
    for s in stocks:cats['Direct equities']+=s['closing_value']
    for f in funds:cats[f['category']]+=f['closing_value']
    return {'total_line_item_value_rupees':round(total,2),
            'hhi_vehicle_line_items':round(sum(w*w for w in weights),6),
            'effective_vehicle_positions':round(1/sum(w*w for w in weights),3),
            'hhi_consolidated_scheme_positions':round(scheme_hhi,6),
            'effective_consolidated_scheme_positions':round(1/scheme_hhi,3),
            'distinct_direct_stocks_plus_fund_schemes':len(scheme_values),
            'top_3_line_item_pct':round(sum(sorted(weights,reverse=True)[:3])*100,2),
            'category_shares_pct':{k:round(v/total*100,2) for k,v in sorted(cats.items())},
            'limitations':['Fund folio rows are independent holdings records; repeated identical schemes inflate vehicle count.',
                'This is NOT underlying stock look-through or true geographic/sector diversification.',
                'Broker snapshots cover potentially different dates; no live portfolio weights']}


def scenario_analysis(portfolio:dict, shocks:dict[str,float])->dict:
    """Illustrative shock assumptions only, not forecasts/VaR. key 'Direct equities' and MF categories."""
    conc=concentration(portfolio); categories=conc['category_shares_pct'];total=conc['total_line_item_value_rupees'];
    known=set(categories)
    if set(shocks)!=known:raise ValueError(f'Scenario requires precisely these category keys: {sorted(known)}')
    for k,v in shocks.items():
        _finite(v,k)
        if not -1<=v<=5:raise ValueError('Shock fraction must be between -100% and +500%')
    catval=defaultdict(float)
    for s in portfolio['stocks']:catval['Direct equities']+=s['closing_value']
    for f in portfolio['mutual_funds']:catval[f['category']]+=f['closing_value']
    delta=math.fsum(v*shocks[k] for k,v in catval.items())
    return {'scenario_only':True,'base_value_rupees':round(total,2),'scenario_value_rupees':round(total+delta,2),
            'scenario_pnl_rupees':round(delta,2),'portfolio_impact_pct':round(delta/total*100,2),
            'shock_by_category':dict(shocks),
            'warning':'Hypothetical simultaneous shocks on two-dated broker values; ignores taxes, FX and cross-fund constituent effects'}


def fund_overlap(holdings_a:list[dict],holdings_b:list[dict], *, max_age_days=100, asof_date:str):
    """Percent stock-overlap= sum(min(wA,wB)), when both official underlying holdings lists are full/current.

    Dict list each: isin, weight_pct, published_date, source_url; no copying third-party proprietary scores.
    """
    asof=dt.date.fromisoformat(asof_date)
    def convert(rows):
        if not rows:raise ValueError('No underlying scheme holdings supplied')
        result={};total=0.
        for r in rows:
            k=r.get('isin','')
            if len(k)!=12 or not k.isalnum() or k in result:raise ValueError('Invalid/duplicate underlying ISIN')
            w=_finite(r.get('weight_pct'),'constituent weight')
            if not 0<=w<=100:raise ValueError('Invalid constituent weight')
            published=dt.date.fromisoformat(r['published_date'])
            if (asof-published).days<0 or (asof-published).days>max_age_days:raise ValueError('Stale or future scheme holdings')
            if not str(r.get('source_url','')).startswith('https://'):raise ValueError('Official/approved source URL required')
            result[k]=w;total+=w
        if not 99.0<=total<=100.5:raise ValueError('Incomplete holdings weight coverage; look-through rejected')
        return result
    aa=convert(holdings_a);bb=convert(holdings_b)
    return {'common_constituents':len(set(aa)&set(bb)),
            'overlap_pct_of_each_fund':round(sum(min(v,bb.get(k,0)) for k,v in aa.items()),3),
            'method':'sum minimum weights on matching company ISINs',
            'limitation':'Only as accurate as supplied dated holdings; ETFs/FoFs require look-through through each level'}


def portfolio_enhancement_report(portfolio:dict)->dict:
    """Uses ONLY broker snapshots. Does not guess history or pretend expense/tax/market metrics exist."""
    c=concentration(portfolio)
    shocks={k:(-0.18 if k=='Direct equities' else -0.22 if k in ('ELSS','Small Cap','Thematic','Sectoral') else -0.10 if k=='Gold' else -0.25 if k=='Silver' else -0.2) for k in c['category_shares_pct']}
    return {'engine_version':'0.4','portfolio_concentration':c,
            'hypothetical_recession_and_metals_shock':scenario_analysis(portfolio,shocks),
            'xirr':{'status':'NOT CALCULABLE FROM HOLDINGS SNAPSHOT','reason':'Dated purchases/sales/dividends/SIPs/withdrawals needed'},
            'twr':{'status':'NOT CALCULABLE FROM HOLDINGS SNAPSHOT','reason':'Dated portfolio valuations at external cash-flow boundaries needed'},
            'mutual_fund_underlying_overlap':{'status':'NOT CALCULABLE FROM MF SCHEME NAMES','reason':'Need dated scheme-wise underlying holdings and ISIN weights'},
            'recommendations':{'status':'WAIT / DATA INCOMPLETE','orders_placed':0}}
