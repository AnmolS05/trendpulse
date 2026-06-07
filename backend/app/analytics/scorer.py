"""Meme Score, Confidence Score, and Risk assessment engines."""
import math
from typing import List, Dict, Any, Tuple

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
    w1 = 20.0
    w2 = 30.0
    w3 = 30.0
    w4 = 10.0
    
    # Cap inputs
    velocity = min(social_velocity, 10.0) # max 10x
    surge = min(volume_surge, 10.0)       # max 10x
    
    # Avoid log(0)
    mc = max(market_cap, 0.1)
    
    base_score = (w1 * (velocity / 10.0)) + (w2 * link_strength) + (w3 * (surge / 5.0))
    cap_penalty = w4 * math.log10(mc)
    
    final_score = base_score - cap_penalty
    
    # Normalize to 0-100
    return max(0.0, min(100.0, final_score * 2.5))


def calculate_confidence_score(
    sources_status: List[Dict[str, Any]],
    match_similarity: float,
    has_market_evidence: bool,
    industry_mismatch: bool = False,
    is_ambiguous: bool = False
) -> Tuple[float, List[str], List[str]]:
    """
    Calculates the confidence score (0-100) based on signal reliability.
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
