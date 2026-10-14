# Online Retail Project: Revenue and Seasonal Analysis

> This project analyzes online retail transactions from December 1, 2009 to December 9, 2011 to explore revenue, returns and Q4 seasonal patterns.

---

## Project Overview

This project processes the Online Retail II dataset to build a clean analytical model and investigate retail sales patterns. It combines two years of transaction data, validates data quality, retains return transactions and produces business KPIs, visualizations and statistical reports.

- **Objective:** Understand revenue trends, identify leading countries/products and compare Q4 revenue and return rates with the rest of the year.
- **Domain:** Retail Analytics and Data Engineering
- **Key Techniques:** Data cleaning, incremental ingestion, star-schema modeling, exploratory data analysis, Welch t-tests and OLS regression.

---

## Project Structure

```text
├── data/
│   ├── raw/                         # Full yearly CSVs and original UCI workbook
│   └── processed/                   # Cleaned data, daily KPIs and warehouse exports
├── code/
│   ├── Online_Retail_Analysis.ipynb  # Interactive analysis notebook
│   ├── run_pipeline.py              # Python/PyCharm entry point
│   ├── retail_pipeline/             # Data processing and analytics modules
│   │   └── settings.py              # Local paths, editable in Python
│   ├── sql/                         # Model transformations and business queries
│   ├── tests/                       # Data quality and ingestion tests
│   ├── aws/                         # Optional AWS instructions and .env example
│   └── docs/                        # Provenance and implementation notes
├── reports/                         # Statistical reports, run summary and charts
├── requirements.txt                 # Dependencies
├── README.md                        # Project documentation
├── main.py                          # Compatibility entry point
└── LICENSE
```

Raw data remains unchanged by analysis. Cleaned data and reusable tables belong in `data/processed`; charts and reports belong in `reports`.

---

## Data

- **Source:** [Online Retail II — UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/502/online+retail+ii)
- **Citation:** Chen, D. (2012). Online Retail II. https://doi.org/10.24432/C5CG6D.
- **Coverage:** December 1, 2009 to December 9, 2011; 1,067,371 original transaction rows.
- **Currency:** GBP.
- **License:** CC BY 4.0; see [data attribution](code/docs/DATA_ATTRIBUTION.md).

The original workbook and both complete yearly CSVs are stored locally in `data/raw` and excluded from GitHub. CSV conversion normalizes headers and formats timestamps without sampling. `source_manifest.txt` records the original workbook checksum and row counts.

The previous `sample` folder contained every 100th original row for a quick test; this version uses the full dataset instead. Previously used JSON files stored local/AWS configuration, source metadata or run counts. Local paths now live in `code/retail_pipeline/settings.py`; source metadata is plain text, run counts are CSV and optional AWS settings use a `.env` file.

---

## Setup and Execution

Use Python **3.11 or newer**. The project was tested with Python 3.14 on macOS. In PyCharm, select the project `.venv` interpreter; if `<No interpreter>` is shown, configure it in **Settings → Python Interpreter**.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python code/run_pipeline.py download
python code/run_pipeline.py prepare
python code/run_pipeline.py
```

Windows: create the environment with `python -m venv .venv` and activate it using `.venv\Scripts\Activate.ps1`.

In PyCharm, choose **Online Retail - Analysis**, or configure Script = `code/run_pipeline.py`, Parameters = `run`, Working directory = the project root, Interpreter = `.venv`. `python main.py` also works.

Large raw and cleaned datasets are excluded from GitHub. On a fresh clone, download the workbook and prepare the yearly CSVs before running the analysis:

```sh
python code/run_pipeline.py download
python code/run_pipeline.py prepare
python code/run_pipeline.py
```

To download the original workbook again: `python code/run_pipeline.py download`. Running the pipeline repeatedly adds only new normalized rows. Input corrections are append-only additions, not updates/deletions. Only one process should use the local database at a time.

For interactive analysis:

```sh
python -m jupyter lab code/Online_Retail_Analysis.ipynb
```

Run the notebook cells in order. It calls the same pipeline as the Python script and reads its generated outputs. Allow about 1 GB of available disk space and several GB of RAM for full-data execution. Initial workbook conversion may take a few minutes.

---

## Analysis

The analysis follows these steps:

- Load both yearly CSVs and normalize data types and whitespace.
- Hash all eight normalized source fields and ingest only new unique rows.
- Profile missing customer/date values, negative quantities and negative prices.
- Remove missing quantity/price, negative prices, stock code `M`, and descriptions `BANK CHARGES` and `AMAZONFEE`; retain negative-quantity returns, zero prices and unknown customers.
- Build date, country, product and customer dimensions plus a sales fact table. Facts require invoice, product, timestamp and country.
- Validate model integrity, calculate daily revenue/order KPIs and rank countries/products.
- Generate five charts and a country/day Tableau export.
- Compare Q4/non-Q4 daily revenue and return rates using Welch t-tests; model daily net revenue using Q4 and order count with OLS and HC3 robust errors.

The cleaned dataset is `data/processed/clean_online_retail.csv`. Query examples are in `code/sql/business_queries.sql`. The notebook is `code/Online_Retail_Analysis.ipynb`.

Prices/revenue use four decimal places. Returns are identified by negative quantity; cancellation prefixes alone do not change signs. Orders count distinct invoices, including cancellation invoices. Missing customers remain NULL. Product descriptions use lexicographic MAX; rebuilt country/fact keys are not stable external IDs.

---

## Results

The full-data pipeline produces **1,033,036 unique normalized raw rows** and **1,031,644 cleaned sales facts**. Net revenue is **GBP 19,097,536.1680** under the documented cleaning and deduplication rules.

Q4 daily net revenue exceeds non-Q4 daily net revenue by about **GBP 18,959.40** in the exploratory Welch comparison. The daily return-rate comparison does not show a statistically significant difference (p ≈ 0.958). The OLS model explains about **48.2%** of daily net-revenue variation using Q4 and daily invoice count.

These findings describe observed trading days and are not causal conclusions. Daily observations may be autocorrelated; missing trading days are not zero-filled and the final December is incomplete. The regression uses HC3 errors but does not correct for temporal dependence.

Outputs include:

- `reports/Online_Retail_Project_Report.md`: readable project report.
- `reports/q4_stats_tests_report.txt`, `reports/q4_regression_report.txt`: detailed statistical results.
- `reports/figures/*.png`: five visualizations.
- `reports/run_summary.csv`, `reports/pipeline.log`: processing counts and diagnostics.
- `data/processed/daily_kpis.csv`, `tableau_daily_kpis.csv`: reusable reporting datasets.
- `data/processed/warehouse/*.csv`, `retail.duckdb`: star-schema exports and generated database.

The database is generated locally and excluded from the downloadable ZIP. Run the pipeline before querying it or publishing to Redshift.

---

## Local and AWS Execution

Local execution uses DuckDB and Python and requires no AWS account. Optional publishing uploads data/reports to S3 and refreshes five tables in an existing Redshift Serverless `retail_demo` schema. See [AWS setup](code/aws/SETUP.md).

```sh
python -m pip install -r code/requirements-aws.txt
# Copy code/aws/.env.example to code/aws/.env and fill in the settings.
python code/publish_aws.py --dry-run
```

AWS publishing is not live-tested and can incur charges. Glue/Step Functions deployment is a future migration step, not a completed component. AWS COPY manifests are generated internally in JSON as required by Redshift; you do not maintain those as local config files.

---

## Verification

```sh
python -m unittest discover -s code/tests -v
python code/run_pipeline.py
python code/run_pipeline.py
```

The second run should report `new_rows: 0`. Detailed checks are in [verification notes](code/docs/VERIFICATION.md). Missing libraries: install requirements with the selected PyCharm interpreter. Database locks: close another process using the same database. Missing yearly CSVs: run `prepare`.

---

## Authors

- [Krystal Tran](https://github.com/tuyettran15999)

---

## License

Project code is licensed under MIT; see [LICENSE](LICENSE). The UCI dataset has a separate CC BY 4.0 license.

---

## Acknowledgements

- Data provider: UCI Machine Learning Repository and Daqing Chen.
- Tools: Python, pandas, NumPy, DuckDB, openpyxl, Matplotlib, SciPy, statsmodels and JupyterLab.
- Workflow reference: [ariah28's AWS retail pipeline](https://github.com/ariah28/End-to-End-Data-Engineering-Analytics-AWS). This project contains an original implementation; reference code is not redistributed.
- Project organization and README style follow the local Weather project. No Weather data or analysis was copied.
