---
name: supplier-performance-analysis
description: Analyse supplier profile risk, supplier-level lead time and observed delivery performance in the Essex supply-chain dataset. Use for supplier comparisons, on-time delivery, late deliveries and supplier reliability questions.
---

# Supplier Performance Analysis

## Purpose

Provide evidence-based analysis of supplier profile attributes and observed fulfilment performance. Use the semantic catalogue for canonical metric definitions and the approved read-only supplier tool for facts.

## Required workflow

1. Establish the snapshot date and warehouse scope. The scenario uses `WH-ESSEX-01` and GBP.
2. Retrieve supplier profile and delivery performance using the approved supplier-performance tool.
3. Keep supplier profile risk tier separate from measured delivery performance. A risk tier is a supplied profile attribute; on-time delivery and late-delivery measures are calculated from delivered fulfilment orders.
4. Interpret the on-time delivery rate using the metric catalogue and its documented denominator. Do not mix open overdue orders into delivered-order performance.
5. Treat lead time as supplier-level context. Do not invent product-level lead times or infer causal relationships from correlation alone.
6. When comparing suppliers, disclose the observation window/sample size where available and avoid overclaiming from small samples.
7. State missing data and limitations. The supplied snapshot supports point-in-time comparison, not an unsupported time trend.

## Response structure

- Snapshot date and warehouse scope.
- Supplier profile risk tier.
- Observed delivery performance, clearly labelled and separated from profile tier.
- Relevant lead-time context.
- Caveats, sample-size limitations and read-only follow-up checks.

## Guardrails

- Read-only only; do not contact suppliers, amend contracts or make commitments.
- Do not equate a high-risk profile tier with poor observed performance, or vice versa.
- Do not mix late delivered orders with overdue open orders.
- Keep currency in GBP and do not invent missing measures.
