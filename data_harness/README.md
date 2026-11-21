# Governed Data Harness

The workshop Data Harness makes business-data understanding and access a first-class layer between ADK agents and BigQuery.

## Components

- `SemanticCatalogue` loads canonical metric definitions, units, formulae, grain and caveats.
- `SemanticQueryPlanner` maps familiar business questions to approved metric IDs and dimensions. It plans; it does not generate arbitrary SQL.
- `BigQuerySchemaDiscovery` inspects only an explicit allow-list of semantic views and returns a timestamped schema snapshot.
- `ReadOnlyQueryValidator` accepts one bounded `SELECT` over approved semantic views, rejects mutation/remote operations and requires a numeric `LIMIT`.
- `run_validated_bigquery_query` performs a dry run, applies a maximum-bytes-billed ceiling and then executes the validated query.
- `GovernedDataHarness` resolves metric definitions, enforces source/metric policy and invokes approved read-only tools.
- `build_evidence_provenance` records metric identity, unit, grain, source view, snapshot date, retrieval time, query hash, query job ID (when available), bytes processed (when available), row count and validation checks.
- `DataSourceAdapter` defines an extension contract for additional data platforms. Only BigQuery is implemented and exercised in this workshop.

## Important security boundary

This is a deliberately narrow workshop implementation, not a complete SQL parser, query firewall or replacement for BigQuery IAM. The query validator is a second application-level guard. BigQuery IAM, dataset/view permissions, service-account policy, audit logging and network controls remain authoritative. The core agent tools use fixed SQL and typed parameters; participant-proposed SQL is only used in the explicit validation exercise.

## Data Agent workflow

1. Interpret the business question.
2. Resolve metric definitions and grain from the semantic catalogue.
3. Discover approved view schemas rather than guessing columns.
4. Produce a reviewable data plan.
5. Validate source, SQL shape, result bounds and estimated cost.
6. Retrieve evidence through approved tools.
7. Attach provenance and validate the result before the agent explains it.

The agent provides reasoning. The Data Harness supplies governed semantic understanding, data access and evidence lineage.
