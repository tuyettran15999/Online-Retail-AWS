-- Run in DuckDB (PyCharm database tooling or Python).
SELECT * FROM analytics.daily_kpis ORDER BY full_date;
SELECT c.country, SUM(f.total_price) net_revenue
FROM analytics.fact_sales f JOIN analytics.dim_country c USING(country_id)
GROUP BY c.country ORDER BY net_revenue DESC LIMIT 10;
SELECT stockcode, SUM(total_price) net_revenue FROM analytics.fact_sales
GROUP BY stockcode ORDER BY net_revenue DESC LIMIT 10;
