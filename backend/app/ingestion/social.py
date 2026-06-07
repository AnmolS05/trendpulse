"""Social data ingestion, trend harvesting, and news RSS polling."""
import logging
import time
import random
import base64
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class SocialHarvestResult:
    """
    Represents the result of a social harvesting attempt for a keyword/topic.
    """
    def __init__(
        self,
        topic: str,
        source: str,
        raw_value: float,
        normalized_value: float,
        status: str = "healthy",
        source_url: str = None,
        error_message: str = None,
        metadata: Dict[str, Any] = None
    ):
        """
        Initializes a SocialHarvestResult.
        """
        self.topic = topic
        self.source = source
        self.raw_value = raw_value
        self.normalized_value = normalized_value
        self.status = status
        self.source_url = source_url
        self.error_message = error_message
        self.metadata = metadata or {}


def get_reddit_access_token(client_id: str, client_secret: str) -> str:
    """
    Retrieves an OAuth access token from Reddit API using client credentials.
    """
    if not client_id or not client_secret:
        return None
    url = "https://www.reddit.com/api/v1/access_token"
    data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode("utf-8")
    auth_str = f"{client_id}:{client_secret}"
    b64_auth = base64.b64encode(auth_str.encode("utf-8")).decode("utf-8")
    
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "Authorization": f"Basic {b64_auth}",
            "User-Agent": "TrendPulse/1.0 (by /u/dev)",
            "Content-Type": "application/x-www-form-urlencoded"
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res = json.loads(response.read().decode("utf-8"))
            return res.get("access_token")
    except Exception as e:
        logger.error(f"Failed to fetch Reddit access token: {e}")
        return None


def fetch_reddit_mentions_v2(
    keywords: List[str],
    client_id: str = "",
    client_secret: str = ""
) -> List[SocialHarvestResult]:
    """
    Queries hot topics from wallstreetbets, counts keyword occurrences,
    weighting them by post score and comments, and returns a list of results.
    Supports authenticated Client credentials or falls back to public API.
    """
    token = get_reddit_access_token(client_id, client_secret)
    is_auth = token is not None
    
    if is_auth:
        url = "https://oauth.reddit.com/r/wallstreetbets/hot?limit=100"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "TrendPulse/1.0 (by /u/dev)"
        }
    else:
        url = "https://www.reddit.com/r/wallstreetbets/hot.json?limit=100"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TrendPulse/1.0"
        }
        
    mentions_counts = {kw: 0.0 for kw in keywords}
    mentions_metadata = {kw: {"posts": []} for kw in keywords}
    status = "healthy"
    error_msg = None
    
    # Retry loop with backoff for rate limits
    max_retries = 3
    for attempt in range(max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode("utf-8"))
                posts = data.get("data", {}).get("children", [])
                
                for post in posts:
                    post_data = post.get("data", {})
                    title = post_data.get("title", "").lower()
                    selftext = post_data.get("selftext", "").lower()
                    combined_text = f"{title} {selftext}"
                    post_url = f"https://reddit.com{post_data.get('permalink', '')}"
                    
                    for kw in keywords:
                        if kw.lower() in combined_text:
                            score = post_data.get("score", 1)
                            num_comments = post_data.get("num_comments", 1)
                            weight = 1.0 + (score * 0.01) + (num_comments * 0.05)
                            mentions_counts[kw] += weight
                            mentions_metadata[kw]["posts"].append({
                                "title": post_data.get("title"),
                                "score": score,
                                "num_comments": num_comments,
                                "url": post_url
                            })
                break # Success, exit retry loop
        except Exception as e:
            status = "error"
            error_msg = str(e)
            logger.warning(f"Reddit ingest attempt {attempt+1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(2 ** attempt + random.uniform(0.1, 0.5))
            else:
                logger.error(f"Reddit ingestion failed after {max_retries} attempts: {e}")

    results = []
    for kw in keywords:
        raw_val = mentions_counts.get(kw, 0.0)
        # Normalize: log scaling or division. Max 10.0
        norm_val = min(10.0, raw_val / 10.0)
        results.append(
            SocialHarvestResult(
                topic=kw,
                source="reddit",
                raw_value=raw_val,
                normalized_value=norm_val,
                status=status,
                source_url=url,
                error_message=error_msg,
                metadata=mentions_metadata[kw]
            )
        )
    return results


def fetch_google_trends_v2(keywords: List[str]) -> List[SocialHarvestResult]:
    """
    Fetches Google Trends search interest over time with retries.
    """
    results = []
    status = "healthy"
    error_msg = None
    
    # We do batches of 5
    pytrends = None
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            pytrends = TrendReq(hl="en-US", tz=360, retries=2, backoff_factor=1)
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(1)
            else:
                status = "error"
                error_msg = str(e)
                logger.error(f"Failed to initialize pytrends: {e}")
                
    trends_raw = {kw: 0.0 for kw in keywords}
    
    if pytrends:
        try:
            # Pytrends builds payloads and fetches in batches
            for i in range(0, len(keywords), 5):
                batch = keywords[i:i+5]
                pytrends.build_payload(batch, cat=0, timeframe="now 1-d", geo="", gprop="")
                data = pytrends.interest_over_time()
                for kw in batch:
                    if not data.empty and kw in data.columns:
                        latest_val = data[kw].iloc[-1]
                        trends_raw[kw] = float(latest_val)
        except Exception as e:
            status = "error"
            error_msg = str(e)
            logger.error(f"Google Trends query failed: {e}")
            
    for kw in keywords:
        raw_val = trends_raw.get(kw, 0.0)
        # Google Trends output is already 0-100, normalize to 0-10 scale
        norm_val = raw_val / 10.0
        results.append(
            SocialHarvestResult(
                topic=kw,
                source="google_trends",
                raw_value=raw_val,
                normalized_value=norm_val,
                status=status,
                source_url="https://trends.google.com",
                error_message=error_msg
            )
        )
    return results


def check_news_rss(keyword: str) -> SocialHarvestResult:
    """
    Checks news mentions of a keyword using Google News RSS search.
    """
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_kw}&hl=en-US&gl=US&ceid=US:en"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) TrendPulse/1.0"}
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall(".//item")
            count = len(items)
            articles = []
            for item in items[:10]: # Store top 10 articles
                title = item.find("title").text if item.find("title") is not None else ""
                link = item.find("link").text if item.find("link") is not None else ""
                pub_date = item.find("pubDate").text if item.find("pubDate") is not None else ""
                source_name = item.find("source").text if item.find("source") is not None else "Google News"
                articles.append({
                    "title": title,
                    "url": link,
                    "published_at": pub_date,
                    "source": source_name
                })
            
            return SocialHarvestResult(
                topic=keyword,
                source="google_news_rss",
                raw_value=float(count),
                normalized_value=min(10.0, float(count) / 2.0),
                status="healthy",
                source_url=url,
                metadata={"articles": articles}
            )
    except Exception as e:
        logger.error(f"Error checking news RSS for {keyword}: {e}")
        return SocialHarvestResult(
            topic=keyword,
            source="google_news_rss",
            raw_value=0.0,
            normalized_value=0.0,
            status="error",
            error_message=str(e)
        )


def calculate_social_velocity(recent_mentions: float, baseline: float = 10.0) -> float:
    """
    Calculates the Velocity Metric (V_t) by dividing current mentions by historical baseline.
    """
    if baseline <= 0:
        return 1.0
    return recent_mentions / baseline
