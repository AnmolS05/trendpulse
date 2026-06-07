"""Tests for the matching engine."""
import pytest
from app.analytics.matching import find_similar

class MockTicker:
    def __init__(self, symbol, company_name):
        self.symbol = symbol
        self.company_name = company_name

@pytest.fixture
def db_tickers():
    return [
        MockTicker("PARLE.NS", "Parle Industries"),
        MockTicker("SIGL", "Signal Advance"),
        MockTicker("AAPL", "Apple Inc")
    ]

def test_phonetic_match_parle(db_tickers):
    results = find_similar("Parle", db_tickers)
    assert len(results) > 0
    assert results[0]["symbol"] == "PARLE.NS"

def test_name_similarity_signal(db_tickers):
    results = find_similar("Signal Messenger", db_tickers)
    assert len(results) > 0
    assert results[0]["symbol"] == "SIGL"

def test_generic_terms_filtered(db_tickers):
    results = find_similar("The Company", db_tickers)
    assert len(results) == 0


def test_matching_with_industry():
    """
    Verifies that industry mismatches penalize the adjusted similarity score.
    """
    class MockTickerWithIndustry:
        def __init__(self, symbol, company_name, industry, avg_volume=20000):
            self.symbol = symbol
            self.company_name = company_name
            self.industry = industry
            self.avg_volume = avg_volume
            
    tickers = [
        MockTickerWithIndustry("SIGL", "Signal Advance", "Medical Devices"),
        MockTickerWithIndustry("AAPL", "Apple Inc", "Consumer Electronics")
    ]
    
    # Matching with same industry should have no penalty
    results_same = find_similar("Signal Messenger", tickers, brand_industry="Medical Devices")
    assert len(results_same) > 0
    # Matching with mismatched industry should penalize
    results_diff = find_similar("Signal Messenger", tickers, brand_industry="Software")
    assert len(results_diff) > 0
    assert results_diff[0]["adjusted_similarity"] < results_same[0]["adjusted_similarity"]
    assert results_diff[0]["industry_mismatch"] is True


def test_liquidity_and_ambiguity_flags():
    """
    Verifies that ambiguous short terms and low liquidity tickers trigger flags.
    """
    class MockTickerWithVolume:
        def __init__(self, symbol, company_name, avg_volume):
            self.symbol = symbol
            self.company_name = company_name
            self.avg_volume = avg_volume
            
    tickers = [
        MockTickerWithVolume("ZOOM", "Zoom Technologies", 500)
    ]
    
    results = find_similar("Zoom", tickers)
    assert len(results) > 0
    assert results[0]["low_liquidity"] is True
    assert results[0]["is_ambiguous"] is True

