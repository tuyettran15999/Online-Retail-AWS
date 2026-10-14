# Optional AWS Publishing

Local analysis runs with Python and DuckDB. AWS publishing is optional and has not been tested against a live account. It does not implement native Glue or Step Functions jobs or provision resources.

## Setup

1. Run the full local analysis first: `python code/run_pipeline.py`.
2. Create a private, encrypted S3 bucket in your chosen region.
3. Configure an existing Redshift Serverless namespace/workgroup and database. Store the database username/password in Secrets Manager. The database user needs CREATE, DELETE and COPY access to the dedicated `retail_demo` schema.
4. Attach a COPY IAM role to Redshift with permission to list/read the published S3 prefixes and decrypt with KMS if applicable.
5. Configure AWS CLI credentials or SSO outside this project. The publishing identity needs S3 upload permissions, `redshift-data:BatchExecuteStatement`, `DescribeStatement`, `CancelStatement`, and `secretsmanager:GetSecretValue`, with relevant KMS permissions.
6. Install dependencies and copy `code/aws/.env.example` to `code/aws/.env`. Fill in the bucket, workgroup, database, secret ARN and COPY role ARN. Do not add access keys or database passwords to the file.

```sh
python -m pip install -r code/requirements-aws.txt
python code/publish_aws.py --dry-run
```

Dry-run generates `reports/redshift_load.sql` without contacting AWS. All placeholder settings must be filled even in dry-run mode.

```sh
# Upload processed data and reports, plus prepared raw CSVs:
python code/publish_aws.py
# Upload and replace rows in the five retail_demo star-schema tables:
python code/publish_aws.py --load-redshift
```

Each run uses an immutable S3 prefix. Exact-object COPY manifests prevent prefix collisions. Those manifests are generated internally in JSON because Redshift requires that format; they are not local configuration files.

The Data API loads the five tables in one transactional batch using DELETE, not TRUNCATE. Failed database loads roll back, while uploaded S3 files remain available for diagnosis. Existing table definitions must match the local export schema. Do not run concurrent publishers. The script waits for completion and requests cancellation after 30 minutes.

Compare `SELECT COUNT(*), SUM(total_price) FROM retail_demo.fact_sales` with `reports/run_summary.csv`. Use a lifecycle policy for old S3 run prefixes and review Serverless spending limits. These commands can incur AWS charges. Remove unused objects and resources through your normal account process.

## Native AWS workflow

For S3 → Glue/PySpark → Redshift → Step Functions → SNS/CloudWatch, separately implement and test native transformations, SQL execution wrappers, credentials/networking, validation, all analytics/export tasks, retry/failure paths and infrastructure definitions. DuckDB SQL is not directly portable to Spark or Redshift. Parse Glue job arguments through `getResolvedOptions`. Profile after ingestion and explicitly include Tableau export. The reference deployment gaps are recorded in `code/docs/REFERENCE_REVIEW.md`.

Official documentation:
- [Redshift Data API](https://docs.aws.amazon.com/redshift/latest/mgmt/data-api.html)
- [Redshift COPY](https://docs.aws.amazon.com/redshift/latest/dg/r_COPY.html)
- [Step Functions Glue integration](https://docs.aws.amazon.com/step-functions/latest/dg/connect-glue.html)
