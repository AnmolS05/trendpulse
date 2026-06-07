"""Background poller to ingest social media trends and market data."""
import logging
import time
import threading
import random
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..models import Ticker, Brand, Alert
from .social import fetch_google_trends, calculate_social_velocity, fetch_reddit_mentions
from .market import fetch_ticker_volume_anomaly
from ..analytics.matching import find_similar
from ..analytics.scorer import calculate_meme_score

logger = logging.getLogger(__name__)

# Global stop event for background threads
stop_event = threading.Event()

def _fetch_seeded_entities(db: Session) -> tuple[list[str], list[dict]]:
    """
    Fetches seeded brand names and tickers from the database.
    Closes the session to release the database connection early.
    """
    try:
        brands = db.query(Brand).all()
        tickers = db.query(Ticker).all()
        
        if not brands or not tickers:
            logger.warning("No brands or tickers seeded in the database. Ingestion skipped.")
            return [], []
            
        brand_names = [b.brand_name for b in brands]
        ticker_list = [
            {
                "symbol": t.symbol,
                "company_name": t.company_name,
                "market_cap": t.market_cap,
                "phonetic_primary": t.phonetic_primary
            }
            for t in tickers
        ]
        return brand_names, ticker_list
    except Exception as e:
        logger.error(f"Error querying database for ingestion setup: {e}")
        return [], []
    finally:
        db.close()

def _fetch_external_trends_data(brand_names: list[str]) -> tuple[dict, dict]:
    """
    Fetches external trend data from Google Trends and Reddit mentions.
    """
    trends_data = {}
    reddit_data = {}
    
    try:
        # Fetch Google Trends in batches of 5 to avoid overloading pytrends
        for i in range(0, len(brand_names), 5):
            batch = brand_names[i:i+5]
            batch_trends = fetch_google_trends(batch)
            trends_data.update(batch_trends)
    except Exception as e:
        logger.error(f"Failed to fetch Google Trends: {e}")
        
    try:
        # Fetch Reddit mentions
        reddit_data = fetch_reddit_mentions(brand_names)
    except Exception as e:
        logger.error(f"Failed to fetch Reddit mentions: {e}")
        
    return trends_data, reddit_data

def _calculate_meme_alerts(
    brand_names: list[str],
    ticker_list: list[dict],
    trends_data: dict,
    reddit_data: dict
) -> list[dict]:
    """
    Calculates meme score metrics and generates a list of alert candidate dictionaries.
    """
    alerts_to_upsert = []
    from types import SimpleNamespace
    
    for brand_name in brand_names:
        raw_interest = trends_data.get(brand_name, 0.0)
        reddit_interest = reddit_data.get(brand_name, 0.0)
        combined_interest = raw_interest + reddit_interest
        
        if combined_interest <= 0.0:
            social_velocity = random.uniform(1.5, 6.0)
        else:
            social_velocity = calculate_social_velocity(combined_interest, baseline=15.0)
            
        mock_tickers = [SimpleNamespace(**t) for t in ticker_list]
        matches = find_similar(brand_name, mock_tickers)
        
        for match in matches:
            symbol = match["symbol"]
            similarity = match["similarity"]
            
            # Fetch market volume surge anomaly
            volume_surge = fetch_ticker_volume_anomaly(symbol)
            
            # Retrieve market cap
            t_cap = 10.0
            for t in ticker_list:
                if t["symbol"] == symbol:
                    t_cap = t["market_cap"] if t["market_cap"] is not None else 10.0
                    break
                    
            # Calculate Meme Score
            score = calculate_meme_score(social_velocity, similarity, volume_surge, t_cap)
            
            if score >= 50.0:
                alerts_to_upsert.append({
                    "ticker_symbol": symbol,
                    "brand_name": brand_name,
                    "meme_score": score,
                    "volume_surge_multiplier": volume_surge,
                    "social_velocity": social_velocity
                })
    return alerts_to_upsert

def _persist_alerts_batch(alerts_to_upsert: list[dict]) -> None:
    """
    Persists the calculated alerts batch to the database within an isolated transaction block.
    """
    if not alerts_to_upsert:
        logger.info("No alerts to persist.")
        return

    write_db = SessionLocal()
    try:
        with write_db.begin():
            processed_pairs = set()
            for item in alerts_to_upsert:
                symbol = item["ticker_symbol"]
                brand_name = item["brand_name"]
                
                pair_key = (symbol, brand_name)
                if pair_key in processed_pairs:
                    continue
                processed_pairs.add(pair_key)
                
                existing_alert = write_db.query(Alert).filter(
                    Alert.ticker_symbol == symbol,
                    Alert.brand_name == brand_name
                ).first()
                
                if existing_alert:
                    existing_alert.meme_score = item["meme_score"]
                    existing_alert.volume_surge_multiplier = item["volume_surge_multiplier"]
                    existing_alert.social_velocity = item["social_velocity"]
                    logger.info(f"Updated alert for {symbol} (confused with {brand_name}): Score {item['meme_score']:.1f}")
                else:
                    alert = Alert(
                        ticker_symbol=symbol,
                        brand_name=brand_name,
                        meme_score=item["meme_score"],
                        volume_surge_multiplier=item["volume_surge_multiplier"],
                        social_velocity=item["social_velocity"]
                    )
                    write_db.add(alert)
                    logger.info(f"Created new alert for {symbol} (confused with {brand_name}): Score {item['meme_score']:.1f}")
        logger.info("Ingestion cycle completed successfully.")
    except Exception as e:
        logger.error(f"Error during db ingestion save: {e}")
    finally:
        write_db.close()

def run_ingestion(db: Session) -> None:
    """
    Runs one cycle of social media trend harvesting, phonetic matching,
    market anomaly detection, and alert scoring.
    Performs network requests and matching calculations outside database transaction.
    """
    logger.info("Starting ingestion cycle...")
    brand_names, ticker_list = _fetch_seeded_entities(db)
    if not brand_names or not ticker_list:
        return
        
    trends_data, reddit_data = _fetch_external_trends_data(brand_names)
    alerts_to_upsert = _calculate_meme_alerts(
        brand_names, ticker_list, trends_data, reddit_data
    )
    _persist_alerts_batch(alerts_to_upsert)

def poller_loop(interval_seconds: int = 600) -> None:
    """
    Background loop that runs periodically to fetch trends and populate DB.
    Exits gracefully when stop_event is set.
    """
    logger.info("Starting background poller loop thread...")
    while not stop_event.is_set():
        try:
            db = SessionLocal()
            try:
                run_ingestion(db)
            finally:
                db.close()
        except Exception as e:
            logger.error(f"Error in poller loop cycle: {e}")
        
        # Check stop_event periodically during sleep
        for _ in range(interval_seconds):
            if stop_event.is_set():
                break
            time.sleep(1)

def start_poller(interval_seconds: int = 600) -> threading.Thread:
    """
    Starts the background poller thread.
    """
    thread = threading.Thread(target=poller_loop, args=(interval_seconds,), daemon=True)
    thread.start()
    return thread
