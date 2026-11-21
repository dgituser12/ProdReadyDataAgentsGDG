# Synthetic supply-chain sample data

Fictional workshop data: 8 suppliers, 60 products, 60 inventory rows, 500 fulfilment orders; one warehouse; GBP; default snapshot 2026-10-01.

Regenerate with `python scripts/generate_data.py --seed 20261013 --snapshot-date 2026-10-01 --products 60 --orders 500 --output-dir data/sample`. Validate with `python scripts/validate_data.py --input-dir data/sample`. The `manifest.json` records seed, snapshot date, currency, warehouse and row counts. See `scripts/README.md`.
