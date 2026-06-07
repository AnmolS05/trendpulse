"""Social data ingestion and trend polling."""
import logging
from pytrends.request import TrendReq
from typing import List, Dict

logger = logging.getLogger(__name__)

def fetch_google_trends(keywords: List[str]) -> Dict[str, float]:
    """
    Fetches relative search volume for a list of keywords.
    """
    try:
        pytrends = TrendReq(hl='en-US', tz=360)
        pytrends.build_payload(keywords, cat=0, timeframe='now 1-d', geo='', gprop='')
        data = pytrends.interest_over_time()
        
        results = {}
        for kw in keywords:
            if not data.empty and kw in data.columns:
                # get the last value
                latest_val = data[kw].iloc[-1]
                results[kw] = float(latest_val)
            else:
                results[kw] = 0.0
                
        return results
    except Exception as e:
        logger.error(f"Error fetching Google Trends: {e}")
        return {kw: 0.0 for kw in keywords}

def calculate_social_velocity(recent_mentions: float, baseline: float = 10.0) -> float:
    """
    Calculates the Velocity Metric (V_t).
    """
    if baseline <= 0:
        return 1.0
    return recent_mentions / baseline

def fetch_reddit_mentions(keywords: List[str]) -> Dict[str, float]:
    """
    Queries hot topics from wallstreetbets and counts keyword occurrences,
    weighting them by post score and engagement metrics.
    """
    import urllib.request
    import json
    
    mentions = {kw: 0.0 for kw in keywords}
    url = "https://www.reddit.com/r/wallstreetbets/hot.json?limit=50"
    
    try:
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) TrendPulse/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            posts = data.get('data', {}).get('children', [])
            for post in posts:
                post_data = post.get('data', {})
                title = post_data.get('title', '').lower()
                selftext = post_data.get('selftext', '').lower()
                combined_text = f"{title} {selftext}"
                
                for kw in keywords:
                    if kw.lower() in combined_text:
                        score = post_data.get('score', 1)
                        num_comments = post_data.get('num_comments', 1)
                        # Score and comments indicate engagement level
                        mentions[kw] += 1.0 + (score * 0.01) + (num_comments * 0.05)
                        
        return mentions
    except Exception as e:
        logger.error(f"Error fetching Reddit mentions: {e}")
        return mentions

