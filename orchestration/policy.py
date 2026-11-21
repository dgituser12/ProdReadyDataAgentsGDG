"""Shared orchestration policy and route-to-tool permissions."""
from __future__ import annotations

from typing import Any, Callable

from .router import ROUTES, RouteDecision, route_question

# Tool allow-list is intentionally narrower than "all tools for all requests".
ROUTE_TOOLS = {
    "INVENTORY_RISK": ("get_inventory_risk", "get_inventory_summary"),
    "SUPPLIER_RISK": ("get_supplier_performance",),
    "FULFILMENT_DELAY": ("get_fulfillment_exposure", "get_fulfillment_summary"),
    "GENERAL_QUESTION": ("get_inventory_summary", "get_fulfillment_summary"),
    # The coordinator delegates to specialists; it receives no direct data tools.
    "CROSS_DOMAIN": (),
    "UNCERTAIN": (),
}


def tools_for_route(route: str, tool_functions: dict[str, Callable[..., Any]]) -> dict[str, Callable[..., Any]]:
    if route not in ROUTES:
        raise ValueError(f"Unsupported route: {route}")
    permitted = ROUTE_TOOLS[route]
    missing = [name for name in permitted if name not in tool_functions]
    if missing:
        raise KeyError(f"Missing required tool function(s): {missing}")
    return {name: tool_functions[name] for name in permitted}


def invoke_routed_tool(
    route: str,
    tool_name: str,
    arguments: dict[str, Any],
    tool_functions: dict[str, Callable[..., Any]],
) -> Any:
    """Enforce route-specific tool allow-list before invoking a read-only tool."""
    available = tools_for_route(route, tool_functions)
    if tool_name not in available:
        raise PermissionError(
            f"Tool '{tool_name}' is not permitted for route '{route}'."
        )
    if not isinstance(arguments, dict):
        raise TypeError("Tool arguments must be a dictionary.")
    return available[tool_name](**arguments)


def prepare_request(
    question: str,
    tool_functions: dict[str, Callable[..., Any]],
    use_decision_model: bool | None = None,
    decision_client: Any | None = None,
    confidence_threshold: float = 0.70,
) -> dict[str, Any]:
    """Return the routing decision and only the tools permitted for that route."""
    decision: RouteDecision = route_question(
        question,
        use_decision_model=use_decision_model,
        client=decision_client,
        confidence_threshold=confidence_threshold,
    )
    permitted_tools = tools_for_route(decision.route, tool_functions)
    return {
        "decision": {
            "route": decision.route,
            "confidence": decision.confidence,
            "source": decision.source,
            "reason": decision.reason,
        },
        "tools": permitted_tools,
        "needs_clarification": decision.route == "UNCERTAIN",
        "read_only": True,
    }


def build_grounded_answer_context(
    decision: dict[str, Any],
    tool_result: dict[str, Any] | None,
    snapshot_date: str = "2026-10-01",
    warehouse_id: str = "WH-ESSEX-01",
    currency: str = "GBP",
) -> dict[str, Any]:
    """Standard context envelope for either track's response composer."""
    return {
        "route": decision["route"],
        "as_of_date": snapshot_date,
        "warehouse_scope": warehouse_id,
        "currency": currency,
        "metric_source": "semantic_catalogue/metrics.json",
        "tool_result": tool_result,
        "answering_rules": [
            "Do not invent a metric or missing value.",
            "Distinguish supplier profile risk from observed delivery performance.",
            "Distinguish late delivered orders from overdue open orders.",
            "Describe inventory value at risk as a safety-stock shortfall valued at unit cost, not lost revenue.",
            "State the as-of date and warehouse scope when reporting snapshot metrics.",
        ],
    }
