import os
os.environ.setdefault("PYTEST_DISABLE_PLUGIN_AUTOLOAD", "1")
import pytest
import os
from sqlalchemy.orm import Session
# Add backend/app to sys.path for test imports
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'app')))
from app.database import engine, Base, SessionLocal, run_schema_migrations
from app.models import Ticker, Brand, Alert, TrendObservation, MarketObservation, SourceHealth, MacroTrend

# Run migrations once for the test session
run_schema_migrations(engine)

@pytest.fixture(scope="function")
def db_session():
    """Provides a clean database session for testing."""
    db = SessionLocal()
    try:
        # Seed minimum entities
        db.query(Alert).delete()
        db.query(TrendObservation).delete()
        db.query(MarketObservation).delete()
        db.query(SourceHealth).delete()
        db.query(Brand).delete()
        db.query(Ticker).delete()
        db.query(MacroTrend).delete()
        db.commit()
        yield db
    finally:
        db.close()
