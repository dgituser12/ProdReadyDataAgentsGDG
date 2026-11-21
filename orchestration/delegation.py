"""Deterministic specialist planning helpers for the workshop coordinator.

These helpers are intentionally separate from the ADK LLM delegation runtime:
they provide a transparent baseline and a testable contract for evaluation.
"""
from __future__ import annotations

from dataclasses import dataclass

SPECIALIST_DOMAINS = {
    "INVENTORY_RISK": "inventory_specialist",
    "SUPPLIER_RISK": "supplier_specialist",
    "FULFILMENT_DELAY": "fulfilment_specialist",
}

DOMAIN_TERMS = {
    "inventory_specialist": (
        "inventory", "stock", "stockout", "safety stock", "shortage",
        "available stock", "inventory value at risk", "replenish",
    ),
    "supplier_specialist": (
        "supplier", "on-time", "on time", "lead time", "late deliveries",
        "supplier risk", "supplier performance",
    ),
    "fulfilment_specialist": (
        "fulfilment", "fulfillment", "order", "overdue", "delayed",
        "promised date", "delivery delay", "late order",
    ),
}


@dataclass(frozen=True)
class DelegationPlan:
    specialists: tuple[str, ...]
    strategy: str
    max_specialist_calls: int


def specialists_for_question(question: str) -> tuple[str, ...]:
    """Return specialists whose domain terms appear in a question.

    This is a transparent workshop baseline, not a semantic classifier. The
    coordinator LLM may reason beyond these terms; policy and evaluation must
    still constrain and inspect actual delegation.
    """
    text = question.casefold()
    return tuple(
        name for name, terms in DOMAIN_TERMS.items()
        if any(term in text for term in terms)
    )


def build_delegation_plan(question: str, max_specialist_calls: int = 3) -> DelegationPlan:
    if max_specialist_calls < 1:
        raise ValueError("max_specialist_calls must be at least 1")
    selected = specialists_for_question(question)
    if not selected:
        return DelegationPlan((), "clarify_or_general", 0)
    if len(selected) > max_specialist_calls:
        raise ValueError(
            f"Question requires {len(selected)} specialist calls, above the configured "
            f"limit of {max_specialist_calls}; narrow the request or raise the reviewed bound."
        )
    strategy = "single" if len(selected) == 1 else "parallel_independent"
    return DelegationPlan(selected, strategy, len(selected))
