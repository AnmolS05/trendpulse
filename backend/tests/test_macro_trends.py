"""Tests for the speculative macro trends engine and API endpoint."""
import pytest
import warnings
warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*The 'app' shortcut is now deprecated.*")
from sqlalchemy.orm import Session
from fastapi.testclient import TestClient
from app.main import app
from app.models import MacroTrend
from app.config import settings

def test_generate_macro_trends_fallback(db_session: Session, monkeypatch):
    """
    Checks that when discover_google_daily_trends returns no matching keywords,
    the fallback seasonal and geopolitical trends are successfully seeded into the database.
    """
    import app.ingestion.poller
    
    # Mock daily trending searches to return nothing
    def mock_discover_trends():
        return []
        
    def mock_fetch_news():
        return []
        
    monkeypatch.setattr(app.ingestion.poller, "discover_google_daily_trends", mock_discover_trends)
    monkeypatch.setattr(app.ingestion.poller, "fetch_live_business_headlines", mock_fetch_news)
    
    # Clear and run macro trends generation
    from app.ingestion.poller import generate_daily_macro_trends
    generate_daily_macro_trends(db_session)
    
    # Verify that the two default trends were seeded
    trends = db_session.query(MacroTrend).all()
    assert len(trends) == 2
    titles = [t.title for t in trends]
    assert "Southwest Monsoon & Rural FMCG Demand" in titles
    assert "Global Geopolitical Energy Fragility" in titles
    
    # Assert fields are correctly populated
    monsoon_trend = next(t for t in trends if "Monsoon" in t.title)
    assert monsoon_trend.trend_type == "Seasonal Shift"
    assert monsoon_trend.impact_direction == "Bullish"
    assert monsoon_trend.suggested_sectors == "Agri-Inputs, FMCG, Consumer Non-Durables"
    assert monsoon_trend.associated_tickers == "PARLE.NS"
    assert monsoon_trend.confidence_score >= 68.0
    assert monsoon_trend.confidence_score <= 92.0


def test_generate_macro_trends_keyword_trigger(db_session: Session, monkeypatch):
    """
    Checks that when discover_google_daily_trends returns matching keywords,
    the spec matrix rules are triggered and stored.
    """
    import app.ingestion.poller
    
    # Mock daily trending searches to return keywords for 'monsoon' and 'nvidia'
    def mock_discover_trends():
        return ["monsoon in agricultural regions", "nvidia launches new chips"]
        
    def mock_fetch_news():
        return []
        
    monkeypatch.setattr(app.ingestion.poller, "discover_google_daily_trends", mock_discover_trends)
    monkeypatch.setattr(app.ingestion.poller, "fetch_live_business_headlines", mock_fetch_news)
    
    from app.ingestion.poller import generate_daily_macro_trends
    generate_daily_macro_trends(db_session)
    
    # Verify keyword-triggered trends are stored
    trends = db_session.query(MacroTrend).all()
    assert len(trends) == 2
    types = [t.trend_type for t in trends]
    assert "Seasonal Shift" in types
    assert "Technology Boom" in types
    
    # Test duplication avoidance within 12 hours
    generate_daily_macro_trends(db_session)
    trends_after_duplication = db_session.query(MacroTrend).all()
    assert len(trends_after_duplication) == 2


def test_get_macro_trends_api(db_session: Session):
    """
    Checks that the GET /api/macro-trends endpoint returns the cached trends correctly.
    """
    # Seed a macro trend in the database
    new_trend = MacroTrend(
        title="Custom Geopolitical Risk Alert",
        trend_type="Geopolitical Shock",
        description="Arbitrary test description for geopolitical risk.",
        impact_direction="Bearish",
        suggested_sectors="Energy, Precious Metals",
        associated_tickers="TSLA, BOMBAY.NS",
        confidence_score=85.0
    )
    db_session.add(new_trend)
    db_session.commit()
    
    client = TestClient(app)
    res = client.get("/api/macro-trends")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 1
    assert data[0]["title"] == "Custom Geopolitical Risk Alert"
    assert data[0]["trend_type"] == "Geopolitical Shock"
    assert data[0]["impact_direction"] == "Bearish"
    assert data[0]["suggested_sectors"] == "Energy, Precious Metals"
    assert data[0]["associated_tickers"] == "TSLA, BOMBAY.NS"
    assert data[0]["confidence_score"] == 85.0
    assert "observed_at" in data[0]
