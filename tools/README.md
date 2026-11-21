# Read-only BigQuery tool layer

This module exposes a small, fixed set of business-oriented Python functions
that both workshop tracks can use. It is intentionally not a general SQL
execution tool.

## Functions

```python
from tools.bigquery_tools import SupplyChainBigQueryTools

bq = SupplyChainBigQueryTools(
    project_id="YOUR_PROJECT_ID",
    dataset_id="gdg_essex_data_agents",
    location="US",  # must match your BigQuery dataset location
)

bq.inventory_summary()
bq.inventory_risk(inventory_status="CRITICAL", limit=10)
bq.supplier_performance(supplier_risk_tier="HIGH", limit=10)
bq.fulfillment_summary()
bq.fulfillment_exposure(only_overdue=True, limit=10)
```

The functions return JSON-friendly dictionaries with `rows`, `row_count`,
`row_limit` and `read_only` fields. Query results are ordered for useful
investigation, and list tools cap results at 100 rows.

## Safety boundaries

- Fixed SQL only; no user-provided SQL, table names, or column names.
- Values are passed as typed query parameters.
- Project and dataset identifiers are validated before use.
- Only allow-listed status/tier filters are accepted.
- List queries have a hard 100-row cap.
- BigQuery `maximum_bytes_billed` defaults to 50 MB per query.
- Functions are read-only `SELECT` queries against the semantic views.
- No arbitrary DDL/DML, write tools, or automatic purchasing actions.

These are workshop safeguards, not a complete production security boundary.
Enforce least-privilege IAM at the Google Cloud layer as well: grant the
runtime identity only the BigQuery job-creation permission and read access to
the required dataset/views. Do not rely on agent instructions as authorization.

## Setup

```bash
pip install -r requirements-agent.txt
gcloud auth application-default login
```

In Colab, use supported user authentication / Application Default Credentials
rather than uploading service-account key files. The identity must have the
appropriate project-level job permission and dataset read permissions.

The dataset location passed to the client must match the dataset location.
The existing loader defaults to `US`; keep the loader and tool configuration
consistent.

## Run smoke query

```bash
python -m tools.bigquery_tools --project YOUR_PROJECT_ID
```

## Agent framework integration

`build_tool_functions(...)` returns five named Python callables:
`get_inventory_risk`, `get_supplier_performance`,
`get_fulfillment_exposure`, `get_inventory_summary`, and
`get_fulfillment_summary`.

Use those callables as the function tools for either agent track after
initialising the module once. The workshop notebooks will wrap them using the
pinned ADK version's verified tool-registration API. This package deliberately
does not assume a particular ADK `FunctionTool` or Skill API signature.

## Local validation

The unit tests use a fake BigQuery client, so they run without cloud access:

```bash
python -m unittest discover -s tests -v
```

A live BigQuery smoke test is still required in the participant's own project.
