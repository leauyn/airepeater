from functools import lru_cache
import boto3
from app.core.config import settings 

#https://docs.aws.amazon.com/code-library/latest/ug/python_3_s3_code_examples.html

@lru_cache
def get_s3_client():
    """
    Get S3 client singleton
    """
    return boto3.client(
        's3',
        aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
        aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
        region_name=settings.AWS_REGION
    )

s3_client = get_s3_client()

