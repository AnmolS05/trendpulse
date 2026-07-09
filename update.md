Here is the systematic, technical content for your `update.md` file. It objective, detailed, and directly reflects the structural audit and proposed development roadmap of the TrendPulse system without using overconfident or superlative language.

***

# Technical Update: System Audit, Core Mechanics, and Strategic Roadmap

## 1. System Status & Audit Summary

The TrendPulse platform contains the foundational architectural skeleton for low-latency brand-to-ticker mapping and market validation. However, under its current configuration, the platform does not function as a reliable, live future-trend analyzer. The end-to-end flow relies heavily on fallback simulations and static data pools:

*   **Deployment Status**: The frontend preview responds as expected on `http://localhost:4173/`. During the current audit, the backend API was not reachable on the checked live ports, preventing verified end-to-end validation of the live dockerized networking layer.
*   **Database Constraints**: The local database contains pre-generated/seeded historical alerts mapping specific high-profile confusion cases (e.g., `PARLE.NS` vs. *Parle Products* and `SIGL` vs. *Signal Messenger*).
*   **Third-Party API Barriers**: Live social collection scripts are subject to strict third-party platform limitations. Google Trends requests returned HTTP 429 (rate-limited), and Reddit requests returned HTTP 403 (blocked). Both collectors default to an interest metric of `0.0` upon encountering these blocks.
*   **Volume Fallbacks**: The `.env` file contains placeholder credentials for the Alpaca API. In the absence of active API keys, the stock volume surge calculation falls back to a randomized float simulation.
*   **Target Scope Limitation**: The system is restricted to scanning pre-seeded brands rather than dynamically discovering new internet trends. It monitors only the brands defined in `backend/seed.py` (line 37): *Parle Products*, *Signal Messenger*, and *Melody Chocolate*, comparing them exclusively against the seeded equities defined in `backend/seed.py` (line 25): `PARLE.NS`, `SIGL`, `BOMBAY.NS`, and `ZOOM`.

---

## 2. Core Operational Architecture & Pipeline Flow

The intended design of the system is structured as follows:

1.  **Orchestrated Polling**: The main application loop in `backend/app/main.py` (line 12) initializes a polling background job configured to execute every 600 seconds.
2.  **Social Ingestion**: The harvester in `backend/app/ingestion/social.py` (line 13) attempts to query relative interest from Google Trends, while `social.py` (line 48) pulls the hot posts feed from Reddit's `/r/wallstreetbets`.
3.  **Entity Resolution & Matching**:
    *   `backend/app/analytics/matching.py` (line 11) runs phonetic indexing to extract similar-sounding target keys.
    *   `backend/app/analytics/matching.py` (line 20) evaluates spelling proximity using normalized Levenshtein similarity distance.
4.  **Financial Validation**: `backend/app/ingestion/market.py` (line 34) is designed to pull historical and current market bars from Alpaca. If credential verification fails, `market.py` (line 62) overrides the error and provides a random volume multiplier fallback.
5.  **Meme Probability Scoring**: `backend/app/analytics/scorer.py` (line 26) calculates a weighted predictive score out of 100 based on social trend velocity, semantic link strength, volume surge multiplier, and equity market capitalization.
6.  **Persistence Threshold**: The poller in `backend/app/ingestion/poller.py` (line 115) evaluates the calculated score, writing the generated alert record to the SQLite database only if the score is $\ge 50$.
7.  **Dashboard Presentation**: The frontend `frontend/src/components/AlertCard.jsx` (line 74) displays the "Trending Topic $\rightarrow$ Confused Stock" layout alongside volume surge and velocity metrics.

### Critical Structural Issue
In `backend/app/ingestion/poller.py` (line 91), the system generates a random social velocity whenever real-world trend interest returns zero. Because this is paired with the randomized market volume fallback, the system frequently publishes alert cards that appear analytical to the end-user but are not backed by live social or financial data.

---

## 3. High-Value Strategic Roadmap

To transition TrendPulse from a simulated proof-of-concept into a reliable quantitative tool, the following features are planned for implementation.

### A. Dynamic Trend Discovery
*   **Arbitrary Entity Detection**: Replace the static seeded lists with open-ended entity extraction. Parse Google Trends Daily Trending Search RSS feeds, Reddit Hot/Rising queries, X/Twitter Local Trends, and RSS financial news headlines using lightweight named-entity recognition (NER).
*   **Alternative Finance Data Feeds**: Integrate StockTwits trending streams and general retail finance message boards to identify speculative retail velocity before it translates to search engines.

### B. Reliable Market Data Validation
*   **Multi-Provider Integration**: Replace the randomized simulation with a robust market gateway supporting Alpaca, Polygon.io, or Yahoo Finance fallbacks.
*   **Global Market Coverage**: Expand database schemas and ingestion scripts to query Indian equities via NSE/BSE data providers alongside US markets.
*   **Structural Micro-metrics**: Incorporate active order-book indicators such as free-float percentage, intraday price velocity, bid-ask spread width, and exchange-enforced circuit limits.

### C. Trust & Transparency Features
*   **No-Random Mode**: Implement a strict enforcement configuration in the poller. Under this mode, alerts are suppressed unless they are backed by verifiable, non-zero live data from both social and financial sources.
*   **Explainable Alert Reasoning**: Include descriptive metadata on the alert cards explaining *why* the topic is trending, *how* the phonetic match was resolved, and *why* the volume anomaly is mathematically significant.
*   **Confidence Score Separation**: Disentangle the speculative "Meme Score" from a data-fidelity "Confidence Score." A ticker may exhibit high speculative momentum (Meme Score) but carry a low Confidence Score if the phonetic mapping is loose or if live data is incomplete.

### D. Algorithmic Refinement
*   **Dynamic Historical Baselines**: Track and store multi-day social velocity curves (1-day, 7-day, and 30-day benchmarks) to reliably detect true acceleration spikes and isolate sudden interest surges from baseline seasonal noise.
*   **False-Positive Mitigation**: Establish industry classification filters, Stopword exclusions, and corporate suffix pruning to prevent generic term overlaps (e.g., matching the word "Best" with *Best Buy*) from generating false alarms.
*   **News Corroboration**: Implement a background check that queries Google News or Yahoo Finance RSS feeds to verify if mainstream publications have already identified the underlying catalyst, establishing the lead time of the social spike.

### E. User Utility & Backtesting
*   **Watchlists & Custom Alerts**: Allow users to monitor specific brands or tickers and configure webhook notifications (Telegram, Discord, email, or desktop push alerts) when calculated scores cross a chosen threshold.
*   **Visual Trend Timeline**: Map the temporal evolution of the signal on the frontend (e.g., *Trend Detection* $\rightarrow$ *Social Peak* $\rightarrow$ *Order-Book Spike* $\rightarrow$ *Alert Generation*).
*   **Historical Backtesting Engine**: Maintain historical logs of generated alerts and subsequent stock performance to calculate the empirical accuracy and predictive value (F-1 Score) of the system over variable horizons (e.g., 24h, 48h, 5d).
*   **Risk Mitigation Dashboard**: Flag low-float equities, penny stock structures, and potential pump-and-dump behavior with explicit warning badges on the frontend.
*   **Source Evidence Hyperlinks**: Provide direct outbound links to the underlying evidence (e.g., specific Reddit threads, live Google Trends charts, or financial volume profiles) to allow manual trader verification.

***