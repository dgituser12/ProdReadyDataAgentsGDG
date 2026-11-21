#!/usr/bin/env python3
"""Calculate canonical workshop business metrics from the synthetic CSV dataset."""
import argparse, csv, json
from collections import defaultdict
from datetime import date
from decimal import Decimal
from pathlib import Path


def rows(path):
    with path.open(newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def dec(v): return Decimal(str(v))
def as_date(v): return date.fromisoformat(v) if v else None
def money(v): return round(float(v), 2)


def calculate(input_dir: Path):
    suppliers = {r['supplier_id']: r for r in rows(input_dir/'suppliers.csv')}
    products = {r['product_id']: r for r in rows(input_dir/'products.csv')}
    inventory = rows(input_dir/'inventory_snapshot.csv')
    orders = rows(input_dir/'fulfillment_orders.csv')
    snapshot = date.fromisoformat(inventory[0]['snapshot_date'])

    inv = []
    for r in inventory:
        p = products[r['product_id']]
        available, safety = int(r['available_quantity']), int(r['safety_stock'])
        shortage = max(safety-available, 0)
        inv.append({**r, 'unit_cost_gbp': p['unit_cost_gbp'], 'shortage_units': shortage,
                    'inventory_value_at_risk_gbp': money(shortage*dec(p['unit_cost_gbp']))})
    total_available = sum(int(r['available_quantity']) for r in inv)
    total_shortage = sum(r['shortage_units'] for r in inv)
    inventory_summary = {
        'snapshot_date': snapshot.isoformat(), 'warehouse_id': inventory[0]['warehouse_id'],
        'product_count': len(inv), 'available_stock_units': total_available,
        'products_below_safety_stock': sum(r['inventory_status'] in ('AT_RISK','CRITICAL') for r in inv),
        'critical_products': sum(r['inventory_status']=='CRITICAL' for r in inv),
        'stockout_products': sum(int(r['available_quantity'])==0 for r in inv),
        'shortage_units': total_shortage,
        'inventory_value_at_risk_gbp': money(sum(dec(r['inventory_value_at_risk_gbp']) for r in inv)),
    }

    delivered = [r for r in orders if r['order_status']=='DELIVERED' and r['actual_delivery_date']]
    on_time = [r for r in delivered if as_date(r['actual_delivery_date']) <= as_date(r['promised_delivery_date'])]
    late_delivered = [r for r in delivered if as_date(r['actual_delivery_date']) > as_date(r['promised_delivery_date'])]
    open_orders = [r for r in orders if r['order_status'] in ('PROCESSING','IN_TRANSIT','DELAYED')]
    overdue = [r for r in open_orders if as_date(r['promised_delivery_date']) < snapshot]
    fulfillment_summary = {
        'snapshot_date': snapshot.isoformat(), 'total_orders': len(orders),
        'delivered_orders': len(delivered), 'open_orders': len(open_orders),
        'overdue_open_orders': len(overdue),
        'current_overdue_days_total': sum((snapshot-as_date(r['promised_delivery_date'])).days for r in overdue),
        'delivered_late_orders': len(late_delivered),
        'on_time_delivery_rate': round(len(on_time)/len(delivered), 4) if delivered else None,
        'delayed_open_order_value_gbp': money(sum(dec(r['order_value_gbp']) for r in overdue)),
    }

    by_supplier = defaultdict(list)
    for r in orders: by_supplier[r['supplier_id']].append(r)
    supplier_metrics=[]
    for sid, profile in suppliers.items():
        facts=by_supplier[sid]
        ds=[r for r in facts if r['order_status']=='DELIVERED' and r['actual_delivery_date']]
        ot=[r for r in ds if as_date(r['actual_delivery_date']) <= as_date(r['promised_delivery_date'])]
        late=[r for r in ds if as_date(r['actual_delivery_date']) > as_date(r['promised_delivery_date'])]
        avg_late=sum((as_date(r['actual_delivery_date'])-as_date(r['promised_delivery_date'])).days for r in late)/len(late) if late else None
        supplier_metrics.append({
            'supplier_id': sid, 'supplier_name': profile['supplier_name'],
            'supplier_risk_tier': profile['supplier_risk_tier'], 'standard_lead_time_days': int(profile['standard_lead_time_days']),
            'active': profile['active'].lower()=='true', 'total_orders': len(facts),
            'delivered_orders': len(ds), 'on_time_deliveries': len(ot), 'late_deliveries': len(late),
            'on_time_delivery_rate': round(len(ot)/len(ds),4) if ds else None,
            'average_late_days': round(avg_late,2) if avg_late is not None else None,
        })
    return {'as_of_date':snapshot.isoformat(),'currency':'GBP','inventory':inventory_summary,
            'fulfillment':fulfillment_summary,'suppliers':supplier_metrics}


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input-dir',type=Path,default=Path('data/sample'))
    ap.add_argument('--output',type=Path,default=Path('data/sample/business_metrics.json'))
    a=ap.parse_args(); result=calculate(a.input_dir)
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8')
    print(f"Wrote canonical metrics for {len(result['suppliers'])} suppliers; as of {result['as_of_date']}")
    print(json.dumps({'inventory':result['inventory'],'fulfillment':result['fulfillment']},indent=2))
if __name__=='__main__': main()
