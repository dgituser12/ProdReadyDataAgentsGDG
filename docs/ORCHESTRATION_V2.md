# Orchestration v2 — implementation notes

## Why v2 exists

Orchestration v1 supplied the data foundation, metric catalogue, inventory Skill, BigQuery tools, route classifier and integration seams. It did not yet build a coordinator with domain specialists. v2 adds that progressive architecture without regenerating the synthetic dataset or business metrics.

## Added in v2

- A standalone ADK single-agent factory for the beginner exercise.
- Inventory, Supplier and Fulfilment specialist agents, each with a domain Skill and narrow read-only tool allow-list.
- An ADK coordinator that declares the specialists as `single_turn` sub-agents.
- `CROSS_DOMAIN` routing for explicit multi-domain questions; `UNCERTAIN` remains reserved for ambiguous/unsupported questions.
- A deterministic specialist-target planner and bounded delegation-plan helper for transparent teaching and local evaluation.
- Multi-agent evaluation fixture and script.
- A Track A coordinator factory that wraps one managed Conversational Analytics data agent with three domain-scoped ADK sub-agent wrappers. These wrappers do not represent three separate managed data-agent resources and are not security boundaries.

## Retained from v1

The synthetic data, generator, validator, BigQuery loader, business metrics, semantic catalogue, SQL views, read-only BigQuery functions, inventory Skill and original tests remain in place. Supplier and fulfilment Skills are additive.

## ADK API decision

The ADK factories target `google-adk==2.15.0`. The implementation uses the documented `LlmAgent.sub_agents` collaboration model and `mode="single_turn"` for specialist sub-agents. Skill loading uses `google.adk.skills.load_skill_from_dir` with `google.adk.tools.skill_toolset.SkillToolset`.

The local build environment did not have `google-adk` installed, and package installation was unavailable. Therefore:

- The Python source is syntax-checked.
- Dependency-free tests cover router, policy, specialist planning, Track A callable routing and Skill package structure.
- The ADK factories have not been imported/executed against the installed package in this environment.
- Live BigQuery, Gemini Decisions and Conversational Analytics API calls have not been run.

Before a live workshop run, install the pinned requirements in Colab, instantiate the ADK factories, run the ADK CLI/Runner smoke test, configure ADC and IAM, and validate the managed Conversational Analytics data-agent resource and API permissions.

## Track A architecture note

Google documents a governed ADK `DataAgentToolset` pattern for invoking a preconfigured Conversational Analytics data agent by resource ID. The repo's callable injection keeps resource IDs, project, region and connection details external to source control. The Track A coordinator wraps that single managed data agent with three ADK specialists scoped by domain prompts. The managed agent still sees the data and permissions configured on its resource; prompt scopes are not equivalent to IAM, row-level security or separate agent resources.

## Evaluation boundaries

- Router evaluation: 16/16 labelled cases pass the deterministic fixture.
- Multi-agent specialist-target evaluation: 6/6 labelled cases pass the deterministic fixture.
- Unit tests: run `python -m pytest -q`.

These results demonstrate fixture consistency only. They do not measure LLM delegation accuracy, grounded-answer quality, live API reliability, security posture or production readiness.
