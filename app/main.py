
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi.middleware.cors import CORSMiddleware
#from app.api.endpoints import segment, llm_chunk, stream_segment, audio_split, llm_service, audio_service
from app.api.endpoints import youtube_service
from app.core.logging import setup_logging
from app.utils.gpt_aws_s3 import S3Downloader

# Logging
setup_logging()

app = FastAPI(
    title="AiRepeater API",
    description="API for AiRepeater Product",
    version="1.0.0"
)

# 初始化 S3Downloader
s3_downloader = S3Downloader()

def cleanup_cache_job():
    s3_downloader.cleanup_cache()

# 设置调度器, 定期清除缓存
scheduler = AsyncIOScheduler()
scheduler.add_job(cleanup_cache_job, 'interval', hours=72)  # 每72小时清理一次
scheduler.start()

@app.on_event("shutdown")
def shutdown_event():
    scheduler.shutdown()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router register
app.include_router(youtube_service.youtube_router, prefix="/api/v1", tags=["youtube_downloader"])
# app.include_router(stream_segment.stream_router, prefix="/api/v1", tags=["stream_segment"])
# app.include_router(llm_chunk.llm_router, prefix="/api/v1", tags=["chunk"])
# app.include_router(audio_split.split_router, prefix="/api/v1", tags=["audio_split"])
# app.include_router(llm_service.llm_service_router, prefix="/api/v1", tags=["llm_service"])
# app.include_router(audio_service.audio_router, prefix="/api/v1", tags=["audio_service"])

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8200, reload=True)
