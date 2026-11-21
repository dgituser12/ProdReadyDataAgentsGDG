# Workshop Agent Skills

Skills supply task-specific reasoning guidance. They do not replace the canonical semantic catalogue or the approved BigQuery tools.

- `inventory-risk-analysis/` — inventory status, shortage, safety-stock and value-at-risk analysis.
- `supplier-performance-analysis/` — supplier profile risk, supplier-level lead time and observed delivery performance.
- `fulfilment-exposure-analysis/` — open orders, overdue commitments and delayed open-order value.

Each specialist receives only its own Skill and read-only domain tools. The skills use the Agent Skills Markdown format and are loaded with the ADK `load_skill_from_dir` and `SkillToolset` interfaces in the pinned ADK environment. The skill is guidance, not a permission boundary; tool allow-lists and Google Cloud IAM enforce access.
