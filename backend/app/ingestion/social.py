"""Social data ingestion, trend harvesting, and news RSS polling with TextBlob NLP."""
import logging
import time
import random
import base64
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Tuple

# Monkeypatch for urllib3 2.0+ compatibility with pytrends
import urllib3.util.retry
if not hasattr(urllib3.util.retry.Retry, 'method_whitelist'):
    class RetryWithWhitelist(urllib3.util.retry.Retry):
        def __init__(self, *args, **kwargs):
            if 'method_whitelist' in kwargs:
                kwargs['allowed_methods'] = kwargs.pop('method_whitelist')
            super().__init__(*args, **kwargs)
    import pytrends.request
    pytrends.request.Retry = RetryWithWhitelist

from pytrends.request import TrendReq
from textblob import TextBlob

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
        self.topic = topic
        self.source = source
        self.raw_value = raw_value
        self.normalized_value = normalized_value
        self.status = status
        self.source_url = source_url
        self.error_message = error_message
        self.metadata = metadata or {}


def get_reddit_access_token(client_id: str, client_secret: str) -> str | None:
    """Obtain Reddit OAuth2 token using client credentials."""
    placeholder_keywords = ["your_reddit", "placeholder", "example"]
    if not client_id or not client_secret:
        logger.info("Reddit credentials not provided; using public API.")
        return None
    lowered_id = client_id.lower()
    lowered_secret = client_secret.lower()
    if any(kw in lowered_id for kw in placeholder_keywords) or any(kw in lowered_secret for kw in placeholder_keywords):
        logger.info("Reddit credentials appear to be placeholders; skipping authentication.")
        return None
    try:
        token_url = "https://www.reddit.com/api/v1/access_token"
        auth = (client_id + ":" + client_secret).encode("utf-8")
        data = urllib.parse.urlencode({"grant_type": "client_credentials"}).encode()
        req = urllib.request.Request(token_url, data=data, method="POST")
        req.add_header("User-Agent", "TrendPulse/1.0 (by /u/dev)")
        req.add_header("Authorization", "Basic " + base64.b64encode(auth).decode())
        with urllib.request.urlopen(req, timeout=10) as resp:
            resp_data = json.loads(resp.read().decode())
            return resp_data.get("access_token")
    except Exception as e:
        logger.warning(f"Failed to obtain Reddit access token: {e}")
        return None


def fetch_reddit_mentions_v2(
    keywords: List[str],
    client_id: str = "",
    client_secret: str = ""
) -> List[SocialHarvestResult]:
    """
    Queries hot topics from Indian retail stock forum r/IndianStreetBets.
    Uses unblocked Atom RSS feeds to guarantee reliable unauthenticated syndication pulls.
    """
    token = get_reddit_access_token(client_id, client_secret)
    is_auth = token is not None
    
    if is_auth:
        url = "https://oauth.reddit.com/r/IndianStreetBets/hot?limit=100"
        headers = {
            "Authorization": f"Bearer {token}",
            "User-Agent": "TrendPulse/1.0 (by /u/dev)"
        }
    else:
        # Switch to unblocked Atom RSS Feed to bypass strict CDN blocks
        url = "https://www.reddit.com/r/IndianStreetBets.rss"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
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
                if is_auth:
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
                else:
                    # XML RSS Parsing for unauthenticated failover
                    xml_data = response.read()
                    root = ET.fromstring(xml_data)
                    entries = root.findall(".//{http://www.w3.org/2005/Atom}entry")
                    if not entries:
                        entries = root.findall(".//entry")
                    
                    for entry in entries:
                        title_elem = entry.find("{http://www.w3.org/2005/Atom}title")
                        title = title_elem.text.lower() if title_elem is not None else ""
                        content_elem = entry.find("{http://www.w3.org/2005/Atom}content")
                        content = content_elem.text.lower() if content_elem is not None else ""
                        combined_text = f"{title} {content}"
                        
                        link_elem = entry.find("{http://www.w3.org/2005/Atom}link")
                        post_url = link_elem.attrib.get("href", "") if link_elem is not None else ""
                        
                        for kw in keywords:
                            if kw.lower() in combined_text:
                                mentions_counts[kw] += 1.0
                                mentions_metadata[kw]["posts"].append({
                                    "title": title,
                                    "score": 1,
                                    "num_comments": 1,
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
    Fetches Google Trends search interest over time with retries for India (geo="IN").
    """
    results = []
    pytrends = None
    max_init_retries = 3
    for attempt in range(max_init_retries):
        try:
            pytrends = TrendReq(hl="en-IN", tz=330, retries=2, backoff_factor=1)
            break
        except Exception as e:
            logger.warning(f"TrendReq init attempt {attempt+1} failed: {e}")
            if attempt < max_init_retries - 1:
                time.sleep(2 ** attempt + random.uniform(0.1, 0.5))
            else:
                logger.error(f"Failed to initialize TrendReq: {e}")

    trends_raw = {}
    trends_status = {}
    trends_error = {}

    for kw in keywords:
        trends_raw[kw] = 0.0
        trends_status[kw] = "healthy"
        trends_error[kw] = None

    if pytrends:
        for i in range(0, len(keywords), 5):
            batch = keywords[i:i+5]
            batch_success = False
            batch_error_msg = None
            
            # Retry loop per batch query
            max_query_retries = 3
            for attempt in range(max_query_retries):
                try:
                    pytrends.build_payload(batch, cat=0, timeframe="now 1-d", geo="IN", gprop="")
                    data = pytrends.interest_over_time()
                    for kw in batch:
                        if not data.empty and kw in data.columns:
                            latest_val = data[kw].iloc[-1]
                            trends_raw[kw] = float(latest_val)
                    batch_success = True
                    break
                except Exception as e:
                    batch_error_msg = str(e)
                    logger.warning(f"Google Trends query attempt {attempt+1} failed: {e}")
                    if attempt < max_query_retries - 1:
                        time.sleep(2 ** attempt + random.uniform(0.1, 0.5))
            
            if not batch_success:
                # Fallback to Google News RSS counts
                for kw in batch:
                    news_res = check_news_rss(kw)
                    if news_res.status == "healthy":
                        trends_raw[kw] = max(1.0, news_res.raw_value)
                        trends_status[kw] = "healthy"
                        trends_error[kw] = "Trends rate-limited; failover to News RSS"
                    else:
                        trends_status[kw] = "error"
                        trends_error[kw] = batch_error_msg
    else:
        for kw in keywords:
            news_res = check_news_rss(kw)
            if news_res.status == "healthy":
                trends_raw[kw] = max(1.0, news_res.raw_value)
                trends_status[kw] = "healthy"
                trends_error[kw] = "TrendReq init failed; failover to News RSS"
            else:
                trends_status[kw] = "error"
                trends_error[kw] = "TrendReq initialization failed"

    for kw in keywords:
        raw_val = trends_raw.get(kw, 0.0)
        norm_val = raw_val / 10.0
        results.append(
            SocialHarvestResult(
                topic=kw,
                source="google_trends",
                raw_value=raw_val,
                normalized_value=norm_val,
                status=trends_status[kw],
                source_url="https://trends.google.com",
                error_message=trends_error[kw]
            )
        )
    return results


def check_news_rss(keyword: str) -> SocialHarvestResult:
    """
    Checks news mentions of a keyword using Google News RSS search centered on India.
    """
    encoded_kw = urllib.parse.quote(keyword)
    url = f"https://news.google.com/rss/search?q={encoded_kw}&hl=en-IN&gl=IN&ceid=IN:en"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"}
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


def calculate_social_velocity(recent_mentions: float, baseline: float = None) -> float:
    """
    Calculates the Velocity Metric (V_t) by dividing current mentions by historical baseline.
    """
    effective_baseline = 10.0 if baseline is None else baseline
    if effective_baseline <= 0:
        return 1.0
    return recent_mentions / effective_baseline


def analyze_text_sentiment(text: str) -> Tuple[float, str]:
    """
    Analyzes corporate sentiment using TextBlob and returns impact projections.
    """
    if not text:
        return 0.0, "NEUTRAL"
    analysis = TextBlob(text)
    polarity = float(analysis.sentiment.polarity)
    
    if polarity > 0.15:
        projection = "BULLISH"
    elif polarity < -0.15:
        projection = "BEARISH"
    else:
        projection = "NEUTRAL"
        
    return polarity, projection


def fetch_wikipedia_pageviews(topic: str) -> float:
    """
    Fetches Wikipedia pageviews for a topic over the last 24 hours.
    Uses unauthenticated, public Wikimedia REST APIs as an unblocked secondary search velocity proxy.
    """
    try:
        # 1. Search Wikipedia to locate the exact page title
        encoded_query = urllib.parse.quote(topic)
        search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={encoded_query}&limit=1&format=json"
        headers = {"User-Agent": "TrendPulse/1.0 (contact: admin@trendpulse.org)"}
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=5) as response:
            search_res = json.loads(response.read().decode("utf-8"))
            if len(search_res) > 1 and search_res[1]:
                page_title = search_res[1][0]
            else:
                page_title = topic
        
        # 2. Query daily pageviews for the article
        from datetime import datetime, timedelta
        today_str = datetime.now().strftime("%Y%m%d")
        yesterday_str = (datetime.now() - timedelta(days=1)).strftime("%Y%m%d")
        
        encoded_title = urllib.parse.quote(page_title.replace(" ", "_"))
        views_url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{encoded_title}/daily/{yesterday_str}/{today_str}"
        
        req_views = urllib.request.Request(views_url, headers=headers)
        with urllib.request.urlopen(req_views, timeout=5) as response_views:
            views_res = json.loads(response_views.read().decode("utf-8"))
            items = views_res.get("items", [])
            if items:
                return float(items[-1].get("views", 0.0))
    except Exception as e:
        logger.warning(f"Wikipedia Pageviews lookup failed for '{topic}': {e}")
    return 0.0
