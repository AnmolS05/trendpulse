"""Database seeding script with expanded ticker and brand universe."""
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
        # Seed Tickers (US and Indian Equities)
        tickers = [
            Ticker(
                symbol="PARLE.NS", 
                company_name="Parle Industries", 
                market_cap=5.0, 
                avg_volume=12000, 
                sector="Consumer Goods",
                industry="Confectionery",
                exchange="NSE",
                float_shares=10.0,
                active=1
            ),
            Ticker(
                symbol="SIGL", 
                company_name="Signal Advance", 
                market_cap=20.0, 
                avg_volume=45000, 
                sector="Healthcare",
                industry="Medical Devices",
                exchange="NASDAQ",
                float_shares=15.0,
                active=1
            ),
            Ticker(
                symbol="BOMBAY.NS", 
                company_name="Bombay Oxygen Investments", 
                market_cap=15.0, 
                avg_volume=2500, 
                sector="Industrials",
                industry="Industrial Gases",
                exchange="BSE",
                float_shares=2.0,
                active=1
            ),
            Ticker(
                symbol="ZOOM", 
                company_name="Zoom Technologies", 
                market_cap=2.0, 
                avg_volume=800, 
                sector="Technology",
                industry="Telecommunications",
                exchange="NASDAQ",
                float_shares=5.0,
                active=1
            ),
            Ticker(
                symbol="AAPL", 
                company_name="Apple Inc", 
                market_cap=3000000.0, 
                avg_volume=52000000, 
                sector="Technology",
                industry="Consumer Electronics",
                exchange="NASDAQ",
                float_shares=15000.0,
                active=1
            ),
            Ticker(
                symbol="MSFT", 
                company_name="Microsoft Corporation", 
                market_cap=3100000.0, 
                avg_volume=22000000, 
                sector="Technology",
                industry="Software",
                exchange="NASDAQ",
                float_shares=7400.0,
                active=1
            ),
            Ticker(
                symbol="TSLA", 
                company_name="Tesla Inc", 
                market_cap=600000.0, 
                avg_volume=85000000, 
                sector="Automotive",
                industry="Electric Vehicles",
                exchange="NASDAQ",
                float_shares=2700.0,
                active=1
            ),
            Ticker(
                symbol="RELIANCE.NS", 
                company_name="Reliance Industries", 
                market_cap=200000.0, 
                avg_volume=6000000, 
                sector="Energy",
                industry="Oil & Gas",
                exchange="NSE",
                float_shares=6700.0,
                active=1
            )
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
