#!/usr/bin/env python3
"""Validate workshop CSVs: schema, relationships, GBP, inventory and order semantics."""
import argparse,csv,json
from datetime import date
from pathlib import Path
REQUIRED={
'suppliers.csv':{'supplier_id','supplier_name','country','supplier_risk_tier','standard_lead_time_days','active'},
'products.csv':{'product_id','product_name','category','supplier_id','unit_cost_gbp','safety_stock','criticality'},
'inventory_snapshot.csv':{'snapshot_id','snapshot_date','warehouse_id','warehouse_name','product_id','quantity_on_hand','quantity_reserved','available_quantity','safety_stock','inventory_status'},
'fulfillment_orders.csv':{'order_id','order_date','promised_delivery_date','actual_delivery_date','product_id','supplier_id','quantity_ordered','order_status','delay_days','warehouse_id','order_value_gbp'}}
RISK={'LOW','MEDIUM','HIGH'}; STATUSES={'DELIVERED','IN_TRANSIT','PROCESSING','DELAYED','CANCELLED'}
def read(path):
    if not path.exists(): raise FileNotFoundError(path)
    with path.open(newline='',encoding='utf-8') as f:
        r=csv.DictReader(f)
        missing=REQUIRED[path.name]-set(r.fieldnames or [])
        if missing: raise ValueError(f'{path.name} missing columns: {sorted(missing)}')
        return list(r)
def validate(folder):
    errors=[]; rows={n:read(folder/n) for n in REQUIRED}; counts={n[:-4]:len(v) for n,v in rows.items()}
    manifest=json.loads((folder/'manifest.json').read_text(encoding='utf-8')); snap=date.fromisoformat(manifest['snapshot_date'])
    if manifest.get('currency')!='GBP': errors.append('manifest currency must be GBP')
    def unique(table,key):
        vals=[r[key] for r in rows[table]]
        if len(vals)!=len(set(vals)): errors.append(f'{table}: duplicate {key}')
        return set(vals)
    sids=unique('suppliers.csv','supplier_id'); pids=unique('products.csv','product_id'); unique('inventory_snapshot.csv','snapshot_id'); unique('fulfillment_orders.csv','order_id')
    for r in rows['suppliers.csv']:
        if r['supplier_risk_tier'] not in RISK: errors.append(f"invalid risk tier: {r['supplier_id']}")
        if int(r['standard_lead_time_days'])<=0: errors.append(f"invalid supplier lead time: {r['supplier_id']}")
    for r in rows['products.csv']:
        if r['supplier_id'] not in sids: errors.append(f"unknown product supplier: {r['product_id']}")
        if float(r['unit_cost_gbp'])<0 or int(r['safety_stock'])<=0: errors.append(f"invalid product metric: {r['product_id']}")
        if r['criticality'] not in RISK: errors.append(f"invalid criticality: {r['product_id']}")
    warehouses=set()
    for r in rows['inventory_snapshot.csv']:
        if r['product_id'] not in pids: errors.append(f"unknown inventory product: {r['product_id']}")
        warehouses.add(r['warehouse_id']); on,res,avail,safety=map(int,[r['quantity_on_hand'],r['quantity_reserved'],r['available_quantity'],r['safety_stock']])
        if min(on,res,avail)<0 or res>on or avail!=on-res: errors.append(f"inventory arithmetic invalid: {r['product_id']}")
        expected='CRITICAL' if avail<safety*.5 else 'AT_RISK' if avail<safety else 'HEALTHY'
        if r['inventory_status']!=expected: errors.append(f"inventory status mismatch: {r['product_id']}")
        if date.fromisoformat(r['snapshot_date'])!=snap: errors.append(f"snapshot date mismatch: {r['product_id']}")
    if len(warehouses)!=1: errors.append(f'expected one warehouse, found {len(warehouses)}')
    for r in rows['fulfillment_orders.csv']:
        if r['product_id'] not in pids or r['supplier_id'] not in sids: errors.append(f"unknown order reference: {r['order_id']}")
        od=date.fromisoformat(r['order_date']); due=date.fromisoformat(r['promised_delivery_date']); actual=date.fromisoformat(r['actual_delivery_date']) if r['actual_delivery_date'] else None; status=r['order_status']
        if due<=od: errors.append(f"promised date not after order date: {r['order_id']}")
        if status not in STATUSES: errors.append(f"invalid order status: {r['order_id']}")
        if status=='DELIVERED':
            if actual is None or actual>snap: errors.append(f"delivered order missing valid actual date: {r['order_id']}")
            expected=max(0,(actual-due).days) if actual else 0
        elif status=='DELAYED':
            if actual is not None or due>=snap: errors.append(f"DELAYED must be open and overdue: {r['order_id']}")
            expected=(snap-due).days
        elif status in ('IN_TRANSIT','PROCESSING'):
            if actual is not None or due<snap: errors.append(f"{status} must be open and not overdue: {r['order_id']}")
            expected=0
        else: expected=0
        if int(r['delay_days'])!=expected: errors.append(f"delay_days mismatch: {r['order_id']}")
        if int(r['quantity_ordered'])<=0 or float(r['order_value_gbp'])<0: errors.append(f"invalid order quantity/value: {r['order_id']}")
        if r['warehouse_id'] not in warehouses: errors.append(f"unknown order warehouse: {r['order_id']}")
    return errors,counts
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--input-dir',type=Path,default=Path('data/sample')); a=p.parse_args()
    try: errors,counts=validate(a.input_dir)
    except (OSError,ValueError,KeyError) as e: print(f'VALIDATION ERROR: {e}'); raise SystemExit(1)
    print('Row counts:',counts)
    if errors:
        print(f'FAILED ({len(errors)}):'); [print(' -',e) for e in errors[:50]]; raise SystemExit(1)
    print('PASSED: schemas, keys, relationships, GBP, one warehouse, inventory arithmetic and order-status rules')
if __name__=='__main__': main()
