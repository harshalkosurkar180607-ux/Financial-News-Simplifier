import os
from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

load_dotenv()

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="allow")

    APP_NAME: str = "FinNews AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # AI and News API Keys
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", "")
    NEWS_API_KEY: Optional[str] = os.getenv("NEWS_API_KEY", "")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    # SQLite Database
    DATABASE_PATH: str = os.getenv("DATABASE_PATH", "finnews.db")
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]

settings = Settings()
