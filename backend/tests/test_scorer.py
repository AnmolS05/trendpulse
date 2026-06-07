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
