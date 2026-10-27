"""Independent offline NSE-format fixtures. Values are invented; NEVER market evidence."""
import csv
import datetime as dt
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch
from nse_pipeline import archive_name,archive_url,ingest_udiff,archive_import,download_udiff
from corporate_actions import adjust_raw
from market_engine import parse_quotes_csv,save_json
DAY=dt.date(2026,10,21)
HEADER='TckrSymb,SctySrs,ISIN,TradDt,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\n'
ROW='NATIONALUM,EQ,INE139A01034,2026-10-21,299,310,295,305,10000\n'
ROW2='TCIEXP,EQ,INE586V01016,2026-10-21,450,465,440,460,23000\n'

class NSEPipelineTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
        self.root=Path(self.tmp.name)
        self.archive=self.root/archive_name(DAY)
        self._write_zip(HEADER+ROW+ROW2)
    def _write_zip(self,csv_content):
        with zipfile.ZipFile(self.archive,'w',compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr(self.archive.name.removesuffix('.zip'),csv_content)
    def _attest(self):
        import hashlib
        save_json(Path(str(self.archive)+'.receipt.json'),{'archive_date':DAY.isoformat(),'sha256':hashlib.sha256(self.archive.read_bytes()).hexdigest(),'download_url':archive_url(DAY),'provenance':'MANUAL_OFFICIAL_EXPORT_ATTESTED'})
    def test_21_extract_two_isin_verified_stocks(self):
        a=ingest_udiff(self.archive,expected_day=DAY)
        self.assertEqual(a['matched_symbols'],2)
        self.assertFalse(a['origin_confirmed'])
        self.assertFalse(a['bars']['NATIONALUM']['adjusted'])
        self.assertEqual(a['bars']['NATIONALUM']['close'],305)
    def test_22_reject_isin_mismatch(self):
        self._write_zip(HEADER+ROW.replace('INE139A01034','INE000000000'))
        with self.assertRaisesRegex(ValueError,'Identity mismatch'):ingest_udiff(self.archive,expected_day=DAY)
    def test_23_reject_date_mismatch(self):
        self._write_zip(HEADER+ROW.replace('2026-10-21','2026-10-20'))
        with self.assertRaisesRegex(ValueError,'Unexpected date'):ingest_udiff(self.archive,expected_day=DAY)
    def test_24_reject_duplicate_ticker(self):
        self._write_zip(HEADER+ROW+ROW)
        with self.assertRaisesRegex(ValueError,'Duplicate'):ingest_udiff(self.archive,expected_day=DAY)
    def test_25_reject_corrupt_zip(self):
        self.archive.write_bytes(b'NOZIP')
        with self.assertRaises(zipfile.BadZipFile):ingest_udiff(self.archive,expected_day=DAY)
    def test_26_source_immutable_reimport(self):
        self._attest()
        out=self.root/'raw'
        x=archive_import(self.archive,date=DAY,store=out)
        self.assertTrue(x['origin_confirmed'])
        with (out/'NATIONALUM.csv').open() as f:
            self.assertEqual(len(list(csv.DictReader(f))),1)
        archive_import(self.archive,date=DAY,store=out)
        with (out/'NATIONALUM.csv').open() as f:
            self.assertEqual(len(list(csv.DictReader(f))),1)
    def test_27_receipt_tampered_must_fail(self):
        self._attest()
        with zipfile.ZipFile(self.archive,'a') as z:z.writestr('extra.txt','tamper')
        with self.assertRaisesRegex(ValueError,'receipt mismatch'):ingest_udiff(self.archive,expected_day=DAY)
    def test_28_no_corporate_action_review_rejects_adjustment(self):
        out=self.root/'raw';archive_import(self.archive,date=DAY,store=out)
        review=self.root/'review.json';save_json(review,{'symbol':'NATIONALUM','isin':'INE139A01034','status':'HUMAN_REVIEWED_APPROVED','covered_from_date':DAY.isoformat(),'reviewed_through_date':DAY.isoformat(),'official_source_url':'https://www.nseindia.com','events':[]})
        with self.assertRaisesRegex(ValueError,'origin not verified'):adjust_raw(out/'NATIONALUM.csv',review,self.root/'adj.csv')
    def test_29_reviewed_split_adjustment_and_backtest_parser(self):
        self._attest()
        out=self.root/'raw';archive_import(self.archive,date=DAY,store=out)
        old=out/'NATIONALUM.csv'
        with old.open() as f:
            v=list(csv.DictReader(f))[0]
        # Add a second, post-split bar in the raw file for pure software testing.
        r=v.copy();r.update({'date':'2026-10-22','open':'150','high':'158','low':'148','close':'155','volume':'20000'})
        with old.open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=v.keys());w.writeheader();w.writerows([v,r])
        review=self.root/'review.json'
        save_json(review,{'symbol':'NATIONALUM','isin':'INE139A01034','status':'HUMAN_REVIEWED_APPROVED','covered_from_date':'2026-10-21','reviewed_through_date':'2026-10-22','official_source_url':'https://www.nseindia.com','events':[{'type':'SPLIT','ex_date':'2026-10-22','shares_after_per_share_before':2,'official_source_url':'https://www.nseindia.com'}]})
        adjusted=self.root/'adj.csv'
        r=adjust_raw(old,review,adjusted)
        bars=parse_quotes_csv(adjusted)
        self.assertEqual(bars[0]['close'],152.5)
        self.assertEqual(bars[0]['volume'],20000)
        self.assertEqual(bars[1]['close'],155)
    def test_30_unsupported_dividend_rejected(self):
        self._attest()
        out=self.root/'raw';archive_import(self.archive,date=DAY,store=out)
        review=self.root/'review.json'
        save_json(review,{'symbol':'NATIONALUM','isin':'INE139A01034','status':'HUMAN_REVIEWED_APPROVED','covered_from_date':DAY.isoformat(),'reviewed_through_date':DAY.isoformat(),'official_source_url':'https://www.nseindia.com','events':[{'type':'DIVIDEND','ex_date':'2026-10-21','shares_after_per_share_before':1,'official_source_url':'https://www.nseindia.com'}]})
        with self.assertRaisesRegex(ValueError,'Unsupported adjustment'):adjust_raw(out/'NATIONALUM.csv',review,self.root/'adj.csv')

if __name__=='__main__':unittest.main()
