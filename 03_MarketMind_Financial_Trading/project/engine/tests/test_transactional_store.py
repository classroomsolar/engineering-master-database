"""Independent synthetic UDiFF and benchmark fixtures; NOT real price records."""
import csv,datetime as dt,hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from market_store import import_archive, audit_store,export_symbol,DB_NAME
from benchmark_pipeline import load_tri,compare_curve,OFFICIAL
from nse_pipeline import archive_name,ingest_udiff,archive_import
from market_engine import save_json
DAY=dt.date(2026,10,21)
HEADER='TckrSymb,SctySrs,ISIN,TradDt,OpnPric,HghPric,LwPric,ClsPric,TtlTradgVol\n'
NALCO='NATIONALUM,EQ,INE139A01034,2026-10-21,300,310,295,305,10000\n'
TCI='TCIEXP,EQ,INE586V01016,2026-10-21,450,465,440,460,23000\n'

class StorageTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.file=self.root/archive_name(DAY);self.db=self.root/DB_NAME;self.write(NALCO+TCI)
 def write(self,rows):
  with zipfile.ZipFile(self.file,'w',zipfile.ZIP_DEFLATED) as z:z.writestr(self.file.name[:-4],HEADER+rows)
 def parsed(self):return ingest_udiff(self.file,expected_day=DAY)
 def test_31_two_symbols_commit_in_one_transaction(self):
  r=import_archive(self.parsed(),db_path=self.db);self.assertEqual(r['status'],'IMPORTED_RAW_UNADJUSTED')
  self.assertEqual(audit_store(self.db)['bars_total'],2)
 def test_32_idempotent_archive_retry(self):
  r=self.parsed();import_archive(r,db_path=self.db)
  x=import_archive(r,db_path=self.db)
  self.assertEqual(x['status'],'ALREADY_IMPORTED');self.assertEqual(audit_store(self.db)['archive_count'],1)
 def test_33_revised_source_archive_rejected_unchanged(self):
  first=self.parsed();import_archive(first,db_path=self.db)
  self.write(NALCO.replace(',305,',',306,')+TCI)
  with self.assertRaisesRegex(ValueError,'Immutable archive conflict'):import_archive(self.parsed(),db_path=self.db)
  self.assertEqual(audit_store(self.db)['bars_total'],2)
 def test_34_unknown_isin_rolls_back_before_insert(self):
  parsed=self.parsed();parsed['bars']['NATIONALUM']['isin']='INE1234567890'
  with self.assertRaisesRegex(ValueError,'identity'):import_archive(parsed,db_path=self.db)
  self.assertEqual(audit_store(self.db)['archive_count'],0)
 def test_35_partial_bad_second_bar_rolls_back(self):
  parsed=self.parsed();parsed['bars']['TCIEXP']['low']=999
  with self.assertRaises(Exception):import_archive(parsed,db_path=self.db)
  self.assertEqual(audit_store(self.db)['archive_count'],0)
 def test_36_regenerate_csv_and_original_remains_unadjusted(self):
  import_archive(self.parsed(),db_path=self.db)
  out=self.root/'NATIONALUM.csv';export_symbol(self.db,'NATIONALUM',out)
  with out.open() as f: rec=list(csv.DictReader(f))
  self.assertEqual(rec[0]['adjusted'],'False');self.assertEqual(rec[0]['close'],'305.0')
 def test_37_missing_date_column_rejected(self):
  self.write(NALCO+TCI);b=self.file.read_bytes()
  with zipfile.ZipFile(self.file,'w',zipfile.ZIP_DEFLATED) as z:
   z.writestr(self.file.name[:-4],(HEADER+NALCO+TCI).replace('TradDt,',''))
  with self.assertRaisesRegex(ValueError,'Missing NSE date column'):self.parsed()
 def test_38_fractional_volume_rejected(self):
  self.write(NALCO.replace('10000','10000.5')+TCI)
  with self.assertRaisesRegex(ValueError,'Invalid numeric'):self.parsed()
 def test_39_repeat_legacy_import_does_not_change_db(self):
  store=self.root/'store';archive_import(self.file,date=DAY,store=store)
  archive_import(self.file,date=DAY,store=store)
  self.assertEqual(audit_store(store/DB_NAME)['bars_total'],2)

class BenchmarkTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  self.csv=self.root/'tri.csv';self.man=self.root/'tri.manifest.json'
  self.csv.write_text('Index Name,Date,Total Returns Index\nNIFTY 50,21-Oct-2026,10000\nNIFTY 50,22-Oct-2026,10100\nNIFTY 50,23-Oct-2026,10200\n')
  save_json(self.man,{'sha256':hashlib.sha256(self.csv.read_bytes()).hexdigest(),'attested_source_url':OFFICIAL,'reviewed_by':'QA_FICTIONAL','expected_index':'NIFTY 50'})
 def test_40_load_source_attested_tri(self):self.assertEqual(len(load_tri(self.csv,manifest_path=self.man)['points']),3)
 def test_41_reject_corrupt_source_sha(self):
  self.csv.write_text(self.csv.read_text()+'BOGUS,25-Oct-2026,10200\n')
  with self.assertRaisesRegex(ValueError,'checksum'):load_tri(self.csv,manifest_path=self.man)
 def test_42_matched_date_comparison(self):
  curve=[{'date':'2026-10-21','equity':100000},{'date':'2026-10-22','equity':102000},{'date':'2026-10-23','equity':103000}]
  x=compare_curve(curve,load_tri(self.csv,manifest_path=self.man))
  self.assertAlmostEqual(x['strategy_minus_tri_percentage_points'],1.0)
 def test_43_mismatched_dates_rejected(self):
  curve=[{'date':'2026-10-20','equity':100000},{'date':'2026-10-22','equity':102000},{'date':'2026-10-23','equity':103000}]
  with self.assertRaisesRegex(ValueError,'coverage'):compare_curve(curve,load_tri(self.csv,manifest_path=self.man))
 def test_44_duplicate_tri_dates_rejected(self):
  with self.csv.open('a') as f:f.write('NIFTY 50,23-Oct-2026,10200\n')
  save_json(self.man,{'sha256':hashlib.sha256(self.csv.read_bytes()).hexdigest(),'attested_source_url':OFFICIAL,'reviewed_by':'QA_FICTIONAL','expected_index':'NIFTY 50'})
  with self.assertRaisesRegex(ValueError,'Duplicate'):load_tri(self.csv,manifest_path=self.man)

if __name__=='__main__':unittest.main()
