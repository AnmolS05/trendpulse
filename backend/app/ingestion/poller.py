"""Background poller to harvest trends, query market data, run analytics, and generate alerts."""
import logging
import time
import threading
import random
import urllib.request
import json
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from ..database import SessionLocal
from ..config import settings
from ..models import (
    Ticker, Brand, Alert, SourceHealth, TrendObservation, 
    MarketObservation, AlertEvidence, DiscoveredTopic, Watchlist, NotificationHistory
)
from .social import (
    fetch_google_trends_v2, fetch_reddit_mentions_v2, check_news_rss,
    calculate_social_velocity, SocialHarvestResult
)
from .market import fetch_ticker_volume_validation, MarketValidationResult
from ..analytics.matching import find_similar
from ..analytics.scorer import calculate_meme_score, calculate_confidence_score, assess_alert_risks

logger = logging.getLogger(__name__)

# Global stop event for background threads
stop_event = threading.Event()

def update_source_health(db: Session, source: str, status: str, error_code: str = None, error_message: str = None) -> None:
    """
    Updates or inserts a source health record in the database.
    Runs inside its own commit block to ensure health stats are saved immediately.
    """
    try:
        health = db.query(SourceHealth).filter(SourceHealth.source == source).first()
        now = datetime.now()
        if not health:
            health = SourceHealth(source=source)
            db.add(health)
        health.status = status
        if status == "healthy":
            health.last_success_at = now
        else:
            health.last_failure_at = now
            health.last_error_code = str(error_code) if error_code is not None else None
            health.last_error_message = str(error_message) if error_message is not None else None
        db.commit()
    except Exception as e:
        logger.error(f"Failed to update source health for {source}: {e}")
        db.rollback()


def discover_google_daily_trends() -> List[str]:
    """
    Parses Google Trends daily trending searches RSS to discover new popular keywords.
    """
    url = "https://trends.google.com/trends/trendingsearches/daily/rss?geo=US"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TrendPulse/1.0"}
    )
    topics = []
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            for item in items:
                title = item.find("title")
                if title is not None and title.text:
                    topics.append(title.text.strip())
    except Exception as e:
        logger.warning(f"Google Trends Daily discovery failed: {e}")
    return topics


def compute_historical_baseline(db: Session, topic: str) -> float:
    """
    Computes historical baseline value from stored TrendObservations for a topic.
    Takes the average raw_value of observations older than the current hour, up to 30 days.
    """
    cutoff = datetime.now() - timedelta(hours=1)
    thirty_days_ago = datetime.now() - timedelta(days=30)
    
    obs = db.query(TrendObservation).filter(
        TrendObservation.topic == topic,
        TrendObservation.observed_at >= thirty_days_ago,
        TrendObservation.observed_at <= cutoff
    ).all()
    
    if not obs:
        return 10.0 # Default baseline
        
    vals = [o.raw_value for o in obs]
    return max(1.0, sum(vals) / len(vals))


def send_discord_notification(alert_id: int, symbol: str, score: float, explanation: str) -> bool:
    """
    Dispatches an alert notification payload to a configured Discord channel webhook.
    """
    webhook_url = settings.DISCORD_WEBHOOK_URL
    if not webhook_url or "discord.com" not in webhook_url:
        return False
        
    payload = {
        "embeds": [{
            "title": f"🚨 TrendPulse Alert: {symbol} 🚨",
            "description": f"**Meme Score:** {score:.1f}/100\n\n**Signal Explanation:**\n{explanation}",
            "color": 15158332,
            "timestamp": datetime.utcnow().isoformat()
        }]
    }
    
    try:
        req = urllib.request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "TrendPulse/1.0"}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            return response.status == 204
    except Exception as e:
        logger.error(f"Failed to send Discord webhook for alert {alert_id} ({symbol}): {e}")
        return False


def process_watchlist_notifications(db: Session, alert: Alert, symbol: str, explanation: str) -> None:
    """
    Checks if a newly created alert ticker is on the watchlists and triggers notifications.
    """
    watchlist_entry = db.query(Watchlist).filter(Watchlist.symbol_or_topic == symbol).first()
    if watchlist_entry and watchlist_entry.notification_enabled:
        if alert.meme_score >= watchlist_entry.alert_threshold:
            # Check if we already notified for this alert in the last 6 hours
            six_hours_ago = datetime.now() - timedelta(hours=6)
            existing = db.query(NotificationHistory).filter(
                NotificationHistory.alert_id == alert.id,
                NotificationHistory.sent_at >= six_hours_ago
            ).first()
            
            if not existing:
                success = send_discord_notification(alert.id, symbol, alert.meme_score, explanation)
                history = NotificationHistory(
                    alert_id=alert.id,
                    channel="discord",
                    status="sent" if success else "failed",
                    error_message=None if success else "Webhook payload dispatch failed"
                )
                db.add(history)
                db.commit()


def run_ingestion(db: Session) -> None:
    """
    Runs one cycle of trend discovery, social harvesting, phonetic matching,
    market anomaly checking, scoring, and alert updates.
    """
    logger.info("Starting ingestion cycle...")
    
    # 1. Trend Discovery
    seeded_brands = db.query(Brand).all()
    brand_map = {b.brand_name: b.industry for b in seeded_brands}
    topics_to_scan = list(brand_map.keys())
    
    # Run daily trend discovery
    discovered = discover_google_daily_trends()
    for topic_name in discovered:
        # Check if topic already exists
        disc_topic = db.query(DiscoveredTopic).filter(DiscoveredTopic.topic == topic_name).first()
        if disc_topic:
            disc_topic.last_seen_at = datetime.now()
            disc_topic.source_count += 1
        else:
            disc_topic = DiscoveredTopic(topic=topic_name, status="active")
            db.add(disc_topic)
        db.commit()
        
    # Add active discovered topics
    active_discovered = db.query(DiscoveredTopic).filter(DiscoveredTopic.status == "active").all()
    for dt in active_discovered:
        if dt.topic not in brand_map:
            topics_to_scan.append(dt.topic)
            brand_map[dt.topic] = "General Trend"  # Default industry description

    if not topics_to_scan:
        logger.warning("No brands or discovered topics to scan.")
        return
        
    # 2. Fetch Tickers
    tickers = db.query(Ticker).filter(Ticker.active == 1).all()
    if not tickers:
        logger.warning("No active tickers loaded. Ingestion halted.")
        return

    # 3. Social Ingestion & Observation Saving
    # Reddit
    reddit_results = fetch_reddit_mentions_v2(
        topics_to_scan, 
        client_id=settings.REDDIT_CLIENT_ID, 
        client_secret=settings.REDDIT_CLIENT_SECRET
    )
    # Google Trends
    trends_results = fetch_google_trends_v2(topics_to_scan)
    
    # Log source health
    reddit_status = "healthy"
    reddit_err = None
    google_status = "healthy"
    google_err = None
    
    for r in reddit_results:
        if r.status == "error":
            reddit_status = "error"
            reddit_err = r.error_message
            break
            
    for t in trends_results:
        if t.status == "error":
            google_status = "error"
            google_err = t.error_message
            break
            
    update_source_health(db, "reddit", reddit_status, error_message=reddit_err)
    update_source_health(db, "google_trends", google_status, error_message=google_err)

    # Convert results into lookup maps
    reddit_map = {r.topic: r for r in reddit_results}
    trends_map = {t.topic: t for t in trends_results}
    
    # Combine observations and persist them
    observations_by_topic = {}
    for topic in topics_to_scan:
        r_res = reddit_map.get(topic)
        t_res = trends_map.get(topic)
        
        # Save observations
        saved_obs = []
        if r_res and r_res.status == "healthy":
            obs = TrendObservation(
                topic=topic,
                source="reddit",
                raw_value=r_res.raw_value,
                normalized_value=r_res.normalized_value,
                source_url=r_res.source_url,
                metadata_json=json.dumps(r_res.metadata)
            )
            db.add(obs)
            db.flush()
            saved_obs.append(obs.id)
            
        if t_res and t_res.status == "healthy":
            obs = TrendObservation(
                topic=topic,
                source="google_trends",
                raw_value=t_res.raw_value,
                normalized_value=t_res.normalized_value,
                source_url=t_res.source_url
            )
            db.add(obs)
            db.flush()
            saved_obs.append(obs.id)
            
        observations_by_topic[topic] = saved_obs
    db.commit()

    # 4. Process Ticker Matching and Scoring
    for topic in topics_to_scan:
        r_res = reddit_map.get(topic)
        t_res = trends_map.get(topic)
        
        raw_interest = t_res.raw_value if t_res else 0.0
        reddit_interest = r_res.raw_value if r_res else 0.0
        combined_interest = raw_interest + reddit_interest
        
        # Determine social velocity with historical baselines
        baseline = compute_historical_baseline(db, topic)
        
        # Strict mode check for social data
        if combined_interest <= 0.0:
            if settings.STRICT_REAL_DATA and not settings.ALLOW_SIMULATED_DATA:
                logger.info(f"Skipping {topic} due to insufficient social evidence in strict mode.")
                continue
            # Simulated fallback for demo mode
            social_velocity = random.uniform(1.5, 6.0)
        else:
            social_velocity = calculate_social_velocity(combined_interest, baseline=baseline)
            
        # Match topic against active tickers
        brand_industry = brand_map.get(topic)
        matches = find_similar(topic, tickers, brand_industry=brand_industry)
        
        for match in matches:
            symbol = match["symbol"]
            similarity = match["similarity"]
            adj_similarity = match["adjusted_similarity"]
            
            # Fetch market validation result
            market_res = fetch_ticker_volume_validation(symbol)
            
            # Save market observation
            market_obs_id = None
            if market_res.status == "success":
                m_obs = MarketObservation(
                    symbol=symbol,
                    provider=market_res.provider,
                    latest_price=market_res.latest_price,
                    latest_volume=market_res.latest_volume,
                    avg_volume=market_res.avg_volume,
                    volume_surge=market_res.volume_surge,
                    metadata_json=json.dumps(market_res.metadata)
                )
                db.add(m_obs)
                db.flush()
                market_obs_id = m_obs.id
                
            # Log market source health
            update_source_health(
                db, 
                f"market_{market_res.provider.lower()}", 
                "healthy" if market_res.status == "success" else "error", 
                error_message=market_res.error_message
            )
            
            # Strict mode checks for market data
            if market_res.status != "success":
                if settings.STRICT_REAL_DATA and not settings.ALLOW_SIMULATED_DATA:
                    logger.info(f"Skipping alert for {symbol} confusion due to market data unavailable in strict mode.")
                    continue
                volume_surge = 1.0 # fallback surge
            else:
                volume_surge = market_res.volume_surge

            # Retrieve average volume and cap
            t_cap = 10.0
            t_vol = 10000.0
            for t in tickers:
                if t.symbol == symbol:
                    t_cap = t.market_cap if t.market_cap is not None else 10.0
                    t_vol = t.avg_volume if t.avg_volume is not None else 10000.0
                    break
                    
            # Calculate Meme Score
            score = calculate_meme_score(social_velocity, adj_similarity, volume_surge, t_cap)
            
            # Calculate Confidence Score
            sources_status = []
            if r_res:
                sources_status.append({"source": "reddit", "status": r_res.status, "raw_value": r_res.raw_value})
            if t_res:
                sources_status.append({"source": "google_trends", "status": t_res.status, "raw_value": t_res.raw_value})
            
            confidence, drivers, weaknesses = calculate_confidence_score(
                sources_status=sources_status,
                match_similarity=similarity,
                has_market_evidence=(market_res.status == "success"),
                industry_mismatch=match["industry_mismatch"],
                is_ambiguous=match["is_ambiguous"]
            )
            
            # Risk warning flags
            r_flags, r_summary = assess_alert_risks(
                market_cap=t_cap,
                avg_volume=t_vol,
                volume_surge=volume_surge,
                industry_mismatch=match["industry_mismatch"]
            )
            
            # Structure alert details
            explanation = (
                f"Social search interest and mentions for brand '{topic}' "
                f"are highly elevated (velocity {social_velocity:.1f}x vs baseline). "
                f" Phonetically matches listed symbol {symbol} ({match['company_name']}) "
                f"with a similarity match of {adj_similarity*100:.1f}%. "
            )
            if market_res.status == "success" and volume_surge > 1.5:
                explanation += f"Confirmed by a {volume_surge:.2f}x volume surge spike in the market."
            else:
                explanation += "No significant market volume corroboration."
                
            evidence_summary = (
                f"Reddit mentions weight: {reddit_interest:.1f} | Google Trends: {raw_interest:.1f} | "
                f"Market Data: avg vol {t_vol:.0f}, latest vol {market_res.latest_volume or 0.0:.0f}"
            )
            
            if score >= 50.0:
                # Store/upsert alert
                existing_alert = db.query(Alert).filter(
                    Alert.ticker_symbol == symbol,
                    Alert.brand_name == topic
                ).first()
                
                if existing_alert:
                    existing_alert.meme_score = score
                    existing_alert.volume_surge_multiplier = volume_surge
                    existing_alert.social_velocity = social_velocity
                    existing_alert.confidence_score = confidence
                    existing_alert.confidence_drivers = ",".join(drivers)
                    existing_alert.confidence_weaknesses = ",".join(weaknesses)
                    existing_alert.explanation = explanation
                    existing_alert.evidence_summary = evidence_summary
                    existing_alert.risk_summary = r_summary
                    existing_alert.risk_flags = ",".join(r_flags)
                    logger.info(f"Updated alert for {symbol} (brand: {topic}) - Score: {score:.1f}")
                    alert_obj = existing_alert
                else:
                    new_alert = Alert(
                        ticker_symbol=symbol,
                        brand_name=topic,
                        meme_score=score,
                        volume_surge_multiplier=volume_surge,
                        social_velocity=social_velocity,
                        confidence_score=confidence,
                        confidence_drivers=",".join(drivers),
                        confidence_weaknesses=",".join(weaknesses),
                        explanation=explanation,
                        evidence_summary=evidence_summary,
                        risk_summary=r_summary,
                        risk_flags=",".join(r_flags)
                    )
                    db.add(new_alert)
                    db.flush()
                    logger.info(f"Created new alert for {symbol} (brand: {topic}) - Score: {score:.1f}")
                    alert_obj = new_alert
                    
                # Link alert to evidence observations
                trend_obs_ids = observations_by_topic.get(topic, [])
                for to_id in trend_obs_ids:
                    # Check if evidence link already exists
                    ae_exists = db.query(AlertEvidence).filter(
                        AlertEvidence.alert_id == alert_obj.id,
                        AlertEvidence.trend_observation_id == to_id
                    ).first()
                    if not ae_exists:
                        ae = AlertEvidence(alert_id=alert_obj.id, trend_observation_id=to_id)
                        db.add(ae)
                        
                if market_obs_id:
                    ae_exists = db.query(AlertEvidence).filter(
                        AlertEvidence.alert_id == alert_obj.id,
                        AlertEvidence.market_observation_id == market_obs_id
                    ).first()
                    if not ae_exists:
                        ae = AlertEvidence(alert_id=alert_obj.id, market_observation_id=market_obs_id)
                        db.add(ae)
                
                db.commit()
                
                # Process Discord Notifications
                process_watchlist_notifications(db, alert_obj, symbol, explanation)
                
    db.commit()
    logger.info("Ingestion cycle completed successfully.")


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
