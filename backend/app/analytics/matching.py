"""Matching engine for phonetic and semantic comparisons."""
import jellyfish
from typing import List, Dict, Any

def generate_phonetic_key(text: str) -> str:
    """
    Generates a Metaphone phonetic key for a given string.
    """
    if not text:
        return ""
    return jellyfish.metaphone(text) or ""

def calculate_similarity(source: str, target: str) -> float:
    """
    Calculates the normalized string similarity score using Levenshtein distance.
    Returns a score between 0.0 and 1.0 (1.0 being exact match).
    """
    if not source or not target:
        return 0.0
    distance = jellyfish.levenshtein_distance(source.lower(), target.lower())
    max_len = max(len(source), len(target))
    if max_len == 0:
        return 1.0
    return 1.0 - (distance / max_len)

def find_similar(brand_name: str, db_tickers: List[Any]) -> List[Dict[str, Any]]:
    """
    Finds similar tickers from the database based on phonetic and string similarity.
    Filters generic words.
    """
    generic_words = {"the", "company", "inc", "ltd", "corp", "holdings", "industries", "products", "messenger"}
    
    def clean_name(name: str) -> str:
        words = name.lower().split()
        cleaned = [w for w in words if w not in generic_words]
        return " ".join(cleaned) if cleaned else name.lower()
    
    target_clean = clean_name(brand_name)
    target_primary = generate_phonetic_key(target_clean)
    
    results = []
    for ticker in db_tickers:
        ticker_clean = clean_name(ticker.company_name)
        
        # Use database pre-calculated phonetic key if available, otherwise generate
        ticker_primary = getattr(ticker, "phonetic_primary", None)
        if not ticker_primary:
            ticker_primary = generate_phonetic_key(ticker_clean)
        
        # Exact phonetic match or high string similarity
        similarity = calculate_similarity(target_clean, ticker_clean)
        
        # First word phonetic match
        target_words = target_clean.split()
        ticker_words = ticker_clean.split()
        first_word_match = False
        if target_words and ticker_words:
            t1 = generate_phonetic_key(target_words[0])
            t2 = generate_phonetic_key(ticker_words[0])
            if t1 and t1 == t2:
                first_word_match = True
        
        if (target_primary and target_primary == ticker_primary) or similarity > 0.6 or first_word_match:
            results.append({
                "symbol": ticker.symbol,
                "company_name": ticker.company_name,
                "similarity": similarity,
                "phonetic_match": target_primary == ticker_primary or first_word_match
            })
            
    return sorted(results, key=lambda x: x["similarity"], reverse=True)
