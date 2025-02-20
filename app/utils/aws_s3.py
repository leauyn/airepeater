import logging
import boto3
from fastapi import HTTPException
from botocore.exceptions import ClientError
from app.core.config import settings
from app.utils.s3_client import s3_client
from pathlib import Path

logger = logging.getLogger(__name__)

class S3Downloader:

    def __init__(self, bucket_name: str = "accentdaily"):
        self.bucket_name = bucket_name

    async def download_file(self, s3_key: str):
        """
        Download from S3 to temp folder
        """
        try:
            local_path = Path(settings.TEMP_DIR) / Path(s3_key).name
            s3_client.download_file(
                self.bucket_name,
                s3_key,
                str(local_path)
            )
            logger.info(f"File download success: {local_path}")
            return local_path
        except ClientError as e:
            logger.error(f"S3 download failed: {str(e)}")
            raise HTTPException(status_code=404, detail=f"File {s3_key} does not exist or have no access")
        except Exception as e:
            logger.error(f"Error in downloading S3 file {s3_key}: {str(e)}")
            raise HTTPException(status_code=500, detail="Server internal Error")

    def cleanup_temp_file(self, file_path: Path):
        try:
            if file_path.exists():
                file_path.unlink()
                logger.info(f"Temp file deleted: {file_path}")
        except Exception as e:
            logger.error(f"Temp file {file_path} removed failed: {str(e)}")

class S3Uploader:

    def __init__(self, bucket_name: str = "accentdaily"):
        self.bucket_name = bucket_name

    async def upload_file(self, file_path: Path, s3_key: str):
        try:
            s3_client.upload_file(
                str(file_path),
                self.bucket_name,
                s3_key
            )
            logger.info(f"File upload success: {s3_key}")
            return s3_key
        except ClientError as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to upload file to S3: {str(e)}")
        except Exception as e:
            logger.error(f"Error in uploading file to S3: {str(e)}")
            raise HTTPException(status_code=500, detail="Server internal Error")
