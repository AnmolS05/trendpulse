"""Application configurations."""
import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    DATABASE_URL: str = "sqlite:///./trendpulse.db"
    API_KEY: str = "dev_secret_key_123"
    ALPACA_API_KEY: str = ""
    ALPACA_SECRET_KEY: str = ""
    REDDIT_CLIENT_ID: str = ""
    REDDIT_CLIENT_SECRET: str = ""
    STRICT_REAL_DATA: bool = True
    ALLOW_SIMULATED_DATA: bool = False
    DISCORD_WEBHOOK_URL: str = ""
    NEWS_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
