"""Integration and unit tests for poller reliability and ingestion logic."""
import pytest
from sqlalchemy.orm import Session
from app.database import engine, Base, SessionLocal
from app.models import Ticker, Brand, Alert, TrendObservation, MarketObservation, SourceHealth
from app.ingestion.poller import run_ingestion
from app.config import settings

@pytest.fixture(scope="function")
def db_session():
    """Provides a clean in-memory or temporary database session for testing."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        # Seed minimum entities
        db.query(Alert).delete()
        db.query(TrendObservation).delete()
        db.query(MarketObservation).delete()
        db.query(SourceHealth).delete()
        db.query(Brand).delete()
        db.query(Ticker).delete()
        db.commit()
        yield db
    finally:
        db.close()


def test_strict_mode_bypass(db_session: Session):
    """
    Verifies that when STRICT_REAL_DATA is enabled and no external data exists,
    simulated mock alerts are not generated.
    """
    # Seed a brand and a ticker
    brand = Brand(brand_name="Parle Products", industry="Confectionery")
    ticker = Ticker(
        symbol="PARLE.NS", 
        company_name="Parle Industries", 
        market_cap=5.0, 
        avg_volume=10000,
        industry="Confectionery",
        phonetic_primary="PRL"
    )
    db_session.add(brand)
    db_session.add(ticker)
    db_session.commit()
    
    # Configure strict mode
    original_strict = settings.STRICT_REAL_DATA
    original_simulated = settings.ALLOW_SIMULATED_DATA
    try:
        settings.STRICT_REAL_DATA = True
        settings.ALLOW_SIMULATED_DATA = False
        
        # Run ingestion. Since we have no mock network responses seeded, it should skip due to lack of real data.
        run_ingestion(db_session)
        
        # Verify no alerts were created
        alerts = db_session.query(Alert).all()
        assert len(alerts) == 0
    finally:
        settings.STRICT_REAL_DATA = original_strict
        settings.ALLOW_SIMULATED_DATA = original_simulated


def test_source_health_update(db_session: Session):
    """
    Verifies that run_ingestion logs source health for Reddit and Google Trends.
    """
    brand = Brand(brand_name="Melody Chocolate", industry="Confectionery")
    ticker = Ticker(
        symbol="PARLE.NS", 
        company_name="Parle Industries", 
        market_cap=5.0, 
        avg_volume=10000,
        industry="Confectionery",
        phonetic_primary="PRL"
    )
    db_session.add(brand)
    db_session.add(ticker)
    db_session.commit()
    
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
    
    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}
    
    # 2. Source health endpoint
    res = client.get("/api/health/sources")
    assert res.status_code == 200
    assert isinstance(res.json(), list)
    
    # 3. Watchlist endpoints
    res = client.post("/api/watchlist", json={"symbol_or_topic": "TSLA", "alert_threshold": 65.0})
    assert res.status_code == 200
    assert res.json()["symbol_or_topic"] == "TSLA"
    assert res.json()["alert_threshold"] == 65.0
    
    res = client.get("/api/watchlist")
    assert res.status_code == 200
    assert len(res.json()) >= 1
    
    res = client.delete("/api/watchlist/TSLA")
    assert res.status_code == 200
    
    # 4. Admin config endpoints
    res = client.get("/api/admin/config")
    assert res.status_code == 200
    assert "strict_real_data" in res.json()
    
    res = client.post("/api/admin/config", json={"strict_real_data": False, "allow_simulated_data": True})
    assert res.status_code == 200
    assert res.json() == {"status": "success", "message": "Configuration updated successfully"}
    
    # Restore defaults
    client.post("/api/admin/config", json={"strict_real_data": True, "allow_simulated_data": False})
    
    # 5. Backtest endpoint
    res = client.post("/api/backtest")
    assert res.status_code == 200
    assert "precision" in res.json()

