import logging
import boto3

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BUCKET = 'spei-fraud-detection-adelalama'
DATABASE_NAME = 'spei_raw'

ACCOUNTS_COLUMNS = [
    {'Name': 'account_id', 'Type': 'bigint'},
    {'Name': 'person_id', 'Type': 'bigint'},
    {'Name': 'bank_code', 'Type': 'string'},
    {'Name': 'plaza_code', 'Type': 'string'},
    {'Name': 'account_number', 'Type': 'string'},
    {'Name': 'clabe', 'Type': 'string'},
    {'Name': 'kyc_tier', 'Type': 'int'},
    {'Name': 'creation_date', 'Type': 'timestamp'},
    {'Name': 'phone_number', 'Type': 'string'},
    {'Name': 'activity_segment', 'Type': 'string'},
    {'Name': 'mule_type', 'Type': 'string'},
]

TRANSACTIONS_COLUMNS = [
    {'Name': 'transaction_id', 'Type': 'bigint'},
    {'Name': 'sender_account_id', 'Type': 'bigint'},
    {'Name': 'sender_clabe', 'Type': 'string'},
    {'Name': 'receiver_account_id', 'Type': 'bigint'},
    {'Name': 'receiver_clabe', 'Type': 'string'},
    {'Name': 'amount', 'Type': 'decimal(12,2)'},
    {'Name': 'transaction_date', 'Type': 'timestamp'},
    {'Name': 'concept_pago', 'Type': 'string'},
    {'Name': 'status', 'Type': 'string'},
    {'Name': 'is_fraud', 'Type': 'boolean'},
    {'Name': 'fraud_typology', 'Type': 'string'},
    {'Name': 'fraud_event_id', 'Type': 'bigint'},
]

def parquet_storage_descriptor(columns, s3_location):
    """Storage Descriptor dict for parquet tables"""
    return {
        'Columns': columns,
        'Location': s3_location,
        'InputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetInputFormat',
        'OutputFormat': 'org.apache.hadoop.hive.ql.io.parquet.MapredParquetHiveOutputFormat',
        'SerdeInfo': {
            'SerializationLibrary': 'org.apache.hadoop.hive.ql.io.parquet.serde.ParquetHiveSerDe',
        },
    }

def ensure_database(glue_client, database_name):
    """Create glue db if not exists"""
    try:
        glue_client.create_database(DatabaseInput = {'Name': database_name})
        logger.info('Created database %s', database_name)
    except glue_client.exceptions.AlreadyExistsException:
        logger.info('Database %s already exists',  database_name)

def recreate_table(glue_client, database_name, table_name, columns, s3_location):
    """Delete and recreate table"""
    try:
        glue_client.delete_table(DatabaseName = database_name, Name = table_name)
        logger.info('Deleted table %s', table_name)
    except glue_client.exceptions.EntityNotFoundException:
        pass

    glue_client.create_table(
        DatabaseName = database_name,
        TableInput = {
            'Name': table_name,
            'StorageDescriptor': parquet_storage_descriptor(columns, s3_location),
            'TableType': 'EXTERNAL_TABLE',
            'Parameters': {'classification': 'parquet'}
        }
    )
    logger.info('Created table %s', table_name)

def main():
    glue = boto3.Session(profile_name='spei').client('glue')

    ensure_database(glue, DATABASE_NAME)

    recreate_table(
        glue,
        DATABASE_NAME,
        'accounts',
        ACCOUNTS_COLUMNS,
        f's3://{BUCKET}/raw/accounts/'
    )

    recreate_table(
        glue,
        DATABASE_NAME,
        'transactions',
        TRANSACTIONS_COLUMNS,
        f's3://{BUCKET}/raw/transactions/'
    )

    logger.info('Glue catalog setup complete')

if __name__ == "__main__":
    main()