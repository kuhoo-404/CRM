from pydantic_settings import BaseSettings
from functools import lru_cache
import os


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres123@localhost:5432/senai_crm"

    # GROQ
    
    GROQ_API_KEY: str = ""

    # App
    APP_ENV: str = "development"
    LOG_LEVEL: str = "INFO"

    # RAG
    CHROMA_PERSIST_DIR: str = "./chroma_db"
    KB_DIR: str = "./knowledge_base"
    CHUNK_SIZE: int = 400
    CHUNK_OVERLAP: int = 50
    RAG_TOP_K: int = 3

    # Scraper cache TTL in seconds (6 hours)
    SCRAPER_CACHE_TTL: int = 21600

    class Config:
        # Look for .env in backend/ AND one level up
        env_file = (
            os.path.join(os.path.dirname(__file__), "..", ".env"),      # backend/.env
            os.path.join(os.path.dirname(__file__), "..", "..", ".env"), # root/.env
        )
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()