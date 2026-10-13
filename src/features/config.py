from pathlib import Path

AWS_PROFILE = 'spei'
AWS_REGION = 'us-east-1'
S3_STAGING_DIR = 's3://spei-fraud-detection-adelalama/athena-results/'
ATHENA_WORKGROUP = 'spei'

DBT_SCHEMA = 'spei_dbt'
FCT_TABLE = 'fct_transaction_features'
DIM_TABLE = 'dim_accounts'

PROJECT_ROOT = Path(__file__).parent.parent.parent
CACHE_DIR = PROJECT_ROOT / 'artifacts' / 'cache'
FCT_CACHE_PATH = CACHE_DIR / 'fct_transaction_features.parquet'
DIM_CACHE_PATH = CACHE_DIR / 'dim_accounts.parquet'