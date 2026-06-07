"""Pydantic schemas for API."""
from pydantic import BaseModel
from typing import List
from datetime import datetime

class AlertBase(BaseModel):
    ticker_symbol: str
    brand_name: str
    meme_score: float
    volume_surge_multiplier: float
    social_velocity: float

class AlertResponse(AlertBase):
    id: int
    timestamp: datetime
    company_name: str = None
    market_cap: float = None
    
    class Config:
        from_attributes = True
