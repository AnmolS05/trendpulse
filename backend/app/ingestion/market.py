"""Market data integration."""
import logging
import random
import urllib.request
import json
from ..config import settings

logger = logging.getLogger(__name__)

def fetch_ticker_volume_anomaly(symbol: str) -> float:
    """
    Checks if a ticker is experiencing a volume surge.
    Queries Alpaca API if credentials are provided; falls back to a simulated surge if credentials are empty.
    Returns a volume surge multiplier.
    """
    api_key = settings.ALPACA_API_KEY
    secret_key = settings.ALPACA_SECRET_KEY
    
    # Check if credentials are valid (not default placeholder strings)
    has_valid_keys = (
        api_key and 
        secret_key and 
        "your_alpaca" not in api_key.lower() and 
        "your_alpaca" not in secret_key.lower()
    )
    
    if has_valid_keys:
        logger.info(f"Fetching live Alpaca volume data for {symbol}...")
        try:
            # Clean symbols like "PARLE.NS" (remove extension for Alpaca)
            clean_symbol = symbol.split('.')[0]
            
            # Alpaca v2 bars endpoint
            url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={clean_symbol}&timeframe=1Day&limit=20"
            req = urllib.request.Request(url, headers={
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": secret_key,
                "Accept": "application/json"
            })
            
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                bars = res_data.get("bars", {}).get(clean_symbol, [])
                
                if len(bars) > 1:
                    # Calculate 20-day average volume (excluding the last bar)
                    volumes = [b.get("v", 0) for b in bars[:-1]]
                    avg_volume = sum(volumes) / len(volumes) if volumes else 1.0
                    
                    # Latest volume
                    latest_volume = bars[-1].get("v", 0)
                    
                    if avg_volume > 0:
                        surge = latest_volume / avg_volume
                        logger.info(f"Live Alpaca volume surge for {symbol}: {surge:.2f}x")
                        return max(0.1, surge)
                        
        except Exception as e:
            logger.error(f"Error fetching live Alpaca data for {symbol}: {e}. Falling back to simulation.")
            
    # Mock fallback if keys are placeholders or request fails
    return random.uniform(0.5, 4.0)

