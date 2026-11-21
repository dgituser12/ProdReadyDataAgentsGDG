# Inventory risk glossary

This reference supports the `inventory-risk-analysis` skill. The canonical definitions remain in `semantic_catalogue/business_glossary.md`; this file is a compact, task-focused explanation for inventory conversations.

| Term | Meaning | How to use it |
|---|---|---|
| On-hand quantity | Physical units recorded at the warehouse | Do not use alone to assess sellable/available stock. |
| Reserved quantity | Units already committed | Deduct from on-hand quantity. |
| Available quantity | `quantity_on_hand - quantity_reserved` | Primary quantity for stock-risk assessment. |
| Safety stock | Product-specific minimum buffer | Compare available quantity against this threshold. |
| Shortage units | `max(safety_stock - available_quantity, 0)` per product | Calculate per product before summing. |
| CRITICAL | Available quantity is below 50% of safety stock | Highest inventory-status band in this workshop. |
| AT_RISK | Available quantity is at least 50% but below 100% of safety stock | Below target, but not in the critical band. |
| HEALTHY | Available quantity is at least safety stock | At or above the defined buffer. |
| Stockout | Available quantity equals zero | Distinct from being below safety stock. |
| Inventory value at risk | Shortage units multiplied by unit cost in GBP | Cost-valued safety-stock gap; not lost revenue or booked loss. |
| Product criticality | Product attribute in the product master | May inform business priority; it does not change the inventory-status formula. |
| Supplier risk tier | Static supplier profile attribute: LOW, MEDIUM or HIGH | Separate from observed supplier delivery performance. |
| Standard lead time | Supplier-level standard lead time in days | Join to supplier; it is not stored at product level. |

## Scope reminders

- Default as-of date: `inventory_snapshot.snapshot_date`.
- Supplied warehouse: `WH-ESSEX-01` (Essex Central Distribution Centre).
- Currency: GBP.
- One snapshot supports point-in-time analysis only.
