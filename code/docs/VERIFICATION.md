# Verification

The weather-style project layout was tested on macOS ARM64 with Python 3.14.
The full input contains 1,067,371 transactions across two yearly CSVs.
The full run produced 1,033,036 normalized unique raw rows and 1,031,644 cleaned sales facts, with net revenue GBP 19,097,536.1680.
Validation checks for staging rules, eligible fact counts and all four dimension references returned zero failures.
The second full run added zero new rows.
The test suite checks deduplication within/across runs, new-row ingestion, returns, missing customers, exclusions, fact integrity and invalid input schemas.
Five PNG charts, two Welch tests, the OLS report, cleaned data, daily KPIs and Tableau export are generated under data/processed and reports.
The notebook executes the same pipeline rather than reimplementing its rules.
AWS integration remains untested against live services; no AWS resources were created.
