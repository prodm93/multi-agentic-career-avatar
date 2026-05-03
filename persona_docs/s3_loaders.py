# GET RID OF MODULE LATER UNLESS HELPER FUNCTIONS NEEDED #

import boto3
import os
from pathlib import Path

import logging
logger = logging.getLogger(__name__)


BUCKET_NAME = 'career-avatar-docs'
LOCAL_DOWNLOAD_DIR = './downloaded_career_files'


s3 = boto3.resource('s3',
                    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
                    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
                    region_name='eu-north-1')
bucket = s3.Bucket(BUCKET_NAME)


def _s3_loader(bucket):
    file_dl_count = 0
    objects = [obj for obj in bucket.objects.all() if not obj.key.endswith('/')]

    for s3_object in objects:
        last_mod = s3_object.last_modified # gotta store this with the key somewhere
        s3_key = s3_object.key
        
        local_file_path = os.path.join(LOCAL_DOWNLOAD_DIR, s3_key)

        Path(os.path.dirname(local_file_path)).mkdir(parents=True, exist_ok=True)

        try:
            bucket.download_file(s3_key, local_file_path)
            file_dl_count += 1
        except Exception as e:
            logger.error(f"Failed to download {s3_key}: {e}") 

    logger.info(f'Successfully loaded {file_dl_count} docs from S3 with {len(objects)} objects')