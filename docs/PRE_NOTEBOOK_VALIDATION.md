# Pre-notebook validation status

## Consolidation result
The v2 archive contains every file present in v1. No v1 file is missing from v2. The following shared files were intentionally updated in v2: README, route evaluation fixture, orchestration/skills/scripts documentation, routing and policy implementation, Track A/B seams, and relevant tests. V2 adds the single-agent factory, specialist/coordinator factories, supplier and fulfilment Skills, specialist planning and multi-agent evaluation.

The consolidated repository therefore uses v2 as its integrated baseline; v1 is retained only as an archived development milestone.

## Checks run in the build environment
- `python -m pytest -q`: 30 passed.
- `python -m unittest discover -s tests -v`: 30 passed.
- `python scripts/validate_data.py --input-dir data/sample`: passed; 8 suppliers, 60 products, 60 inventory rows, 500 orders.
- `python scripts/calculate_metrics.py --input-dir data/sample --output <temporary-file>`: passed; generated the expected 2026-10-01 metrics.
- `python scripts/evaluate_router.py`: 16/16 passed.
- `python scripts/evaluate_multi_agent.py`: 6/6 passed.
- `python -m compileall -q .`: passed.

## Not yet verified
- ADK package installation and runtime execution.
- ADK SkillToolset compatibility at runtime.
- Actual single-agent and coordinator construction against the installed ADK package.
- Live ADK delegation and trace behaviour.
- Live BigQuery loading, view creation, query results, IAM and cost limits.
- Live Gemini Decisions API.
- Live managed Conversational Analytics connection and callable.
- Public GitHub security/licence review.

These remaining checks are listed in `TESTING.md`. This is a pre-notebook baseline, not a final participant release.
