import datetime as dt
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from portfolio_analytics_v04 import xirr, time_weighted_return,concentration,scenario_analysis,fund_overlap,portfolio_enhancement_report
ROOT=Path(__file__).resolve().parents[1]
class NewPortfolioAnalyticsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.portfolio=json.loads((ROOT/'data'/'portfolio_statement_snapshot.json').read_text())
    def test_xirr_one_year(self):self.assertAlmostEqual(xirr([('2025-01-01',-100),('2026-01-01',110)]),0.1,places=9)
    def test_xirr_two_year(self):self.assertAlmostEqual(xirr([('2024-01-01',-100),('2025-12-31',121)]),0.1,places=9)
    def test_xirr_multi_purchases(self):self.assertAlmostEqual(xirr([('2025-01-01',-100),('2025-01-01',-50),('2026-01-01',165)]),0.1,places=9)
    def test_xirr_no_dates(self):
        with self.assertRaises(ValueError):xirr([('2025-01-01',-100)])
    def test_xirr_ambiguous(self):
        with self.assertRaises(ValueError):xirr([('2024-01-01',-100),('2025-01-01',220),('2026-01-01',-121)])
    def test_twr_deposit_not_profit(self):
        r=time_weighted_return([{'start_value':100,'end_value':110},{'start_value':110,'end_value':160,'flow_end':50}]);self.assertAlmostEqual(r['twr_total_return'],0.1)
    def test_twr_disconnected(self):
        with self.assertRaises(ValueError):time_weighted_return([{'start_value':100,'end_value':110},{'start_value':100,'end_value':120}])
    def test_concentration_total(self):self.assertAlmostEqual(concentration(self.portfolio)['total_line_item_value_rupees'],2349296.90,places=2)
    def test_concentration_disclosure(self):self.assertEqual(len(concentration(self.portfolio)['limitations']),3)
    def test_scenario_no_shock(self):
        c=concentration(self.portfolio)
        r=scenario_analysis(self.portfolio,{k:0. for k in c['category_shares_pct']});self.assertAlmostEqual(r['scenario_pnl_rupees'],0.)
    def test_scenario_bad_key(self):
        with self.assertRaises(ValueError):scenario_analysis(self.portfolio,{'Gold':-0.1})
    def test_overlap(self):
        def h(a,b):return [{'isin':'INE586V01016','weight_pct':a,'published_date':'2026-10-01','source_url':'https://example.org/fund'},{'isin':'INE917I01010','weight_pct':b,'published_date':'2026-10-01','source_url':'https://example.org/fund'}]
        self.assertAlmostEqual(fund_overlap(h(60,40),h(30,70),asof_date='2026-10-23')['overlap_pct_of_each_fund'],70.)
    def test_overlap_incomplete(self):
        with self.assertRaises(ValueError):fund_overlap([{'isin':'INE586V01016','weight_pct':70,'published_date':'2026-10-01','source_url':'https://example.org'}],[{'isin':'INE586V01016','weight_pct':100,'published_date':'2026-10-01','source_url':'https://example.org'}],asof_date='2026-10-23')
    def test_report_flags(self):
        x=portfolio_enhancement_report(self.portfolio);self.assertEqual(x['xirr']['status'],'NOT CALCULABLE FROM HOLDINGS SNAPSHOT');self.assertEqual(x['recommendations']['orders_placed'],0)
if __name__=='__main__':unittest.main()
