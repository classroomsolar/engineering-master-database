"""Fail-closed prerequisites for non-synthetic strategy backtests.

This is a validation of review *records*, not independent assurance the
human-reviewed source is correct. It is not an algorithm-profitability claim.
"""
from __future__ import annotations
import csv
import datetime as dt
import hashlib
import json
from pathlib import Path

OFFICIAL_EXCHANGES=('https://www.nseindia.com/','https://www.niftyindices.com/','https://www.bseindia.com/')


def verify_backtest_input(price_file:Path,review_file:Path)->dict:
    data=Path(price_file).read_bytes();digest=hashlib.sha256(data).hexdigest()
    if not Path(review_file).exists():raise FileNotFoundError('Full historical price review JSON required')
    review=json.loads(Path(review_file).read_text(encoding='utf-8'))
    expected={'status':'HUMAN_REVIEWED_COMPLETE','file_sha256':digest,
              'adjustment_scope':'ALL_RELEVANT_PRICE_ACTIONS_AND_CASH_DIVIDENDS_RECONCILED',
              'point_in_time_verified':True,'source_historical_data_reviewed':True,
              'rights_and_licensing_confirmed':True}
    for k,v in expected.items():
        if review.get(k)!=v:raise ValueError(f'Real history review incomplete: {k}')
    urls=review.get('primary_sources',[])
    if not isinstance(urls,list) or not urls or any(not isinstance(u,str) or not u.startswith(OFFICIAL_EXCHANGES) for u in urls):
        raise ValueError('Official exchange/issuer source URL required')
    if not review.get('reviewed_by') or not review.get('reviewed_at_ist'):
        raise ValueError('Dated human review record missing')
    with Path(price_file).open(encoding='utf-8-sig',newline='') as file:
        reader=csv.DictReader(file)
        if not reader.fieldnames or 'date' not in reader.fieldnames or 'symbol' not in reader.fieldnames:
            raise ValueError('Price identity/date columns missing')
        dates=[];syms=set()
        for row in reader:
            dates.append(dt.date.fromisoformat(row['date']))
            syms.add(row['symbol'])
    if not dates or len(syms)!=1:raise ValueError('One nonempty symbol history required')
    if review.get('symbol')!=next(iter(syms)) or review.get('covered_from_date')>min(dates).isoformat() or review.get('reviewed_through_date')<max(dates).isoformat():
        raise ValueError('Human review must cover entire instrument/date range')
    return {'status':'HUMAN_REVIEW_RECORD_PRESENT_NOT_INDEPENDENT_AUDIT','symbol':next(iter(syms)),
            'source_file_sha256':digest,'period_start':min(dates).isoformat(),'period_end':max(dates).isoformat(),
            'reviewed_by':review['reviewed_by'],'limitations':'Manual review assertions are NOT independently corroborated by software. Still audit benchmark, costs, universe survivorship, and P&L.'}
