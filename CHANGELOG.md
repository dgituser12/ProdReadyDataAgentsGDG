## Data Agent enhancement pass

- Added a semantic metric comparison exercise to Notebook 1, emphasizing metric meaning, units and interpretation.
- Added an executable BigQuery freshness and basic completeness preflight to Notebook 2; its status is injected into the Inventory Specialist context so stale data is qualified in agent answers.
- Made query allow-list, row-bounding and bytes-billed controls more explicit across the practical notebooks.
- Added an evidence-backed answer summary and executable data-aware evaluation scorecard to Notebook 3.
- Updated the participant environment to the Colab-tested `google-adk[bigquery-analytics]==2.15.0`; Decision 1 SDK remains excluded.
- Updated the facilitation plan to 165 minutes.

# Changelog

## Orchestration v2

- Preserved the v1 synthetic data, metrics, semantic catalogue, BigQuery tools and inventory Skill.
- Added supplier-performance and fulfilment-exposure Skills.
- Added a single-agent ADK factory for the beginner learning path.
- Added Inventory, Supplier and Fulfilment specialist ADK agents with scoped tools.
- Added an ADK coordinator with `single_turn` specialist sub-agents.
- Added explicit `CROSS_DOMAIN` routing; retained `UNCERTAIN` for ambiguous/unsupported requests.
- Added deterministic specialist planning, bounded delegation-plan validation and multi-agent evaluation fixtures.
- Added Track A coordinator wrappers around one injected managed Conversational Analytics data agent.
- Expanded documentation to distinguish prompt scoping from IAM/security boundaries and local tests from live integration.

## 2026-11-19 — Notebook 2

- Added a 35-minute Colab lab for semantic grounding, Agent Skills, scoped read-only tools, three ADK specialists and deterministic routing preview.
- Reused the shared participant bootstrap and configuration pattern.

## Notebook 3 — Multi-agent system

- Added a 35-minute Colab-first lab that assembles the three domain specialists under an ADK coordinator.
- Includes single-domain and cross-domain execution, event-trace inspection, deterministic planning comparison, fixture evaluation, failure/guardrail review and a participant challenge.
- Includes explicit mapping to the ten workshop concepts and preserves the 150-minute facilitation schedule.

## Notebook 3 — Multi-agent system

- Added a 35-minute Colab-first lab that assembles the three domain specialists under an ADK coordinator.
- Includes single-domain and cross-domain execution, event-trace inspection, deterministic planning comparison, fixture evaluation, failure/guardrail review and a participant challenge.
- Includes explicit mapping to the ten workshop concepts and preserves the 150-minute facilitation schedule.

## Optional integration and Data Harness completion

- Added a governed Data Harness package with semantic metric resolution, source adapter contract, BigQuery semantic-view adapter and policy checks.
- Added optional ADK DataAgentToolset bridge for a pre-configured Conversational Analytics Data Agent.
- Added optional Gemini Decision 1 client factory, explicitly separate from Vertex AI ADC.
- Added optional BigQuery Agent Analytics ADK plugin wiring and a Colab appendix example.
- Added Notebook 2 Data Harness execution exercises and Notebook 3 opt-in integration appendix; all optional switches default to disabled.


## 2026-11-19 — Decision 1 structured exception assessment

- Expanded the optional Notebook 3 Decision 1 lab from single-label route classification to three typed questions about one supply-chain exception dossier: primary domain (`choice`), urgency (`noul`) and severity (`score`).
- Added confidence inspection, configurable threshold, deterministic route fallback, and safe omission of urgency/severity when confidence is low or the API fails.
- Added unit tests for the single-request contract, low-confidence fallback and API-error fallback.
- Core workshop remains unchanged; the optional section is disabled by default and does not add time to the 150-minute agenda.

## Data Agent strengthening

- Added a deterministic semantic query planner that resolves business questions to approved metrics and dimensions, with clarification for unsupported questions.
- Added supplier cross-domain semantic metrics and `v_supplier_cross_domain_risk`, aggregating inventory and overdue orders independently at supplier grain before joining.
- Expanded metric/evidence metadata and specialist instructions to preserve formula, unit, grain, snapshot/as-of date, denominator, caveats and non-causal attribution.
- Added guided exercises to all three Colab notebooks for question-to-plan resolution, metric-contract inspection, grain/fan-out reasoning and cross-domain evidence retrieval.


## Data Agent strengthening — schema, query governance and provenance

- Added allow-listed BigQuery schema discovery for approved semantic views.
- Added conservative single-statement SELECT validation, approved-view checks and required numeric LIMIT.
- Added BigQuery dry-run cost estimation and `maximum_bytes_billed` enforcement before execution.
- Added evidence provenance containing metric contract, source view, snapshot date, retrieval time, query SHA-256, job ID/bytes when available, row count and validation checks.
- Expanded all three Colab notebooks with practical schema discovery, query validation and evidence-lineage exercises.
- Added governance-control unit tests.
