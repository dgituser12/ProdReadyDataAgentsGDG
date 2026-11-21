import importlib.util, tempfile, unittest
from datetime import date
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path); m=importlib.util.module_from_spec(s); s.loader.exec_module(m); return m
gen=load('gen',ROOT/'scripts/generate_data.py'); val=load('val',ROOT/'scripts/validate_data.py')
class DataTests(unittest.TestCase):
 def test_default_counts_and_validation(self):
  with tempfile.TemporaryDirectory() as d:
   counts=gen.generate(20261013,Path(d),60,500,date(2026,10,1)); errors,actual=val.validate(Path(d)); self.assertEqual(counts,{'suppliers':8,'products':60,'inventory_snapshot':60,'fulfillment_orders':500}); self.assertEqual(actual,counts); self.assertEqual(errors,[])
 def test_reproducibility(self):
  with tempfile.TemporaryDirectory() as a,tempfile.TemporaryDirectory() as b:
   gen.generate(42,Path(a),12,30,date(2026,10,1)); gen.generate(42,Path(b),12,30,date(2026,10,1))
   for n in ['suppliers.csv','products.csv','inventory_snapshot.csv','fulfillment_orders.csv','manifest.json']: self.assertEqual((Path(a)/n).read_bytes(),(Path(b)/n).read_bytes())
 def test_schema_decisions(self):
  import csv
  with tempfile.TemporaryDirectory() as d:
   gen.generate(1,Path(d),5,10,date(2026,10,1))
   with (Path(d)/'suppliers.csv').open() as f: sf=set(next(csv.reader(f)))
   with (Path(d)/'products.csv').open() as f: pf=set(next(csv.reader(f)))
   self.assertIn('supplier_risk_tier',sf); self.assertIn('standard_lead_time_days',sf); self.assertNotIn('on_time_delivery_rate',sf); self.assertNotIn('standard_lead_time_days',pf); self.assertIn('unit_cost_gbp',pf)
if __name__=='__main__': unittest.main()
