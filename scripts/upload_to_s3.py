import logging
import boto3
from src.data_generator.accounts import generate_accounts
from src.data_generator.transactions import generate_transactions
from src.data_generator.fraud_injection import inject_fraud

logging.basicConfig(level=logging.INFO, format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BUCKET = 'spei-fraud-detection-adelalama'
REGION = 'us-east-1'

def upload_to_s3():
    logger.info('Starting SPEI data generation')
    accounts_df = generate_accounts(10_000)
    transactions_df = generate_transactions(accounts_df)
    final_df = inject_fraud(transactions_df, accounts_df)

    logger.info('Writing Parquet files')
    accounts_df.to_parquet('/tmp/accounts.parquet', index = False)
    final_df.to_parquet('/tmp/transactions.parquet', index = False)

    logger.info("Uploading to S3 bucket %s", BUCKET)
    s3 = boto3.Session(profile_name= 'spei').client('s3')
    s3.upload_file('/tmp/accounts.parquet', BUCKET, 'raw/accounts/accounts.parquet')
    s3.upload_file('/tmp/transactions.parquet', BUCKET, 'raw/transactions/transactions.parquet')

    logger.info("Upload complete: %d accounts, %d transactions", len(accounts_df), len(final_df))

if __name__ == '__main__':
    upload_to_s3()

