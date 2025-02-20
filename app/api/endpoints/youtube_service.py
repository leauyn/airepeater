
import logging
import yt_dlp
#import uuid
#import subprocess
#import asyncio
from pathlib import Path
#from tempfile import TemporaryDirectory
from datetime import datetime
from typing import List, Optional
from app.utils.gpt_aws_s3 import S3Downloader, S3Uploader
#from app.core.config import settings
from pydantic import BaseModel, Field, validator, HttpUrl
from fastapi import APIRouter, HTTPException, BackgroundTasks #, UploadFile, File,

logger = logging.getLogger(__name__)

youtube_router = APIRouter()

# 初始化 S3 客户端
s3_downloader = S3Downloader()
s3_uploader = S3Uploader()

class DownloadRequest(BaseModel):
    request_id: str
    project_id: str
    user_id: str
    url: HttpUrl
    output_dir: str = "downloads"
    subtitle_langs: List[str] = ["en"]

class DownloadResponse(BaseModel):
    success: bool
    message: str
    file_path: Optional[str] = None
    error: Optional[str] = None

class BatchDownloadRequest(BaseModel):
    urls: List[HttpUrl]
    output_dir: str = "downloads"
    subtitle_langs: List[str] = ["en"]

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

    async def download(self, url: str, subtitle_langs: List[str] = ['en']) -> DownloadResponse:
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

                return DownloadResponse(
                    success=True,
                    message=f"Successfully downloaded: {video_title}",
                    file_path=file_path
                )

        except Exception as e:
            error_msg = f"Error downloading {url}: {str(e)}"
            logger.error(error_msg)
            return DownloadResponse(
                success=False,
                message="Download failed",
                error=error_msg
            )

@youtube_router.post("/download", response_model=DownloadResponse)
async def download_video(request: DownloadRequest, background_tasks: BackgroundTasks):
    """
    Download a single YouTube video
    """
    downloader = YoutubeDownloader(request.output_dir)
    return await downloader.download(
        str(request.url), 
        request.subtitle_langs
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
            request.subtitle_langs
        )
        results.append(result)

    overall_success = all(result.success for result in results)
    
    return BatchDownloadResponse(
        overall_success=overall_success,
        results=results
    )

