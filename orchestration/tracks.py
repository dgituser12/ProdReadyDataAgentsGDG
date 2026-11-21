"""Framework integration seam for the two workshop implementation tracks.

Track B has an optional ADK-native builder. Track A receives the managed
Conversational Analytics call as an injected function because tenant setup,
API surface and permissions are environment-specific.
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable

from .policy import prepare_request, build_grounded_answer_context


def run_track_a(
    question: str,
    managed_conversational_analytics: Callable[..., Any],
    tool_functions: dict[str, Callable[..., Any]],
    use_decision_model: bool | None = None,
    decision_client: Any | None = None,
) -> dict[str, Any]:
    """ADK-orchestrator seam for Track A's managed Conversational Analytics.

    The injected callable is expected to invoke the configured managed data
    agent using the same question and semantic context. This avoids assuming
    one managed-agent API, project ID, region or connection name.
    """
    prepared = prepare_request(
        question, tool_functions, use_decision_model, decision_client
    )
    decision = prepared["decision"]
    if prepared["needs_clarification"]:
        return {
            "decision": decision,
            "needs_clarification": True,
            "clarification": "Should I focus on inventory, supplier performance, or fulfilment delays?",
            "answer": None,
        }
    result = managed_conversational_analytics(
        question=question,
        route=decision["route"],
        metric_catalogue="semantic_catalogue/metrics.json",
        read_only=True,
    )
    return {
        "decision": decision,
        "needs_clarification": False,
        "answer_context": build_grounded_answer_context(decision, result),
        "answer": result,
    }



def create_track_a_adk_agent(
    managed_conversational_analytics: Callable[..., Any],
    route: str,
    model: str = "gemini-2.5-flash",
) -> Any:
    """Create an ADK orchestrator agent around an injected managed data agent.

    The managed Conversational Analytics endpoint itself is configured outside
    this repository; this function supplies a stable callable boundary.
    """
    try:
        from google.adk.agents import LlmAgent
    except ImportError as exc:
        raise RuntimeError(
            "Install the pinned ADK dependencies from requirements-agent.txt"
        ) from exc
    from .policy import ROUTE_TOOLS

    if route not in ROUTE_TOOLS or route == "UNCERTAIN":
        raise ValueError("A supported, non-UNCERTAIN route is required.")

    def ask_managed_data_agent(question: str) -> dict[str, Any]:
        """Ask the managed Conversational Analytics agent a read-only question."""
        return managed_conversational_analytics(
            question=question,
            route=route,
            metric_catalogue="semantic_catalogue/metrics.json",
            read_only=True,
        )

    ask_managed_data_agent.__name__ = "ask_managed_data_agent"
    ask_managed_data_agent.__doc__ = (
        "Run a read-only question against the configured managed Conversational "
        f"Analytics data agent. The request has already been classified as {route}."
    )
    return LlmAgent(
        name="gdg_essex_managed_data_orchestrator",
        model=model,
        instruction=f"""
You are the ADK orchestration agent for the managed Conversational Analytics
track. The request has already been classified as {route}.
Use ask_managed_data_agent for business data questions. Do not invent SQL or
attempt write operations. Respect semantic_catalogue/metrics.json.
Distinguish supplier profile risk from observed performance and late delivered
orders from overdue open orders. State snapshot date, warehouse scope and GBP.
If the managed data agent returns an error or unsupported result, explain it.
""",
        tools=[ask_managed_data_agent],
    )


def create_track_b_adk_agent(
    project_id: str,
    model: str = "gemini-2.5-flash",
    dataset_id: str = "gdg_essex_data_agents",
    location: str = "US",
    route: str = "INVENTORY_RISK",
    skill_directory: str | Path | None = None,
) -> Any:
    """Build the beginner single agent or the multi-agent coordinator.

    CROSS_DOMAIN builds a coordinator with Inventory, Supplier and Fulfilment
    single-turn sub-agents. Other supported routes build one focused agent.
    """
    from .agents import build_coordinator_agent, build_single_agent

    if route == "CROSS_DOMAIN":
        return build_coordinator_agent(
            project_id=project_id,
            model=model,
            dataset_id=dataset_id,
            location=location,
            skill_directory=skill_directory,
        )
    return build_single_agent(
        project_id=project_id,
        model=model,
        dataset_id=dataset_id,
        location=location,
        route=route,
        skill_directory=skill_directory,
    )


def create_track_a_coordinator_adk_agent(
    managed_conversational_analytics: Callable[..., Any],
    model: str = "gemini-2.5-flash",
) -> Any:
    """Create an ADK coordinator with domain-scoped wrappers over one managed CA agent.

    The three ADK specialists are prompt-scoped wrappers around the same
    configured managed Conversational Analytics data agent. They are not three
    separately provisioned managed data-agent resources, and their prompt
    boundaries are not substitutes for IAM or data-level security.
    """
    try:
        from google.adk.agents import LlmAgent
    except ImportError as exc:
        raise RuntimeError(
            "Install google-adk==2.15.0 from requirements-agent.txt"
        ) from exc

    def make_domain_tool(route: str):
        def ask_managed_data_agent(question: str) -> dict[str, Any]:
            """Run a read-only question against the configured managed data agent."""
            return managed_conversational_analytics(
                question=question,
                route=route,
                metric_catalogue="semantic_catalogue/metrics.json",
                read_only=True,
            )
        ask_managed_data_agent.__name__ = f"ask_{route.casefold()}_data_agent"
        ask_managed_data_agent.__doc__ = (
            f"Ask the configured managed Conversational Analytics data agent a read-only {route} question."
        )
        return ask_managed_data_agent

    domain_specs = [
        ("inventory_specialist", "INVENTORY_RISK", "Analyse stock availability, safety-stock gaps, stockouts and inventory value at risk."),
        ("supplier_specialist", "SUPPLIER_RISK", "Analyse supplier profile risk, lead time and observed delivery performance."),
        ("fulfilment_specialist", "FULFILMENT_DELAY", "Analyse open orders, overdue commitments and delayed order value."),
    ]
    specialists = []
    for name, route, description in domain_specs:
        specialists.append(LlmAgent(
            name=name,
            model=model,
            description=description,
            mode="single_turn",
            instruction=(
                f"You are the {name.replace('_', ' ').title()}. Handle only {route} questions. "
                "Use the managed data-agent tool for all data facts. Keep supplier profile risk "
                "separate from observed performance, late delivered orders separate from overdue "
                "open orders, and inventory value at risk separate from lost revenue. Return a "
                "concise evidence-based result to the coordinator. Never perform write actions."
            ),
            tools=[make_domain_tool(route)],
        ))

    return LlmAgent(
        name="gdg_essex_managed_ca_coordinator",
        model=model,
        description="Coordinates domain-scoped specialists backed by a managed Conversational Analytics data agent.",
        instruction=(
            "Coordinate the user's supply-chain question. Delegate to inventory_specialist, "
            "supplier_specialist and/or fulfilment_specialist. For cross-domain questions, "
            "call all relevant specialists and synthesise their evidence. The specialists are "
            "domain-scoped wrappers over one managed data agent, not separate managed resources. "
            "Disclose missing results; never invent facts or perform write actions."
        ),
        sub_agents=specialists,
    )
