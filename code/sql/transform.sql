CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;
CREATE OR REPLACE TABLE staging.online_retail_clean AS
SELECT *, CAST(quantity * price AS DECIMAL(18,4)) AS total_price
FROM raw.online_retail
WHERE quantity IS NOT NULL AND price IS NOT NULL AND price >= 0
 AND stockcode IS NOT NULL AND stockcode <> 'M'
 AND COALESCE(description, '') NOT IN ('BANK CHARGES', 'AMAZONFEE');

CREATE OR REPLACE TABLE analytics.dim_date AS
SELECT DISTINCT CAST(strftime(invoicedate, '%Y%m%d') AS INTEGER) date_key,
 CAST(invoicedate AS DATE) full_date,
 CAST(year(invoicedate) AS INTEGER) AS "year",
 CAST(month(invoicedate) AS INTEGER) AS "month",
 monthname(invoicedate) month_name,
 CAST(quarter(invoicedate) AS INTEGER) AS "quarter",
 CAST(day(invoicedate) AS INTEGER) AS "day",
 CAST(dayofweek(invoicedate) AS INTEGER) AS "day_of_week",
 dayname(invoicedate) day_name,
 CAST(week(invoicedate) AS INTEGER) AS "week_of_year"
FROM staging.online_retail_clean WHERE invoicedate IS NOT NULL;
CREATE OR REPLACE TABLE analytics.dim_country AS
SELECT CAST(row_number() OVER (ORDER BY country) AS BIGINT) country_id, country
FROM (SELECT DISTINCT country FROM staging.online_retail_clean WHERE country IS NOT NULL);
CREATE OR REPLACE TABLE analytics.dim_product AS
SELECT stockcode, max(description) product_name FROM staging.online_retail_clean
GROUP BY stockcode;
CREATE OR REPLACE TABLE analytics.dim_customer AS
SELECT customer_id, min(CAST(invoicedate AS DATE)) first_seen_date,
 max(CAST(invoicedate AS DATE)) last_seen_date
FROM staging.online_retail_clean WHERE customer_id IS NOT NULL GROUP BY customer_id;
CREATE OR REPLACE TABLE analytics.fact_sales AS
SELECT CAST(row_number() OVER (ORDER BY row_hash) AS BIGINT) fact_id,
 s.invoice, s.stockcode, s.customer_id, c.country_id,
 CAST(strftime(s.invoicedate, '%Y%m%d') AS INTEGER) date_key,
 s.quantity, s.price, s.total_price, s.invoicedate invoice_ts
FROM staging.online_retail_clean s JOIN analytics.dim_country c USING(country)
WHERE s.invoice IS NOT NULL AND s.invoicedate IS NOT NULL;

CREATE OR REPLACE VIEW analytics.daily_kpis AS
SELECT d.full_date, d.year, d.month, d.month_name,
 count(DISTINCT f.invoice) daily_orders,
 sum(CASE WHEN quantity > 0 THEN total_price ELSE 0 END) gross_revenue,
 -sum(CASE WHEN quantity < 0 THEN total_price ELSE 0 END) returned_revenue,
 sum(total_price) net_revenue,
 CASE WHEN d.quarter = 4 THEN 1 ELSE 0 END is_q4
FROM analytics.fact_sales f JOIN analytics.dim_date d USING(date_key)
GROUP BY ALL;
CREATE OR REPLACE VIEW analytics.tableau_daily_kpis AS
SELECT d.full_date, d.year, d.month, d.month_name, c.country,
 count(DISTINCT invoice) daily_orders,
 sum(CASE WHEN total_price > 0 THEN total_price ELSE 0 END) gross_revenue,
 sum(CASE WHEN total_price < 0 THEN total_price ELSE 0 END) returns_revenue,
 sum(total_price) net_revenue,
 CASE WHEN d.quarter = 4 THEN 1 ELSE 0 END is_q4
FROM analytics.fact_sales f JOIN analytics.dim_date d USING(date_key)
JOIN analytics.dim_country c USING(country_id) GROUP BY ALL;
