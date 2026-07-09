"""Market data validation, provider abstraction, and anomaly checking."""
import logging
import random
import urllib.request
import urllib.parse
import json
from typing import Dict, Any, List
from ..config import settings

logger = logging.getLogger(__name__)

# Enforce a safe try-except fallback block for yfinance imports to prevent server startup crashes
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    yf = None
    YFINANCE_AVAILABLE = False
    logger.warning("yfinance package is missing from the active virtual environment. Indian equities volume metrics will fall back to unauthenticated raw queries.")


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
        raise NotImplementedError("Subclasses must implement fetch_volume_anomaly")


class AlpacaMarketDataProvider(MarketDataProvider):
    """
    Market data provider using the Alpaca V2 bars API.
    """
    def __init__(self, api_key: str, secret_key: str):
        self.api_key = api_key
        self.secret_key = secret_key

    def fetch_volume_anomaly(self, symbol: str) -> MarketValidationResult:
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
            clean_symbol = symbol.split('.')[0]
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
                    volumes = [b.get("v", 0) for b in bars[:-1]]
                    avg_volume = sum(volumes) / len(volumes) if volumes else 1.0
                    
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


class YahooFinanceDataProvider(MarketDataProvider):
    """
    Real-time market data provider using the public yfinance library wrapper.
    Bypasses crumb and cookie blocks autonomously.
    """
    def fetch_volume_anomaly(self, symbol: str) -> MarketValidationResult:
        if not YFINANCE_AVAILABLE:
            # Fallback to the raw urllib scraper if yfinance is missing
            return self._fetch_volume_anomaly_raw_fallback(symbol)
            
        logger.info(f"Fetching live Yahoo Finance data via yfinance for {symbol}...")
        try:
            ticker_obj = yf.Ticker(symbol)
            history = ticker_obj.history(period="20d", interval="1d")
            
            if history.empty:
                return MarketValidationResult(
                    symbol=symbol,
                    provider="YahooFinance",
                    status="unavailable",
                    error_message=f"No quote results returned for {symbol} by yfinance"
                )
            
            volumes = history["Volume"].tolist()
            closes = history["Close"].tolist()
            
            latest_volume = float(volumes[-1])
            latest_price = float(closes[-1])
            
            historical_volumes = volumes[:-1] if len(volumes) > 1 else volumes
            avg_volume = sum(historical_volumes) / len(historical_volumes)
            
            volume_surge = latest_volume / avg_volume if avg_volume > 0 else 1.0
            
            return MarketValidationResult(
                symbol=symbol,
                provider="YahooFinance",
                latest_price=latest_price,
                latest_volume=latest_volume,
                avg_volume=avg_volume,
                volume_surge=max(0.1, float(volume_surge)),
                status="success",
                metadata={"provider_library": "yfinance"}
            )
        except Exception as e:
            logger.error(f"yfinance data pull failed for {symbol}: {e}. Trying raw fallback...")
            return self._fetch_volume_anomaly_raw_fallback(symbol)

    def _fetch_volume_anomaly_raw_fallback(self, symbol: str) -> MarketValidationResult:
        """Raw urllib fallback scraper in case yfinance is missing or blocked."""
        logger.info(f"Using unauthenticated raw chart scraper fallback for {symbol}...")
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{symbol}?range=20d&interval=1d"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                result = data.get("chart", {}).get("result", [])
                if not result:
                    return MarketValidationResult(symbol=symbol, provider="YahooFinanceRaw", status="unavailable", error_message="Empty raw chart payload")
                
                quote_data = result[0]
                indicators = quote_data.get("indicators", {}).get("quote", [{}])[0]
                volumes = [v for v in indicators.get("volume", []) if v is not None]
                closes = [c for c in indicators.get("close", []) if c is not None]
                
                if not volumes or not closes:
                    return MarketValidationResult(symbol=symbol, provider="YahooFinanceRaw", status="unavailable", error_message="Empty raw values")
                
                latest_volume = float(volumes[-1])
                latest_price = float(closes[-1])
                historical_volumes = volumes[:-1] if len(volumes) > 1 else volumes
                avg_volume = sum(historical_volumes) / len(historical_volumes)
                volume_surge = latest_volume / avg_volume if avg_volume > 0 else 1.0
                
                return MarketValidationResult(
                    symbol=symbol, provider="YahooFinanceRaw", latest_price=latest_price,
                    latest_volume=latest_volume, avg_volume=avg_volume, volume_surge=max(0.1, float(volume_surge)),
                    status="success", metadata={"fallback_raw": True}
                )
        except Exception as e:
            return MarketValidationResult(symbol=symbol, provider="YahooFinanceRaw", status="error", error_message=str(e))


def fetch_ticker_volume_validation(symbol: str) -> MarketValidationResult:
    if symbol.endswith(".NS") or symbol.endswith(".BO"):
        y_provider = YahooFinanceDataProvider()
        return y_provider.fetch_volume_anomaly(symbol)

    if settings.ALPACA_API_KEY and "your_alpaca" not in settings.ALPACA_API_KEY.lower():
        provider = AlpacaMarketDataProvider(settings.ALPACA_API_KEY, settings.ALPACA_SECRET_KEY)
        result = provider.fetch_volume_anomaly(symbol)
        if result.status == "success":
            return result

    y_provider = YahooFinanceDataProvider()
    return y_provider.fetch_volume_anomaly(symbol)


def discover_listed_tickers_for_topic(topic: str) -> List[Dict[str, Any]]:
    """
    Queries the public Yahoo Finance auto-suggest API to discover related tickers for a topic.
    Strictly filters out any non-Indian exchanges (NSE and BSE only).
    """
    url = f"https://query2.finance.yahoo.com/v1/finance/search?q={urllib.parse.quote(topic)}&quotesCount=3&newsCount=0"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    
    discovered = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
            quotes = data.get("quotes", [])
            for q in quotes:
                symbol = q.get("symbol", "")
                is_indian_equity = symbol.endswith(".NS") or symbol.endswith(".BO")
                if q.get("quoteType") in ["EQUITY", "ETF"] and is_indian_equity:
                    discovered.append({
                        "symbol": symbol,
                        "company_name": q.get("shortname") or q.get("longname") or symbol,
                        "sector": None,
                        "industry": None,
                        "exchange": q.get("exchange")
                    })
    except Exception as e:
        logger.warning(f"Failed to discover tickers for topic {topic}: {e}")
        
    return discovered
