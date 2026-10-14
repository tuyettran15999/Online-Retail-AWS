# Reference inspection

Repository: https://github.com/ariah28/End-to-End-Data-Engineering-Analytics-AWS
Inspected main commit: `2f056d28a7fee0740d36e1440abed91fa3b3f55f`, October 14, 2026.

Reviewed the README, raw-to-staging script, star-schema SQL, statistics/regression/BI export scripts, Glue Terraform, IAM/scheduler setup and state machine. The repository contains no raw dataset; its README expects two yearly Online Retail II CSVs in S3. The original public UCI workbook supplies that dataset under CC BY 4.0.

Preserved workflow: ingestion → raw quality profiling → clean staging retaining returns → four dimensions + sales fact → daily/country/product KPIs → five charts → Q4 revenue/return-rate Welch tests → revenue OLS controlling for orders → Tableau export.

Adaptations: DuckDB local execution; original source preparation; eight-field null-safe deduplication; transactional model rebuild; explicit integrity failures; four-decimal monetary precision; Student-t Welch inference; HC3 OLS errors; regression report saved; all exports included in local orchestration. See README for resulting semantic differences. Local project organization follows data/raw, data/processed, code and reports.

Reference deployment gaps observed at this commit:

- Glue scripts read configuration from `os.environ`, while Terraform supplies `--PARAMETER` job arguments. Glue argument parsing must bridge this explicitly.
- The state machine names schema/raw/profiling/model/query/visual jobs for which the reviewed Glue Terraform does not define corresponding job resources or executable SQL wrappers.
- Raw profiling precedes the raw sync, so a first run profiles an empty raw table.
- Tableau export is defined as a job but not included in the state machine sequence.
- Job names are hard-coded in the state machine while Terraform uses a configurable project prefix.
- Failure notification uses `$$.State.Name` inside the notification state, which identifies that state rather than the original failed task.

These are why this project provides an independently runnable local implementation and an explicit AWS bridge, rather than representing the reference's Terraform as a verified deployment.
