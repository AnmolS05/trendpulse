# Execution-Ready Action Plan: TrendPulse (MVP)

---

## 1. PROJECT UNDERSTANDING

### Goal
Build a low-overhead, automated ingestion pipeline that monitors social media trends, maps them to public equities via a phonetic and semantic mapping engine (to capture retail "mistaken identity" anomalies), validates these trends against active market volume spikes, and alerts momentum traders.

### Target Users
*   **Retail Momentum Traders:** Looking for early speculative volume surges on illiquid micro-caps driven by viral misunderstandings.
*   **Risk Managers / Short Sellers:** Needing to flag irrational sentiment shifts on illiquid tickers to manage portfolio risk.

### Core Problem
Social media trends can trigger rapid, irrational buying of listed stocks due to phonetic similarity or brand confusion (e.g., *Parle Industries* rallying when the unlisted *Parle Products* was featured in a viral news story [1.1.1, 1.1.6]). Existing tools do not map unlisted brands to listed confusion tickers, nor do they combine this analysis with live financial volume anomalies.

### Success Criteria
*   **Low Latency:** Generate speculative alerts within 30 minutes of a social trend spike.
*   **High Precision:** Maintain a false-positive mapping rate below 25% for phonetic alignments.
*   **Cost-Efficient Execution:** Keep the operating infrastructure run-rate below $50/month for the MVP.

---

## 2. MVP BREAKDOWN

To maximize launch speed and contain costs, we bypass complex multimodal video parsing and dedicated GPU clusters. We focus strictly on text-heavy metadata, phonetic algorithms, and on-demand APIs.

```
┌────────────────────────────────────────────────────────────────────────┐
│                              MVP SCOPE                                 │
├────────────────────────────────────────┬───────────────────────────────┤
│ MUST HAVE (v1)                         │ SHOULD HAVE                   │
│ • Text-only metadata ingestion         │ • Automated Instagram scraper │
│ • SQLite phonetic mapping DB           │ • WebSocket live price streams│
│ • Hourly stock anomaly poller          │ • Celery background workers   │
│ • Static dashboard with Meme Scores    │ • Discord/Telegram Alerts     │
├────────────────────────────────────────┼───────────────────────────────┤
│ NICE TO HAVE                           │ REMOVE FOR NOW                │
│ • Video audio Whisper ASR              │ • Auto-execution trading bot  │
│ • OCR keyframe reading                 │ • Multi-GPU dedicated cluster │
│ • Llama-3-8B local inference           │ • Real-time order book depth  │
└────────────────────────────────────────┴───────────────────────────────┘
```

---

## 3. SYSTEM DESIGN

A solo developer can build and deploy this entire architecture on a single, low-cost virtual private server (VPS).

```
                      +-----------------------------+
                      |       Ingestion Cron        |
                      | (Reddit/Google Trends/Apify)|
                      +--------------+--------------+
                                     |
                                     v
+-------------------------+   +------+------+   +--------------------------+
|  Stock Price API        |-->|  FastAPI    |<--| SQLite DB                |
|  (Alpaca / Upstox API)  |   |  Backend    |   | (Tickers & Phonetics)    |
+-------------------------+   +------+------+   +--------------------------+
                                     |
                                     v
                      +--------------+--------------+
                      |       React Dashboard       |
                      |      (Vite + Tailwind)      |
                      +-----------------------------+
```

### Frontend
*   **Stack:** React (Vite) + Tailwind CSS + Lucide React (for iconography).
*   **Design:** A clean, single-page dashboard displaying the speculative alert feed, historical trending tickers, dynamic "Meme Scores," and volume indicators.

### Backend
*   **Stack:** FastAPI (Python 3.11+).
*   **Background Processing:** FastAPIs built-in `BackgroundTasks` for scraping and calculations, avoiding the compute and setup overhead of Celery and Redis in v1.

### Database
*   **Database:** SQLite.
*   **Schema Design:** A single relational file storing tickers, brands, historical trend counts, and calculated scores. Phonetic values are stored as pre-calculated Double Metaphone strings for instant SQL indexing.

### APIs
*   **Social Data:** Apify (X and Instagram metadata scraper APIs).
*   **Trend Data:** PyTrends (Google Trends Python wrapper).
*   **Financial Data:** Alpaca API (US Markets) or Upstox/Kite Connect (Indian Markets) [1.3.1, 2.1.5, 2.2.1].

### Authentication
*   **Security:** Simple static API Key header authentication (`X-API-KEY`) for write endpoints. The frontend operates with read-only access to prevent manipulation of the scoring indicators.

### Deployment
*   **Target:** Single VPS instance (e.g., $10 Hetzner Cloud or DigitalOcean droplet).
*   **Containerization:** Fully containerized setup utilizing Docker Compose.

### AI/Agent Architecture (Cost Sparing)
*   Instead of calling expensive LLM APIs for metadata analysis, the MVP utilizes local Python algorithms:
    *   **Double Metaphone:** For phonetic matching [1.1.1].
    *   **Levenshtein Distance:** For text-similarity scoring [1.1.1].
    *   **TextBlob / VADER:** For lightweight, CPU-friendly sentiment analysis of captions and comments.

---

## 4. TASK BREAKDOWN

| Task ID | Task Name | Dependencies | Difficulty (1–10) | Estimated Time |
| :--- | :--- | :--- | :--- | :--- |
| **T1** | Core Repository Setup & Containerization Config | None | 2 | 2 Hours |
| **T2** | SQLite Database Schema and Seed Data (Phonetics & Tickers) | T1 | 3 | 4 Hours |
| **T3** | Phonetic & Brand-to-Ticker Link Engine Implementation | T2 | 5 | 6 Hours |
| **T4** | Social Ingestion Scripts (Google Trends, Reddit, & Scrapers) | T1 | 4 | 8 Hours |
| **T5** | Market Data Polling & Volume Anomaly Detector | T2 | 5 | 6 Hours |
| **T6** | Meme Score Aggregator Engine | T3, T4, T5 | 6 | 8 Hours |
| **T7** | FastAPI Backend REST Interface | T6 | 3 | 6 Hours |
| **T8** | React + Tailwind CSS Front-End Dashboard | T7 | 4 | 12 Hours |
| **T9** | System Integration, Verification, and VPS Deployment | T8 | 5 | 8 Hours |

---

## 5. DEVELOPMENT ORDER

```
Step 1: Database & Mapping Engine (T1, T2, T3)
  └── Establish repository, seed local stock names, and build phonetic parsing.
Step 2: Data Gatherers (T4, T5)
  └── Build ingestion logic for Google Trends, Reddit feeds, and Alpaca/Upstox API data.
Step 3: Analytics Core (T6)
  └── Implement the scoring formula combining social velocity and volume anomalies.
Step 4: API Backend (T7)
  └── Wrap SQLite and analytical functions inside clean FastAPI routes.
Step 5: Frontend Interface (T8)
  └── Develop the single-page dashboard with Tailwind to expose the alerts.
Step 6: Live Deployment (T9)
  └── Deploy the app on a single Docker container to a cheap VPS.
```

---

## 6. AGENT EXECUTION PLAN

For developers utilizing AI coding assistants (such as Cursor, Claude, or Copilot), use this execution roadmap:

### Agent 1: Schema & Match Specialist
*   **Input:** Tickers seed data + Phonetic requirements (Levenshtein & Double Metaphone logic).
*   **Output:** `models.py` (SQLite schema definitions) + `matching_engine.py` (matching class).
*   **Validation:** Verify that running `find_similar("Melody")` correctly returns `Parle Industries` based on phonetic proximity.

### Agent 2: Social & Market Harvester
*   **Input:** PyTrends integration pattern + Alpaca/Upstox ticker poller logic.
*   **Output:** `ingestion/social_harvester.py` + `ingestion/market_poller.py`.
*   **Validation:** Run standalone scripts to verify data inserts into local SQLite tables without throwing network errors.

### Agent 3: Formula Integrator
*   **Input:** Meme score math specifications + SQLite engine access patterns.
*   **Output:** `analytics/meme_scorer.py`.
*   **Validation:** Mock inputs of high social velocity and 3x volume spikes, confirming that the output score resolves correctly to high-priority categories.

### Agent 4: Backend API Builder
*   **Input:** FastAPI setup instructions + Scorer query references.
*   **Output:** `main.py` + `api/routes.py`.
*   **Validation:** Hit local endpoints (`curl http://localhost:8000/api/alerts`) to verify correct JSON schema serialization.

### Agent 5: Frontend UI Builder
*   **Input:** Tailwind styling UI sketches + API endpoints configuration.
*   **Output:** Complete React code containing `App.jsx`, `AlertCard.jsx`, and charting elements.
*   **Validation:** Verify dashboard renders correctly without errors and updates elements when mocked HTTP endpoints return dummy values.

---

## 7. FILE/FOLDER STRUCTURE

```
trendpulse/
├── .github/
│   └── workflows/
│       └── deploy.yml          # Basic CI/CD Pipeline
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py             # FastAPI entrypoint
│   │   ├── config.py           # Environment configurations
│   │   ├── database.py         # SQLite connection setup
│   │   ├── models.py           # SQLAlchemy / SQLModel schema definitions
│   │   ├── schemas.py          # Pydantic request/response models
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   └── routes.py       # REST API endpoints
│   │   ├── analytics/
│   │   │   ├── __init__.py
│   │   │   ├── matching.py     # Metaphone & Levenshtein matching
│   │   │   └── scorer.py       # Calculates "Meme Score"
│   │   └── ingestion/
│   │       ├── __init__.py
│   │       ├── social.py       # Scrapers for Google Trends / Reddit
│   │       └── market.py       # Market polling logic
│   ├── tests/
│   │   ├── test_matching.py
│   │   └── test_scorer.py
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── assets/
│   │   ├── components/
│   │   │   ├── AlertCard.jsx   # Card displaying triggered tickers
│   │   │   ├── Dashboard.jsx   # Main interface layout
│   │   │   └── MetricsGrid.jsx # Summary values showing active triggers
│   │   ├── App.jsx
│   │   ├── index.css
│   │   └── main.jsx
│   ├── Dockerfile
│   ├── package.json
│   ├── tailwind.config.js
│   └── vite.config.js
├── docker-compose.yml          # Combines Frontend + Backend
├── .env.example                # Template for environment keys
└── README.md
```

---

## 8. RISKS

### 1. Technical Risk: Scraper Invalidation
*   *Detail:* Platforms like X and Instagram change their frontends frequently, which can break unauthenticated DOM scraping scripts.
*   *Mitigation:* Use structured RSS feeds (such as Google Trends RSS) and Reddit JSON API endpoints (`/r/wallstreetbets/hot.json`) as our primary reliable signals, relying on third-party proxies only as a secondary enhancement.

### 2. Scope Risk: Compute Cost Escalation
*   *Detail:* Attempting to parse video media reels on low-cost hardware will cause execution timeouts and run-out-of-memory errors.
*   *Mitigation:* Ban all automated video downloads in the MVP codebase. Process only text titles, descriptions, hashtags, and comments.

### 3. Scaling Risk: SQLite Write Blocking
*   *Detail:* Concurrent write operations from the scraper and the market data engine can cause SQLite database locking errors.
*   *Mitigation:* Configure SQLite in WAL (Write-Ahead Logging) mode and specify a connection timeout limit of 30 seconds inside database configuration scripts.

---

## 9. TESTING PLAN

### Unit Testing
*   **Target:** `backend/app/analytics/matching.py`
*   **Cases:**
    *   Verify input `"Parle"` matches database entry `"Parle Industries"` (Phonetic validation).
    *   Verify input `"Signal Messenger"` matches `"Signal Advance"` (Name similarity validation).
    *   Verify generic terms (e.g., `"The"`, `"Company"`) are filtered out to prevent false matches.

### Integration Testing
*   **Target:** `backend/app/ingestion/market.py`
*   **Cases:**
    *   Mock stock API payloads to verify the processing code correctly identifies volume increases exceeding 3 standard deviations.
    *   Test standard error boundaries when API keys are invalid or networks timeout.

### End-to-End Testing (E2E)
*   **Target:** Full system execution run.
*   **Process:** Inject a mock social trend (`"Melody Chocolate"`) and a simulated stock volume spike into the database. Verify that calling the API output endpoint `/api/alerts` correctly lists the mapping anomaly alert with its calculated score.

### Edge Cases Checked
*   **Market-Closed Behavior:** Ensure the volume analyzer defaults safely during weekends, holidays, or off-market hours without generating false alert signals.
*   **Common Term Conflicts:** Prevent generic terms (e.g., `"Target"`, `"Best Buy"`, `"Crown"`) from triggering system-wide alerts unless volume surges are exceptionally high.

---

## 10. DAILY EXECUTION PLAN

```
┌────────────────────────────────────────────────────────────────────────┐
│                        14-DAY EXECUTION TIMELINE                       │
├────────────────────────────────────────────────────────────────────────┤
│ DAY 1-2   : Project Initialization, Database Schema Setup & Seed Data  │
│ DAY 3-5   : Write Ingestion Scripts (Google Trends, Reddit, & RSS)     │
│ DAY 6-7   : Integrate Stock Market APIs (Volume & Price Fetchers)      │
│ DAY 8-9   : Implement Scorer Logic (Phonetic & Score Algorithms)       │
│ DAY 10    : Expose REST Endpoints via FastAPI Server                   │
│ DAY 11-12 : Build Dashboard Frontend using React and Tailwind CSS      │
│ DAY 13    : Conduct System Testing, Fix Bugs & Configure Docker Files  │
│ DAY 14    : Deploy Live Application to VPS Host Container              │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 11. FIRST ACTION

Open a terminal on your workstation and construct the workspace layout exactly as shown below:

```bash
mkdir -p trendpulse/{backend/app/{api,analytics,ingestion},backend/tests,frontend/src/components}
touch trendpulse/backend/app/{main.py,config.py,database.py,models.py,schemas.py}
touch trendpulse/backend/app/analytics/{matching.py,scorer.py}
touch trendpulse/backend/app/ingestion/{social.py,market.py}
touch trendpulse/docker-compose.yml
```

**STOP: Do not write any more code until this directory structure is created and you have configured your environment configuration file (`.env`).**