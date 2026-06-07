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
