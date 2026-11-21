from pathlib import Path
from data_harness.core import SemanticCatalogue, SemanticQueryPlanner

ROOT = Path(__file__).resolve().parents[1]


def test_inventory_question_resolves_to_catalogue_metrics():
    planner = SemanticQueryPlanner(SemanticCatalogue(ROOT / 'semantic_catalogue/metrics.json'))
    plan = planner.plan('Which products have the largest stock shortages?')
    assert 'inventory' in plan.domains
    assert 'inventory.shortage_units' in plan.metric_ids
    assert not plan.requires_clarification


def test_cross_domain_supplier_question_includes_attribution_metrics():
    planner = SemanticQueryPlanner(SemanticCatalogue(ROOT / 'semantic_catalogue/metrics.json'))
    plan = planner.plan('Which suppliers are associated with inventory risk and overdue fulfilment orders?')
    assert set(plan.domains) == {'inventory', 'supplier', 'fulfillment'}
    assert 'supplier.inventory_exposure_gbp' in plan.metric_ids
    assert 'supplier.overdue_open_order_value_gbp' in plan.metric_ids


def test_ambiguous_question_requests_clarification():
    planner = SemanticQueryPlanner(SemanticCatalogue(ROOT / 'semantic_catalogue/metrics.json'))
    plan = planner.plan('Tell me something interesting')
    assert plan.requires_clarification
    assert not plan.metric_ids
