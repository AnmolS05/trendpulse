"""API routes."""
from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import Alert, Ticker
from ..schemas import AlertResponse
from ..config import settings

router = APIRouter()
api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == settings.API_KEY:
        return api_key_header
    raise HTTPException(status_code=403, detail="Could not validate credentials")

@router.get("/alerts", response_model=List[AlertResponse])
def get_alerts(db: Session = Depends(get_db)):
    """Fetch active alerts with company name and market capitalization details."""
    # Perform a single SQL outer join to avoid N+1 query overhead
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
            "market_cap": ticker.market_cap if ticker else None
        })
    return enriched_alerts

@router.post("/ingest")
def trigger_ingestion(db: Session = Depends(get_db), api_key: str = Security(get_api_key)):
    """
    Manually triggers the ingestion pipeline to fetch trends and identify matches.
    Secured by static API key header verification.
    """
    from ..ingestion.poller import run_ingestion
    run_ingestion(db)
    return {"status": "success", "message": "Ingestion pipeline completed successfully"}

