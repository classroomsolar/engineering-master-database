import copy
import csv
import datetime as dt
import json
import math
import os
import tempfile
import unittest
from pathlib import Path

from market_engine import (IST,read_json,portfolio_audit,position_size,sma,ema,rsi,atr,
    indicators,parse_quotes_csv,valid_quote,evaluate_candidate,backtest_strategy,
    walk_forward,benchmark_buyhold,signal_for_strategy)
from pdf_pipeline import register,validate_and_purge,overdue_jobs

ROOT=Path(__file__).resolve().parents[1]


def bars(n=420, *, synthetic=True):
    cur=dt.date(2024,1,1)
    out=[]
    for i in range(n):
        while cur.weekday()>4:cur+=dt.timedelta(days=1)
        # Deterministic trend + reversal; NEVER a real NSE ticker's historical price.
        close=100+i*0.07 + 3*math.sin(i/11) + (15 if 255<i<300 else 0)
        start=close-0.15
        out.append({'date':cur,'symbol':'TESTONLY','open':start,'high':close+1.2,
                    'low':close-1.4,'close':close,'volume':12000+i*3,
                    'source_url':'https://example.invalid/synthetic','synthetic':synthetic})
        cur+=dt.timedelta(days=1)
    return out


class EngineTests(unittest.TestCase):
    def test_01_portfolio_snapshot_and_recon(self):
        a=portfolio_audit(read_json(ROOT/'data/portfolio_statement_snapshot.json'))
        self.assertEqual((a['stocks_count'],a['mutual_fund_folio_count']),(6,18))
        self.assertEqual(a['summary_statement_rupees']['market_value'],2349296.92)
        self.assertEqual(a['statement_minus_row_totals']['stock_invested_rupees'],4.35)
        self.assertEqual(a['statement_minus_row_totals']['mf_value_rupees'],0.02)
        self.assertEqual(a['risk_exposures']['gold_funds_rupees'],784285.92)
        self.assertEqual(a['risk_exposures']['silver_funds_rupees'],299126.04)

    def test_02_duplicate_isin_rejected(self):
        p=read_json(ROOT/'data/portfolio_statement_snapshot.json')
        p['stocks'].append(copy.deepcopy(p['stocks'][0]))
        with self.assertRaises(ValueError):portfolio_audit(p)

    def test_03_identity_mismatch_rejected(self):
        p=read_json(ROOT/'data/portfolio_statement_snapshot.json')
        p['stocks'][0]['isin']='INE000000000'
        with self.assertRaises(ValueError):portfolio_audit(p)

    def test_04_position_size_dimensionally_correct(self):
        x=position_size(entry=200,review_exit=190,free_cash=100000,
                        cap_fraction=0.1,risk_fraction=0.01)
        self.assertEqual(x['candidate_shares'],50)
        self.assertEqual(x['candidate_notional_rupees'],10000)
        self.assertEqual(x['planned_exit_risk_rupees'],500)
        self.assertGreater(x['loss_if_15pct_gap_below_review_exit_rupees'],500)

    def test_05_restrict_concentrated_existing_position(self):
        x=position_size(entry=200,review_exit=190,free_cash=100000,
                cap_fraction=0.1,risk_fraction=0.01,existing_exposure=250000,
                portfolio_total=900000,max_weight_after=0.15)
        self.assertEqual(x['candidate_shares'],0)

    def test_06_no_bad_capital_or_exit(self):
        with self.assertRaises(ValueError):position_size(entry=150,review_exit=180,free_cash=10000,cap_fraction=.1,risk_fraction=.01)

    def test_07_basic_moving_average(self):
        self.assertEqual(sma([1,2,3,4],3),[None,None,2,3])
        self.assertAlmostEqual(ema([1,2,3],3)[-1],2)

    def test_08_rsi_is_100_for_rising_market(self):
        self.assertAlmostEqual(rsi(list(range(30)),14)[-1],100)

    def test_09_atr_and_indicator_history(self):
        b=bars(220)
        self.assertGreater(atr(b)[-1],0)
        i=indicators(b)[-1]
        self.assertIsNotNone(i['sma200']);self.assertIsNotNone(i['macd_signal'])

    def test_10_stale_quote_is_blocked(self):
        now=dt.datetime(2026,10,22,14,40,tzinfo=IST)
        q={'symbol':'TESTONLY','price':130,'exchange':'NSE','source_url':'https://www.nseindia.com','time_ist':'2026-10-22T10:00:00+05:30'}
        self.assertEqual(valid_quote(q,now)[1],'QUOTE_STALE_OR_FUTURE')

    def test_11_incomplete_research_never_buy(self):
        v=evaluate_candidate(available_cash=10000,one_month_reserve=0,planned_entry=100,review_exit=90)
        self.assertEqual(v['decision'],'WAIT');self.assertEqual(v['candidate_shares'],0)

    def test_12_adjustment_validation(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'px.csv'
            p.write_text('date,symbol,open,high,low,close,volume,adjusted,corporate_actions_checked,source_url,synthetic\n2026-01-01,TESTONLY,100,110,90,100,10,false,false,https://example.invalid,false\n')
            with self.assertRaises(ValueError):parse_quotes_csv(p)

    def test_13_fake_data_rejected_without_test_switch(self):
        with self.assertRaises(ValueError):backtest_strategy(bars(),strategy='trend_200d_atr')

    def test_14_backtest_next_open_and_costs(self):
        result=backtest_strategy(bars(),strategy='trend_200d_atr',allow_synthetic=True)
        self.assertEqual(result['execution'].split(';')[0],'signals at close')
        self.assertIn('volatility_annual_pct',result['performance'])
        self.assertTrue(result['synthetic'])
        self.assertGreaterEqual(result['performance']['traded_notional_rupees'],0)
        for rec in result['trades']:
            self.assertIn(rec['action'],('BUY','SELL_SIGNAL','SELL_STOP_GAP_AWARE'))

    def test_15_all_three_strategy_functions(self):
        b=bars();ind=indicators(b)
        snap=[{'published_date':'2024-01-01','source_url':'https://example.invalid/filing',
               'point_in_time_confirmed':True,'quality_score':80,'valuation_score':70}]
        ev=[{'available_to_trade_date':b[250]['date'].isoformat(),
             'verified':True,'filing_url':'https://example.invalid/filing',
             'profit_surprise_pct':20,'revenue_surprise_pct':10}]
        self.assertEqual(signal_for_strategy('quality_valuation_momentum',b,ind,250,fundamental_snapshots=snap),'BUY')
        self.assertEqual(signal_for_strategy('earnings_event',b,ind,250,earnings_events=ev),'BUY')
        self.assertIsNone(signal_for_strategy('earnings_event',b,ind,249,earnings_events=ev))
        for kind in ['quality_valuation_momentum','earnings_event']:
            bt=backtest_strategy(b,strategy=kind,fundamental_snapshots=snap,
                                 earnings_events=ev,allow_synthetic=True)
            self.assertIn('max_drawdown_pct',bt['performance'])

    def test_16_walk_forward_has_unseen_periods(self):
        v=walk_forward(bars(440),strategy='trend_200d_atr',train_days=300,test_days=60,step_days=60,allow_synthetic=True)
        self.assertGreaterEqual(len(v['folds']),2)
        for x in v['folds']:
            self.assertLess(x['train_end'],x['test_start'])

    def test_17_buy_hold_benchmark(self):
        b=bars(220)
        x=benchmark_buyhold(b)
        self.assertEqual(x['end_date'],b[-1]['date'].isoformat())

    def test_18_pdf_rights_gate(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaises(PermissionError):
                register(Path(td)/'none.pdf',db=Path(td)/'jobs.sqlite',publisher='Example',source_reference='licensed',usage_permitted=False)

    def test_19_pdf_complete_then_local_purge(self):
        from pypdf import PdfWriter
        with tempfile.TemporaryDirectory() as td:
            pdf=Path(td)/'authorized.pdf'
            writer=PdfWriter();writer.add_blank_page(width=300,height=300);writer.add_blank_page(width=300,height=300)
            with pdf.open('wb') as f:writer.write(f)
            db=Path(td)/'jobs.sqlite'
            job=register(pdf,db=db,publisher='Fixture only',source_reference='local test fixture',usage_permitted=True)
            self.assertEqual(job['pages'],2)
            extracted=Path(td)/'research.json'
            extracted.write_text(json.dumps({'sha256':job['sha256'],'pages':[{'page_index':1,'status':'NO_RELEVANT_ARTICLES','facts':[]},{'page_index':2,'status':'NO_RELEVANT_ARTICLES','facts':[]}]}))
            receipt=validate_and_purge(db=db,sha256=job['sha256'],extracted_json_file=extracted,durable_output=Path(td)/'results.json')
            self.assertFalse(pdf.exists());self.assertTrue(receipt['local_path_absent'])
            self.assertEqual(overdue_jobs(db),[])

    def test_20_pdf_missing_pages_never_deletes(self):
        from pypdf import PdfWriter
        with tempfile.TemporaryDirectory() as td:
            pdf=Path(td)/'authorized.pdf'
            w=PdfWriter();w.add_blank_page(width=300,height=300);w.add_blank_page(width=300,height=300)
            with pdf.open('wb') as f:w.write(f)
            db=Path(td)/'jobs.sqlite'
            j=register(pdf,db=db,publisher='Fixture only',source_reference='local test fixture',usage_permitted=True)
            evidence=Path(td)/'extraction.json'
            evidence.write_text(json.dumps({'sha256':j['sha256'],'pages':[{'page_index':1,'status':'EXTRACTED','facts':[]}]}))
            with self.assertRaises(ValueError):
                validate_and_purge(db=db,sha256=j['sha256'],extracted_json_file=evidence,durable_output=Path(td)/'result.json')
            self.assertTrue(pdf.exists())

if __name__=='__main__':unittest.main(verbosity=2)
