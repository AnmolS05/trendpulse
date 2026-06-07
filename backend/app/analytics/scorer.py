"""Meme Score calculation engine."""
import math

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
    return max(0.0, min(100.0, final_score * 2.5)) # scaled arbitrarily for UI
