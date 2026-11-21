---
name: fulfilment-exposure-analysis
description: Analyse open fulfilment orders, overdue commitments, current overdue days and delayed open-order value in the Essex supply-chain dataset. Use for backlog, promised-date and order-delay questions.
---

# Fulfilment Exposure Analysis

## Purpose

Explain current fulfilment exposure using the approved read-only fulfilment tools and canonical definitions in the semantic catalogue.

## Required workflow

1. Establish the snapshot date and warehouse scope. The scenario uses `WH-ESSEX-01` and GBP.
2. Retrieve open-order exposure and order-level details only through the approved fulfilment tools.
3. Distinguish open orders from delivered orders. An overdue open order is an unfulfilled order whose promised date is before the snapshot date.
4. Interpret current overdue days relative to the snapshot date, not the date the question is asked.
5. Treat delayed open-order value as the value defined by the catalogue; do not label it as realised loss or lost revenue.
6. Keep late delivered orders separate from overdue open orders. Delivered-late performance belongs to the supplier-performance domain.
7. Identify data gaps and explain that one snapshot does not establish a trend.

## Response structure

- Snapshot date and warehouse scope.
- Total/open/overdue order counts where available.
- Current overdue days and delayed open-order value.
- A concise list of priority commitments when supported by tool output.
- Caveats and read-only next checks.

## Guardrails

- Read-only only; do not amend orders, promise dates or contact customers/suppliers.
- Do not conflate delayed open-order value with lost revenue or realised loss.
- Do not mix overdue open orders with late delivered orders.
- Keep currency in GBP and do not invent missing values.
