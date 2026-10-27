import csv
import json
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from test_engine import bars
root=Path(__file__).resolve().parents[1]
out=root/'samples'/'SYNTHETIC_ONLY_TESTONLY_adjusted.csv'
with out.open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f)
    w.writerow(['date','symbol','open','high','low','close','volume','adjusted','corporate_actions_checked','source_url','synthetic'])
    for b in bars(440):
        w.writerow([b['date'],b['symbol'],b['open'],b['high'],b['low'],b['close'],b['volume'],'true','true',b['source_url'],'true'])
start=bars(440)[250]['date'].isoformat()
(root/'samples'/'SYNTHETIC_ONLY_earnings_events.json').write_text(json.dumps([{
    'available_to_trade_date':start,'verified':True,
    'filing_url':'https://example.invalid/test-fixture',
    'profit_surprise_pct':20,'revenue_surprise_pct':10}],indent=2))
(root/'samples'/'SYNTHETIC_ONLY_pit_fundamentals.json').write_text(json.dumps([{
    'published_date':'2024-01-01','source_url':'https://example.invalid/test-fixture',
    'point_in_time_confirmed':True,'quality_score':80,'valuation_score':70}],indent=2))
print('Synthetic test fixtures built')
