#!/usr/bin/env python3
"""Generate deterministic synthetic supply-chain data. All monetary values are GBP."""
from __future__ import annotations
import argparse, csv, json, random
from datetime import date, timedelta
from pathlib import Path
SUPPLIERS=[("SUP-001","Northstar Components","United Kingdom","LOW"),("SUP-002","Apex Industrial","Germany","MEDIUM"),("SUP-003","Pacific Circuitry","Singapore","HIGH"),("SUP-004","Meridian Materials","India","MEDIUM"),("SUP-005","BlueRiver Logistics","Netherlands","LOW"),("SUP-006","Summit Manufacturing","United States","HIGH"),("SUP-007","Orion Precision","Japan","LOW"),("SUP-008","CedarWorks Supply","Poland","MEDIUM")]
CATEGORIES=["Electronics","Mechanical","Packaging","Safety"]
WAREHOUSE_ID="WH-ESSEX-01"; WAREHOUSE_NAME="Essex Central Distribution Centre"; DEFAULT_SNAPSHOT_DATE=date(2026,10,1)
def write_csv(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
def generate(seed, output_dir, products_count=60, orders_count=500, snapshot_date=DEFAULT_SNAPSHOT_DATE):
    rng=random.Random(seed)
    suppliers=[{"supplier_id":sid,"supplier_name":name,"country":country,"supplier_risk_tier":risk,"standard_lead_time_days":rng.randint(5,28),"active":True} for sid,name,country,risk in SUPPLIERS]
    supplier_map={s['supplier_id']:s for s in suppliers}
    products=[]
    for i in range(1,products_count+1):
        supplier=rng.choice(suppliers); category=rng.choice(CATEGORIES)
        products.append({"product_id":f"PRD-{i:04d}","product_name":f"{category[:-1] if category.endswith('s') else category} Component {i:03d}","category":category,"supplier_id":supplier['supplier_id'],"unit_cost_gbp":round(rng.uniform(8,950),2),"safety_stock":rng.randint(15,100),"criticality":rng.choice(["LOW","MEDIUM","HIGH"])})
    inventory=[]
    for p in products:
        safety=p['safety_stock']; mode=rng.choices(['healthy','watch','critical'],weights=[.58,.27,.15])[0]
        if mode=='healthy': on_hand=rng.randint(safety+20,safety*4+80)
        elif mode=='watch': on_hand=rng.randint(max(1,int(safety*.50)),safety-1)
        else: on_hand=rng.randint(0,max(0,int(safety*.49)))
        reserved=rng.randint(0,min(on_hand,max(0,int(on_hand*.35)))); available=on_hand-reserved
        status='CRITICAL' if available<safety*.5 else 'AT_RISK' if available<safety else 'HEALTHY'
        inventory.append({"snapshot_id":f"INV-{p['product_id']}","snapshot_date":snapshot_date.isoformat(),"warehouse_id":WAREHOUSE_ID,"warehouse_name":WAREHOUSE_NAME,"product_id":p['product_id'],"quantity_on_hand":on_hand,"quantity_reserved":reserved,"available_quantity":available,"safety_stock":safety,"inventory_status":status})
    orders=[]; statuses=['DELIVERED','IN_TRANSIT','PROCESSING','DELAYED','CANCELLED']; weights=[.55,.18,.12,.11,.04]
    for i in range(1,orders_count+1):
        p=rng.choice(products); supplier=supplier_map[p['supplier_id']]; lead=supplier['standard_lead_time_days']; status=rng.choices(statuses,weights=weights)[0]
        order_date=snapshot_date-timedelta(days=rng.randint(1,120)); promised=order_date+timedelta(days=rng.randint(max(2,lead-3),lead+8)); actual=''
        if status=='DELIVERED':
            order_date=min(order_date,snapshot_date-timedelta(days=2)); promised=min(promised,snapshot_date-timedelta(days=1)); actual_date=min(promised+timedelta(days=rng.randint(-4,12)),snapshot_date); actual=actual_date.isoformat(); delay=max(0,(actual_date-promised).days)
        elif status=='DELAYED':
            order_date=min(order_date,snapshot_date-timedelta(days=lead+2)); promised=max(order_date+timedelta(days=1),snapshot_date-timedelta(days=rng.randint(1,21))); promised=min(promised,snapshot_date-timedelta(days=1)); delay=(snapshot_date-promised).days
        elif status in ('IN_TRANSIT','PROCESSING'):
            order_date=min(order_date,snapshot_date-timedelta(days=1)); promised=max(promised,snapshot_date+timedelta(days=rng.randint(1,21))); delay=0
        else: delay=0
        qty=rng.randint(5,180)
        orders.append({"order_id":f"ORD-{i:05d}","order_date":order_date.isoformat(),"promised_delivery_date":promised.isoformat(),"actual_delivery_date":actual,"product_id":p['product_id'],"supplier_id":supplier['supplier_id'],"quantity_ordered":qty,"order_status":status,"delay_days":delay,"warehouse_id":WAREHOUSE_ID,"order_value_gbp":round(qty*p['unit_cost_gbp'],2)})
    output_dir.mkdir(parents=True,exist_ok=True)
    for name,rows in [('suppliers',suppliers),('products',products),('inventory_snapshot',inventory),('fulfillment_orders',orders)]: write_csv(output_dir/f'{name}.csv',rows)
    counts={'suppliers':len(suppliers),'products':len(products),'inventory_snapshot':len(inventory),'fulfillment_orders':len(orders)}
    manifest={"synthetic_data":True,"seed":seed,"snapshot_date":snapshot_date.isoformat(),"currency":"GBP","warehouse_id":WAREHOUSE_ID,"row_counts":counts}
    (output_dir/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
    return counts
def main():
    ap=argparse.ArgumentParser(description=__doc__); ap.add_argument('--seed',type=int,default=20261013); ap.add_argument('--products',type=int,default=60); ap.add_argument('--orders',type=int,default=500); ap.add_argument('--snapshot-date',type=date.fromisoformat,default=DEFAULT_SNAPSHOT_DATE); ap.add_argument('--output-dir',type=Path,default=Path('data/sample')); a=ap.parse_args()
    if a.products<1 or a.orders<1: ap.error('--products and --orders must be positive')
    for k,v in generate(a.seed,a.output_dir,a.products,a.orders,a.snapshot_date).items(): print(f'{k}: {v:,}')
if __name__=='__main__': main()
