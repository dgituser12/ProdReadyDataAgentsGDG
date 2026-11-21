# Workshop data scripts

Default synthetic profile: 8 suppliers, 60 products, 60 inventory rows, 500 fulfilment orders, one Essex warehouse, GBP currency, snapshot date 2026-10-01, seed 20261013.

Generate: `python scripts/generate_data.py`

Customise: `python scripts/generate_data.py --seed 20261013 --products 60 --orders 500 --snapshot-date 2026-10-01 --output-dir data/sample`

Validate: `python scripts/validate_data.py --input-dir data/sample`

Load: install `google-cloud-bigquery`, authenticate using an approved ADC flow, then run `python scripts/load_to_bigquery.py --project YOUR_PROJECT_ID --dataset gdg_essex_data_agents --create-dataset`. No service-account JSON upload is required. Default write mode `fail` refuses to overwrite; use `--write-mode truncate` to replace or `append` deliberately.

Business rules: supplier risk is a profile tier (LOW/MEDIUM/HIGH), distinct from observed delivery performance calculated from fulfilment orders. Standard lead time lives only on suppliers. Monetary fields use GBP and `_gbp` suffixes. Inventory status is CRITICAL below 50% of safety stock, AT_RISK from 50% to below 100%, and HEALTHY at or above 100%. DELAYED means open and overdue at snapshot; IN_TRANSIT and PROCESSING are open but not overdue.

All data is fictional. BigQuery charges may apply. Delete the dataset when no longer needed, after checking the project and dataset identifiers.

## Calculate canonical business metrics

```bash
python scripts/calculate_metrics.py --input-dir data/sample --output data/sample/business_metrics.json
```

This writes inventory, fulfilment and supplier performance summaries using the inventory snapshot date as the as-of date. Definitions and SQL equivalents live in `semantic_catalogue/`.

## Agent routing and orchestration evaluations

```bash
python scripts/evaluate_router.py
python scripts/evaluate_multi_agent.py
```

The first script evaluates the deterministic single-domain/cross-domain route baseline. The second evaluates expected specialist targets for a small multi-agent fixture. These are local labelled fixtures, not evaluations of live LLM delegation or answer quality.
