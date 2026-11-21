"""Governed Data Harness: semantic routing and policy-enforced source adapters.

The workshop ships a working BigQuery adapter and a source-adapter contract.
Additional federated systems can implement the same interface without changing
agent-facing tools. This module does not provision or claim live federation.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol


class DataSourceAdapter(Protocol):
    """Minimal adapter contract for a governed data source."""
    source_name: str
    def fetch_metric(self, metric_id: str, parameters: dict[str, Any]) -> dict[str, Any]: ...


@dataclass(frozen=True)
class HarnessPolicy:
    allowed_sources: tuple[str, ...] = ("bigquery",)
    allowed_metric_ids: tuple[str, ...] = ()
    max_rows: int = 100
    read_only: bool = True

    def validate(self, source_name: str, metric_id: str) -> None:
        if not self.read_only:
            raise PermissionError("Workshop Data Harness is read-only.")
        if source_name not in self.allowed_sources:
            raise PermissionError(f"Source '{source_name}' is not approved by policy.")
        if self.allowed_metric_ids and metric_id not in self.allowed_metric_ids:
            raise PermissionError(f"Metric '{metric_id}' is not approved by policy.")


class SemanticCatalogue:
    """Loads canonical metric definitions and resolves IDs to governed metadata."""
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.document = json.loads(self.path.read_text(encoding="utf-8"))
        self.metrics = {m["id"]: m for m in self.document.get("metrics", [])}

    def get_metric(self, metric_id: str) -> dict[str, Any]:
        try:
            return self.metrics[metric_id]
        except KeyError as exc:
            raise KeyError(f"Metric '{metric_id}' is not in the semantic catalogue.") from exc


class BigQuerySemanticViewAdapter:
    """Read-only BigQuery adapter restricted to an explicit metric->view map."""
    source_name = "bigquery"

    METRIC_VIEW_MAP = {
        "inventory.products_below_safety_stock": "v_inventory_risk_summary",
        "inventory.shortage_units": "v_inventory_risk_summary",
        "inventory.value_at_risk_gbp": "v_inventory_risk_summary",
        "supplier.on_time_delivery_rate": "v_supplier_delivery_performance",
        "supplier.late_deliveries": "v_supplier_delivery_performance",
        "supplier.average_late_days": "v_supplier_delivery_performance",
        "fulfillment.overdue_open_orders": "v_fulfillment_risk_summary",
        "fulfillment.delayed_open_order_value_gbp": "v_fulfillment_risk_summary",
        "supplier.inventory_exposure_gbp": "v_supplier_cross_domain_risk",
        "supplier.products_below_safety_stock": "v_supplier_cross_domain_risk",
        "supplier.overdue_open_order_value_gbp": "v_supplier_cross_domain_risk",
    }

    def __init__(self, project_id: str, dataset_id: str, location: str = "US", client: Any | None = None):
        if client is None:
            from google.cloud import bigquery
            client = bigquery.Client(project=project_id, location=location)
        self.client = client
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.location = location

    def fetch_metric(self, metric_id: str, parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        if metric_id not in self.METRIC_VIEW_MAP:
            raise KeyError(f"No governed BigQuery view mapping for metric '{metric_id}'.")
        view = self.METRIC_VIEW_MAP[metric_id]
        sql = f"SELECT * FROM `{self.project_id}.{self.dataset_id}.{view}` LIMIT @row_limit"
        from google.cloud import bigquery
        job_config = bigquery.QueryJobConfig(query_parameters=[
            bigquery.ScalarQueryParameter("row_limit", "INT64", min(int((parameters or {}).get("limit", 100)), 100))
        ])
        rows = [dict(row.items()) for row in self.client.query(sql, job_config=job_config, location=self.location).result()]
        return {"source": self.source_name, "view": view, "metric_id": metric_id, "rows": rows,
                "row_count": len(rows), "query_sql": sql, "read_only": True}


class GovernedDataHarness:
    """Resolve semantics, enforce source/metric policy, then call an adapter."""
    def __init__(self, catalogue: SemanticCatalogue, adapters: dict[str, DataSourceAdapter], policy: HarnessPolicy):
        self.catalogue = catalogue
        self.adapters = adapters
        self.policy = policy

    def invoke_tool(self, metric_id: str, tool_callable: Any, parameters: dict[str, Any] | None = None, source_name: str = "bigquery") -> dict[str, Any]:
        """Invoke a pre-approved read-only tool through semantic and policy checks."""
        metric = self.catalogue.get_metric(metric_id)
        self.policy.validate(source_name, metric_id)
        if not callable(tool_callable):
            raise TypeError("tool_callable must be callable")
        evidence = tool_callable(**(parameters or {}))
        # Standardise the view identifier in the evidence envelope. Individual
        # BigQuery tools historically returned this as `view`; notebook checks
        # and downstream consumers use the clearer `source_view` name.
        if isinstance(evidence, dict) and "source_view" not in evidence and evidence.get("view"):
            evidence = {**evidence, "source_view": evidence["view"]}
        return {
            "metric": {"id": metric["id"], "name": metric["name"], "unit": metric["unit"], "interpretation": metric["interpretation"], "formula": metric.get("formula"), "entity_grain": metric.get("entity_grain"), "caveats": metric.get("caveats", [])},
            "evidence": evidence,
            "provenance": {"source": source_name, "metric_id": metric_id, "catalogue_file": self.catalogue.path.name, "retrieved_at_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat()},
            "policy": {"source": source_name, "read_only": self.policy.read_only, "max_rows": self.policy.max_rows},
        }

    def retrieve(self, metric_id: str, source_name: str = "bigquery", parameters: dict[str, Any] | None = None) -> dict[str, Any]:
        metric = self.catalogue.get_metric(metric_id)
        self.policy.validate(source_name, metric_id)
        if source_name not in self.adapters:
            raise KeyError(f"No adapter is registered for source '{source_name}'.")
        bounded_parameters = dict(parameters or {})
        requested_limit = int(bounded_parameters.get("limit", self.policy.max_rows))
        bounded_parameters["limit"] = max(1, min(requested_limit, self.policy.max_rows))
        result = self.adapters[source_name].fetch_metric(metric_id, bounded_parameters)
        from .governance import build_evidence_provenance
        metric_contract = {"id": metric["id"], "name": metric["name"], "unit": metric["unit"],
                           "interpretation": metric["interpretation"], "formula": metric.get("formula"),
                           "entity_grain": metric.get("entity_grain"), "caveats": metric.get("caveats", [])}
        evidence_payload = result
        sql = result.get("query_sql", "") if isinstance(result, dict) else ""
        provenance = build_evidence_provenance(
            metric=metric_contract, source_view=(result.get("source_view") or result.get("view", "unknown")) if isinstance(result, dict) else "unknown",
            sql=sql, row_count=result.get("row_count") if isinstance(result, dict) else None,
            snapshot_date=(str(result.get("rows", [{}])[0].get("snapshot_date") or result.get("rows", [{}])[0].get("as_of_date"))
                           if isinstance(result, dict) and result.get("rows") else None),
            validation_checks=("semantic_metric_resolved", "source_allow_list", "read_only", "row_limit"),
        )
        return {
            "metric": metric_contract,
            "evidence": evidence_payload,
            "provenance": provenance,
            "policy": {"source": source_name, "read_only": self.policy.read_only, "max_rows": self.policy.max_rows},
        }


def build_bigquery_harness(project_id: str, dataset_id: str, catalogue_path: str | Path, location: str = "US") -> GovernedDataHarness:
    catalogue = SemanticCatalogue(catalogue_path)
    allowed_ids = tuple(BigQuerySemanticViewAdapter.METRIC_VIEW_MAP.keys())
    adapter = BigQuerySemanticViewAdapter(project_id, dataset_id, location)
    policy = HarnessPolicy(allowed_sources=("bigquery",), allowed_metric_ids=allowed_ids, max_rows=100, read_only=True)
    return GovernedDataHarness(catalogue, {"bigquery": adapter}, policy)

# Business-question planning is deliberately deterministic in the core lab:
# it resolves business language to approved semantic metrics before any data
# retrieval. A model may propose a plan in an advanced extension, but policy
# validation and allow-listed execution remain deterministic.
@dataclass(frozen=True)
class BusinessQuestionPlan:
    question: str
    domains: tuple[str, ...]
    metric_ids: tuple[str, ...]
    dimensions: tuple[str, ...]
    source: str = "semantic_catalogue_rules"
    requires_clarification: bool = False
    clarification: str | None = None


class SemanticQueryPlanner:
    """Resolve common workshop business questions to approved metric plans."""
    RULES = (
        ("inventory", ("inventory", "stock", "shortage", "safety stock", "stockout")),
        ("supplier", ("supplier", "vendor", "on-time", "on time", "late delivery", "lead time")),
        ("fulfillment", ("fulfilment", "fulfillment", "order", "overdue", "customer delivery")),
    )
    METRICS = {
        "inventory": ("inventory.products_below_safety_stock", "inventory.shortage_units", "inventory.value_at_risk_gbp"),
        "supplier": ("supplier.on_time_delivery_rate", "supplier.late_deliveries", "supplier.average_late_days"),
        "fulfillment": ("fulfillment.overdue_open_orders", "fulfillment.delayed_open_order_value_gbp"),
    }
    DIMENSION_TERMS = {
        "supplier": ("supplier", "vendor"),
        "product": ("product", "sku"),
        "warehouse": ("warehouse", "site"),
        "category": ("category", "categories"),
        "date": ("trend", "over time", "by date", "snapshot"),
    }

    def __init__(self, catalogue: SemanticCatalogue):
        self.catalogue = catalogue

    def plan(self, question: str) -> BusinessQuestionPlan:
        if not question or not question.strip():
            raise ValueError("A business question is required.")
        q = question.casefold()
        domains = tuple(domain for domain, terms in self.RULES if any(term in q for term in terms))
        if not domains:
            return BusinessQuestionPlan(question, (), (), (), requires_clarification=True,
                clarification="I could not map the question to an approved inventory, supplier or fulfilment domain. Please specify the business subject.")
        metric_ids = []
        for domain in domains:
            metric_ids.extend(self.METRICS[domain])
        # Cross-domain supplier attribution is only selected when the question
        # explicitly asks to relate suppliers to stock or order exposure.
        if "supplier" in domains and ("inventory" in domains or "fulfillment" in domains):
            metric_ids.extend(("supplier.inventory_exposure_gbp", "supplier.products_below_safety_stock", "supplier.overdue_open_order_value_gbp"))
        # Validate every planned metric against the catalogue, not just the rule table.
        for metric_id in metric_ids:
            self.catalogue.get_metric(metric_id)
        dimensions = tuple(name for name, terms in self.DIMENSION_TERMS.items() if any(term in q for term in terms))
        return BusinessQuestionPlan(question, domains, tuple(dict.fromkeys(metric_ids)), dimensions)


def plan_business_question(question: str, catalogue_path: str | Path | None = None) -> dict[str, Any]:
    """Public helper for notebook and agent use; plans but does not execute SQL."""
    if catalogue_path is None:
        catalogue_path = Path(__file__).resolve().parents[1] / "semantic_catalogue" / "metrics.json"
    planner = SemanticQueryPlanner(SemanticCatalogue(catalogue_path))
    result = planner.plan(question)
    return {
        "question": result.question,
        "domains": list(result.domains),
        "metric_ids": list(result.metric_ids),
        "dimensions": list(result.dimensions),
        "source": result.source,
        "requires_clarification": result.requires_clarification,
        "clarification": result.clarification,
        "execution": "not_executed",
    }
