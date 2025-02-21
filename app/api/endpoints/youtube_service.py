
import logging
import yt_dlp
import os
#import uuid
#import subprocess
import asyncio
from asyncio import TimeoutError
from pathlib import Path
from datetime import datetime
from typing import List, Optional
from app.utils.gpt_aws_s3 import S3Uploader
from app.core.config import settings
from pydantic import BaseModel, HttpUrl
from fastapi import APIRouter, HTTPException, BackgroundTasks #, UploadFile, File,

logger = logging.getLogger(__name__)

youtube_router = APIRouter()

# 初始化 S3 客户端
s3_uploader = S3Uploader()

class DownloadRequest(BaseModel):
    url: HttpUrl
    output_dir: str = "downloads"
    subtitle_langs: List[str] = ["en"]
    request_id: str
    user_id: str
    project_id: str
    timeout: int = 600  # 默认超时时间10分钟

class DownloadResponse(BaseModel):
    success: bool
    message: str
    request_id: str
    user_id: str
    project_id: str
    file_path: Optional[str] = None
    s3_url: Optional[str] = None
    error: Optional[str] = None
    status: str = "completed"  # 可能的状态: completed, timeout, error

class BatchDownloadRequest(BaseModel):
    urls: List[HttpUrl]
    request_id: str
    project_id: str
    user_id: str
    output_dir: str = "downloads"
    subtitle_langs: List[str] = ["en"]
    timeout: int = 600  # 默认超时时间10分钟

class BatchDownloadResponse(BaseModel):
    overall_success: bool
    results: List[DownloadResponse]

class YoutubeDownloader:
    def __init__(self, output_dir: str = 'downloads'):
        self.output_dir = Path(output_dir)
        self.ensure_output_directory()

    def ensure_output_directory(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def progress_hook(self, d):
        if d['status'] == 'downloading':
            percent = d.get('_percent_str', '0%')
            speed = d.get('_speed_str', 'N/A')
            logger.info(f"Downloading... {percent} at {speed}")
        elif d['status'] == 'finished':
            logger.info("Download finished.")

    async def upload_to_s3(
        self, 
        file_path: Path, 
        user_id: str, 
        project_id: str
        ) -> str:
        """Upload file to S3 and return the S3 URL"""
        try:
            # 构建S3键值，格式: user/{user_id}/project/{project_id}/youtube/{filename}
            s3_key = f"{user_id}/project/{project_id}/youtube/{file_path.name}"
            
            # 上传文件到S3
            await s3_uploader.upload_file(file_path, s3_key)
            
            # 生成S3 URL
            s3_url = s3_uploader.generate_s3_url(s3_key)
            logger.info(f"File uploaded to S3: {s3_url}")
            
            return s3_url
        except Exception as e:
            logger.error(f"Failed to upload to S3: {str(e)}")
            raise

    async def download_and_upload(
        self, 
        url: str, 
        subtitle_langs: List[str], 
        request_id: str,  
        user_id: str, 
        project_id: str
        ) -> DownloadResponse:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

        ydl_opts = {
            'format': 'bestaudio/best',
            'writeautomaticsub': True,
            'writesubtitles': True,
            'subtitleslangs': subtitle_langs,
            'subtitlesformat': 'srt',
            'outtmpl': str(self.output_dir / f'%(title)s_{timestamp}.%(ext)s'),
            'progress_hooks': [self.progress_hook],
            'no_warnings': True,
            'quiet': False,
            'socket_timeout': 30,
            'nocheckcertificate': True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                video_title = info.get('title', 'video')
                logger.info(f"Starting download for: {video_title}")

                ydl.download([url])
                file_path = str(self.output_dir / f"{video_title}_{timestamp}")

                # 上传到S3
                s3_url = await self.upload_to_s3(file_path, user_id, project_id)

                return DownloadResponse(
                    success=True,
                    message=f"Successfully downloaded and uploaded: {video_title}",
                    request_id=request_id,
                    user_id=user_id, 
                    project_id=project_id,
                    file_path=file_path,
                    s3_url=s3_url,
                    status="completed"
                )

        except Exception as e:
            error_msg = f"Error downloading {url}: {str(e)}"
            logger.error(error_msg)
            return DownloadResponse(
                success=False,
                message="Download failed",
                request_id=request_id,
                user_id=user_id, 
                project_id=project_id,
                error=error_msg,
                status="error"
            )

    async def download(
        self, 
        url: str, 
        subtitle_langs: List[str], 
        user_id: str, 
        project_id: str, 
        timeout: int
        ) -> DownloadResponse:
        """带超时控制的下载和上传"""
        try:
            # 使用 asyncio.wait_for 添加超时控制
            result = await asyncio.wait_for(
                self.download_and_upload(
                    url, 
                    subtitle_langs, 
                    user_id, 
                    project_id
                ),
                timeout=timeout
            )
            return result
        except TimeoutError:
            error_msg = f"Operation timed out after {timeout} seconds"
            logger.error(error_msg)
            return DownloadResponse(
                success=False,
                message="Operation timed out",
                request_id=request_id,
                user_id=user_id, 
                project_id=project_id,
                error=error_msg,
                status="timeout"
            )
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            return DownloadResponse(
                success=False,
                message="Operation failed",
                request_id=request_id,
                user_id=user_id, 
                project_id=project_id,
                error=error_msg,
                status="error"
            )

@youtube_router.post("/download", response_model=DownloadResponse)
async def download_video(request: DownloadRequest):
    """
    Download a single YouTube video
    """
    downloader = YoutubeDownloader(request.output_dir)
    return await downloader.download(
        str(request.url), 
        request.subtitle_langs,
        request.user_id,
        request.project_id,
        request.timeout
    )

@youtube_router.post("/batch-download", response_model=BatchDownloadResponse)
async def batch_download_videos(request: BatchDownloadRequest):
    """
    Download multiple YouTube videos
    """
    downloader = YoutubeDownloader(request.output_dir)
    results = []
    
    for url in request.urls:
        result = await downloader.download(
            str(url), 
            request.subtitle_langs,
            request.user_id,
            request.project_id,
            request.timeout
        )
        results.append(result)

    overall_success = all(result.success for result in results)
    
    return BatchDownloadResponse(
        overall_success=overall_success,
        results=results
    )

