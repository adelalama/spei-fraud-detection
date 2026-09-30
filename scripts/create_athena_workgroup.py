import logging
import boto3


logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BUCKET = 'spei-fraud-detection-adelalama'
REGION = 'us-east-1'
WORKGROUP_NAME = 'spei'
RESULTS_LOCATION = 's3://spei-fraud-detection-adelalama/athena-results/'

def ensure_workgroup(athena_client, workgroup_name, results_location):
    """Create athena workgroup if it doesn't exist"""
    try:
        athena_client.create_work_group(
            Name=workgroup_name,
            Configuration={
                'ResultConfiguration': {
                    'OutputLocation': results_location
                },
                'EnforceWorkGroupConfiguration': True,
                'PublishCloudWatchMetricsEnabled': False,
            },
            Description='Workgroup for SPEI queries',
        )
        logger.info('Created workgroup %s', workgroup_name)

    except athena_client.exceptions.InvalidRequestException as e:
        if 'already exists' in str(e).lower():
            logger.info('Workgroup %s already exists', workgroup_name)
        else:
            raise


def main():
    athena = boto3.Session(profile_name='spei').client('athena', region_name=REGION)
    ensure_workgroup(athena, WORKGROUP_NAME, RESULTS_LOCATION)
    logger.info('Athena setup complete')

if __name__ == '__main__':
    main()