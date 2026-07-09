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
    GOOGLE_API_KEY: str = ""
    GOOGLE_CSE_ID: str = ""
    
    @property
    def STRICT_REAL_DATA(self) -> bool:
        return True
        
    @property
    def ALLOW_SIMULATED_DATA(self) -> bool:
        return False
        
    DISCORD_WEBHOOK_URL: str = ""
    NEWS_API_KEY: str = "ab113727ec0a4ade8f560160b233b384"

    # Dynamic Scoring Weights and Threshold Configuration
    MEME_WEIGHT_VELOCITY: float = 20.0
    MEME_WEIGHT_LINK: float = 30.0
    MEME_WEIGHT_SURGE: float = 30.0
    MEME_WEIGHT_CAP: float = 10.0
    GLOBAL_ALERT_THRESHOLD: float = 50.0

    SCALE_VELOCITY: float = 10.0
    SCALE_SURGE: float = 5.0
    PENALTY_INSUFFICIENT_HISTORY: float = 30.5

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

settings = Settings()
