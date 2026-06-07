# TrendPulse

TrendPulse is an automated, low-latency ingestion and scanning pipeline that monitors social media search velocities (Google Trends, Reddit hot topics), maps them phonetically and semantically to publicly listed equities (to catch retail "mistaken identity" anomalies), validates them using volume surges, and generates momentum alerts.

---

## Repository Structure

```text
trendpulse/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   └── routes.py       # API endpoints (Alert feed, manual trigger)
│   │   ├── analytics/
│   │   │   ├── matching.py     # Metaphone & Levenshtein similarity engine
│   │   │   └── scorer.py       # Meme Score calculation heuristics
│   │   ├── ingestion/
│   │   │   ├── social.py       # Google Trends and Reddit WSB JSON scrapers
│   │   │   ├── market.py       # Alpaca API volume surge fetcher
│   │   │   └── poller.py       # Background daemon polling & DB writer
│   │   ├── main.py             # FastAPI entrypoint & Lifespan hook
│   │   ├── models.py           # SQLAlchemy SQLite models
│   │   └── database.py         # SQLite connection & WAL mode configuration
│   └── tests/
│       ├── test_matching.py    # Phonetic algorithm unit tests
│       └── test_scorer.py      # Score heuristics unit tests
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.jsx   # Metrics, controls, and alert feed layout
│   │   │   ├── AlertCard.jsx   # Alert info, warnings, and scoring drawers
│   │   │   └── MetricsGrid.jsx # Summary values and active indicators
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── index.css           # Styling directives and custom animations
│   ├── package.json
│   └── vite.config.js
├── docker-compose.yml          # Container orchestration configuration
└── render.yaml                 # Infrastructure Blueprint specification
```

---

## Local Development & Setup

### Prerequisites
*   Python 3.12+
*   Node.js 20+

### 1. Database Initialization
From the `backend/` directory, run the seeding script to initialize the tables and seed default equities:
```bash
cd backend
python seed.py
```

### 2. Launch Backend API
Install requirements and start the FastAPI uvicorn server:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```
The API documentation is available at `http://127.0.0.1:8000/docs`.

### 3. Launch Frontend Client
From the `frontend/` directory, install dependencies and start the Vite dev server:
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## Verification & Testing

### Run Backend Tests
Run pytest from the `backend/` folder:
```bash
cd backend
python -m pytest
```

### Manual Ingestion Sync
Trigger a manual social metadata scan via `curl` (secured by API key verification):
```bash
curl -X POST -H "X-API-KEY: dev_secret_key_123" http://127.0.0.1:8000/api/ingest
```
Check the feed again at `GET http://127.0.0.1:8000/api/alerts`.
