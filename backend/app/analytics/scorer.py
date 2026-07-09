"""Meme Score, Confidence Score, and Risk assessment engines."""
import math
from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from textblob import TextBlob
from sqlalchemy.orm import Session
from ..config import settings
from ..models import TrendObservation

def calculate_meme_score(
    social_velocity: float,
    link_strength: float,
    volume_surge: float,
    market_cap: float
) -> float:
    """
    Calculates the predictive FOMO Meme Score (0-100).
    Meme Score = (w1 * Trend Velocity) + (w2 * Link Strength) + (w3 * Volatility) - (w4 * log(Market Cap))
    """
    w1 = settings.MEME_WEIGHT_VELOCITY
    w2 = settings.MEME_WEIGHT_LINK
    w3 = settings.MEME_WEIGHT_SURGE
    w4 = settings.MEME_WEIGHT_CAP
    
    # Cap inputs
    velocity = min(social_velocity, 10.0) # max 10x
    surge = min(volume_surge, 10.0)       # max 10x
    
    # Avoid log(0)
    mc = max(market_cap, 0.1)
    
    base_score = (w1 * (velocity / settings.SCALE_VELOCITY)) + (w2 * link_strength) + (w3 * (surge / settings.SCALE_SURGE))
    cap_penalty = w4 * math.log10(mc)
    
    final_score = base_score - cap_penalty
    
    # Normalize to 0-100
    return max(0.0, min(100.0, final_score * 2.5))


def calculate_confidence_score(
    sources_status: List[Dict[str, Any]],
    match_similarity: float,
    has_market_evidence: bool,
    industry_mismatch: bool = False,
    is_ambiguous: bool = False,
    news_count: int = 0,
    insufficient_history: bool = False
) -> Tuple[float, List[str], List[str]]:
    """
    Calculates the confidence score (0-100) based on signal reliability.

    Args:
        sources_status: List of dictionaries tracking health and value of social sources.
        match_similarity: Similarity match level between query topic and target ticker.
        has_market_evidence: True if market volume surge corroboration is found.
        industry_mismatch: True if the brand and ticker industries mismatch.
        is_ambiguous: True if the topic matches common words or dictionary definitions.
        news_count: The number of news articles corroborating the brand or ticker.
        insufficient_history: True if there is not enough historical baseline data.

    Returns:
        Tuple containing (confidence_score, list of drivers, list of weaknesses)
    """
    score = 50.0
    drivers = []
    weaknesses = []
    
    # 1. Source verification
    active_sources = [
        s for s in sources_status 
        if s.get("status") == "healthy" and s.get("raw_value", 0.0) > 0.0
    ]
    
    if len(active_sources) >= 2:
        score += 15.0
        drivers.append("Multiple social sources agree")
    elif len(active_sources) == 1:
        score += 5.0
        drivers.append(f"Confirmed on {active_sources[0]['source']}")
    else:
        score -= 20.0
        weaknesses.append("No active social mentions detected")
        
    # 2. Market evidence validation
    if has_market_evidence:
        score += 20.0
        drivers.append("Real market volume confirmation")
    else:
        score -= 15.0
        weaknesses.append("Missing market volume data")
        
    # 3. Brand-ticker matching strength
    if match_similarity >= 0.8:
        score += 15.0
        drivers.append("Strong phonetic/semantic similarity match")
    elif match_similarity < 0.6:
        score -= 10.0
        weaknesses.append("Weak phonetic similarity match")
        
    # 4. Industry mismatch
    if industry_mismatch:
        score -= 20.0
        weaknesses.append("Industry mismatch detected (high false positive risk)")
    else:
        score += 5.0
        drivers.append("Consistent industry alignment")
        
    # 5. Ambiguity
    if is_ambiguous:
        score -= 15.0
        weaknesses.append("Ambiguous keyword (short or common dictionary word)")
        
    # 6. News Catalyst
    if news_count > 0:
        score += 10.0
        drivers.append("News catalyst corroboration")
        
    # 7. Insufficient history penalty
    if insufficient_history:
        score -= settings.PENALTY_INSUFFICIENT_HISTORY
        weaknesses.append("Insufficient historical baseline")
        
    return max(0.0, min(100.0, score)), drivers, weaknesses


def assess_alert_risks(
    market_cap: float,
    avg_volume: float,
    volume_surge: float,
    industry_mismatch: bool
) -> Tuple[List[str], str]:
    """
    Identifies risk factors and generates safety warning texts.
    Returns:
        Tuple containing (list of risk flags, risk warning string)
    """
    flags = []
    warnings = []
    
    # Microcap risk
    if market_cap is not None and market_cap < 50.0:
        flags.append("microcap")
        warnings.append("Micro-cap stock with extreme volatility risk")
        
    # Liquidity risk
    if avg_volume is not None and avg_volume < 10000:
        flags.append("liquidity")
        warnings.append("Low daily trading volume (liquidity risk)")
        
    # Industry mismatch
    if industry_mismatch:
        flags.append("ambiguity")
        warnings.append("High risk of brand confusion or mistaken identity")
        
    # Pump risk
    if volume_surge is not None and volume_surge > 3.0:
        flags.append("pump_risk")
        warnings.append("Volume surge detected (possible pump momentum)")
        
    if not warnings:
        warnings.append("Standard market and liquidity conditions apply")
        
    risk_summary = " | ".join(warnings)
    return flags, risk_summary


def calculate_social_acceleration(db_session: Session, topic: str, current_value: float) -> float:
    """
    Calculates the rate of change of social velocity over the past 3 hours.
    Returns 0.0 if insufficient historical trend observations exist.
    """
    three_hours_ago = datetime.now() - timedelta(hours=3)
    one_hour_ago = datetime.now() - timedelta(hours=1)
    
    obs = db_session.query(TrendObservation).filter(
        TrendObservation.topic == topic,
        TrendObservation.observed_at >= three_hours_ago,
        TrendObservation.observed_at <= one_hour_ago
    ).all()
    
    if not obs:
        return 0.0
        
    past_value = sum(o.raw_value for o in obs) / len(obs)
    if past_value <= 0:
        return 0.0
        
    return (current_value - past_value) / past_value


def calculate_surge_probability(
    acceleration: float,
    similarity: float,
    market_cap: float,
    float_shares: float = None
) -> float:
    """
    Computes a probability score (0-100) indicating the likelihood of an imminent market breakout.
    Penalizes mega-caps and high float structures.
    """
    base_prob = (acceleration * 20.0) + (similarity * 30.0)
    
    mc = max(market_cap, 0.1)
    cap_penalty = math.log10(mc) * 5.0
    
    float_penalty = 0.0
    if float_shares and float_shares > 100.0:
        float_penalty = math.log10(float_shares) * 2.0
        
    prob = base_prob - cap_penalty - float_penalty
    return max(0.0, min(100.0, prob))


def calculate_news_sentiment(news_articles: List[Dict[str, Any]]) -> Tuple[str, float, str]:
    """
    Calculates the average polarity of news headlines using TextBlob.
    Returns a tuple of (Sentiment_Tag, Average_Polarity, Explanation).
    """
    if not news_articles:
        return "NEUTRAL", 0.0, "No mainstream news catalyst detected."
        
    total_polarity = 0.0
    for art in news_articles:
        title = art.get("title", "")
        if title:
            try:
                blob = TextBlob(title)
                total_polarity += blob.sentiment.polarity
            except Exception:
                total_polarity += 0.0
        
    avg_polarity = total_polarity / len(news_articles)
    
    if avg_polarity > 0.15:
        return "BULLISH", avg_polarity, "Dynamic positive catalyst detected in mainstream news. Speculative Indian retail capital is highly likely to drive buying pressure."
    elif avg_polarity < -0.15:
        return "BEARISH", avg_polarity, "Negative catalyst detected. High risk of sell-off, or possible high-volatility contrarian retail squeeze on short positions."
    else:
        return "NEUTRAL", avg_polarity, "Neutral or mixed sentiment detected in news."
