# -*- coding:utf-8 -*-

#================================================================
#
#   File：gpt_aws_s3.py
#   Author：YongLiao, leauyn@hotmail.com
#   Date：2024-12-27 17:25
#   Description：
#
#================================================================

# app/utils/aws_s3.py

import logging
import asyncio
from datetime import datetime, timedelta
from aiobotocore.session import get_session
from pathlib import Path
from app.core.config import settings

logger = logging.getLogger(__name__)

class S3Downloader:
    def __init__(self, bucket_name: str = settings.AWS_BUCKET_NAME):
        self.bucket = bucket_name
        self.session = get_session()
        self.cache_dir = settings.CACHE_DIR
        self.cache_ttl = timedelta(seconds=settings.CACHE_TTL)
        self.lock = asyncio.Lock() # 处理并发下载

    async def download_file(self, s3_key: str, download_dir: Path) -> Path:
        cached_file_path = self.cache_dir / Path(s3_key).name
        async with self.lock:
            if cached_file_path.exists():
                file_mod_time = datetime.fromtimestamp(cached_file_path.stat().st_mtime)
                if datetime.now() - file_mod_time < self.cache_ttl:
                    logger.info(f"Using cached file: {cached_file_path}")
                    return cached_file_path
                else:
                    logger.info(f"Cached file expires, re-download: {cached_file_path}")
                    cached_file_path.unlink() # 删除过期的缓存文件

            logger.info(f"Download file from S3: {s3_key} to {cached_file_path}")
            async with self.session.create_client(
                's3',
                region_name=settings.AWS_REGION,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID
            ) as client:
                response = await client.get_object(Bucket=self.bucket, Key=s3_key)
                with open(cached_file_path, 'wb') as f:
                    async for chunk in response['Body'].iter_chunks():
                        if chunk:
                            f.write(chunk)
                return cached_file_path

    def cleanup_cache(self):
        """
        清理过期的缓存文件
        """
        now = datetime.now()
        for file in self.cache_dir.iterdir():
            if file.is_file():
                file_mod_time = datetime.fromtimestamp(file.stat().st_mtime)
                if now - file_mod_time > self.cache_ttl:
                    try:
                        file.unlink()
                        logger.info(f"Clean the cached file: {file}")
                    except Exception as e:
                        logger.error(f"Unable to clean the cached {file}: {e}")

class S3Uploader:
    def __init__(self, bucket_name: str = settings.AWS_BUCKET_NAME):
        self.bucket = bucket_name
        self.session = get_session()

    async def upload_file(self, file_path: Path, s3_key: str) -> str:
        async with self.session.create_client(
            's3',
            region_name=settings.AWS_REGION,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID
        ) as client:
            with open(file_path, 'rb') as f:
                await client.put_object(Bucket=self.bucket, Key=s3_key, Body=f)
            return s3_key

    def generate_s3_url(self, s3_key: str) -> str:
        return f"https://{self.bucket}.s3.{settings.AWS_REGION}.amazonaws.com/{s3_key}"

