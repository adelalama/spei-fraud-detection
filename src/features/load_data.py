import logging
import pandas as pd
from pyathena import connect

from src.features.config import (
    AWS_PROFILE,
    AWS_REGION,
    S3_STAGING_DIR,
    ATHENA_WORKGROUP,
    DBT_SCHEMA,
    FCT_TABLE,
    DIM_TABLE,
    FCT_CACHE_PATH,
    DIM_CACHE_PATH,
    CACHE_DIR
)

logger = logging.getLogger(__name__)

def _get_athena_connection():
    """pyathena connection using configured AWS profile"""
    return connect(
        profile_name = AWS_PROFILE,
        region_name=AWS_REGION,
        s3_staging_dir=S3_STAGING_DIR,
        work_group = ATHENA_WORKGROUP,
    )

def load_fct_features(refresh: bool = False) -> pd.DataFrame:
    """Load fct_transaction_features from Athena and cache locally as parquet"""
    if FCT_CACHE_PATH.exists() and not refresh:
        logger.info('Loading FCT features from cache')
        return pd.read_parquet(FCT_CACHE_PATH)

    logger.info('Querying Athena for FCT features')
    query = f"SELECT * FROM {DBT_SCHEMA}.{FCT_TABLE}"
    connection = _get_athena_connection()
    try:
        df = pd.read_sql(query, connection)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(FCT_CACHE_PATH, index = False)
        return df
    finally:
        connection.close()

def load_dim_accounts(refresh: bool = False) -> pd.DataFrame:
    """Load dim_accounts from Athena and cache locally as parquet"""
    if DIM_CACHE_PATH.exists() and not refresh:
        logger.info('Loading DIM accounts from cache')
        return pd.read_parquet(DIM_CACHE_PATH)

    logger.info('Querying Athena for DIM accounts')
    query = f'SELECT * FROM {DBT_SCHEMA}.{DIM_TABLE}'
    connection = _get_athena_connection()
    try:
        df = pd.read_sql(query, connection)
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(DIM_CACHE_PATH, index = False)
        return df
    finally:
        connection.close()