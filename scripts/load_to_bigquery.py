#!/usr/bin/env python3
"""Load synthetic CSVs to BigQuery using explicit schemas. Requires google-cloud-bigquery."""
import argparse
from pathlib import Path
try: from google.cloud import bigquery
except ImportError: bigquery=None
SCHEMAS={
'suppliers':[('supplier_id','STRING'),('supplier_name','STRING'),('country','STRING'),('supplier_risk_tier','STRING'),('standard_lead_time_days','INT64'),('active','BOOL')],
'products':[('product_id','STRING'),('product_name','STRING'),('category','STRING'),('supplier_id','STRING'),('unit_cost_gbp','NUMERIC'),('safety_stock','INT64'),('criticality','STRING')],
'inventory_snapshot':[('snapshot_id','STRING'),('snapshot_date','DATE'),('warehouse_id','STRING'),('warehouse_name','STRING'),('product_id','STRING'),('quantity_on_hand','INT64'),('quantity_reserved','INT64'),('available_quantity','INT64'),('safety_stock','INT64'),('inventory_status','STRING')],
'fulfillment_orders':[('order_id','STRING'),('order_date','DATE'),('promised_delivery_date','DATE'),('actual_delivery_date','DATE'),('product_id','STRING'),('supplier_id','STRING'),('quantity_ordered','INT64'),('order_status','STRING'),('delay_days','INT64'),('warehouse_id','STRING'),('order_value_gbp','NUMERIC')]}
def exists(client,table_id):
    from google.api_core.exceptions import NotFound
    try: client.get_table(table_id); return True
    except NotFound: return False
def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--project',required=True); p.add_argument('--dataset',required=True); p.add_argument('--input-dir',type=Path,default=Path('data/sample')); p.add_argument('--location',default='US'); p.add_argument('--write-mode',choices=['fail','truncate','append'],default='fail'); p.add_argument('--create-dataset',action='store_true'); a=p.parse_args()
    if bigquery is None: raise SystemExit('Install workshop dependencies: pip install -r requirements-agent.txt')
    client=bigquery.Client(project=a.project); ds=f'{a.project}.{a.dataset}'
    if a.create_dataset:
        d=bigquery.Dataset(ds); d.location=a.location; client.create_dataset(d,exists_ok=True)
    else: client.get_dataset(ds)
    for name,cols in SCHEMAS.items():
        path=a.input_dir/f'{name}.csv'; table=f'{ds}.{name}'
        if not path.exists(): raise SystemExit(f'Missing {path}')
        present=exists(client,table)
        if present and a.write_mode=='fail': raise SystemExit(f'{table} exists; choose --write-mode truncate or append explicitly')
        disposition={'fail':bigquery.WriteDisposition.WRITE_EMPTY,'truncate':bigquery.WriteDisposition.WRITE_TRUNCATE,'append':bigquery.WriteDisposition.WRITE_APPEND}[a.write_mode]
        config=bigquery.LoadJobConfig(schema=[bigquery.SchemaField(n,t) for n,t in cols],source_format=bigquery.SourceFormat.CSV,skip_leading_rows=1,autodetect=False,write_disposition=disposition)
        with path.open('rb') as f: job=client.load_table_from_file(f,table,job_config=config)
        job.result(); result=client.get_table(table); print(f'Loaded {result.num_rows:,} rows into {result.full_table_id}')
if __name__=='__main__': main()
