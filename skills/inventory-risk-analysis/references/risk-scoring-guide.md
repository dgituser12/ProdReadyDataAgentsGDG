# Inventory risk interpretation and prioritisation guide

## First: report the canonical status

Use the status recorded/calculated under the shared rules:

- `CRITICAL`: available quantity < 50% of safety stock.
- `AT_RISK`: 50% <= available quantity < 100% of safety stock.
- `HEALTHY`: available quantity >= safety stock.
- `STOCKOUT`: available quantity = 0; this is a separate condition and can be called out alongside the status band.

Do not invent alternative thresholds or silently modify the canonical status.

## Then: prioritise investigation using visible factors

The workshop does not define a canonical numeric composite risk score. For a transparent action list, consider these factors in order and show the evidence:

1. **Immediate availability:** stockout first, then `CRITICAL`, then `AT_RISK`.
2. **Depth of shortage:** larger shortage units indicate a larger gap to safety stock.
3. **Product criticality:** use the product master attribute and explain its role.
4. **Cost exposure:** larger inventory value-at-risk contribution indicates a larger cost-valued gap.
5. **Supplier context:** where relevant, display supplier profile tier and standard lead time separately. Do not treat profile tier as observed performance; retrieve delivered-order performance as a separate measure if the question requires it.

This is a qualitative triage order, not a statistically validated risk score or replenishment recommendation. If two items trade off across factors, say so rather than implying false precision.

## Suggested investigation questions

- Is the available quantity correct after reservations and recent movements?
- Is there a demand spike, promotion, or forecast change?
- Are there open orders or inbound commitments that could cover the gap?
- What is the supplier's standard lead time?
- Does the product's criticality justify escalation?
- Is the safety-stock parameter still appropriate?

These are investigation prompts only. The supplied dataset may not contain all the evidence needed to answer them.

## Explain value at risk accurately

`shortage_units * unit_cost_gbp` estimates the purchase-cost value of the units needed to restore safety stock. It is not a prediction of lost sales, revenue, margin, cash impact, or recognised financial loss. Do not sum across multiple snapshots.

## Example response wording

> Product P-… is CRITICAL as of 1 October 2026: 12 units are available against safety stock of 40, leaving a 28-unit gap. At a unit cost of £… the cost-valued safety-stock gap is £…. This is an inventory exposure estimate, not lost revenue. Confirm reservations and inbound commitments before deciding on replenishment.
