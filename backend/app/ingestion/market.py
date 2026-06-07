"""Market data validation, provider abstraction, and anomaly checking."""
import logging
import random
import urllib.request
import urllib.parse
import json
from typing import Dict, Any
from ..config import settings

logger = logging.getLogger(__name__)

class MarketValidationResult:
    """
    Represents the validation result from querying market APIs.
    """
    def __init__(
        self,
        symbol: str,
        provider: str,
        latest_price: float = None,
        latest_volume: float = None,
        avg_volume: float = None,
        volume_surge: float = None,
        status: str = "success", # success, unavailable, error
        error_message: str = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Initializes a MarketValidationResult.
        """
        self.symbol = symbol
        self.provider = provider
        self.latest_price = latest_price
        self.latest_volume = latest_volume
        self.avg_volume = avg_volume
        self.volume_surge = volume_surge
        self.status = status
        self.error_message = error_message
        self.metadata = metadata or {}


class MarketDataProvider:
    """
    Base abstraction class for fetching market data anomalies.
    """
    def fetch_volume_anomaly(self, symbol: str) -> MarketValidationResult:
        """
        Fetches the volume anomaly metrics for a given stock symbol.
        Must be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement fetch_volume_anomaly")


class AlpacaMarketDataProvider(MarketDataProvider):
    """
    Market data provider using the Alpaca V2 bars API.
    """
    def __init__(self, api_key: str, secret_key: str):
        """
        Initializes Alpaca credentials.
        """
        self.api_key = api_key
        self.secret_key = secret_key

    def fetch_volume_anomaly(self, symbol: str) -> MarketValidationResult:
        """
        Queries Alpaca API to fetch latest and average historical volumes.
        """
        has_valid_keys = (
            self.api_key and 
            self.secret_key and 
            "your_alpaca" not in self.api_key.lower() and 
            "your_alpaca" not in self.secret_key.lower()
        )
        
        if not has_valid_keys:
            return MarketValidationResult(
                symbol=symbol,
                provider="Alpaca",
                status="unavailable",
                error_message="Missing or placeholder Alpaca API credentials"
            )
            
        logger.info(f"Fetching live Alpaca volume data for {symbol}...")
        try:
            # Clean symbols like "PARLE.NS" (remove extension for Alpaca)
            clean_symbol = symbol.split('.')[0]
            
            # Alpaca v2 bars endpoint
            url = f"https://data.alpaca.markets/v2/stocks/bars?symbols={clean_symbol}&timeframe=1Day&limit=20"
            req = urllib.request.Request(url, headers={
                "APCA-API-KEY-ID": self.api_key,
                "APCA-API-SECRET-KEY": self.secret_key,
                "Accept": "application/json"
            })
            
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                bars = res_data.get("bars", {}).get(clean_symbol, [])
                
                if not bars:
                    return MarketValidationResult(
                        symbol=symbol,
                        provider="Alpaca",
                        status="unavailable",
                        error_message=f"No bars returned from Alpaca for symbol {clean_symbol}"
                    )
                
                if len(bars) > 1:
                    # Calculate 20-day average volume (excluding the last bar)
                    volumes = [b.get("v", 0) for b in bars[:-1]]
                    avg_volume = sum(volumes) / len(volumes) if volumes else 1.0
                    
                    # Latest volume
                    latest_volume = bars[-1].get("v", 0)
                    latest_price = float(bars[-1].get("c", 0.0))
                    
                    if avg_volume > 0:
                        surge = latest_volume / avg_volume
                        logger.info(f"Live Alpaca volume surge for {symbol}: {surge:.2f}x")
                        return MarketValidationResult(
                            symbol=symbol,
                            provider="Alpaca",
                            latest_price=latest_price,
                            latest_volume=float(latest_volume),
                            avg_volume=float(avg_volume),
                            volume_surge=max(0.1, float(surge)),
                            status="success"
                        )
                
                # If only one bar or empty averages
                latest_volume = bars[-1].get("v", 0) if bars else 0.0
                latest_price = float(bars[-1].get("c", 0.0)) if bars else 0.0
                return MarketValidationResult(
                    symbol=symbol,
                    provider="Alpaca",
                    latest_price=latest_price,
                    latest_volume=float(latest_volume),
                    avg_volume=latest_volume,
                    volume_surge=1.0,
                    status="success",
                    metadata={"note": "Insufficient bars to compute 20-day baseline"}
                )
                        
        except Exception as e:
            logger.error(f"Error fetching live Alpaca data for {symbol}: {e}")
            return MarketValidationResult(
                symbol=symbol,
                provider="Alpaca",
                status="error",
                error_message=str(e)
            )


class SimulatedMarketDataProvider(MarketDataProvider):
    """
    Generates mock market data anomalies for demonstration and testing.
    """
    def fetch_volume_anomaly(self, symbol: str) -> MarketValidationResult:
        """
        Returns a simulated surge with mock average/latest volume stats.
        """
        logger.info(f"Generating simulated market data for {symbol}...")
        avg_vol = float(random.randint(50000, 200000))
        surge = float(random.uniform(0.5, 4.0))
        latest_vol = avg_vol * surge
        latest_price = float(random.uniform(5.0, 150.0))
        
        return MarketValidationResult(
            symbol=symbol,
            provider="Simulated",
            latest_price=latest_price,
            latest_volume=latest_vol,
            avg_volume=avg_vol,
            volume_surge=surge,
            status="success",
            metadata={"simulated": True}
        )


def fetch_ticker_volume_validation(symbol: str) -> MarketValidationResult:
    """
    Orchestrates market volume validation based on settings.
    Queries Alpaca API; if strict mode is disabled, falls back to simulation.
    """
    provider = AlpacaMarketDataProvider(
        api_key=settings.ALPACA_API_KEY,
        secret_key=settings.ALPACA_SECRET_KEY
    )
    result = provider.fetch_volume_anomaly(symbol)
    
    # Fallback to simulation if strict mode is disabled and credentials or request fails
    if result.status in ["unavailable", "error"]:
        if not settings.STRICT_REAL_DATA or settings.ALLOW_SIMULATED_DATA:
            sim_provider = SimulatedMarketDataProvider()
            return sim_provider.fetch_volume_anomaly(symbol)
            
    return result
