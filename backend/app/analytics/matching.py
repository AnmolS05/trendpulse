"""Matching engine for phonetic and semantic comparisons with false positive filters."""
import jellyfish
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

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


def find_similar(
    brand_name: str,
    db_tickers: List[Any],
    brand_industry: str = None
) -> List[Dict[str, Any]]:
    """
    Finds similar tickers from the database based on phonetic and string similarity.
    Integrates stopword cleaning, industry mismatch penalties, and ambiguity metrics.
    """
    generic_words = {
        "the", "company", "inc", "ltd", "corp", "holdings", "industries", 
        "products", "messenger", "advance", "oxygen", "investments", 
        "technologies", "group", "limited", "co", "solutions"
    }
    
    known_dictionary_terms = {"zoom", "signal", "melody", "box", "car", "fast", "app"}
    
    def clean_name(name: str) -> str:
        words = name.lower().split()
        cleaned = [w for w in words if w not in generic_words]
        return " ".join(cleaned) if cleaned else name.lower()
    
    target_clean = clean_name(brand_name)
    target_primary = generate_phonetic_key(target_clean)
    
    # Calculate target name ambiguity
    is_ambiguous = target_clean in known_dictionary_terms or len(target_clean) <= 4
    
    results = []
    for ticker in db_tickers:
        ticker_company_name = getattr(ticker, "company_name", "")
        ticker_industry = getattr(ticker, "industry", None)
        ticker_symbol = getattr(ticker, "symbol", "")
        ticker_avg_volume = getattr(ticker, "avg_volume", None)
        
        ticker_clean = clean_name(ticker_company_name)
        
        # Use database pre-calculated phonetic key if available, otherwise generate
        ticker_primary = getattr(ticker, "phonetic_primary", None)
        if not ticker_primary:
            ticker_primary = generate_phonetic_key(ticker_clean)
        
        # Calculate base string similarity
        similarity = calculate_similarity(target_clean, ticker_clean)
        
        # Check first word phonetic match
        target_words = target_clean.split()
        ticker_words = ticker_clean.split()
        first_word_match = False
        if target_words and ticker_words:
            t1 = generate_phonetic_key(target_words[0])
            t2 = generate_phonetic_key(ticker_words[0])
            if t1 and t1 == t2:
                first_word_match = True
        
        is_phonetic = (target_primary and target_primary == ticker_primary) or first_word_match
        
        # Only check match if phonetic overlaps or similarity is decent
        if is_phonetic or similarity > 0.45:
            # Apply industry mismatch penalty
            industry_mismatch = False
            penalty = 0.0
            if brand_industry and ticker_industry:
                b_ind = brand_industry.lower()
                t_ind = ticker_industry.lower()
                # If neither contains the other or matches partially
                if (b_ind not in t_ind) and (t_ind not in b_ind):
                    industry_mismatch = True
                    penalty = 0.20 # 20% penalty for industry mismatch
            
            # Apply ambiguity penalty (e.g. short/common words require higher similarity)
            if is_ambiguous:
                penalty += 0.10
                
            adjusted_similarity = max(0.0, similarity - penalty)
            
            # Liquidity warning
            low_liquidity = False
            if ticker_avg_volume is not None and ticker_avg_volume < 10000:
                low_liquidity = True
                
            # Keep if adjusted similarity passes threshold, or if it is a strong phonetic match
            if adjusted_similarity > 0.45 or (is_phonetic and adjusted_similarity > 0.3):
                results.append({
                    "symbol": ticker_symbol,
                    "company_name": ticker_company_name,
                    "similarity": similarity,
                    "adjusted_similarity": adjusted_similarity,
                    "phonetic_match": is_phonetic,
                    "industry_mismatch": industry_mismatch,
                    "is_ambiguous": is_ambiguous,
                    "low_liquidity": low_liquidity,
                    "ticker_industry": ticker_industry
                })
                
    # Sort by adjusted similarity
    return sorted(results, key=lambda x: x["adjusted_similarity"], reverse=True)
