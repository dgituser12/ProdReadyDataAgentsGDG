# Business metrics and semantic catalogue

This folder is the shared business-language contract for both workshop tracks. It keeps the same definitions across Conversational Analytics + ADK and the ADK-only BigQuery agent.

## Contents

- `metrics.json` — machine-readable entities, grain, joins, canonical metrics, formulas, caveats, dimensions and agent-answering policy.
- `business_glossary.md` — plain-language definitions and interpretation guidance.
- `sql/metric_views.sql` — BigQuery Standard SQL views implementing the principal metrics. Replace `PROJECT_ID` before running.

## Generate a reproducible metric snapshot

From the repository root:

```bash
python scripts/calculate_metrics.py --input-dir data/sample --output data/sample/business_metrics.json
```

The calculator uses only Python's standard library. It uses the snapshot date from `inventory_snapshot.csv`, not the machine's current date. The generated JSON is a convenient expected-result artifact for notebooks and tests; it is not a separate source of truth. `metrics.json` defines the meaning, and SQL/Python implement it.

## BigQuery setup

After loading the four source tables with `scripts/load_to_bigquery.py`, edit the project/dataset references in `sql/metric_views.sql` and execute it in BigQuery. The views are read-only semantic surfaces; they do not create or update operational data.

## Design rules

1. Always identify the snapshot/as-of date and warehouse scope.
2. GBP is the only currency in this scenario.
3. Supplier risk tier is a supplier profile attribute; delivery rate and delay are observed performance metrics.
4. Late delivered orders and overdue open orders are different populations.
5. Rates include their denominator. A missing denominator produces `null`, not zero.
6. Inventory value at risk is the cost value of the safety-stock shortfall, not lost revenue.
7. The supplied data contains one warehouse and one inventory snapshot. Do not claim warehouse comparisons or inventory trends.
