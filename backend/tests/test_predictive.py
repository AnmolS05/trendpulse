import pytest
from datetime import datetime, timedelta
from app.models import TrendObservation, Alert, Ticker, Watchlist
from app.analytics.scorer import calculate_social_acceleration, calculate_surge_probability
from app.ingestion.poller import run_ingestion
from app.config import settings

def test_acceleration_correctness(db_session):
    # Setup historical observations 1 to 3 hours ago
    two_hours_ago = datetime.now() - timedelta(hours=2)
    
    obs1 = TrendObservation(topic="Tesla", source="reddit", raw_value=10.0, normalized_value=10.0, observed_at=two_hours_ago)
    obs2 = TrendObservation(topic="Tesla", source="google_trends", raw_value=20.0, normalized_value=20.0, observed_at=two_hours_ago)
    db_session.add(obs1)
    db_session.add(obs2)
    db_session.commit()
    
    # Average past value = 15.0
    # Current value = 30.0
    # Accel = (30.0 - 15.0) / 15.0 = 1.0
    accel = calculate_social_acceleration(db_session, "Tesla", 30.0)
    assert accel == 1.0

def test_surge_probability_logic():
    prob = calculate_surge_probability(acceleration=1.0, similarity=1.0, market_cap=10.0, float_shares=50.0)
    # base = (1.0*20) + (1.0*30) = 50.0
    # mc_penalty = log10(10)*5.0 = 5.0
    # float_penalty = 0.0
    # expected = 45.0
    assert abs(prob - 45.0) < 0.1

import uuid
def test_divergence_logic_is_predictive(db_session, monkeypatch):
    unique_id = str(uuid.uuid4())[:8]
    topic_name = f"Tesla_{unique_id}"
    ticker_sym = f"TSLA_{unique_id}"
    # Ensure tickers are present
    ticker = Ticker(symbol=ticker_sym, company_name=topic_name, active=1, market_cap=10.0, phonetic_primary="TSLA")
    db_session.add(ticker)
    db_session.commit()
    
    # Mock settings
    monkeypatch.setattr(settings, "GLOBAL_ALERT_THRESHOLD", 0.0)
    
    # Mock google trends and reddit to return high values
    from app.ingestion import poller
    from app.ingestion.social import SocialHarvestResult
    from app.ingestion.market import MarketValidationResult
    
    def mock_fetch_reddit(*args, **kwargs):
        return [SocialHarvestResult(topic=topic_name, source="reddit", status="healthy", raw_value=5.0, normalized_value=5.0)]
    
    def mock_fetch_trends(*args, **kwargs):
        return [SocialHarvestResult(topic=topic_name, source="google_trends", status="healthy", raw_value=5.0, normalized_value=5.0)]
        
    def mock_fetch_market(symbol, *args, **kwargs):
        return MarketValidationResult(symbol=symbol, provider="mock", latest_price=10.0, latest_volume=1000, avg_volume=1000, volume_surge=1.1, status="success")
        
    def mock_baseline(*args, **kwargs):
        return 1.0 # high baseline velocity = (5+5)/1 = 10.0
        
    def mock_discover_tickers(*args, **kwargs):
        return [{"symbol": ticker_sym, "company_name": topic_name, "sector": "Auto", "industry": "Auto", "exchange": "NASDAQ"}]
        
    def mock_discover_trends(*args, **kwargs):
        return [topic_name]
        
    monkeypatch.setattr(poller, "fetch_reddit_mentions_v2", mock_fetch_reddit)
    monkeypatch.setattr(poller, "fetch_google_trends_v2", mock_fetch_trends)
    monkeypatch.setattr(poller, "fetch_ticker_volume_validation", mock_fetch_market)
    monkeypatch.setattr(poller, "compute_historical_baseline", mock_baseline)
    monkeypatch.setattr(poller, "discover_google_daily_trends", mock_discover_trends)
    from app.ingestion import market
    monkeypatch.setattr(market, "discover_listed_tickers_for_topic", mock_discover_tickers)
    
    run_ingestion(db_session)
    
    alert = db_session.query(Alert).filter_by(ticker_symbol=ticker_sym).first()
    assert alert is not None
    assert alert.is_predictive == 1
    assert alert.volume_surge_multiplier == 1.1
    assert alert.social_velocity > 3.0

def test_strict_mode_blocks_fallback(db_session, monkeypatch):
    import uuid
    uid = str(uuid.uuid4())[:8]
    topic_name = f"Tesla_{uid}"
    ticker = Ticker(symbol=f"TSLA_{uid}", company_name=f"Tesla Inc_{uid}", active=1)
    db_session.add(ticker)
    db_session.commit()
    
    # The test naturally runs in strict mode now.
    from app.ingestion import poller
    from app.ingestion.social import SocialHarvestResult
    
    # Return empty/zero values to trigger fallback
    def mock_fetch_reddit(*args, **kwargs):
        return [SocialHarvestResult(topic="Tesla", source="reddit", status="healthy", raw_value=0.0, normalized_value=0.0)]
    
    def mock_fetch_trends(*args, **kwargs):
        return [SocialHarvestResult(topic="Tesla", source="google_trends", status="healthy", raw_value=0.0, normalized_value=0.0)]
        
    def mock_discover_tickers(*args, **kwargs):
        return [{"symbol": "TSLA", "company_name": "Tesla Inc", "sector": "Auto", "industry": "Auto", "exchange": "NASDAQ"}]
        
    def mock_discover_trends(*args, **kwargs):
        return [topic_name]
        
    monkeypatch.setattr(poller, "fetch_reddit_mentions_v2", mock_fetch_reddit)
    monkeypatch.setattr(poller, "fetch_google_trends_v2", mock_fetch_trends)
    monkeypatch.setattr(poller, "discover_google_daily_trends", mock_discover_trends)
    from app.ingestion import market
    monkeypatch.setattr(market, "discover_listed_tickers_for_topic", mock_discover_tickers)
    
    # This should block alert creation entirely
    run_ingestion(db_session)
    
    alert = db_session.query(Alert).filter_by(ticker_symbol="TSLA").first()
    assert alert is None
