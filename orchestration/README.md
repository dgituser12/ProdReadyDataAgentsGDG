# Shared orchestration and progressive agent architecture

This package now supports the workshop progression from a single agent to a coordinator-led team of domain specialists. The core router, delegation baseline and policy tests remain dependency-free. ADK agent factories import Google ADK lazily.

## Progressive architecture

1. **Single agent:** `orchestration.agents.build_single_agent()` builds one focused agent for a selected domain. This is the Notebook 1 beginner path.
2. **Specialists:** `orchestration.agents.build_specialist_agents()` creates Inventory, Supplier and Fulfilment agents with narrow read-only tool access and domain Skills.
3. **Coordinator:** `orchestration.agents.build_coordinator_agent()` creates a root `LlmAgent` with the three specialists as `single_turn` sub-agents. ADK exposes these as delegation tools to the coordinator.

The factories target `google-adk==2.15.0`. The ADK collaboration API supports `sub_agents` and `mode="single_turn"` for specialist agents. The coordinator is the root; do not assign it a sub-agent mode. The ADK package is not installed in the lightweight test environment used for this repository build, so these factories have been syntax-checked and reviewed against the official 2.15.0 docs but have not been executed against a live ADK runtime. See the repository README and test notes.

## Route contract

- `INVENTORY_RISK`
- `SUPPLIER_RISK`
- `FULFILMENT_DELAY`
- `GENERAL_QUESTION`
- `CROSS_DOMAIN`
- `UNCERTAIN`

`CROSS_DOMAIN` is used for explicit requests that mention two or more specialist domains. `UNCERTAIN` remains for ambiguous or unsupported questions. A cross-domain route gives the coordinator no direct BigQuery tools; it must delegate to the relevant specialists. The deterministic route and specialist planner are teaching baselines, not production-grade semantic classifiers.

## Deterministic fallback and Gemini Decision 1

The local router is always available and needs no credentials. Enable Decision 1 only when explicitly opted in:

```python
from orchestration.router import route_question

local = route_question("Which products are below safety stock?")
decision = route_question(
    "Which suppliers contribute to inventory shortages and overdue orders?",
    use_decision_model=True,
)
```

Decision 1 is retained as an illustrative integration only and is not enabled in the workshop environment. Its Decisions API requires `google-genai>=3.2.0,<4`, which conflicts with the `google-genai<3` dependency required by the pinned ADK 2.15.0 environment. Do not upgrade the SDK or install a separate Decision 1 dependency set for this workshop. Use the deterministic local router.

The default threshold of 0.70 is a workshop starting value, not a validated production threshold. Calibrate it against labelled examples. Run `python scripts/evaluate_router.py` for the small labelled routing fixture; its score is not production evidence.

## Route-to-tool policy

| Route | Direct tools | Behaviour |
|---|---|---|
| INVENTORY_RISK | `get_inventory_risk`, `get_inventory_summary` | Focused inventory agent |
| SUPPLIER_RISK | `get_supplier_performance` | Focused supplier agent |
| FULFILMENT_DELAY | `get_fulfillment_exposure`, `get_fulfillment_summary` | Focused fulfilment agent |
| GENERAL_QUESTION | `get_inventory_summary`, `get_fulfillment_summary` | General summary path |
| CROSS_DOMAIN | none | Coordinator delegates to relevant specialists |
| UNCERTAIN | none | Ask a clarifying question |

`tools_for_route()` and `invoke_routed_tool()` enforce allow-lists for deterministic tool invocation. Specialist ADK agents are constructed with only their domain's functions.

## Specialist planning baseline

`orchestration.delegation.specialists_for_question()` is a transparent keyword-based baseline for evaluation. `build_delegation_plan()` applies a maximum specialist-call bound. The ADK coordinator uses its `sub_agents` collaboration tools for actual LLM-directed delegation; do not mistake the keyword planner for a hard security boundary.

Run:

```bash
python scripts/evaluate_router.py
python scripts/evaluate_multi_agent.py
python -m pytest -q
```

The fixtures are small teaching sets. Extend and review them with participant-generated questions before calibrating thresholds or making reliability claims.

## Track integration

- **Track A — Managed Conversational Analytics + ADK:** `create_track_a_adk_agent()` wraps an injected managed data-agent callable for a focused single-agent exercise. `create_track_a_coordinator_adk_agent()` builds a coordinator and three domain-scoped ADK wrappers that call the same configured managed Conversational Analytics data agent. They are not three independently provisioned managed data-agent resources. The wrapper prompts are not security boundaries; IAM and the managed data-agent's data permissions remain authoritative. For a production integration, Google documents ADK's governed `DataAgentToolset` pattern for calling a preconfigured data agent by ID; configure that separately with the project's actual agent resource and IAM.
- **Track B — ADK-only + BigQuery:** `create_track_b_adk_agent()` builds a focused single agent for domain routes, or the coordinator with three specialists when `route="CROSS_DOMAIN"`. `build_specialist_agents()` and `build_coordinator_agent()` are also exposed directly.

Track A's injected callable keeps project ID, region, agent resource and connection details out of this repository. Both tracks must be configured read-only and use the same business definitions. Live managed-service and ADK execution require Google Cloud setup and have not been tested in this local build.

## Response grounding

`build_grounded_answer_context()` provides the as-of date, warehouse, currency, metric catalogue path and mandatory interpretation rules. In live notebooks, set the snapshot date and warehouse from the validated dataset manifest rather than accepting defaults.
