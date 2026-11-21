# Optional integrations — code included, execution not required

These integrations are deliberately outside the core hands-on path. The repository includes runnable integration modules and notebook appendix examples. Participants can inspect the code without enabling any of them.

## 1. Managed Conversational Analytics data agent

`integrations/conversational_analytics.py` builds an ADK `DataAgentToolset` bridge to an existing, pre-configured Conversational Analytics Data Agent. This is the governed pattern: the resource contains its knowledge sources, structured context, instructions, verified queries and glossary. It requires a Data Agent resource, API enablement, IAM permissions and a compatible ADK version. It is not created automatically by this workshop.

## 2. Gemini Decision 1 routing

`integrations/decision1.py` creates an explicit Google AI Studio client for the Decisions API. Pass it to `orchestration.router.route_question(..., use_decision_model=True, client=client)`. The classifier only selects among the fixed route labels. It cannot select SQL, grant permissions or execute tools. The deterministic router remains the supported workshop path. Decision 1 is retained for architectural illustration only and must remain disabled: its Decisions API requires `google-genai>=3.2.0,<4`, which conflicts with the `google-genai<3` SDK range used by ADK 2.15.0. Do not upgrade or separately install SDK packages for this path.

## 3. BigQuery Agent Analytics

`integrations/bigquery_agent_analytics.py` wraps an ADK root agent in an `App` with `BigQueryAgentAnalyticsPlugin`. The required ADK extra is included in the single participant install (`requirements-agent.txt`); no second installation is required. The plugin is installed but remains disabled unless the participant explicitly enables the notebook appendix.

The plugin streams ADK events to a BigQuery events table using the Storage Write API. Use a dedicated dataset, grant the required IAM permissions, review payload logging and retention, and avoid sending sensitive user data. The notebook appendix includes an example query to inspect recent events. The plugin is installed by the common requirements file but is not enabled in the core path.

## Workshop default

No optional integration is enabled by default. The core workshop uses the deterministic router, custom read-only BigQuery tools, Skills, and the in-memory ADK event trace.

## Official implementation references

- [ADK DataAgentToolset](https://adk.dev/integrations/data-agent/) — governed access to an existing Data Agent resource.
- [Conversational Analytics integration patterns](https://docs.cloud.google.com/gemini/data-agents/conversational-analytics-api/integration-patterns) — distinguishes schema-driven and governed ADK integrations.
- [BigQuery Agent Analytics](https://docs.cloud.google.com/bigquery/docs/bigquery-agent-analytics) — plugin-based capture, Storage Write API streaming, SQL analysis and trace reconstruction.
- [ADK BigQuery Agent Analytics plugin](https://adk.dev/integrations/bigquery-agent-analytics/) — Python installation and `App` wiring.
