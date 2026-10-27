import csv,datetime as dt,hashlib,json,tempfile,unittest
from pathlib import Path
from backtest_quality_gate import verify_backtest_input
from market_engine import save_json
class QualityGateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.csv=self.root/'prices.csv';self.csv.write_text('date,symbol,close\n2026-01-01,TCIEXP,123\n2026-01-02,TCIEXP,124\n')
  self.json=self.root/'review.json'
  self.review={'status':'HUMAN_REVIEWED_COMPLETE','file_sha256':hashlib.sha256(self.csv.read_bytes()).hexdigest(),'adjustment_scope':'ALL_RELEVANT_PRICE_ACTIONS_AND_CASH_DIVIDENDS_RECONCILED','point_in_time_verified':True,'source_historical_data_reviewed':True,'rights_and_licensing_confirmed':True,'primary_sources':['https://www.nseindia.com/all-reports'],'reviewed_by':'QA_FIXTURE','reviewed_at_ist':'2026-10-22T08:00:00+05:30','covered_from_date':'2026-01-01','reviewed_through_date':'2026-01-02','symbol':'TCIEXP'}
  save_json(self.json,self.review)
 def test_45_valid_complete_attestation(self):
  self.assertEqual(verify_backtest_input(self.csv,self.json)['symbol'],'TCIEXP')
 def test_46_missing_review_blocks_real_test(self):
  with self.assertRaises(FileNotFoundError):verify_backtest_input(self.csv,self.root/'missing.json')
 def test_47_price_file_change_invalidates_review(self):
  self.csv.write_text(self.csv.read_text()+'2026-01-03,TCIEXP,122\n')
  with self.assertRaisesRegex(ValueError,'file_sha256'):verify_backtest_input(self.csv,self.json)
 def test_48_split_only_not_enough(self):
  self.review['adjustment_scope']='SPLITS_BONUS_ONLY';save_json(self.json,self.review)
  with self.assertRaisesRegex(ValueError,'adjustment_scope'):verify_backtest_input(self.csv,self.json)
 def test_49_wrong_symbol_rejected(self):
  self.review['symbol']='NATIONALUM';save_json(self.json,self.review)
  with self.assertRaisesRegex(ValueError,'instrument'):verify_backtest_input(self.csv,self.json)
 def test_50_official_source_required(self):
  self.review['primary_sources']=['https://example.invalid'];save_json(self.json,self.review)
  with self.assertRaisesRegex(ValueError,'Official'):verify_backtest_input(self.csv,self.json)
if __name__=='__main__':unittest.main()
