"""Application configurations."""
import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    DATABASE_URL: str = "sqlite:///./trendpulse.db"
    API_KEY: str = "dev_secret_key_123"
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""

    class Config:
        env_file = ".env"

settings = Settings()
