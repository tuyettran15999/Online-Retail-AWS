import csv
import logging
from pathlib import Path
import duckdb
from .config import ROOT

LOG = logging.getLogger(__name__)

def ingest(connection, pattern):
    files = sorted(Path(pattern).parent.glob(Path(pattern).name))
    if not files:
        raise FileNotFoundError(f"No input CSVs: {pattern}. Run prepare for full mode.")
    connection.execute("CREATE SCHEMA IF NOT EXISTS raw")
    connection.execute("""CREATE TABLE IF NOT EXISTS raw.online_retail (
        row_hash VARCHAR PRIMARY KEY, invoice VARCHAR, stockcode VARCHAR,
        description VARCHAR, quantity BIGINT, invoicedate TIMESTAMP,
        price DECIMAL(18,4), customer_id BIGINT, country VARCHAR)""")
    before = connection.execute("SELECT count(*) FROM raw.online_retail").fetchone()[0]
    input_rows = 0
    for source in files:
        connection.execute("CREATE OR REPLACE TEMP TABLE incoming AS SELECT * FROM read_csv(?, header=true, all_varchar=true)", [str(source)])
        cols = {r[0] for r in connection.execute("DESCRIBE incoming").fetchall()}
        expected = {"invoice", "stockcode", "description", "quantity", "invoicedate", "price", "customer_id", "country"}
        if cols != expected:
            raise ValueError(f"Unexpected columns in {source.name}: {cols}")
        input_rows += connection.execute("SELECT count(*) FROM incoming").fetchone()[0]
        connection.execute("""INSERT INTO raw.online_retail
        SELECT DISTINCT sha256(to_json(struct_pack(invoice := invoice, stockcode := stockcode,
        description := description, quantity := quantity, invoicedate := invoicedate,
        price := price, customer_id := customer_id, country := country))), *
        FROM (SELECT nullif(trim(invoice),'') invoice, nullif(trim(stockcode),'') stockcode,
        nullif(trim(description),'') description, try_cast(quantity AS BIGINT) quantity,
        try_cast(invoicedate AS TIMESTAMP) invoicedate, try_cast(price AS DECIMAL(18,4)) price,
        try_cast(customer_id AS BIGINT) customer_id, nullif(trim(country),'') country FROM incoming)
        ON CONFLICT DO NOTHING""")
    after = connection.execute("SELECT count(*) FROM raw.online_retail").fetchone()[0]
    return {"input_rows": input_rows, "new_rows": after-before, "raw_rows": after}

def validate(connection):
    checks = {}
    for dim, key in [("dim_country","country_id"), ("dim_date","date_key"), ("dim_product","stockcode"), ("dim_customer","customer_id")]:
        checks[dim + "_orphans"] = connection.execute(f"SELECT count(*) FROM analytics.fact_sales f LEFT JOIN analytics.{dim} d USING({key}) WHERE f.{key} IS NOT NULL AND d.{key} IS NULL").fetchone()[0]
    checks['invalid_staging'] = connection.execute("SELECT count(*) FROM staging.online_retail_clean WHERE quantity IS NULL OR price IS NULL OR price < 0 OR stockcode = 'M' OR description IN ('BANK CHARGES','AMAZONFEE')").fetchone()[0]
    eligible = connection.execute("SELECT count(*) FROM staging.online_retail_clean WHERE invoice IS NOT NULL AND invoicedate IS NOT NULL AND country IS NOT NULL").fetchone()[0]
    fact = connection.execute("SELECT count(*) FROM analytics.fact_sales").fetchone()[0]
    checks['missing_fact_rows'] = eligible-fact
    if any(checks.values()) or fact == 0:
        raise ValueError(f"Data validation failed: {checks}; fact rows={fact}")
    return checks

def export(connection, processed):
    tables = ['dim_date','dim_country','dim_product','dim_customer','fact_sales']
    folder = processed / 'warehouse'; folder.mkdir(parents=True, exist_ok=True)
    for table in tables:
        path = str(folder / (table + '.csv'))
        connection.execute(f"COPY analytics.{table} TO ? (HEADER, NULL '')", [path])
    reports = {'daily_kpis': 'SELECT * FROM analytics.daily_kpis ORDER BY full_date',
               'tableau_daily_kpis': 'SELECT * FROM analytics.tableau_daily_kpis ORDER BY full_date,country',
               'top_countries': 'SELECT country, sum(total_price) net_revenue FROM analytics.fact_sales JOIN analytics.dim_country USING(country_id) GROUP BY country ORDER BY net_revenue DESC LIMIT 10',
               'top_products': 'SELECT stockcode, sum(total_price) net_revenue FROM analytics.fact_sales GROUP BY stockcode ORDER BY net_revenue DESC LIMIT 10'}
    for name, sql in reports.items():
        connection.execute(f"COPY ({sql}) TO ? (HEADER)", [str(processed / (name+'.csv'))])

def run(config):
    from .analytics import analyze
    out = Path(config['output_dir']); out.mkdir(parents=True, exist_ok=True)
    processed = Path(config['processed_dir']); processed.mkdir(parents=True, exist_ok=True)
    Path(config['database']).parent.mkdir(parents=True, exist_ok=True)
    with duckdb.connect(config['database']) as connection:
        connection.execute('BEGIN')
        try:
            metrics = ingest(connection, config['full_glob'])
            metrics['profiling'] = dict(zip(['missing_customer','missing_date','negative_quantity','negative_price'],connection.execute('SELECT count(*) FILTER (WHERE customer_id IS NULL), count(*) FILTER (WHERE invoicedate IS NULL), count(*) FILTER (WHERE quantity < 0), count(*) FILTER (WHERE price < 0) FROM raw.online_retail').fetchone()))
            connection.execute((ROOT / 'code/sql/transform.sql').read_text())
            metrics['checks'] = validate(connection)
            metrics['staging_rows'] = connection.execute('SELECT count(*) FROM staging.online_retail_clean').fetchone()[0]
            metrics['fact_rows'] = connection.execute('SELECT count(*) FROM analytics.fact_sales').fetchone()[0]
            metrics['net_revenue'] = str(connection.execute('SELECT sum(total_price) FROM analytics.fact_sales').fetchone()[0])
            connection.execute('COMMIT')
        except Exception:
            connection.execute('ROLLBACK'); raise
        export(connection, processed)
        connection.execute("COPY staging.online_retail_clean TO ? (HEADER, NULL '')", [str(processed / 'clean_online_retail.csv')])
        analyze(processed, out)
    rows = []
    for name, value in metrics.items():
        if isinstance(value, dict):
            rows.extend((name + "." + key, result) for key, result in value.items())
        else:
            rows.append((name, value))
    with (out / 'run_summary.csv').open('w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file); writer.writerow(['metric', 'value']); writer.writerows(rows)
    LOG.info('Completed: %s', metrics)
    for name, value in rows:
        print(f"{name}: {value}")
    return metrics
