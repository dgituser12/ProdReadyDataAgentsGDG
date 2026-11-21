-- BigQuery Standard SQL. Replace `PROJECT_ID.gdg_essex_data_agents` with your project/dataset.
-- These views implement the canonical definitions in ../metrics.json.

CREATE OR REPLACE VIEW `PROJECT_ID.gdg_essex_data_agents.v_inventory_product_risk` AS
SELECT
  i.snapshot_date, i.warehouse_id, i.warehouse_name, i.product_id,
  p.product_name, p.category, p.criticality, i.quantity_on_hand,
  i.quantity_reserved, i.available_quantity, i.safety_stock,
  GREATEST(i.safety_stock - i.available_quantity, 0) AS shortage_units,
  p.unit_cost_gbp,
  GREATEST(i.safety_stock - i.available_quantity, 0) * p.unit_cost_gbp AS inventory_value_at_risk_gbp,
  i.inventory_status
FROM `PROJECT_ID.gdg_essex_data_agents.inventory_snapshot` i
JOIN `PROJECT_ID.gdg_essex_data_agents.products` p USING (product_id);

CREATE OR REPLACE VIEW `PROJECT_ID.gdg_essex_data_agents.v_supplier_delivery_performance` AS
SELECT
  s.supplier_id, s.supplier_name, s.supplier_risk_tier,
  s.standard_lead_time_days, s.active,
  COUNTIF(o.order_status = 'DELIVERED' AND o.actual_delivery_date IS NOT NULL) AS delivered_orders,
  COUNTIF(o.order_status = 'DELIVERED' AND o.actual_delivery_date IS NOT NULL
          AND o.actual_delivery_date <= o.promised_delivery_date) AS on_time_deliveries,
  COUNTIF(o.order_status = 'DELIVERED' AND o.actual_delivery_date IS NOT NULL
          AND o.actual_delivery_date > o.promised_delivery_date) AS late_deliveries,
  SAFE_DIVIDE(
    COUNTIF(o.order_status = 'DELIVERED' AND o.actual_delivery_date IS NOT NULL
            AND o.actual_delivery_date <= o.promised_delivery_date),
    COUNTIF(o.order_status = 'DELIVERED' AND o.actual_delivery_date IS NOT NULL)
  ) AS on_time_delivery_rate,
  AVG(IF(o.order_status = 'DELIVERED' AND o.actual_delivery_date > o.promised_delivery_date,
         DATE_DIFF(o.actual_delivery_date, o.promised_delivery_date, DAY), NULL)) AS average_late_days
FROM `PROJECT_ID.gdg_essex_data_agents.suppliers` s
LEFT JOIN `PROJECT_ID.gdg_essex_data_agents.fulfillment_orders` o USING (supplier_id)
GROUP BY s.supplier_id, s.supplier_name, s.supplier_risk_tier, s.standard_lead_time_days, s.active;

CREATE OR REPLACE VIEW `PROJECT_ID.gdg_essex_data_agents.v_fulfillment_order_exposure` AS
WITH snapshot AS (
  SELECT MAX(snapshot_date) AS as_of_date
  FROM `PROJECT_ID.gdg_essex_data_agents.inventory_snapshot`
)
SELECT
  o.*, snapshot.as_of_date,
  DATE_DIFF(snapshot.as_of_date, o.promised_delivery_date, DAY) AS current_overdue_days,
  (o.order_status IN ('PROCESSING','IN_TRANSIT','DELAYED')
   AND o.promised_delivery_date < snapshot.as_of_date) AS is_overdue_open_order
FROM `PROJECT_ID.gdg_essex_data_agents.fulfillment_orders` o
CROSS JOIN snapshot;

CREATE OR REPLACE VIEW `PROJECT_ID.gdg_essex_data_agents.v_inventory_risk_summary` AS
SELECT
  snapshot_date, warehouse_id,
  COUNT(DISTINCT product_id) AS product_count,
  SUM(available_quantity) AS available_stock_units,
  COUNTIF(available_quantity < safety_stock) AS products_below_safety_stock,
  COUNTIF(inventory_status = 'CRITICAL') AS critical_products,
  COUNTIF(available_quantity = 0) AS stockout_products,
  SUM(shortage_units) AS shortage_units,
  SUM(inventory_value_at_risk_gbp) AS inventory_value_at_risk_gbp
FROM `PROJECT_ID.gdg_essex_data_agents.v_inventory_product_risk`
GROUP BY snapshot_date, warehouse_id;

CREATE OR REPLACE VIEW `PROJECT_ID.gdg_essex_data_agents.v_fulfillment_risk_summary` AS
SELECT
  as_of_date,
  COUNT(*) AS total_orders,
  COUNTIF(order_status = 'DELIVERED' AND actual_delivery_date IS NOT NULL) AS delivered_orders,
  COUNTIF(order_status IN ('PROCESSING','IN_TRANSIT','DELAYED')) AS open_orders,
  COUNTIF(is_overdue_open_order) AS overdue_open_orders,
  SUM(IF(is_overdue_open_order, current_overdue_days, 0)) AS current_overdue_days_total,
  COUNTIF(order_status = 'DELIVERED' AND actual_delivery_date > promised_delivery_date) AS delivered_late_orders,
  SAFE_DIVIDE(
    COUNTIF(order_status = 'DELIVERED' AND actual_delivery_date IS NOT NULL
            AND actual_delivery_date <= promised_delivery_date),
    COUNTIF(order_status = 'DELIVERED' AND actual_delivery_date IS NOT NULL)
  ) AS on_time_delivery_rate,
  SUM(IF(is_overdue_open_order, order_value_gbp, 0)) AS delayed_open_order_value_gbp
FROM `PROJECT_ID.gdg_essex_data_agents.v_fulfillment_order_exposure`
GROUP BY as_of_date;

-- Cross-domain supplier risk: aggregate each fact domain to supplier grain
-- before joining, preventing inventory x orders fan-out.
CREATE OR REPLACE VIEW `PROJECT_ID.gdg_essex_data_agents.v_supplier_cross_domain_risk` AS
WITH inventory_by_supplier AS (
  SELECT
    p.supplier_id,
    i.snapshot_date,
    i.warehouse_id,
    COUNT(DISTINCT IF(i.available_quantity < i.safety_stock, i.product_id, NULL)) AS products_below_safety_stock,
    SUM(GREATEST(i.safety_stock - i.available_quantity, 0) * p.unit_cost_gbp) AS inventory_value_at_risk_gbp
  FROM `PROJECT_ID.gdg_essex_data_agents.inventory_snapshot` i
  JOIN `PROJECT_ID.gdg_essex_data_agents.products` p USING (product_id)
  GROUP BY p.supplier_id, i.snapshot_date, i.warehouse_id
),
orders_by_supplier AS (
  SELECT
    supplier_id,
    as_of_date,
    COUNTIF(is_overdue_open_order) AS overdue_open_orders,
    SUM(IF(is_overdue_open_order, order_value_gbp, 0)) AS overdue_open_order_value_gbp
  FROM `PROJECT_ID.gdg_essex_data_agents.v_fulfillment_order_exposure`
  GROUP BY supplier_id, as_of_date
),
supplier_performance AS (
  SELECT * FROM `PROJECT_ID.gdg_essex_data_agents.v_supplier_delivery_performance`
)
SELECT
  s.supplier_id,
  s.supplier_name,
  s.supplier_risk_tier,
  s.standard_lead_time_days,
  s.delivered_orders,
  s.on_time_delivery_rate,
  s.late_deliveries,
  s.average_late_days,
  i.snapshot_date AS as_of_date,
  i.warehouse_id,
  COALESCE(i.products_below_safety_stock, 0) AS products_below_safety_stock,
  COALESCE(i.inventory_value_at_risk_gbp, 0) AS inventory_value_at_risk_gbp,
  COALESCE(o.overdue_open_orders, 0) AS overdue_open_orders,
  COALESCE(o.overdue_open_order_value_gbp, 0) AS overdue_open_order_value_gbp
FROM supplier_performance s
LEFT JOIN inventory_by_supplier i USING (supplier_id)
LEFT JOIN orders_by_supplier o
  ON o.supplier_id = s.supplier_id AND o.as_of_date = i.snapshot_date;
