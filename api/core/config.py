from pydantic_settings import BaseSettings
from functools import lru_cache
from config import Config

class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "FaceForge AI API"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "AI-powered image and video processing API"
    
    # API Key validation
    API_KEY_ACCESS: str = Config.API_KEY_ACCESS
    
    class Config:
        case_sensitive = True

@lru_cache()
def get_settings() -> Settings:
    return Settings() 