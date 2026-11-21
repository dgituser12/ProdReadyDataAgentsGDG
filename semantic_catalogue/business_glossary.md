# Supply-chain business glossary

## Inventory

- **On-hand quantity:** Physical units recorded at the warehouse.
- **Reserved quantity:** Units already committed and therefore unavailable for new demand.
- **Available quantity:** `quantity_on_hand - quantity_reserved`. This is the stock quantity used for risk assessment.
- **Safety stock:** Product-specific minimum buffer quantity.
- **Shortage units:** `max(safety_stock - available_quantity, 0)`, calculated per product before aggregation.
- **Inventory status:** `CRITICAL` below 50% of safety stock; `AT_RISK` from 50% inclusive to below 100%; `HEALTHY` at or above safety stock.
- **Inventory value at risk:** Shortage units multiplied by product unit cost in GBP. It estimates the cost value of the safety-stock gap; it is not lost sales, revenue at risk, or a booked financial liability.
- **Stockout:** Available quantity equals zero. A product can be below safety stock without being stocked out.

## Supplier

- **Supplier risk tier:** Static profile attribute (`LOW`, `MEDIUM`, `HIGH`) held on the supplier record. It is not calculated from order history.
- **Standard lead time:** Supplier-level standard lead time in days. It is not a product attribute in this model.
- **On-time delivery:** A delivered order where actual delivery date is on or before promised delivery date.
- **On-time delivery rate:** On-time delivered orders divided by all delivered orders with an actual delivery date. Open and cancelled orders are excluded. Show the delivered-order denominator.
- **Late delivery:** A delivered order where actual delivery date is after promised delivery date.
- **Average late days:** Average positive difference between actual and promised dates among late delivered orders only. It is null when there are no late delivered orders.

## Fulfilment

- **Open order:** An order in `PROCESSING`, `IN_TRANSIT`, or `DELAYED` status.
- **Overdue open order:** An open order whose promised delivery date is earlier than the inventory snapshot date.
- **Current overdue days:** Snapshot date minus promised delivery date for an overdue open order. This is an as-of measure and can change as the snapshot date changes.
- **Delayed open-order value:** Sum of order values for overdue open orders. It is an exposure indicator, not a measure of realised loss.
- **Late delivered vs overdue open:** Late delivered is historical performance (actual date exists); overdue open is a current unresolved commitment (actual date absent).

## Reporting conventions

- Use the inventory snapshot date as the default as-of date.
- Use GBP for monetary values.
- The supplied scenario represents one warehouse, `WH-ESSEX-01` (Essex Central Distribution Centre).
- A single snapshot supports point-in-time analysis, not a trend. A trend requires multiple comparable snapshots.
- If the denominator is zero or a required date/value is missing, report the metric as unavailable rather than inventing a value.
