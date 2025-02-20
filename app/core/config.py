from pydantic_settings import BaseSettings
from pathlib import Path
from functools import lru_cache

class Settings(BaseSettings):
    MODEL_SIZE: str = "tiny.en"
    MODEL_DIR: str = "/models"
    BATCH_MODE: bool = False
    BATCH_SIZE: int = 4
    DEVICE: str = "cpu"

    TEMP_DIR: str = "./temp"
    LOG_LEVEL: str = "INFO"

    AWS_REGION: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_ACCESS_KEY_ID: str
    AWS_BUCKET_NAME: str

    OPENAI_API_KEY: str

    MAX_CONCURRENT_TRANSCRIBERS: int = 4

    CACHE_DIR: Path = Path("./temp") # Cache dir
    CACHE_TTL: int = 3600 * 24 # Cache expire time, second, 3600s=1h

    #SAVE_VIDEO_TO_S3: True

    class Config:
        env_file = ".env"

settings = Settings()

# ensure temp folder exist
Path(settings.TEMP_DIR).mkdir(parents=True, exist_ok=True)

