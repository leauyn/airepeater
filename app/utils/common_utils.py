# -*- coding:utf-8 -*-

#================================================================
#
#   File：common_utils.py
#   Author：YongLiao, leauyn@hotmail.com
#   Date：2025-02-06 22:44
#   Description：
#
#================================================================
import logging
import uuid
import subprocess
import asyncio
from pathlib import Path
from fastapi import HTTPException #, UploadFile, File,

logger = logging.getLogger(__name__)

async def check_media_type(file_path: Path) -> str:
    try:
        command = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_streams",
            str(file_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFprobe failed: {stderr.decode()}")

        import json
        info = json.loads(stdout.decode())

        # Check while contains video stream or not
        for stream in info.get("streams", []):
            if stream.get('codec_type') == "video":
                return "video"
        return "audio"
    except Exception as e:
        logger.error(f"Error checking media type: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to check media type: {str(e)}")

async def extract_audio(input_path: Path, output_path: Path):
    try:
        command = [
            "ffmpeg",
            "-i", str(input_path),
            "-vn", # remove video stream
            "-acodec", "libmp3lame", # encode with mp3
            "-q:a", "2",
            str(output_path)
        ]

        process = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            raise Exception(f"FFmpeg failed: {stderr.decode()}")

    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to extract audio: {str(e)}")
