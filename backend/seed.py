"""Database seeding script with zero hardcoded brands or tickers."""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import Ticker, Brand, Alert, SourceHealth

logging.basicConfig(level=logging.INFO)

def seed_data():
    """Initializes the database, runs migrations, and purges all old historical alerts."""
    logging.info("Running database migrations...")
    from app.database import run_schema_migrations
    run_schema_migrations(engine)
    
    db = SessionLocal()
    
    try:
        # Purge old pre-seeded mock tickers to ensure strict autonomous live operation
        mock_symbols = ["PARLE.NS", "SIGL", "BOMBAY.NS", "ZOOM", "AAPL", "MSFT", "TSLA", "RELIANCE.NS"]
        deleted_tickers = db.query(Ticker).filter(Ticker.symbol.in_(mock_symbols)).delete(synchronize_session=False)
        if deleted_tickers:
            logging.info(f"Purged {deleted_tickers} old pre-seeded mock tickers.")
            
        # Purge old pre-seeded mock brands
        mock_brands = ["Parle Products", "Signal Messenger", "Melody Chocolate"]
        deleted_brands = db.query(Brand).filter(Brand.brand_name.in_(mock_brands)).delete(synchronize_session=False)
        if deleted_brands:
            logging.info(f"Purged {deleted_brands} old pre-seeded mock brands.")
            
        # Delete ALL old alerts to start with a completely clean, real-time dashboard
        deleted_alerts = db.query(Alert).delete(synchronize_session=False)
        if deleted_alerts:
            logging.info(f"Purged {deleted_alerts} old historical alerts.")
            
        # Purge any old source health records to prevent stale status banners on start
        deleted_health = db.query(SourceHealth).delete(synchronize_session=False)
        if deleted_health:
            logging.info(f"Purged {deleted_health} stale source health tracking records.")
            
        db.commit()
        logging.info("Database initialized successfully with zero static mock companies. Ready for strict autonomous discovery.")
    except Exception as e:
        db.rollback()
        logging.error(f"Error during database initialization: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
