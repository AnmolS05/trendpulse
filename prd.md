Product Requirement Document (PRD)

PRD: "TrendPulse" – Multimodal Social Trend & Mistaken Identity Stock Predictor

Document Owner: Lead Product Engineer
Target Audience: Engineering, Data Science, and Quantitative Trading Teams
Status: Draft (Open for Feedback)

1. Executive Summary & Market Context

The convergence of retail trading and viral social media has introduced a
volatile market anomaly: meme-driven name mix-ups. Retail trading volumes are
increasingly influenced by rapid herd mentality, where immediate action often
takes precedence over fundamental research. This behavior manifests in three
distinct patterns of market distortion:

1.  Brand-to-Ticker Confusion (The "Melody" Effect): Social media buzz
    surrounding a consumer product leads retail investors to buy a similarly
    named, but completely unrelated, public company.
      - Example: In May 2026, PM Modi’s viral gift of "Melody" chocolates to
        Italian PM Meloni sparked a rally in the penny stock Parle Industries,
        even though the confectionery is manufactured by the privately-held,
        unlisted company Parle Products.
2.  Literal Name Confusion: A trending news cycle around a brand or technology
    drives volume into an unrelated ticker with a similar name.
      - Example: Elon Musk tweeting "Use Signal" (referencing the private
        messaging app) causing a 1,100% surge in Signal Advance Inc..
      - Example: The work-from-home boom driving surges in Zoom Technologies
        (unrelated) instead of Zoom Video Communications.
3.  Semantic/Theme Overlap: High search volumes for a specific commodity or
    theme cause speculative flows into companies that simply feature the word in
    their name.
      - Example: Bombay Oxygen Investments surging during the oxygen cylinder
        shortage of the 2021 pandemic, despite operating purely as an investment
        firm.

Core Product Objective

TrendPulse aims to build an automated, low-latency pipeline that ingests
high-velocity social media content (specifically Instagram Reels, TikTok, and
X), extracts viral entities, maps them to public markets using a semantic
knowledge graph, and flags early-stage speculative buying pressure on both
direct and "mistaken identity" stocks before they reach their peak.

2. User Personas & Use Cases

  - Momentum & Trend Traders: Looking to capture early-stage retail "meme runs."
    They require rapid alerts identifying which listed tickers are being
    incorrectly linked to viral web trends.
  - Risk Managers & Market Makers: Looking to protect short positions or adjust
    liquidity parameters on illiquid micro-caps experiencing irrational,
    trend-induced order-book spikes.

3. Core Functional Requirements

[Social Media Inputs] -> [Tiered Ingestion Filter] -> [Entity & Phonetic Graph] -> [Order Book Validation] -> [FOMO Alert Engine]

Feature 3.1: Multi-Platform Ingestion & Trend Detection (The Harvester)

Processing raw visual media at scale is computationally and financially
unviable. TrendPulse utilizes a two-tier ingestion strategy to minimize compute
costs:

  - Tier 1 (High-Velocity / Low-Compute Monitoring):
      - Continuous polling of low-overhead text streams: Google Trends RSS, X
        Trending Topics, Reddit Pushshift API, and Instagram Hashtag growth
        metrics (leveraging structured metadata via third-party social listening
        APIs like Brandwatch or RapidAPI proxies to navigate platform rate
        limits).
      - System calculates a Velocity Metric (V_t) for keywords:
        V_t = \frac{\text{Mentions in past 3 hours}}{\text{Average 3-hour baseline over past 7 days}}
  - Tier 2 (High-Compute Multimodal Extraction):
      - When V_t for a specific topic (e.g., #Melodi or Melody Chocolate)
        crosses a predefined threshold, the system triggers targeted media
        extraction.
      - The system pulls a statistically relevant sample of high-engagement
        video assets (Reels, TikToks).
      - It passes the audio through a lightweight ASR model (e.g., Whisper-nano)
        and runs OCR on selected keyframes to capture text overlays and brand
        logos.

Feature 3.2: The Semantic Market Knowledge Graph (The Entity Mapper)

This database maps the relationships between what is trending online and what
can actually be traded on public exchanges. Built on a graph database (e.g.,
Neo4j), it maintains nodes representing:

  - Listed Equities: Globally (e.g., NSE, BSE, NASDAQ, NYSE) with attributes
    such as ticker, official name, aliases, market cap, and average volume.
  - Unlisted Entities & Brands: (e.g., "Parle Products", "Signal Messenger").
  - Relational Edges:
      - DIRECT_OWNER: (e.g., Reliance Industries \rightarrow Jio).
      - PHONETIC_SIMILAR: Generated using Double Metaphone and Levenshtein
        Distance algorithms to capture names that sound alike or look alike
        (e.g., Parle Products [unlisted] \leftrightarrow Parle Industries
        [listed]).
      - SEMANTIC_OVERLAP: Connecting companies based on keywords in their
        business description (e.g., "Oxygen" \rightarrow Bombay Oxygen
        Investments).

Feature 3.3: Real-Time Market Anomaly Engine

Social trends alone do not always translate into financial movement. The system
validates social signals against live trading data via WebSocket feeds (e.g.,
Alpaca or Kite Connect).

  - A background worker continuously monitors mapped tickers generated by the
    Knowledge Graph.
  - An Anomaly Flag is raised if a target ticker experiences:
      - Volume Surge: Volume exceeding 3\sigma (standard deviations) of
        its 20-day Volume Moving Average.
      - Price Velocity: Rapid, multi-minute price increases or hitting early
        upper circuit limits.
      - Order Size Metric: A drop in average order size alongside a surge in
        overall volume, indicating high retail/individual participation rather
        than institutional flow.

Feature 3.4: Predictive FOMO / Meme Probability Score

For every mapped trend-ticker pair, the system generates a dynamic Meme Score
(0–100) indicating the likelihood of a speculative rally:

\text{Meme Score} = (w_1 \cdot \text{Trend Velocity}) + (w_2 \cdot \text{Phonetic/Semantic Link Strength}) + (w_3 \cdot \text{Order Book Volatility}) - (w_4 \cdot \log(\text{Market Capitalization}))

  - Why Market Cap matters: Low-priced, illiquid micro-caps (like Parle
    Industries or Signal Advance) are highly sensitive to retail capital
    inflows, making them much easier to "pump" into upper circuits than highly
    liquid mid- or large-cap stocks. Lower market cap and lower liquidity
    increase the overall meme score.

4. Proposed Technical Architecture & Data Pipeline

  +-------------------------------------------------------------+
  |                      INGESTION LAYER                        |
  |  [X / Reddit / Google Trends API]    [IG / TikTok Proxies]  |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  |                      PROCESSING LAYER                       |
  |      [Celery Task Queue]  --->  [Whisper ASR / OCR]         |
  |      [FastAPI Entity Parser (NER / Llama-3-8B)]             |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  |                      DATABASE LAYER                         |
  |   [Neo4j Knowledge Graph]  <--->  [PostgreSQL (Metadata)]   |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  |                   ANALYTICS & SCORING                       |
  |  [Market Data WebSockets] ---> [Pandas/PySpark Streaming]   |
  |  [Score Calculator (Meme Score Engine)]                     |
  +------------------------------+------------------------------+
                                 |
                                 v
  +-------------------------------------------------------------+
  |                      DELIVERY LAYER                         |
  |             [WebSocket Real-Time Alert UI]                  |
  +-------------------------------------------------------------+

5. Non-Functional Requirements & Key Engineering Constraints

5.1 Compute & Cost Constraints

  - The Challenge: Running open-source LLMs or video transcription services on
    all social media data is financially prohibitive.
  - The Solution: Implement strict cascading analysis. 95% of incoming social
    streams are filtered out using inexpensive, deterministic keyword regex and
    heuristic frequency counts. Deep transformer models (e.g., Llama-3-8B or
    Mistral-7B) and multimodal parsers are only spun up on demand when a
    localized phrase experiences an exponential volume surge.

5.2 API Limits & Scraping Resilience

  - The Challenge: Major social media networks enforce strict rate limits and
    anti-scraping measures.
  - The Solution: The pipeline must not rely on direct scraping of video
    platforms. Instead, it should aggregate data from:
    1.  Official APIs where accessible (Reddit, X, Google Trends).
    2.  Commercial social listening APIs that handle proxy rotation and data
        cleaning at scale.
    3.  Publicly available RSS feeds and web indexes.

5.3 System Latency Target

  - The Challenge: Retail traders on trading apps respond to social trends
    within hours.
  - The Solution: The end-to-end latency—from a trend crossing the Tier 2
    threshold to mapping the entity, validating order-book anomalies, and
    pushing a "Meme Score Alert"—must be targeted at under 15 minutes to remain
    actionable.

6. Strategic Risks & Practical Mitigations

| Risk                                 | Impact                                                                                                                                           | Engineering / Product Mitigation                                                                                                                                                                                                                                                                                    |
| :----------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------- | :------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **High False-Positive Rate**         | Users experience alert fatigue from trends that never translate to market activity.                                                              | **Order-Book Interlocking:** Never issue a high-severity trading alert based solely on social media metrics. A high-priority alert requires both a social trend spike *and* an active volume anomaly in the stock exchange feed.                                                                                    |
| **Market Illiquidity & Slippage**    | Users try to trade illiquid penny stocks experiencing upper circuits and find themselves unable to exit (getting "stuck holding the bag").       | **UI Safeguards:** The interface must feature prominent, real-time liquidity warnings. Stocks with low free-float or consecutive upper circuits should be flagged with an "Exiting Danger" warnings, highlighting that trading such stocks behaves more like speculative betting.                                   |
| **Regulatory & Compliance Scrutiny** | Algorithms analyzing speculative retail behavior can face regulatory hurdles regarding "market manipulation" or "unauthorized financial advice." | **Pure Informational Framing:** The system must strictly position itself as a "Social and Phonetic Trend Analysis Tool," mapping names and visual trends. The application must not issue buy/sell recommendations, and must explicitly state that the name alignments discovered are often irrational or erroneous. |

7. Metrics for Success

  - Detection Latency: Time elapsed between a social trend's first exponential
    pivot and the system's generation of a mapped ticker alert.
  - Mapping Precision: Percentage of generated phonetic/semantic matches that
    are valid, high-probability associations (minimizing irrelevant
    connections).
  - Predictive Value (F-1 Score): Evaluating how accurately a high "Meme Score"
    (>85) correlates with actual subsequent price/volume spikes within the
    next 1–2 trading sessions.
