# Changelog

## [2026-06-07T12:45:00+05:30]
- Consolidated phonetic matching pipeline: deleted the unused Soundex (`phonetic_secondary`) column from `backend/app/models.py`, calculations from `backend/app/analytics/matching.py`, and database seeds from `backend/seed.py`.
- Replaced `Levenshtein` package dependency with jellyfish built-in `jellyfish.levenshtein_distance` to consolidate dependencies.
- Enforced clean background poller thread termination by implementing a `threading.Event()` shutdown handle in `backend/app/ingestion/poller.py` and hooking it to FastAPI's lifespan exit in `backend/app/main.py`.
- Files affected:
  - `backend/app/analytics/matching.py`
  - `backend/app/models.py`
  - `backend/seed.py`
  - `backend/app/ingestion/poller.py`
  - `backend/app/main.py`
  - `backend/requirements.txt`
  - `backend/tests/test_matching.py`

## [2026-06-07T12:30:00+05:30]
- Refactored `run_ingestion` in `backend/app/ingestion/poller.py` into distinct private functions `_fetch_seeded_entities`, `_fetch_external_trends_data`, `_calculate_meme_alerts`, and `_persist_alerts_batch` to deconstruct the monolithic ingestion engine.
- Wrapped database upsert operations inside `_persist_alerts_batch` in an isolated SQL transaction context manager (`with write_db.begin():`) to guarantee atomicity and prevent concurrency locks.
- Exposed the static API Key verification token in `frontend/src/components/Dashboard.jsx` using `import.meta.env.VITE_API_KEY || 'dev_secret_key_123'` to allow environment-independent configuration.
- Removed the manual `/api/test-match` endpoint from `backend/app/api/routes.py` and `MatchRequest` schema from `backend/app/schemas.py` to eliminate duplicate logic and reduce codebase size.
- Cleaned up unused/dead configurations (`UPSTOX_API_KEY`, `UPSTOX_API_SECRET`, and `APIFY_API_TOKEN`) from `backend/app/config.py`.
- Made database engine creation and WAL mode execution flexible and SQLite-only in `backend/app/database.py` to support serverless PostgreSQL.
- Files affected:
  - `backend/app/ingestion/poller.py`
  - `backend/app/api/routes.py`
  - `backend/app/schemas.py`
  - `backend/app/config.py`
  - `backend/app/database.py`
  - `frontend/src/components/Dashboard.jsx`

## 2026-06-07
- Integrated frontend with backend REST API and implemented manual ingestion triggering
- Developed a robust in-memory background scanner for Google Trends and Reddit keywords (`backend/app/ingestion/poller.py`)
- Created a Reddit JSON API parser in `backend/app/ingestion/social.py` to extract mentions weighted by engagement
- Secured the `/api/ingest` endpoint in `backend/app/api/routes.py` and integrated it with frontend fetch headers
- Refactored database transaction logic in `backend/app/ingestion/poller.py` to decouple SQLite sessions from slow, blocking network queries
- Configured CORSMiddleware in `backend/app/main.py` with `allow_credentials=False` to fix wildcard origins validation conflicts
- Optimized phonetic matching loop in `backend/app/analytics/matching.py` by retrieving pre-calculated database keys instead of generating Metaphone keys dynamically on the fly
- Upgraded the frontend UI with premium dark aesthetics, micro-animations, glassmorphic metrics, and detailed scoring breakdowns (`frontend/src/components/Dashboard.jsx`, `AlertCard.jsx`, `MetricsGrid.jsx`, `index.css`)
- Dynamically joined ticker metadata in `backend/app/schemas.py` and optimized the `/api/alerts` endpoint in `backend/app/api/routes.py` using a single SQL outer join query to eliminate N+1 database querying overhead and trigger liquidity warnings for micro-cap stocks
- Created `render.yaml` Blueprint specification at the project root and `vercel.json` SPA routing configuration in the `frontend/` directory to prepare for one-click deployments

## 2026-05-28
- Created project folder structure
- Configured `.env` and `.env.example`
- Created `requirements.txt` with required dependencies
- Set up SQLite database connection in `backend/app/database.py`
- Defined database models in `backend/app/models.py`
- Added configuration using Pydantic settings in `backend/app/config.py`
- Created phonetic and string similarity engine in `backend/app/analytics/matching.py`
- **Fixed test regression**: Updated `matching.py` to correctly evaluate first-word phonetic matching, allowing instances like "Signal Messenger" and "Signal Advance" to properly align based on common primary words.
- Created data ingestion mocks in `backend/app/ingestion/social.py` and `backend/app/ingestion/market.py`
- Created meme score calculator in `backend/app/analytics/scorer.py`
- Created FastAPI endpoints and schemas in `backend/app/api/routes.py` and `backend/app/schemas.py`
- Set up FastAPI app entry in `backend/app/main.py`
- Built frontend layout using React, Vite, and Tailwind in `frontend/src/`
- Added Dockerfile for frontend and backend
- Created docker-compose.yml for orchestration
- Written seeding and testing scripts (tests passing 3/3).
