import logging
import pandas as pd
from pyathena import connect
from pyathena.pandas.cursor import PandasCursor

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
        cursor_class=PandasCursor
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
        cursor = connection.cursor()
        cursor.execute(query)
        df = cursor.as_pandas()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        amount_cols = [
            'amount',
            'amount_vs_sender_avg',
            'sender_amount_sum_24h',
            'sender_amount_avg_24h',
            'sender_amount_max_7d',
            'receiver_amount_max_7d',
        ]
        for col in amount_cols:
            df[col] = pd.to_numeric(df[col], errors='coerce')
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
        cursor = connection.cursor()
        cursor.execute(query)
        df = cursor.as_pandas()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(DIM_CACHE_PATH, index = False)
        return df
    finally:
        connection.close()

def load_fraud_typology(refresh: bool = False) -> pd.DataFrame:
    """Loads fraud typology labels for all fraud transactions"""

    cache_path = CACHE_DIR / 'fraud_typology.parquet'
    if cache_path.exists() and not refresh:
        logger.info('Loading fraud typlogy from cache')
        return pd.read_parquet(cache_path)

    logger.info('Querying Athena for fraud typology labels')
    query = f'SELECT transaction_id, fraud_typology FROM {DBT_SCHEMA}.stg_transactions WHERE is_fraud = true'
    connection = _get_athena_connection()
    try:
        cursor = connection.cursor()
        cursor.execute(query)
        df = cursor.as_pandas()
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        df.to_parquet(cache_path, index = False)
        return df
    finally:
        connection.close()

