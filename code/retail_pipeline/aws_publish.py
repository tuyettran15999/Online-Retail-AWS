"""Optional, explicit AWS bridge; never invoked by a local pipeline run."""
import argparse
import json
import re
import time
import uuid
from pathlib import Path
import duckdb
from .config import ROOT, load

TABLES = ['dim_date','dim_country','dim_product','dim_customer','fact_sales']

def literal(value):
    return "'" + str(value).replace("'", "''") + "'"

def build_sql(config, database, run_prefix):
    schema = 'retail_demo'
    statements = [f'CREATE SCHEMA IF NOT EXISTS {schema}']
    with duckdb.connect(database, read_only=True) as connection:
        for table in TABLES:
            columns = connection.execute(f'DESCRIBE analytics.{table}').fetchall()
            ddl = ', '.join('"' + column[0] + '" ' + ('VARCHAR(65535)' if column[1]=='VARCHAR' else column[1]) for column in columns)
            statements.append(f'CREATE TABLE IF NOT EXISTS {schema}.{table} ({ddl})')
            # DELETE participates in the batch transaction; Redshift TRUNCATE commits.
            statements.append(f'DELETE FROM {schema}.{table}')
            manifest = f"s3://{config['bucket']}/{run_prefix}/processed/warehouse/{table}.manifest.json"
            statements.append(f"COPY {schema}.{table} FROM {literal(manifest)} IAM_ROLE {literal(config['copy_role_arn'])} MANIFEST FORMAT AS CSV IGNOREHEADER 1 EMPTYASNULL BLANKSASNULL DATEFORMAT 'auto' TIMEFORMAT 'auto' REGION {literal(config['region'])}")
    return statements

def main():
    parser = argparse.ArgumentParser(description='Publish local outputs to S3; optionally refresh retail_demo in Redshift Serverless')
    parser.add_argument('--load-redshift',action='store_true')
    parser.add_argument('--dry-run',action='store_true',help='Generate SQL locally without calling AWS')
    args = parser.parse_args()
    import os
    from dotenv import load_dotenv
    load_dotenv(ROOT / 'code/aws/.env')
    config = {
        'region': os.environ.get('AWS_REGION', 'us-east-1'),
        'profile': os.environ.get('AWS_PROFILE'),
        'bucket': os.environ.get('RETAIL_S3_BUCKET'),
        'prefix': os.environ.get('RETAIL_S3_PREFIX', 'online-retail'),
        'workgroup': os.environ.get('RETAIL_REDSHIFT_WORKGROUP'),
        'database': os.environ.get('RETAIL_REDSHIFT_DATABASE', 'dev'),
        'secret_arn': os.environ.get('RETAIL_SECRET_ARN'),
        'copy_role_arn': os.environ.get('RETAIL_COPY_ROLE_ARN'),
    }
    for key in ['bucket','prefix','region','copy_role_arn','workgroup','database','secret_arn']:
        if not config.get(key) or 'REPLACE' in config[key]:
            raise ValueError(f'Configure {key} in code/aws/.env')
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]{1,61}[a-z0-9]',config['bucket']):
        raise ValueError('Invalid S3 bucket name')
    if not re.fullmatch(r'[A-Za-z0-9/_-]+',config['prefix']):
        raise ValueError('Prefix must contain letters, digits, /, _ or -')
    local = load()
    out = Path(local['output_dir'])
    if not (out/'run_summary.csv').exists():
        raise ValueError('Run the local pipeline successfully before publishing')
    run_prefix = config['prefix'].strip('/') + '/runs/' + uuid.uuid4().hex
    sql = build_sql(config,local['database'],run_prefix)
    (out/'redshift_load.sql').write_text(';\n'.join(sql)+';\n')
    if args.dry_run:
        print('Dry run: generated reports/redshift_load.sql. No AWS calls.'); return
    import boto3
    session = boto3.Session(profile_name=config.get('profile'),region_name=config['region'])
    s3 = session.client('s3')
    for folder, label in [(out, 'reports'), (Path(local['processed_dir']), 'processed')]:
        for path in folder.rglob('*'):
            if not path.is_file() or '.mplconfig' in path.parts or path.suffix in ['.duckdb', '.wal']:
                continue
            key = run_prefix + '/' + label + '/' + path.relative_to(folder).as_posix()
            s3.upload_file(str(path), config['bucket'], key)
    # COPY manifests point to exactly one immutable object, avoiding prefix matches.
    for table in TABLES:
        key = f'{run_prefix}/processed/warehouse/{table}.csv'
        manifest = {'entries':[{'url':f"s3://{config['bucket']}/{key}",'mandatory':True}]}
        s3.put_object(Bucket=config['bucket'],Key=f'{run_prefix}/processed/warehouse/{table}.manifest.json',Body=json.dumps(manifest).encode())
    # Upload prepared full yearly source CSVs.
    for path in Path(local['raw_dir']).glob('*.csv'):
        s3.upload_file(str(path),config['bucket'],f'{run_prefix}/raw/{path.name}')
    print(f"Published s3://{config['bucket']}/{run_prefix}/")
    if args.load_redshift:
        client = session.client('redshift-data')
        result = client.batch_execute_statement(WorkgroupName=config['workgroup'],Database=config['database'],SecretArn=config['secret_arn'],Sqls=sql,ClientToken=uuid.uuid4().hex)
        statement_id = result['Id']; deadline = time.monotonic()+1800
        print('Redshift statement:',statement_id)
        while time.monotonic()<deadline:
            status = client.describe_statement(Id=statement_id)
            if status['Status']=='FINISHED':
                print('Loaded five tables into retail_demo.'); return
            if status['Status'] in ['FAILED','ABORTED']:
                raise RuntimeError(status.get('Error',status['Status']))
            time.sleep(2)
        client.cancel_statement(Id=statement_id)
        raise TimeoutError('Redshift load exceeded 30 minutes; cancellation requested')

if __name__ == '__main__':
    main()
