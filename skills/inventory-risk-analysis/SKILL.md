---
name: inventory-risk-analysis
description: Analyse point-in-time inventory exposure for the Essex supply-chain scenario, identify products below safety stock, explain cost-valued shortfalls, and recommend evidence-based follow-up actions. Use when a user asks about stock risk, stockouts, replenishment priorities, safety stock, or inventory value at risk.
---

# Inventory Risk Analysis

## Purpose

Help the user understand inventory exposure in the synthetic Essex supply-chain dataset and decide what to investigate next. Use the shared semantic catalogue for metric definitions and approved data tools for facts. This skill supplies domain reasoning; it does not replace data access, SQL, authorisation, or business policy.

## Required workflow

1. **Establish scope.** Use the inventory snapshot date as the default as-of date and identify the warehouse. The supplied scenario has one warehouse, `WH-ESSEX-01` (Essex Central Distribution Centre). Do not imply multi-warehouse coverage.
2. **Retrieve evidence.** Use the approved read-only inventory and product tools. Retrieve product-level available quantity, safety stock, inventory status, unit cost, category, criticality, and supplier identifier as needed. Do not invent missing fields or values.
3. **Apply canonical definitions.** Consult `semantic_catalogue/metrics.json` and `semantic_catalogue/business_glossary.md`. Available quantity is on-hand minus reserved. Shortage units are calculated per product as `max(safety_stock - available_quantity, 0)`.
4. **Classify correctly.** `CRITICAL` means available quantity is below 50% of safety stock; `AT_RISK` means at least 50% but below 100%; `HEALTHY` means at least 100%. A stockout means available quantity is exactly zero. Do not conflate a stockout with every below-safety-stock condition.
5. **Quantify exposure carefully.** Inventory value at risk is shortage units multiplied by unit cost in GBP. Describe it as the estimated purchase-cost value of the safety-stock gap—not lost sales, lost revenue, a booked liability, or a guaranteed replenishment cost.
6. **Prioritise transparently.** Use the risk-scoring guide. Show the factors and evidence behind any ordering. Treat product criticality as a prioritisation input, not as a substitute for inventory status. Do not invent a numeric risk score unless the user asks for one and the scoring method is explicitly disclosed.
7. **Explain limits.** State snapshot date, warehouse and GBP context. A single snapshot supports point-in-time analysis, not a trend. If data is missing or stale, say so and ask for the necessary input.
8. **Recommend bounded next actions.** Suggest investigation such as confirming demand, checking open purchase/fulfilment commitments, validating supplier lead time, or reviewing replenishment policy. Do not place orders, change stock, or contact suppliers.

## Response structure

For a portfolio question, provide:

- **As-of context:** snapshot date and warehouse.
- **Exposure summary:** available stock, products below safety stock, critical products and stockouts where available.
- **Priority items:** a short ranked list with product, available quantity, safety stock, shortage units, status, unit cost and value-at-risk contribution.
- **Interpretation:** why the items matter and what the metric does—and does not—mean.
- **Next checks:** specific, read-only investigations.

For a single-product question, lead with its status and available-versus-safety-stock position, then explain shortage and cost exposure.

## Guardrails

- Read-only analysis only. Never mutate inventory, create purchase orders, approve spend, or make supplier commitments.
- Never treat supplier profile risk tier as measured delivery performance. If supplier context is needed, retrieve the supplier profile and observed order performance separately.
- Never calculate shortage from on-hand quantity without deducting reserved quantity.
- Never aggregate repeated snapshots together. Select one snapshot unless a valid multi-snapshot trend analysis is explicitly supported.
- Do not claim a trend from the single supplied snapshot.
- Do not describe inventory value at risk as financial loss or lost revenue.
- Keep currency in GBP. Do not silently convert currencies.
- Respect tool row limits and approved query constraints. Aggregate before returning broad lists; show at most 100 rows unless an explicitly authorised workflow says otherwise.
- If the user asks for an action outside read-only scope, explain the limitation and propose a human-controlled next step.

## Progressive disclosure

Load the core instructions first. Read `references/inventory-glossary.md` when terminology needs explanation. Read `references/risk-scoring-guide.md` when comparing or prioritising products. Use the semantic catalogue for canonical formulas and join/grain details rather than duplicating those definitions here.
