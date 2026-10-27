"""Conservative and transparent price/volume back adjustment of approved stock splits/bonus.
No dividend/rights/merger adjustments or official action completeness are inferred.
Input is a dated, manually approved issuer/exchange-backed ledger, not AI guesses.
"""
from __future__ import annotations
import argparse,csv,datetime as dt,json,math
from pathlib import Path
from market_engine import KNOWN_ISINS,save_json

FIELDS=['date','symbol','open','high','low','close','volume','adjusted','corporate_actions_checked','source_url','synthetic']

def review_approved(review,*,symbol,isin,start,end):
    if review.get('symbol')!=symbol or review.get('isin')!=isin:raise ValueError('Review not for the matching instrument')
    if review.get('status')!='HUMAN_REVIEWED_APPROVED':raise ValueError('Corporate action review not approved')
    if not str(review.get('official_source_url','')).startswith('https://'):raise ValueError('Official source reference missing')
    if dt.date.fromisoformat(review['reviewed_through_date'])<end:raise ValueError('Review ends before last data date')
    if dt.date.fromisoformat(review['covered_from_date'])>start:raise ValueError('Review starts after history')
    events=review.get('events',[])
    seen=set()
    for ev in events:
        if ev.get('type') not in ('SPLIT','BONUS'):
            raise ValueError('Unsupported adjustment event; rights/dividend/merger requires separate review')
        day=dt.date.fromisoformat(ev['ex_date'])
        if day in seen:raise ValueError('Multiple actions on same ex-date require consolidated review')
        seen.add(day)
        if not str(ev.get('official_source_url','')).startswith('https://'):raise ValueError('Event official source URL missing')
        if not isinstance(ev.get('shares_after_per_share_before'),(float,int)) or ev['shares_after_per_share_before']<=0:
            raise ValueError('Invalid corporate action share ratio')
        if day>end:raise ValueError('Future event cannot be included in this adjustment')
    return events

def adjust_raw(raw:Path,review_json:Path,output:Path)->dict:
    with raw.open(encoding='utf-8',newline='') as f:rows=list(csv.DictReader(f))
    if not rows:raise ValueError('No raw series')
    for row in rows:
        if row.get('adjusted','').lower()!='false':raise ValueError('Only raw unadjusted bars accepted')
        if row.get('synthetic','').lower()!='false':raise ValueError('Synthetic history not approved')
        if row.get('exchange')!='NSE' or not row.get('source_file_sha256') or row.get('origin_confirmed','').lower()!='true':raise ValueError('NSE source origin not verified; cannot approve adjustments')
    sym=rows[0]['symbol'];isin=rows[0]['isin']
    if KNOWN_ISINS.get(sym)!=isin or any(x['symbol']!=sym or x['isin']!=isin for x in rows):raise ValueError('Identity mismatch')
    rows.sort(key=lambda x:x['date'])
    dates=[dt.date.fromisoformat(x['date']) for x in rows]
    if len(set(dates))!=len(dates):raise ValueError('Duplicate dates')
    review=json.loads(review_json.read_text(encoding='utf-8'))
    events=review_approved(review,symbol=sym,isin=isin,start=dates[0],end=dates[-1])
    records=[]
    for row,day in zip(rows,dates):
        factor=math.prod(ev['shares_after_per_share_before'] for ev in events if day<dt.date.fromisoformat(ev['ex_date']))
        # Back-adjust raw earlier dates for later splits/bonus; adjusted historical volume reflects share-count equivalence.
        records.append({'date':row['date'],'symbol':sym,
                        **{k:float(row[k])/factor for k in ('open','high','low','close')},
                        'volume':round(int(float(row['volume']))*factor),
                        'adjusted':'true','corporate_actions_checked':'true',
                        'source_url':row['source_url'],'synthetic':'false'})
    output.parent.mkdir(parents=True,exist_ok=True)
    tmp=output.with_suffix('.partial')
    with tmp.open('w',newline='',encoding='utf-8') as f:
        wr=csv.DictWriter(f,FIELDS);wr.writeheader();wr.writerows(records)
    tmp.replace(output)
    receipt={'symbol':sym,'isin':isin,'start_date':dates[0].isoformat(),'end_date':dates[-1].isoformat(),
             'bars':len(records),'events_applied':len(events),'review_source':str(review_json),
             'official_review_url':review['official_source_url'],
             'limitations':'Split/bonus share-factor adjusted ONLY. Dividends, rights, mergers, delistings, total-return and survivorship biases are NOT resolved; not automatically strategy-production ready.',
             'output':str(output)}
    save_json(output.with_suffix('.audit.json'),receipt)
    return receipt

def main(argv=None):
    p=argparse.ArgumentParser()
    p.add_argument('--raw',required=True);p.add_argument('--review',required=True);p.add_argument('--out',required=True)
    a=p.parse_args(argv)
    print(json.dumps(adjust_raw(Path(a.raw),Path(a.review),Path(a.out)),indent=2))
if __name__=='__main__':main()
