from pydantic_settings import BaseSettings
from typing import List

class Settings(BaseSettings):
    PROJECT_NAME: str = "GMGN Trending Service"
    API_V1_STR: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["*"]
    
    # App settings
    LOG_LEVEL: str = "INFO"
    
    # External Services
    GMGN_WRAPPER_URL: str = "http://5.189.166.36:4001"
    GMGN_API_KEY: str = "test-api-key-1"
    
    class Config:
        env_file = ".env"

settings = Settings()
