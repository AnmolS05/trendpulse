"""Tests for the Meme Score calculation engine."""
import pytest
from app.analytics.scorer import calculate_meme_score

def test_high_intensity_microcap():
    """
    Checks that high social velocity and volume surge on a microcap
    produces a very high meme score.
    """
    # social_velocity=9.0 (high), similarity=0.9, volume_surge=8.0 (high), market_cap=2.0 (microcap)
    score = calculate_meme_score(9.0, 0.9, 8.0, 2.0)
    assert score > 70.0
    assert score <= 100.0

def test_low_intensity_largecap():
    """
    Checks that low social velocity and volume surge on a largecap
    produces a low meme score due to capitalization penalty.
    """
    # social_velocity=1.0 (low), similarity=0.3, volume_surge=0.8 (low), market_cap=50000.0 (largecap)
    score = calculate_meme_score(1.0, 0.3, 0.8, 50000.0)
    assert score < 30.0
    assert score >= 0.0

def test_mathematical_bounds():
    """
    Verifies that the score remains strictly within the [0.0, 100.0] range
    even under extreme edge inputs.
    """
    # Extreme high
    score_high = calculate_meme_score(100.0, 1.0, 100.0, 0.001)
    assert score_high == 100.0
    
    # Extreme low / negative results
    score_low = calculate_meme_score(0.0, 0.0, 0.0, 99999999.0)
    assert score_low == 0.0


def test_confidence_calculation():
    """
    Verifies that confidence calculation returns correct scores, drivers, and weaknesses.
    """
    from app.analytics.scorer import calculate_confidence_score
    
    # Complete evidence
    sources = [{"source": "reddit", "status": "healthy", "raw_value": 5.0}, {"source": "google_trends", "status": "healthy", "raw_value": 2.0}]
    score, drivers, weaknesses = calculate_confidence_score(sources, 0.9, True, False, False)
    assert score > 80.0
    assert "Multiple social sources agree" in drivers
    assert "Real market volume confirmation" in drivers
    assert not weaknesses

    # Ambiguous, missing market and industry mismatch
    sources_weak = [{"source": "reddit", "status": "healthy", "raw_value": 1.0}]
    score_weak, drivers_weak, weaknesses_weak = calculate_confidence_score(sources_weak, 0.5, False, True, True)
    assert score_weak < 40.0
    assert "Missing market volume data" in weaknesses_weak
    assert "Industry mismatch detected (high false positive risk)" in weaknesses_weak


def test_risk_assessment():
    """
    Verifies risk flags are correctly identified and caution messages generated.
    """
    from app.analytics.scorer import assess_alert_risks
    
    # Highly risky microcap
    flags, summary = assess_alert_risks(15.0, 2000, 4.5, True)
    assert "microcap" in flags
    assert "liquidity" in flags
    assert "pump_risk" in flags
    assert "ambiguity" in flags
    assert "Micro-cap" in summary
    assert "Low daily trading volume" in summary

