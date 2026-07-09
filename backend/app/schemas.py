"""Pydantic schemas for API validation."""
from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

class AlertBase(BaseModel):
    """Base schema containing shared alert properties."""
    ticker_symbol: str
    brand_name: str
    meme_score: float
    volume_surge_multiplier: float
    social_velocity: float


class AlertResponse(AlertBase):
    """Enriched schema for alert response data."""
    id: int
    timestamp: datetime
    company_name: Optional[str] = None
    market_cap: Optional[float] = None
    confidence_score: float = 0.0
    confidence_drivers: Optional[str] = None
    confidence_weaknesses: Optional[str] = None
    explanation: Optional[str] = None
    evidence_summary: Optional[str] = None
    risk_summary: Optional[str] = None
    risk_flags: Optional[str] = None
    news_count: int = 0
    is_predictive: int = 0
    surge_probability: Optional[float] = None
    social_acceleration: Optional[float] = None
    est_lead_time_hours: Optional[float] = None
    
    model_config = ConfigDict(from_attributes=True)


class SourceHealthResponse(BaseModel):
    """Schema for reporting external API source health metrics."""
    source: str
    status: str
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    last_error_code: Optional[str] = None
    last_error_message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TrendObservationResponse(BaseModel):
    """Schema for individual social observation details."""
    id: int
    topic: str
    source: str
    raw_value: float
    normalized_value: float
    observed_at: datetime
    source_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MarketObservationResponse(BaseModel):
    """Schema for individual financial validation observations."""
    id: int
    symbol: str
    provider: str
    latest_price: Optional[float] = None
    latest_volume: Optional[float] = None
    avg_volume: Optional[float] = None
    volume_surge: Optional[float] = None
    observed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class WatchlistRequest(BaseModel):
    """Schema for adding/modifying watchlists."""
    symbol_or_topic: str
    alert_threshold: float = 50.0
    notification_enabled: int = 1


class WatchlistResponse(WatchlistRequest):
    """Schema for reporting watchlist details."""
    id: int

    model_config = ConfigDict(from_attributes=True)


class NewsArticleResponse(BaseModel):
    """Schema for catalyst news articles."""
    id: int
    title: str
    source: str
    url: str
    published_at: datetime
    summary: Optional[str] = None
    topic: Optional[str] = None
    ticker_symbol: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class AdminConfigRequest(BaseModel):
    """Schema for dynamically altering configurations."""
    meme_weight_velocity: float
    meme_weight_link: float
    meme_weight_surge: float
    meme_weight_cap: float
    global_alert_threshold: float


class TickerCreateRequest(BaseModel):
    """Schema for adding/creating a ticker symbol."""
    symbol: str
    company_name: str
    market_cap: Optional[float] = None
    avg_volume: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    exchange: Optional[str] = None
    float_shares: Optional[float] = None
    active: int = 1


class TickerResponse(BaseModel):
    """Schema for reporting ticker details."""
    id: int
    symbol: str
    company_name: str
    market_cap: Optional[float] = None
    avg_volume: Optional[float] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    exchange: Optional[str] = None
    float_shares: Optional[float] = None
    active: int

    model_config = ConfigDict(from_attributes=True)


class BrandCreateRequest(BaseModel):
    """Schema for adding/creating a tracked brand/topic."""
    brand_name: str
    industry: Optional[str] = None


class BrandResponse(BaseModel):
    """Schema for reporting brand details."""
    id: int
    brand_name: str
    industry: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class MacroTrendResponse(BaseModel):
    """Response schema for today's speculative macro trend analyses."""
    id: int
    title: str
    trend_type: str
    description: str
    impact_direction: str
    suggested_sectors: str
    associated_tickers: str
    confidence_score: float
    observed_at: datetime

    model_config = ConfigDict(from_attributes=True)


class EntityRecommendationResponse(BaseModel):
    """Response schema for dynamically discovered stock suggestions."""
    id: int
    symbol: str
    company_name: str
    sector: Optional[str] = None
    industry: Optional[str] = None
    exchange: Optional[str] = None
    status: str
    observed_at: datetime

    model_config = ConfigDict(from_attributes=True)
