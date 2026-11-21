from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_cross_domain_view_aggregates_fact_tables_before_join():
    sql = (ROOT / 'semantic_catalogue/sql/metric_views.sql').read_text()
    view = sql.split('v_supplier_cross_domain_risk', 1)[1]
    assert 'inventory_by_supplier AS' in view
    assert 'orders_by_supplier AS' in view
    assert 'GROUP BY p.supplier_id, i.snapshot_date, i.warehouse_id' in view
    assert 'GROUP BY supplier_id, as_of_date' in view
    assert 'LEFT JOIN inventory_by_supplier' in view
    assert 'LEFT JOIN orders_by_supplier' in view


def test_supplier_cross_domain_metrics_are_in_semantic_catalogue():
    import json
    metrics = json.loads((ROOT / 'semantic_catalogue/metrics.json').read_text())['metrics']
    ids = {m['id'] for m in metrics}
    assert {'supplier.inventory_exposure_gbp', 'supplier.products_below_safety_stock',
            'supplier.overdue_open_order_value_gbp'} <= ids
