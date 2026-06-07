"""API routes for TrendPulse."""
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from ..database import get_db
from ..models import (
    Alert, Ticker, AlertEvidence, TrendObservation, 
    MarketObservation, SourceHealth, Watchlist
)
from ..schemas import (
    AlertResponse, SourceHealthResponse, WatchlistRequest, 
    WatchlistResponse, AdminConfigRequest
)
from ..config import settings

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)) -> str:
    """
    Dependency to validate incoming static X-API-KEY header token.
    """
    if api_key_header == settings.API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")


@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Fetch active alerts with company name, market capitalization, 
    and enriched analytical confidence metrics.
    """
    results = db.query(Alert, Ticker).outerjoin(
        Ticker, Ticker.symbol == Alert.ticker_symbol
    ).order_by(Alert.meme_score.desc()).limit(50).all()
    
    enriched_alerts = []
    for alert, ticker in results:
        enriched_alerts.append({
            "id": alert.id,
            "ticker_symbol": alert.ticker_symbol,
            "brand_name": alert.brand_name,
            "meme_score": alert.meme_score,
            "volume_surge_multiplier": alert.volume_surge_multiplier,
            "social_velocity": alert.social_velocity,
            "timestamp": alert.timestamp,
            "company_name": ticker.company_name if ticker else "Unknown Equities",
            "market_cap": ticker.market_cap if ticker else None,
            "confidence_score": alert.confidence_score or 0.0,
            "confidence_drivers": alert.confidence_drivers,
            "confidence_weaknesses": alert.confidence_weaknesses,
            "explanation": alert.explanation,
            "evidence_summary": alert.evidence_summary,
            "risk_summary": alert.risk_summary,
            "risk_flags": alert.risk_flags,
            "news_count": alert.news_count or 0
        })
    return enriched_alerts


@router.get("/alerts/{alert_id}/evidence")
def get_alert_evidence(alert_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Fetch supporting social, market, and news catalyst evidence observations linked to an alert.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")

    evidence = db.query(AlertEvidence).filter(AlertEvidence.alert_id == alert_id).all()
        
    trend_obs_ids = [e.trend_observation_id for e in evidence if e.trend_observation_id]
    market_obs_ids = [e.market_observation_id for e in evidence if e.market_observation_id]
    
    trend_obs = db.query(TrendObservation).filter(TrendObservation.id.in_(trend_obs_ids)).all() if trend_obs_ids else []
    market_obs = db.query(MarketObservation).filter(MarketObservation.id.in_(market_obs_ids)).all() if market_obs_ids else []
    
    from ..models import NewsArticle
    news = db.query(NewsArticle).filter(
        (NewsArticle.topic == alert.brand_name) | 
        (NewsArticle.ticker_symbol == alert.ticker_symbol)
    ).all()
    
    return {
        "trend_observations": [
            {
                "id": o.id,
                "topic": o.topic,
                "source": o.source,
                "raw_value": o.raw_value,
                "normalized_value": o.normalized_value,
                "observed_at": o.observed_at,
                "source_url": o.source_url
            }
            for o in trend_obs
        ],
        "market_observations": [
            {
                "id": o.id,
                "symbol": o.symbol,
                "provider": o.provider,
                "latest_price": o.latest_price,
                "latest_volume": o.latest_volume,
                "avg_volume": o.avg_volume,
                "volume_surge": o.volume_surge,
                "observed_at": o.observed_at
            }
            for o in market_obs
        ],
        "news_articles": [
            {
                "id": n.id,
                "title": n.title,
                "source": n.source,
                "url": n.url,
                "published_at": n.published_at,
                "summary": n.summary
            }
            for n in news
        ]
    }



@router.get("/alerts/{alert_id}/timeline")
def get_alert_timeline(alert_id: int, db: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """
    Fetch chronological timeline events illustrating how a signal was detected.
    """
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    evidence = db.query(AlertEvidence).filter(AlertEvidence.alert_id == alert_id).all()
    trend_obs_ids = [e.trend_observation_id for e in evidence if e.trend_observation_id]
    market_obs_ids = [e.market_observation_id for e in evidence if e.market_observation_id]
    
    events = []
    
    if trend_obs_ids:
        trends = db.query(TrendObservation).filter(
            TrendObservation.id.in_(trend_obs_ids)
        ).order_by(TrendObservation.observed_at.asc()).all()
        for t in trends:
            events.append({
                "timestamp": t.observed_at,
                "event": "Social Mentions Logged",
                "details": f"Source: {t.source} | Mentions: {t.raw_value:.1f} | Normalized search power: {t.normalized_value:.1f}"
            })
            
    if market_obs_ids:
        markets = db.query(MarketObservation).filter(
            MarketObservation.id.in_(market_obs_ids)
        ).order_by(MarketObservation.observed_at.asc()).all()
        for m in markets:
            events.append({
                "timestamp": m.observed_at,
                "event": "Market Activity Validation",
                "details": f"Provider: {m.provider} | Price: ${m.latest_price or 0.0:.2f} | Volume Surge: {m.volume_surge or 1.0:.2f}x"
            })
            
    events.append({
        "timestamp": alert.timestamp,
        "event": "Alert Trigger Released",
        "details": f"Meme Score: {alert.meme_score:.1f} | Confidence Score: {alert.confidence_score:.1f}"
    })
    
    events.sort(key=lambda x: x["timestamp"])
    return events


@router.get("/health/sources", response_model=List[SourceHealthResponse])
def get_source_health(db: Session = Depends(get_db)) -> List[SourceHealth]:
    """
    Retrieve success/failure health records for all social/market API ingest adapters.
    """
    return db.query(SourceHealth).all()


@router.get("/watchlist", response_model=List[WatchlistResponse])
def get_watchlist(db: Session = Depends(get_db)) -> List[Watchlist]:
    """
    Retrieve the current user watchlist from database.
    """
    return db.query(Watchlist).all()


@router.post("/watchlist", response_model=WatchlistResponse)
def add_to_watchlist(req: WatchlistRequest, db: Session = Depends(get_db)) -> Watchlist:
    """
    Add a new equity symbol or topic tag to user-monitored watchlists.
    """
    symbol_upper = req.symbol_or_topic.upper()
    existing = db.query(Watchlist).filter(Watchlist.symbol_or_topic == symbol_upper).first()
    if existing:
        existing.alert_threshold = req.alert_threshold
        existing.notification_enabled = req.notification_enabled
        db.commit()
        return existing
        
    entry = Watchlist(
        symbol_or_topic=symbol_upper,
        alert_threshold=req.alert_threshold,
        notification_enabled=req.notification_enabled
    )
    db.add(entry)
    db.commit()
    return entry


@router.delete("/watchlist/{symbol_or_topic}")
def remove_from_watchlist(symbol_or_topic: str, db: Session = Depends(get_db)) -> Dict[str, str]:
    """
    Delete a specified symbol or topic entry from user watchlists.
    """
    symbol_upper = symbol_or_topic.upper()
    entry = db.query(Watchlist).filter(Watchlist.symbol_or_topic == symbol_upper).first()
    if not entry:
        raise HTTPException(status_code=404, detail="Watchlist entry not found")
    db.delete(entry)
    db.commit()
    return {"status": "success", "message": f"Removed {symbol_upper} from watchlist"}


@router.post("/backtest")
def trigger_backtesting(db: Session = Depends(get_db)) -> Dict[str, Any]:
    """
    Simulates outcome replay of generated alerts to calculate precision stats.
    Measures percentage of alerts followed by price increases based on market observations.
    """
    alerts = db.query(Alert).all()
    if not alerts:
        return {
            "precision": 0.0,
            "recall": 0.0,
            "average_return": 0.0,
            "total_alerts": 0,
            "evaluated_alerts": 0
        }
        
    success_count = 0
    total_return = 0.0
    valid_count = 0
    
    for alert in alerts:
        # Check if we have multiple market observations for this symbol
        obs = db.query(MarketObservation).filter(
            MarketObservation.symbol == alert.ticker_symbol
        ).order_by(MarketObservation.observed_at.asc()).all()
        
        if len(obs) >= 2:
            start_price = obs[0].latest_price
            end_price = obs[-1].latest_price
            if start_price and end_price and start_price > 0:
                ret = (end_price - start_price) / start_price
                total_return += ret
                valid_count += 1
                if ret > 0.02: # 2% gain considered success
                    success_count += 1
                    
    precision = (success_count / valid_count) * 100.0 if valid_count > 0 else 0.0
    avg_return = (total_return / valid_count) * 100.0 if valid_count > 0 else 0.0
    
    return {
        "precision": precision,
        "recall": 100.0 if alerts else 0.0,
        "average_return": avg_return,
        "total_alerts": len(alerts),
        "evaluated_alerts": valid_count
    }


@router.get("/admin/config")
def get_admin_config() -> Dict[str, bool]:
    """
    Retrieve current ingestion settings configuration.
    """
    return {
        "strict_real_data": settings.STRICT_REAL_DATA,
        "allow_simulated_data": settings.ALLOW_SIMULATED_DATA
    }


@router.post("/admin/config")
def update_admin_config(req: AdminConfigRequest) -> Dict[str, str]:
    """
    Update ingestion settings configuration dynamically.
    """
    settings.STRICT_REAL_DATA = req.strict_real_data
    settings.ALLOW_SIMULATED_DATA = req.allow_simulated_data
    return {"status": "success", "message": "Configuration updated successfully"}


@router.post("/ingest")
def trigger_ingestion(db: Session = Depends(get_db), api_key: str = Security(get_api_key)) -> Dict[str, str]:
    """
    Manually triggers the ingestion pipeline to fetch trends and identify matches.
    Secured by static API key header verification.
    """
    from ..ingestion.poller import run_ingestion
    run_ingestion(db)
    return {"status": "success", "message": "Ingestion pipeline completed successfully"}
