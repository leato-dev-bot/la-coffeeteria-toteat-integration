CREATE SCHEMA IF NOT EXISTS reporting;

CREATE OR REPLACE FUNCTION reporting.format_number_cl(value numeric, decimals integer DEFAULT 0)
RETURNS text
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT CASE
    WHEN value IS NULL THEN NULL
    WHEN decimals = 0 THEN reverse(regexp_replace(reverse(to_char(round(value)::numeric, 'FM999999999999990')), '(\d{3})(?=\d)', '\1.', 'g'))
    ELSE replace(reverse(regexp_replace(reverse(split_part(to_char(round(value, decimals), 'FM999999999999990D' || repeat('0', decimals)), '.', 1)), '(\d{3})(?=\d)', '\1.', 'g')) || ',' || lpad(split_part(to_char(round(value, decimals), 'FM999999999999990D' || repeat('0', decimals)), '.', 2), decimals, '0'), '.,', ',')
  END
$$;

CREATE OR REPLACE FUNCTION reporting.to_chile_timestamp(value text)
RETURNS timestamp
LANGUAGE sql
IMMUTABLE
AS $$
  SELECT CASE WHEN value IS NULL OR btrim(value) = '' THEN NULL ELSE ((value::timestamp AT TIME ZONE 'UTC') AT TIME ZONE 'America/Santiago') END
$$;

CREATE OR REPLACE VIEW reporting.sales_orders_v AS
WITH sales_raw AS (
  SELECT
    raw_id,
    business_date,
    jsonb_array_elements(COALESCE(response_payload->'data', '[]'::jsonb)) AS sale
  FROM toteat.raw_api_responses
  WHERE endpoint_key = 'sales'
), deduped AS (
  SELECT *
  FROM (
    SELECT
      raw_id,
      business_date,
      sale,
      row_number() OVER (
        PARTITION BY sale->>'orderId', sale->>'paymentId'
        ORDER BY raw_id DESC
      ) AS rn
    FROM sales_raw
  ) t
  WHERE rn = 1
)
SELECT
  raw_id,
  business_date,
  sale->>'orderId' AS order_id,
  sale->>'paymentId' AS payment_id,
  reporting.to_chile_timestamp(sale->>'dateOpen') AS opened_at_cl,
  reporting.to_chile_timestamp(sale->>'dateClosed') AS closed_at_cl,
  (reporting.to_chile_timestamp(sale->>'dateOpen'))::date AS sale_date_cl,
  sale->>'waiterId' AS waiter_id,
  sale->>'waiterName' AS waiter_name,
  sale->>'registerId' AS register_id,
  sale->>'registerName' AS register_name,
  sale->>'tableId' AS table_id,
  sale->>'tableName' AS table_name,
  sale->>'zoneId' AS zone_id,
  sale->>'zoneName' AS zone_name,
  NULLIF(sale->>'numberClients', '')::integer AS number_clients,
  NULLIF(sale->>'subtotal', '')::numeric AS subtotal_amount,
  NULLIF(sale->>'taxes', '')::numeric AS taxes_amount,
  NULLIF(sale->>'discounts', '')::numeric AS discounts_amount,
  NULLIF(sale->>'gratuity', '')::numeric AS gratuity_amount,
  NULLIF(sale->>'total', '')::numeric AS total_amount,
  NULLIF(sale->>'payed', '')::numeric AS paid_amount,
  NULLIF(sale->>'change', '')::numeric AS change_amount,
  NULLIF(sale->>'difference', '')::numeric AS difference_amount,
  NULLIF(sale->>'totalWithGratuity', '')::numeric AS total_with_gratuity_amount,
  reporting.format_number_cl(NULLIF(sale->>'subtotal', '')::numeric, 0) AS subtotal_cl,
  reporting.format_number_cl(NULLIF(sale->>'taxes', '')::numeric, 0) AS taxes_cl,
  reporting.format_number_cl(NULLIF(sale->>'discounts', '')::numeric, 0) AS discounts_cl,
  reporting.format_number_cl(NULLIF(sale->>'gratuity', '')::numeric, 0) AS gratuity_cl,
  reporting.format_number_cl(NULLIF(sale->>'total', '')::numeric, 0) AS total_cl,
  reporting.format_number_cl(NULLIF(sale->>'payed', '')::numeric, 0) AS paid_cl,
  reporting.format_number_cl(NULLIF(sale->>'change', '')::numeric, 0) AS change_cl,
  reporting.format_number_cl(NULLIF(sale->>'difference', '')::numeric, 0) AS difference_cl,
  reporting.format_number_cl(NULLIF(sale->>'totalWithGratuity', '')::numeric, 0) AS total_with_gratuity_cl,
  sale->>'fiscalId' AS fiscal_id,
  sale->>'fiscalType' AS fiscal_type,
  NULLIF(sale->>'fiscalAmt', '')::numeric AS fiscal_amount,
  sale->>'fiscalPrinter' AS fiscal_printer,
  sale->>'client' AS client_name,
  sale->>'comment' AS sale_comment,
  sale->>'discountComment' AS discount_comment,
  sale AS raw_sale
FROM deduped;

CREATE OR REPLACE VIEW reporting.sales_payments_v AS
WITH base AS (
  SELECT raw_sale, raw_id, business_date, order_id, payment_id, closed_at_cl
  FROM reporting.sales_orders_v
), forms AS (
  SELECT
    raw_id,
    business_date,
    order_id,
    payment_id,
    closed_at_cl,
    jsonb_array_elements(COALESCE(raw_sale->'paymentForms', '[]'::jsonb)) AS form
  FROM base
)
SELECT
  raw_id,
  business_date,
  order_id,
  payment_id,
  closed_at_cl,
  form->>'id' AS payment_form_id,
  form->>'name' AS payment_form_name,
  NULLIF(form->>'amount', '')::numeric AS amount,
  reporting.format_number_cl(NULLIF(form->>'amount', '')::numeric, 0) AS amount_cl,
  form->>'comment' AS comment
FROM forms;

CREATE OR REPLACE VIEW reporting.sales_products_v AS
WITH base AS (
  SELECT raw_sale, raw_id, business_date, order_id, payment_id, closed_at_cl
  FROM reporting.sales_orders_v
), products AS (
  SELECT
    raw_id,
    business_date,
    order_id,
    payment_id,
    closed_at_cl,
    jsonb_array_elements(COALESCE(raw_sale->'products', '[]'::jsonb)) AS product
  FROM base
)
SELECT
  raw_id,
  business_date,
  order_id,
  payment_id,
  closed_at_cl,
  product->>'id' AS product_id,
  product->>'name' AS product_name,
  product->>'hierarchyId' AS hierarchy_id,
  product->>'hierarchyName' AS hierarchy_name,
  NULLIF(product->>'quantity', '')::numeric AS quantity,
  NULLIF(product->>'netPrice', '')::numeric AS net_price,
  NULLIF(product->>'payed', '')::numeric AS paid_amount,
  NULLIF(product->>'taxes', '')::numeric AS taxes_amount,
  NULLIF(product->>'discounts', '')::numeric AS discounts_amount,
  NULLIF(product->>'unitCost', '')::numeric AS unit_cost,
  NULLIF(product->>'totalCost', '')::numeric AS total_cost,
  reporting.format_number_cl(NULLIF(product->>'netPrice', '')::numeric, 0) AS net_price_cl,
  reporting.format_number_cl(NULLIF(product->>'payed', '')::numeric, 0) AS paid_amount_cl,
  reporting.format_number_cl(NULLIF(product->>'taxes', '')::numeric, 0) AS taxes_amount_cl,
  reporting.format_number_cl(NULLIF(product->>'discounts', '')::numeric, 0) AS discounts_amount_cl,
  reporting.format_number_cl(NULLIF(product->>'unitCost', '')::numeric, 0) AS unit_cost_cl,
  reporting.format_number_cl(NULLIF(product->>'totalCost', '')::numeric, 0) AS total_cost_cl
FROM products;

CREATE OR REPLACE VIEW reporting.sales_daily_summary_v AS
SELECT
  sale_date_cl,
  count(DISTINCT order_id) AS orders_count,
  count(DISTINCT payment_id) AS payments_count,
  sum(total_amount) AS total_sales_amount,
  sum(paid_amount) AS total_paid_amount,
  sum(gratuity_amount) AS total_gratuity_amount,
  sum(discounts_amount) AS total_discounts_amount,
  sum(taxes_amount) AS total_taxes_amount,
  reporting.format_number_cl(sum(total_amount), 0) AS total_sales_cl,
  reporting.format_number_cl(sum(paid_amount), 0) AS total_paid_cl,
  reporting.format_number_cl(sum(gratuity_amount), 0) AS total_gratuity_cl,
  reporting.format_number_cl(sum(discounts_amount), 0) AS total_discounts_cl,
  reporting.format_number_cl(sum(taxes_amount), 0) AS total_taxes_cl,
  min(opened_at_cl::time) AS first_sale_time_cl,
  max(closed_at_cl::time) AS last_sale_time_cl
FROM reporting.sales_orders_v
GROUP BY sale_date_cl
ORDER BY sale_date_cl;
