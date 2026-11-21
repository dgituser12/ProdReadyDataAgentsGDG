# Enterprise Data Agents on Google Cloud — GDG Essex

**Workshop:** From Data to Action: Building Enterprise Data Agents with Google Cloud  
**Format:** 165-minute hands-on workshop  
**Learning path:** single Data Agent → domain specialists → coordinator-led multi-agent system

This is the consolidated workshop codebase. It combines the original v1 data foundation with the v2 progressive agent architecture. There is one copy of each shared component; v1 and v2 are not separate participant downloads.

> **Current status:** Three Colab-first practical notebooks are included. Unit tests and static notebook checks are available; live cloud integrations must still be rehearsed in a fresh Colab runtime before the event.

## Learning architecture

1. **Beginner — single agent:** one focused, read-only Data Agent answers a business question using approved tools and canonical business definitions.
2. **Intermediate — specialists:** Inventory, Supplier and Fulfilment specialists receive domain-specific instructions, Skills and narrow tool allow-lists.
3. **Advanced — coordinator:** an ADK coordinator delegates to one or more specialists and synthesises their evidence for cross-domain questions.

## Participant notebooks

| Notebook | Facilitated time | Focus |
|---|---:|---|
| 1 — Build Your First Enterprise Data Agent | 25 min | First read-only ADK + BigQuery agent |
| 2 — Give Your Agent Enterprise Expertise | 35 min | Semantic grounding, Agent Skills and three specialists |
| 3 — Build the Multi-Agent System | 35 min | Coordinator, bounded delegation, evaluation and traces |

Notebook 0 is completed before the event; Notebook 4 is the post-workshop reference hub. Each practical notebook can be opened independently in Colab after the environment setup and includes the same participant configuration experience.

## Repository contents

| Path | Purpose |
|---|---|
| `data/` | Synthetic Essex distribution-centre CSV data and manifest |
| `scripts/` | Generate, validate, load and calculate business metrics |
| `semantic_catalogue/` | Canonical metric definitions, glossary and BigQuery views |
| `data_harness/` | Governed source-adapter layer, semantic metric resolution and read-only policy enforcement |
| `integrations/` | Optional managed analytics, Decision 1 and BigQuery Agent Analytics integrations |
| `tools/` | Read-only, parameterised BigQuery business tools |
| `skills/` | Inventory, Supplier and Fulfilment Agent Skills |
| `orchestration/` | Routing, route policy, delegation planning and ADK agent factories |
| `notebooks/` | Three Colab-first practical notebooks (25 + 35 + 35 minutes) |
| `evals/` | Labelled routing and specialist-selection fixtures |
| `tests/` | Unit tests for data, metrics, tools, skills and orchestration |
| `docs/` | Architecture and implementation notes |

## Quick start — local checks

The data generator, validator, metric calculator, routing baselines and unit tests use Python's standard library. BigQuery and ADK integrations are optional until you run the live-cloud checks.

```bash
git clone https://github.com/<your-github-username>/enterprise-data-agents-gdg-essex.git
cd enterprise-data-agents-gdg-essex

python scripts/validate_data.py --input-dir data/sample
python scripts/calculate_metrics.py --input-dir data/sample
python scripts/evaluate_router.py
python scripts/evaluate_multi_agent.py
python -m unittest discover -s tests -v
```

See [TESTING.md](TESTING.md) for the full validation sequence and expected results.

## Synthetic business scenario

The sample dataset represents **Essex Central Distribution Centre** (`WH-ESSEX-01`), with GBP as the currency and a snapshot date of `2026-10-01`.

- 8 suppliers
- 60 products
- 60 inventory snapshot rows
- 500 fulfilment orders

The data is synthetic and intended for education. The business definitions in `semantic_catalogue/` are authoritative for this workshop.

Important metric distinctions:

- Inventory value at risk = shortage units × unit cost; it is not lost revenue.
- Supplier profile risk tier is distinct from observed delivery performance.
- Late delivered orders are distinct from overdue open orders.
- Lead time is modelled at supplier level.

## Google Cloud and agent setup

The workshop uses one participant dependency file, `requirements-agent.txt`. It includes ADK, the compatible Google Gen AI SDK, BigQuery access and the BigQuery Agent Analytics plugin extra. Decision 1 dependencies are intentionally excluded because they conflict with the pinned ADK SDK range. Each Colab notebook installs this same file during bootstrap:

```bash
python -m pip install -r requirements-agent.txt
```

You will also need a Google Cloud project, the required APIs and IAM permissions, and Application Default Credentials (ADC). In Colab, use the supported user authentication flow. Do not upload or commit service-account JSON keys.

The BigQuery loader is explicit about dataset creation and write mode. Review its arguments before running it against a project. The agent-facing query tools are read-only and use fixed SQL, typed parameters and row/bytes limits.

## Two implementation tracks

- **Track A — Managed Conversational Analytics + ADK:** optional integration code uses ADK `DataAgentToolset` to call a pre-configured governed Data Agent resource. A legacy callable-injection seam is also retained for custom API clients. Neither pattern provisions the managed resource; prompt scopes are not security boundaries.
- **Track B — ADK + BigQuery:** custom ADK agents use the shared read-only BigQuery tools, semantic catalogue and Agent Skills.

Optional integration code is included under `integrations/`; it is not enabled by default. See [docs/OPTIONAL_INTEGRATIONS.md](docs/OPTIONAL_INTEGRATIONS.md). The managed Conversational Analytics Data Agent resource and its permissions must be configured in the organiser's Google Cloud environment.

## Governed Data Harness

The `data_harness/` package provides a working BigQuery-backed Data Harness: canonical metric resolution, an explicit source-adapter contract, allow-listed metric/source policy and bounded read-only retrieval through approved semantic views. Additional sources can implement the adapter contract, but real federation requires separate connectivity, credentials, source-native permissions and validation. The workshop does not provision external federation infrastructure. See [data_harness/README.md](data_harness/README.md).

## Optional integrations

The repository contains optional code for a managed Conversational Analytics Data Agent via ADK `DataAgentToolset`, Gemini Decision 1 routing, and persistent BigQuery Agent Analytics. All are outside the core workshop path and disabled by default. See [docs/OPTIONAL_INTEGRATIONS.md](docs/OPTIONAL_INTEGRATIONS.md).

## Safety and scope

- Workshop agents and tools are read-only. No purchasing, stock mutation, supplier contact or other business write action is implemented.
- Never commit API keys, access tokens, credentials, real customer data or local `.env` files.
- Skills provide task guidance; they are not security controls. IAM, data permissions and tool allow-lists remain essential.
- A passing local test suite is not proof of a live cloud integration or production readiness.

## Public repository setup

1. Create a **public** repository in your personal GitHub account named `enterprise-data-agents-gdg-essex`.
2. Push this repository's contents to the `main` branch.
3. Replace `<your-github-username>` in this README with your GitHub username.
4. Add the three practical Colab notebooks and their **Open in Colab** links after the fresh-runtime validation gate is complete.
5. Tag the eventual participant-ready workshop snapshot as a GitHub release.

## Licence

Add the licence you intend to publish this material under before making the repository public. No licence has been selected in this starter package.

## Workshop facilitation

The 165-minute agenda is in [docs/FACILITATION_150_MIN.md](docs/FACILITATION_150_MIN.md). It allocates 20 minutes to the opening talk, 30 minutes to Notebook 1, 45 minutes to Notebook 2, 45 minutes to Notebook 3, and preserves time for a break, Q&A and close.

## Participant notebooks

**Notebook location:** `notebooks/` is the single canonical location for all three participant notebooks. There are no duplicate notebook copies at the repository root. Open the `.ipynb` files from that directory in Google Colab.

## Why this is a Data Agent workshop

The workshop distinguishes a general-purpose agent from an enterprise Data Agent through a repeatable **business-question-to-evidence** workflow:

1. Resolve business language to canonical metric definitions in `semantic_catalogue/metrics.json`.
2. Produce a reviewable semantic plan (domains, metric IDs and dimensions) with `SemanticQueryPlanner` in `data_harness/core.py`.
3. Enforce approved source/metric policies and read-only access through the Data Harness.
4. Retrieve bounded evidence from allow-listed BigQuery semantic views.
5. Preserve metric formula, unit, entity grain, caveats and retrieval provenance for the agent's explanation.
6. Evaluate data correctness separately from conversational quality.

The Data Harness now includes allow-listed BigQuery schema discovery, a conservative read-only SQL validator, dry-run cost checks with a maximum-bytes-billed ceiling, and evidence provenance (metric contract, source view, snapshot date, query fingerprint and validation checks). These are application-level safeguards and do not replace BigQuery IAM. See `data_harness/README.md` for the boundaries and workflow.

The workshop adds `v_supplier_cross_domain_risk`, a supplier-grain semantic view. Inventory exposure and overdue-order exposure are aggregated independently before joining to supplier delivery performance, preventing raw fact-table fan-out. Supplier attribution is explicitly association, not proof of causation.
