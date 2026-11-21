#!/usr/bin/env python3
"""Read-only, allow-listed BigQuery tools for the GDG Essex supply-chain agents.

The public functions are deliberately plain Python callables so they can be
wrapped by either workshop agent track. No user-supplied SQL or table names.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

try:
    from google.cloud import bigquery
except ImportError:  # Keep local tests and CSV-only track dependency-free.
    bigquery = None

DEFAULT_DATASET = "gdg_essex_data_agents"
DEFAULT_LOCATION = "US"
MAX_ROWS = 100
DEFAULT_MAX_BYTES_BILLED = 50_000_000
ALLOWED_INVENTORY_STATUSES = {"CRITICAL", "AT_RISK", "HEALTHY"}
ALLOWED_ORDER_STATUSES = {"PROCESSING", "IN_TRANSIT", "DELAYED", "DELIVERED", "CANCELLED"}
ALLOWED_SUPPLIER_TIERS = {"LOW", "MEDIUM", "HIGH"}
_IDENTIFIER = re.compile(r"^[A-Za-z0-9_-]+$")


def _json_value(value: Any) -> Any:
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


class SupplyChainBigQueryTools:
    """Small read-only query surface over the canonical semantic views."""

    def __init__(
        self,
        project_id: str,
        dataset_id: str = DEFAULT_DATASET,
        location: str = DEFAULT_LOCATION,
        client: Any | None = None,
        max_bytes_billed: int = DEFAULT_MAX_BYTES_BILLED,
    ):
        if not _IDENTIFIER.fullmatch(project_id):
            raise ValueError("Invalid project_id")
        if not _IDENTIFIER.fullmatch(dataset_id):
            raise ValueError("Invalid dataset_id")
        if max_bytes_billed <= 0:
            raise ValueError("max_bytes_billed must be positive")
        self.project_id = project_id
        self.dataset_id = dataset_id
        self.location = location
        self.max_bytes_billed = max_bytes_billed
        if client is None:
            if bigquery is None:
                raise RuntimeError(
                    "BigQuery SDK not installed. Run: pip install google-cloud-bigquery"
                )
            client = bigquery.Client(project=project_id, location=location)
        self.client = client

    def _query(self, sql: str, parameters: list[Any], limit: int) -> dict[str, Any]:
        safe_limit = max(1, min(int(limit), MAX_ROWS))
        # Every query is fixed SQL with typed parameters; caller input never becomes SQL.
        sql = sql.replace("@row_limit", str(safe_limit))
        if bigquery is not None:
            config = bigquery.QueryJobConfig(
                query_parameters=parameters,
                maximum_bytes_billed=self.max_bytes_billed,
                use_legacy_sql=False,
            )
        else:
            # Allows unit tests to exercise query construction with a fake client.
            config = {"query_parameters": parameters, "maximum_bytes_billed": self.max_bytes_billed}
        job = self.client.query(sql, job_config=config, location=self.location)
        rows = list(job.result())
        return {
            "rows": [{k: _json_value(v) for k, v in dict(row.items()).items()} for row in rows],
            "row_count": len(rows),
            "row_limit": safe_limit,
            "read_only": True,
            "query_sql": sql,
            "source_view": (re.search(r"FROM\s+`[^`]+\.([^`.]+)`", sql, re.IGNORECASE).group(1)
                           if re.search(r"FROM\s+`[^`]+\.([^`.]+)`", sql, re.IGNORECASE) else None),
        }

    def inventory_risk(
        self,
        inventory_status: str | None = None,
        category: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List products with inventory risk, ordered by value at risk then shortage."""
        if inventory_status and inventory_status not in ALLOWED_INVENTORY_STATUSES:
            raise ValueError(f"inventory_status must be one of {sorted(ALLOWED_INVENTORY_STATUSES)}")
        sql = f"""
        SELECT snapshot_date, warehouse_id, product_id, product_name, category,
               criticality, available_quantity, safety_stock, shortage_units,
               unit_cost_gbp, inventory_value_at_risk_gbp, inventory_status
        FROM `{self.project_id}.{self.dataset_id}.v_inventory_product_risk`
        WHERE (@inventory_status IS NULL OR inventory_status = @inventory_status)
          AND (@category IS NULL OR category = @category)
        ORDER BY inventory_value_at_risk_gbp DESC, shortage_units DESC, product_id
        LIMIT @row_limit
        """
        params = []
        if bigquery is not None:
            params = [
                bigquery.ScalarQueryParameter("inventory_status", "STRING", inventory_status),
                bigquery.ScalarQueryParameter("category", "STRING", category),
            ]
        else:
            params = [{"name":"inventory_status","type":"STRING","value":inventory_status},
                      {"name":"category","type":"STRING","value":category}]
        return self._query(sql, params, limit)

    def supplier_performance(
        self,
        supplier_risk_tier: str | None = None,
        limit: int = 20,
    ) -> dict[str, Any]:
        """Compare supplier profile tier and observed delivery performance separately."""
        if supplier_risk_tier and supplier_risk_tier not in ALLOWED_SUPPLIER_TIERS:
            raise ValueError(f"supplier_risk_tier must be one of {sorted(ALLOWED_SUPPLIER_TIERS)}")
        sql = f"""
        SELECT supplier_id, supplier_name, supplier_risk_tier, standard_lead_time_days,
               delivered_orders, on_time_deliveries, late_deliveries,
               on_time_delivery_rate, average_late_days
        FROM `{self.project_id}.{self.dataset_id}.v_supplier_delivery_performance`
        WHERE (@supplier_risk_tier IS NULL OR supplier_risk_tier = @supplier_risk_tier)
        ORDER BY on_time_delivery_rate ASC NULLS FIRST, late_deliveries DESC, supplier_id
        LIMIT @row_limit
        """
        param = (bigquery.ScalarQueryParameter("supplier_risk_tier", "STRING", supplier_risk_tier)
                 if bigquery is not None else
                 {"name":"supplier_risk_tier","type":"STRING","value":supplier_risk_tier})
        return self._query(sql, [param], limit)

    def fulfillment_exposure(
        self,
        order_status: str | None = None,
        only_overdue: bool = True,
        limit: int = 20,
    ) -> dict[str, Any]:
        """List open overdue orders by age and value; optionally include other statuses."""
        if order_status and order_status not in ALLOWED_ORDER_STATUSES:
            raise ValueError(f"order_status must be one of {sorted(ALLOWED_ORDER_STATUSES)}")
        sql = f"""
        SELECT order_id, as_of_date, order_date, promised_delivery_date,
               product_id, supplier_id, quantity_ordered, order_status,
               current_overdue_days, is_overdue_open_order, order_value_gbp
        FROM `{self.project_id}.{self.dataset_id}.v_fulfillment_order_exposure`
        WHERE (@order_status IS NULL OR order_status = @order_status)
          AND (NOT @only_overdue OR is_overdue_open_order)
        ORDER BY is_overdue_open_order DESC, current_overdue_days DESC,
                 order_value_gbp DESC, order_id
        LIMIT @row_limit
        """
        if bigquery is not None:
            params = [
                bigquery.ScalarQueryParameter("order_status", "STRING", order_status),
                bigquery.ScalarQueryParameter("only_overdue", "BOOL", only_overdue),
            ]
        else:
            params = [{"name":"order_status","type":"STRING","value":order_status},
                      {"name":"only_overdue","type":"BOOL","value":only_overdue}]
        return self._query(sql, params, limit)

    def inventory_summary(self) -> dict[str, Any]:
        """Return one row per snapshot and warehouse with canonical inventory KPIs."""
        sql = f"""
        SELECT snapshot_date, warehouse_id, product_count, available_stock_units,
               products_below_safety_stock, critical_products, stockout_products,
               shortage_units, inventory_value_at_risk_gbp
        FROM `{self.project_id}.{self.dataset_id}.v_inventory_risk_summary`
        ORDER BY snapshot_date DESC, warehouse_id
        LIMIT 100
        """
        return self._query(sql, [], 100)

    def supplier_cross_domain_risk(self, limit: int = 20) -> dict[str, Any]:
        """Compare supplier delivery performance with attributed inventory and overdue-order exposure."""
        sql = f"""
        SELECT supplier_id, supplier_name, supplier_risk_tier, standard_lead_time_days,
               delivered_orders, on_time_delivery_rate, late_deliveries, average_late_days,
               as_of_date, warehouse_id, products_below_safety_stock,
               inventory_value_at_risk_gbp, overdue_open_orders,
               overdue_open_order_value_gbp
        FROM `{self.project_id}.{self.dataset_id}.v_supplier_cross_domain_risk`
        ORDER BY inventory_value_at_risk_gbp DESC, overdue_open_order_value_gbp DESC,
                 on_time_delivery_rate ASC NULLS FIRST, supplier_id
        LIMIT @row_limit
        """
        return self._query(sql, [], limit)

    def fulfillment_summary(self) -> dict[str, Any]:
        """Return portfolio-level fulfilment exposure and delivery performance."""
        sql = f"""
        SELECT as_of_date, total_orders, delivered_orders, open_orders,
               overdue_open_orders, current_overdue_days_total,
               delivered_late_orders, on_time_delivery_rate,
               delayed_open_order_value_gbp
        FROM `{self.project_id}.{self.dataset_id}.v_fulfillment_risk_summary`
        ORDER BY as_of_date DESC
        LIMIT 100
        """
        return self._query(sql, [], 100)


def build_tool_functions(project_id: str, dataset_id: str = DEFAULT_DATASET,
                         location: str = DEFAULT_LOCATION) -> dict[str, Any]:
    """Return agent callables routed through the governed Data Harness."""
    from functools import wraps
    from pathlib import Path
    from data_harness.core import build_bigquery_harness

    tools = SupplyChainBigQueryTools(project_id, dataset_id, location)
    catalogue_path = Path(__file__).resolve().parents[1] / "semantic_catalogue" / "metrics.json"
    harness = build_bigquery_harness(project_id, dataset_id, catalogue_path, location)

    def governed(metric_id: str, fn: Any) -> Any:
        @wraps(fn)
        def invoke(**kwargs: Any) -> dict[str, Any]:
            return harness.invoke_tool(metric_id, fn, kwargs, source_name="bigquery")
        invoke.__doc__ = (fn.__doc__ or "") + " Governed by the workshop Data Harness; read-only, semantic metric allow-list enforced."
        return invoke

    return {
        "get_inventory_risk": governed("inventory.value_at_risk_gbp", tools.inventory_risk),
        "get_supplier_performance": governed("supplier.on_time_delivery_rate", tools.supplier_performance),
        "get_fulfillment_exposure": governed("fulfillment.overdue_open_orders", tools.fulfillment_exposure),
        "get_inventory_summary": governed("inventory.shortage_units", tools.inventory_summary),
        "get_fulfillment_summary": governed("fulfillment.delayed_open_order_value_gbp", tools.fulfillment_summary),
        "get_supplier_cross_domain_risk": governed("supplier.inventory_exposure_gbp", tools.supplier_cross_domain_risk),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", required=True)
    parser.add_argument("--dataset", default=DEFAULT_DATASET)
    parser.add_argument("--location", default=DEFAULT_LOCATION)
    args = parser.parse_args()
    tools = SupplyChainBigQueryTools(args.project, args.dataset, args.location)
    print(json.dumps({
        "inventory": tools.inventory_summary(),
        "fulfillment": tools.fulfillment_summary(),
    }, indent=2))


if __name__ == "__main__":
    main()
