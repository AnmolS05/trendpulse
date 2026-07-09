"""Integration and unit tests for poller reliability and ingestion logic."""
import pytest
import uuid
import warnings

# Suppress HTTPX deprecation warning triggered by Starlette's TestClient
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models import Ticker, Brand, Alert, TrendObservation, MarketObservation, SourceHealth, Watchlist
from app.ingestion.poller import run_ingestion
from app.config import settings

def test_strict_mode_bypass(db_session: Session, monkeypatch):
    """
    Verifies that when STRICT_REAL_DATA is enabled and no external data exists,
    simulated mock alerts are not generated.
    """
    uid = str(uuid.uuid4())[:8]
    ticker = Ticker(
        symbol=f"PARLE{uid}.NS", 
        company_name=f"Parle Industries {uid}", 
        market_cap=5.0, 
        avg_volume=10000,
        industry="Confectionery",
        phonetic_primary=f"PRL{uid}"
    )
    db_session.add(ticker)
    db_session.commit()
    
    import app.ingestion.poller
    import app.ingestion.market
    
    def mock_discover_trends():
        return []
        
    def mock_discover_tickers(*args, **kwargs):
        return []
        
    monkeypatch.setattr(app.ingestion.poller, "discover_google_daily_trends", mock_discover_trends)
    monkeypatch.setattr(app.ingestion.market, "discover_listed_tickers_for_topic", mock_discover_tickers)
    
    # Run ingestion. Since we have no mock network responses seeded, it should skip due to lack of real data.
    run_ingestion(db_session)
    
    # Verify no alerts were created
    alerts = db_session.query(Alert).all()
    assert len(alerts) == 0


def test_source_health_update(db_session: Session, monkeypatch):
    """
    Verifies that run_ingestion logs source health for Reddit and Google Trends.
    """
    uid = str(uuid.uuid4())[:8]
    topic_name = f"Melody Chocolate {uid}"
    ticker = Ticker(
        symbol=f"PARLE{uid}.NS", 
        company_name=f"Parle Industries {uid}", 
        market_cap=5.0, 
        avg_volume=10000,
        industry="Confectionery",
        phonetic_primary=f"PRL{uid}"
    )
    db_session.add(ticker)
    db_session.commit()
    
    import app.ingestion.poller
    import app.ingestion.market
    
    def mock_discover_trends():
        return [topic_name]
        
    def mock_discover_tickers(*args, **kwargs):
        return []
        
    monkeypatch.setattr(app.ingestion.poller, "discover_google_daily_trends", mock_discover_trends)
    monkeypatch.setattr(app.ingestion.market, "discover_listed_tickers_for_topic", mock_discover_tickers)
    
    run_ingestion(db_session)
    
    # Verify source health rows exist
    health_records = db_session.query(SourceHealth).all()
    assert len(health_records) >= 2
    sources = [h.source for h in health_records]
    assert "reddit" in sources
    assert "google_trends" in sources


def test_api_routes():
    """
    Verifies that the newly created REST endpoints respond with correct status codes and payloads.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.models import Alert
    
    client = TestClient(app)
    headers = {"X-API-KEY": settings.API_KEY}
    
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    
    # 2. Source health endpoint
    res = client.get("/api/health/sources")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    

    
    # 4. Admin config endpoints
    res = client.get("/api/admin/config", headers=headers)
    assert res.status_code == 200
    assert "strict_real_data" in res.json()
    
    res = client.post("/api/admin/config", json={
        "meme_weight_velocity": 20.0,
        "meme_weight_link": 30.0,
        "meme_weight_surge": 30.0,
        "meme_weight_cap": 10.0,
        "global_alert_threshold": 50.0
    }, headers=headers)
    assert res.status_code == 200
    assert res.json() == {"status": "success", "message": "Configuration updated successfully"}
    
    # Restore defaults
    client.post("/api/admin/config", json={
        "meme_weight_velocity": 20.0,
        "meme_weight_link": 30.0,
        "meme_weight_surge": 30.0,
        "meme_weight_cap": 10.0,
        "global_alert_threshold": 50.0
    }, headers=headers)
    
    # 5. Backtest endpoint
    res = client.post("/api/backtest", headers=headers)
    assert res.status_code == 200
    assert "precision" in res.json()


def test_crawler_failover(db_session, monkeypatch):
    """
    Verifies that if social scraping fails (e.g. rate limit / timeout / exception),
    health is logged as error and poller continues.
    """
    import app.ingestion.poller
    from app.ingestion.social import SocialHarvestResult
    
    uid = str(uuid.uuid4())[:8]
    topic_name = f"Parle Products {uid}"
    # Seed a ticker so poller has items to scan
    ticker = Ticker(
        symbol=f"PARLE{uid}.NS", 
        company_name=f"Parle Industries {uid}", 
        market_cap=5.0, 
        avg_volume=10000,
        industry="Confectionery",
        phonetic_primary=f"PRL{uid}",
        active=1
    )
    db_session.add(ticker)
    db_session.commit()
    
    # Mock google trends to return an error status
    def mock_fetch_google_trends(topics):
        return [
            SocialHarvestResult(
                topic=t,
                source="google_trends",
                raw_value=0.0,
                normalized_value=0.0,
                status="error",
                error_message="HTTP Error 429: Too Many Requests"
            ) for t in topics
        ]
        
    def mock_discover_trends():
        return [topic_name]

    def mock_discover_tickers(*args, **kwargs):
        return [{"symbol": f"PARLE{uid}.NS", "company_name": f"Parle Industries {uid}", "sector": "Auto", "industry": "Auto", "exchange": "NSE"}]
        
    monkeypatch.setattr(app.ingestion.poller, "fetch_google_trends_v2", mock_fetch_google_trends)
    monkeypatch.setattr(app.ingestion.poller, "discover_google_daily_trends", mock_discover_trends)
    from app.ingestion import market
    monkeypatch.setattr(market, "discover_listed_tickers_for_topic", mock_discover_tickers)
    
    # Run ingestion
    run_ingestion(db_session)
    
    # Verify health record is error
    health = db_session.query(SourceHealth).filter(SourceHealth.source == "google_trends").first()
    assert health is not None
    assert health.status == "error"
    assert "Too Many Requests" in health.last_error_message


def test_api_key_rejection():
    """
    Verifies that accessing secured endpoints with invalid or missing API keys returns 403 Forbidden.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    
    # Missing key
    res = client.post("/api/admin/config")
    assert res.status_code == 403
    
    # Invalid key
    res = client.post("/api/admin/config", headers={"X-API-KEY": "wrong_key"})
    assert res.status_code == 403


def test_evidence_links_and_shapes(db_session):
    """
    Verifies that generated alerts have correct AlertEvidence links and that 
    the API returns the correct JSON payload shape for evidence and timeline.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    from app.models import TrendObservation, MarketObservation, Alert, AlertEvidence
    from datetime import datetime, timezone
    
    client = TestClient(app)
    
    # Seed alert, trend observation, and market observation
    trend = TrendObservation(
        topic="Melody Chocolate",
        source="reddit",
        raw_value=5.0,
        normalized_value=2.0,
        observed_at=datetime.now(timezone.utc)
    )
    market = MarketObservation(
        symbol="PARLE.NS",
        provider="alpaca",
        latest_price=10.5,
        latest_volume=50000.0,
        avg_volume=12000.0,
        volume_surge=4.16,
        observed_at=datetime.now(timezone.utc)
    )
    db_session.add(trend)
    db_session.add(market)
    db_session.flush()
    
    alert = Alert(
        ticker_symbol="PARLE.NS",
        brand_name="Melody Chocolate",
        meme_score=75.0,
        volume_surge_multiplier=4.16,
        social_velocity=2.5,
        confidence_score=80.0,
        timestamp=datetime.now(timezone.utc)
    )
    db_session.add(alert)
    db_session.flush()
    
    # Link them using AlertEvidence
    ae1 = AlertEvidence(alert_id=alert.id, trend_observation_id=trend.id)
    ae2 = AlertEvidence(alert_id=alert.id, market_observation_id=market.id)
    db_session.add(ae1)
    db_session.add(ae2)
    db_session.commit()
    
    # Query evidence endpoint
    res = client.get(f"/api/alerts/{alert.id}/evidence")
    assert res.status_code == 200
    data = res.json()
    
    # Verify shape of response
    assert "trend_observations" in data
    assert "market_observations" in data
    assert "news_articles" in data
    
    assert len(data["trend_observations"]) == 1
    assert data["trend_observations"][0]["topic"] == "Melody Chocolate"
    assert data["trend_observations"][0]["raw_value"] == 5.0
    
    assert len(data["market_observations"]) == 1
    assert data["market_observations"][0]["symbol"] == "PARLE.NS"
    assert data["market_observations"][0]["latest_price"] == 10.5
    
    # Query timeline endpoint
    res_tl = client.get(f"/api/alerts/{alert.id}/timeline")
    assert res_tl.status_code == 200
    tl_data = res_tl.json()
    assert isinstance(tl_data, list)
    assert len(tl_data) >= 3  # 1 trend, 1 market, 1 alert release
    
    # Validate timeline shape
    for event in tl_data:
        assert "timestamp" in event
        assert "event" in event
        assert "details" in event


def test_admin_keys_masking():
    """
    Verifies that the /api/admin/keys endpoint lists the status of API keys 
    without exposing raw variables.
    """
    from fastapi.testclient import TestClient
    from app.main import app
    
    client = TestClient(app)
    headers = {"X-API-KEY": settings.API_KEY}
    
    res = client.get("/api/admin/keys", headers=headers)
    assert res.status_code == 200
    data = res.json()
    
    assert "alpaca_api_key" in data
    assert "reddit_client_id" in data
    assert "discord_webhook_url" in data
    # Enforce that it only reports status and doesn't leak raw credentials
    for val in data.values():
        assert val in ["configured", "missing"]





def test_dynamic_weights_scoring():
    """
    Verifies that changing meme weights configurations dynamically alters 
    the calculated score from the scorer engine.
    """
    from app.analytics.scorer import calculate_meme_score
    from app.config import settings
    
    # Save original settings
    orig_vel = settings.MEME_WEIGHT_VELOCITY
    orig_link = settings.MEME_WEIGHT_LINK
    
    try:
        # 1. Default config
        settings.MEME_WEIGHT_VELOCITY = 20.0
        settings.MEME_WEIGHT_LINK = 30.0
        score_1 = calculate_meme_score(social_velocity=5.0, link_strength=0.8, volume_surge=1.0, market_cap=10.0)
        
        # 2. Alter velocity weight to high value
        settings.MEME_WEIGHT_VELOCITY = 100.0
        score_2 = calculate_meme_score(social_velocity=5.0, link_strength=0.8, volume_surge=1.0, market_cap=10.0)
        
        assert score_2 > score_1
        
    finally:
        # Restore
        settings.MEME_WEIGHT_VELOCITY = orig_vel
        settings.MEME_WEIGHT_LINK = orig_link

