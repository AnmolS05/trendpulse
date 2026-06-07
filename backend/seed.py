"""Database seeding script."""
import logging
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, Base, SessionLocal
from app.models import Ticker, Brand
from app.analytics.matching import generate_phonetic_key

logging.basicConfig(level=logging.INFO)

def seed_data():
    """Drops all tables, recreates them, and seeds initial data."""
    logging.info("Creating tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    
    try:
        # Seed Tickers
        tickers = [
            Ticker(symbol="PARLE.NS", company_name="Parle Industries", market_cap=5.0, avg_volume=10000),
            Ticker(symbol="SIGL", company_name="Signal Advance", market_cap=20.0, avg_volume=50000),
            Ticker(symbol="BOMBAY.NS", company_name="Bombay Oxygen Investments", market_cap=15.0, avg_volume=2000),
            Ticker(symbol="ZOOM", company_name="Zoom Technologies", market_cap=2.0, avg_volume=1000)
        ]
        
        for t in tickers:
            t.phonetic_primary = generate_phonetic_key(t.company_name)
            db.add(t)
            
        # Seed Brands
        brands = [
            Brand(brand_name="Parle Products", industry="Confectionery"),
            Brand(brand_name="Signal Messenger", industry="Software"),
            Brand(brand_name="Melody Chocolate", industry="Confectionery")
        ]
        
        for b in brands:
            db.add(b)
            
        db.commit()
        logging.info("Database seeded successfully.")
    except Exception as e:
        db.rollback()
        logging.error(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_data()
