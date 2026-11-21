import json, subprocess, sys, tempfile, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class BusinessMetricTests(unittest.TestCase):
    def test_metric_calculation_and_catalogue(self):
        with tempfile.TemporaryDirectory() as td:
            out=Path(td)/'metrics.json'
            subprocess.run([sys.executable,str(ROOT/'scripts/calculate_metrics.py'),'--input-dir',str(ROOT/'data/sample'),'--output',str(out)],check=True,capture_output=True,text=True)
            data=json.loads(out.read_text())
        self.assertEqual(data['as_of_date'],'2026-10-01')
        self.assertEqual(data['currency'],'GBP')
        self.assertEqual(len(data['suppliers']),8)
        self.assertGreaterEqual(data['inventory']['inventory_value_at_risk_gbp'],0)
        self.assertGreaterEqual(data['fulfillment']['overdue_open_orders'],0)
        self.assertLessEqual(data['fulfillment']['overdue_open_orders'],data['fulfillment']['open_orders'])
        self.assertTrue(all(s['on_time_delivery_rate'] is None or 0<=s['on_time_delivery_rate']<=1 for s in data['suppliers']))
    def test_catalogue_contains_core_separation_rules(self):
        c=json.loads((ROOT/'semantic_catalogue/metrics.json').read_text())
        ids={m['id'] for m in c['metrics']}
        self.assertIn('supplier.profile_risk_tier',ids)
        self.assertIn('supplier.on_time_delivery_rate',ids)
        self.assertIn('fulfillment.overdue_open_orders',ids)
        self.assertIn('inventory.value_at_risk_gbp',ids)
        self.assertIn('late delivered orders', ' '.join(c['agent_usage']['answering_policy']).lower())
if __name__=='__main__': unittest.main()
