import json
import yt_dlp

URL = 'https://www.youtube.com/watch?v=qyfBj44Bykc'

# ℹ️ See help(yt_dlp.YoutubeDL) for a list of available options and public functions
ydl_opts = {
    'format': 'm4a/bestaudio/best',
    # ℹ️ See help(yt_dlp.postprocessor) for a list of available Postprocessors and their arguments
    'postprocessors': [{  # Extract audio using ffmpeg
        'key': 'FFmpegExtractAudio',
        'preferredcodec': 'mp3',
    }]
}
with yt_dlp.YoutubeDL(ydl_opts) as ydl:
    ydl.extract_info(URL)
