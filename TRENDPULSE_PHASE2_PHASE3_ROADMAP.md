# TrendPulse Phase 2 and Phase 3 Senior Dev Action Plan

Date: 2026-06-07

## Purpose

This document turns the current TrendPulse reliability concerns into an execution-ready action plan.

Current assessment:

TrendPulse is not reliably a real future-trend analyzer right now. The project has the skeleton for live analysis, but current behavior is partly demo/simulated.

The next work should be split into:

- **Phase 2:** Make TrendPulse trustworthy, evidence-backed, and non-simulated.
- **Phase 3:** Add the highest-value product features that make TrendPulse genuinely useful, not just impressive-looking.

## Senior Dev Execution Rules

Every task must be performed using this workflow:

1. **Plan**
2. **Code**
3. **Tests**
4. **Edge Cases**
5. **Verify**

Implementation rules:

- Modify only relevant files.
- Avoid unrelated refactors.
- Do not introduce random or fake production signals.
- Keep source-specific failures visible.
- Add tests close to the changed behavior.
- Preserve existing app behavior unless the task explicitly changes it.
- Prefer small, reviewable increments.
- Add proper error handling for external APIs, database writes, and missing configuration.
- Treat API keys, user settings, and source data as security-sensitive.

Required verification for every task:

- Acceptance criteria met.
- No unnecessary code added.
- Proper error handling exists.
- Security considerations reviewed.
- Tests pass.

## Current Problems

### Problem 1: The App Scans Only Seeded Brands

TrendPulse currently checks a small seeded list of brands instead of discovering new trends dynamically.

Current seeded brands:

- Parle Products
- Signal Messenger
- Melody Chocolate

Impact:

The app cannot reliably detect arbitrary future trends unless those trend names already exist in the database.

Relevant files:

- `backend/seed.py`
- `backend/app/models.py`
- `backend/app/ingestion/poller.py`

### Problem 2: Social Data Sources Are Fragile

The app attempts to use Google Trends and Reddit, but those sources can fail due to rate limits or blocking.

Observed risks:

- Google Trends can return rate-limit errors.
- Reddit unauthenticated JSON can return blocked or forbidden responses.
- Failed sources currently do not create a clear source-health record.

Relevant files:

- `backend/app/ingestion/social.py`
- `backend/app/ingestion/poller.py`

### Problem 3: Random Social Velocity Fallback

If social sources return no usable data, the app can generate random social velocity.

Impact:

Alerts can appear even when no real trend was confirmed.

Relevant file:

- `backend/app/ingestion/poller.py`

### Problem 4: Random Market Volume Fallback

If Alpaca credentials are missing or invalid, market volume surge can be randomly simulated.

Impact:

The UI can show volume surge even when no real market data exists.

Relevant files:

- `backend/app/ingestion/market.py`
- `backend/app/config.py`
- `.env`
- `.env.example`

### Problem 5: No Evidence Trail

Alerts do not store or display the source evidence behind the score.

Missing evidence:

- trend source
- source timestamp
- raw trend value
- normalized trend value
- market data provider
- volume baseline
- latest volume
- supporting URLs
- source failure status

Relevant files:

- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/api/routes.py`
- `frontend/src/components/AlertCard.jsx`
- `frontend/src/components/Dashboard.jsx`

### Problem 6: No Confidence Score

The app has a "Meme Score" but no separate confidence rating.

Impact:

A high score from weak or simulated data can look as trustworthy as a high score backed by real evidence.

Relevant files:

- `backend/app/analytics/scorer.py`
- `backend/app/schemas.py`
- `frontend/src/components/AlertCard.jsx`

### Problem 7: No Historical Baseline

The app does not persist enough trend history to detect whether a topic is truly accelerating.

Needed baselines:

- 1-hour acceleration
- 24-hour baseline
- 7-day baseline
- 30-day baseline

Relevant files:

- `backend/app/models.py`
- `backend/app/ingestion/poller.py`
- `backend/app/analytics/scorer.py`

### Problem 8: Very Small Ticker Universe

The current seeded ticker list is too small for real scanning.

Current seeded tickers:

- PARLE.NS
- SIGL
- BOMBAY.NS
- ZOOM

Relevant file:

- `backend/seed.py`

### Problem 9: Weak False Positive Controls

The app uses phonetic and string similarity, but it needs stronger controls around ambiguity, industry mismatch, liquidity, and generic words.

Relevant file:

- `backend/app/analytics/matching.py`

### Problem 10: No Backtesting

The app does not validate whether generated alerts historically predicted meaningful stock movement.

Impact:

The scoring model has no measured reliability.

## Phase 2: Make TrendPulse Trustworthy

Phase 2 goal:

Convert TrendPulse from a partially simulated prototype into a strict, evidence-backed scanner.

Phase 2 should be completed before adding broader product features.

## Phase 2 Task 1: Add Strict No-Random Mode

### Plan

Add a configuration option that prevents simulated social velocity and simulated market volume from producing production alerts.

Recommended setting:

- `STRICT_REAL_DATA=true`

The default for local development can be explicit, but production-like behavior should be strict.

### Code

Relevant files only:

- `backend/app/config.py`
- `backend/app/ingestion/poller.py`
- `backend/app/ingestion/market.py`
- `.env.example`

Implementation actions:

- Add `STRICT_REAL_DATA` to settings.
- In social scoring, return "insufficient social evidence" instead of random velocity when strict mode is enabled.
- In market validation, return "market data unavailable" instead of random surge when strict mode is enabled.
- Prevent alerts from being persisted when required evidence is missing.
- Preserve optional demo behavior only behind an explicit `ALLOW_SIMULATED_DATA=true` flag if needed.

### Tests

Add or update tests for:

- strict mode blocks random social velocity
- strict mode blocks random market volume
- missing social data creates no alert
- missing market data creates no high-confidence alert
- non-strict/demo mode remains explicitly marked as simulated

Suggested test files:

- `backend/tests/test_poller.py`
- `backend/tests/test_market.py`
- `backend/tests/test_config.py`

### Edge Cases

Handle:

- empty API keys
- placeholder API keys
- failed API requests
- source returns empty response
- source returns malformed data
- partial evidence exists from social but not market
- partial evidence exists from market but not social

### Verify

Acceptance criteria:

- No alert is created from random social velocity in strict mode.
- No alert is created from random market volume in strict mode.
- Missing data is visible as unavailable, not silently simulated.
- No unnecessary code added.
- Proper error handling exists.
- API keys are not logged.
- Tests pass.

## Phase 2 Task 2: Add Evidence Storage

### Plan

Every alert must be traceable to source evidence.

Add data models to store social observations, market observations, and source health.

### Code

Relevant files only:

- `backend/app/models.py`
- `backend/app/schemas.py`
- `backend/app/api/routes.py`
- `backend/app/ingestion/poller.py`
- `backend/app/ingestion/social.py`
- `backend/app/ingestion/market.py`

Suggested models:

- `TrendObservation`
- `MarketObservation`
- `AlertEvidence`
- `SourceHealth`

Suggested fields for `TrendObservation`:

- `id`
- `topic`
- `source`
- `raw_value`
- `normalized_value`
- `observed_at`
- `source_url`
- `metadata_json`

Suggested fields for `MarketObservation`:

- `id`
- `symbol`
- `provider`
- `latest_price`
- `latest_volume`
- `avg_volume`
- `volume_surge`
- `observed_at`
- `metadata_json`

Suggested fields for `SourceHealth`:

- `source`
- `status`
- `last_success_at`
- `last_failure_at`
- `last_error_code`
- `last_error_message`

### Tests

Add tests for:

- evidence rows are stored during successful ingestion
- failed sources update source health
- alert API returns linked evidence
- evidence timestamps are stored correctly
- duplicate evidence does not create duplicate alerts unnecessarily

### Edge Cases

Handle:

- multiple evidence rows for one alert
- duplicate source records
- source success followed by failure
- source failure followed by success
- missing source URL
- very large metadata payloads

### Verify

Acceptance criteria:

- Every alert can be traced to stored evidence.
- API returns evidence or evidence summary with each alert.
- Source health is visible internally.
- No unnecessary schema fields added.
- Proper database transaction handling exists.
- No secrets are stored in evidence metadata.
- Tests pass.

## Phase 2 Task 3: Improve Social Ingestion Reliability

### Plan

Make social data ingestion resilient and auditable.

Do not depend on a single fragile unauthenticated source.

### Code

Relevant files only:

- `backend/app/ingestion/social.py`
- `backend/app/ingestion/poller.py`
- `backend/app/config.py`
- `.env.example`

Implementation actions:

- Add provider-level response objects instead of raw dictionaries only.
- Track success, failure, freshness, and source error.
- Add retries with backoff for rate-limited sources.
- Replace or supplement unauthenticated Reddit JSON scraping with an authenticated client or reliable provider.
- Add at least one additional source option such as RSS, GDELT, Apify, NewsAPI, or StockTwits.

### Tests

Add tests for:

- successful source response
- rate-limited response
- blocked response
- malformed response
- retry behavior
- source health update
- merged social score from multiple sources

### Edge Cases

Handle:

- one source fails while another succeeds
- all sources fail
- source returns duplicated topics
- source returns unrelated topics
- source returns stale data
- source returns extreme values

### Verify

Acceptance criteria:

- Source failure does not create fake trend evidence.
- Source status is trackable.
- Social velocity uses real observations only.
- Errors are logged without secrets.
- No unnecessary provider complexity added.
- Tests pass.

## Phase 2 Task 4: Add Real Market Data Validation

### Plan

Replace random volume simulation with real market data or explicit unavailable status.

Market validation should support multiple providers over time.

### Code

Relevant files only:

- `backend/app/ingestion/market.py`
- `backend/app/config.py`
- `backend/app/models.py`
- `.env.example`

Implementation actions:

- Keep Alpaca support, but require valid credentials.
- Add a provider abstraction so future providers can be added safely.
- Return structured market results with status.
- Store latest volume, average volume, volume surge, latest price, and provider name.
- If data is unavailable, return unavailable status rather than random values.

### Tests

Add tests for:

- valid provider response
- missing credentials
- placeholder credentials
- provider timeout
- malformed provider response
- zero average volume
- unavailable market data in strict mode

### Edge Cases

Handle:

- non-US ticker symbols
- symbols with exchange suffixes such as `.NS`
- market closed
- no bars returned
- zero or null volume
- provider-specific limits
- API timeout

### Verify

Acceptance criteria:

- Market surge is real or explicitly unavailable.
- No random volume is used for production alerts.
- Provider failures are visible.
- API keys are not logged.
- Tests pass.

## Phase 2 Task 5: Add Confidence Score

### Plan

Separate hype intensity from evidence reliability.

"Meme Score" should represent signal intensity. "Confidence Score" should represent how trustworthy the evidence is.

### Code

Relevant files only:

- `backend/app/analytics/scorer.py`
- `backend/app/schemas.py`
- `backend/app/api/routes.py`
- `frontend/src/components/AlertCard.jsx`

Implementation actions:

- Add `confidence_score`.
- Add confidence drivers.
- Add confidence weaknesses.
- Include source count, source freshness, match strength, market evidence, and source agreement.

Suggested confidence factors:

- social evidence present
- market evidence present
- multiple independent sources agree
- topic is fresh
- ticker match is strong
- source health is good
- liquidity is sufficient

### Tests

Add tests for:

- high confidence with complete evidence
- low confidence with partial evidence
- zero confidence with simulated evidence
- stale evidence reduces confidence
- weak match reduces confidence

### Edge Cases

Handle:

- high meme score with low confidence
- low meme score with high confidence
- missing market data
- missing social data
- stale but valid source data
- conflicting source data

### Verify

Acceptance criteria:

- UI clearly separates Meme Score and Confidence Score.
- Low-confidence alerts are not presented as strong signals.
- Confidence calculation is deterministic.
- Tests pass.

## Phase 2 Task 6: Add Historical Baselines

### Plan

Replace fixed or random baselines with observed historical baselines.

### Code

Relevant files only:

- `backend/app/models.py`
- `backend/app/analytics/scorer.py`
- `backend/app/ingestion/poller.py`
- `backend/app/ingestion/social.py`

Implementation actions:

- Store trend observations over time.
- Compute 1-hour, 24-hour, 7-day, and 30-day baselines.
- Calculate social velocity from observed current value versus historical baseline.
- Make baseline windows configurable.

### Tests

Add tests for:

- baseline calculation with enough data
- baseline calculation with insufficient data
- spike detection
- zero baseline handling
- stale observation exclusion

### Edge Cases

Handle:

- first run with no history
- topic appears for the first time
- sudden source outage
- extreme spike
- low-volume but fast-growing trend

### Verify

Acceptance criteria:

- Social velocity is based on historical observations.
- First-run data does not create fake confidence.
- Baseline logic is deterministic.
- Tests pass.

## Phase 2 Task 7: Improve Alert Explanation

### Plan

Every alert should explain why it exists using actual evidence.

### Code

Relevant files only:

- `backend/app/schemas.py`
- `backend/app/api/routes.py`
- `frontend/src/components/AlertCard.jsx`
- `frontend/src/components/Dashboard.jsx`

Implementation actions:

- Add explanation fields to alert response.
- Add evidence summary.
- Add risk summary.
- Show source names and timestamps.
- Avoid language that sounds like investment advice.

### Tests

Add tests for:

- explanation generated from complete evidence
- explanation generated from partial evidence
- explanation avoids unsupported claims
- frontend renders explanation fields safely

### Edge Cases

Handle:

- missing company name
- missing market cap
- missing source link
- stale evidence
- contradictory evidence

### Verify

Acceptance criteria:

- Alert explanation references real data points.
- Explanation is clear and cautious.
- No unsupported prediction language.
- No raw secrets or sensitive metadata displayed.
- Tests pass.

## Phase 2 Done Criteria

Phase 2 is complete when:

- Random fallback alerts are disabled or explicitly labeled as demo-only.
- Every alert has source evidence.
- Market volume is real or explicitly unavailable.
- Social velocity is real or explicitly unavailable.
- Confidence score is separate from Meme Score.
- Historical baselines are used for trend velocity.
- Source health is tracked.
- Frontend displays evidence, confidence, and risk.
- Tests cover normal paths, failure paths, and edge cases.

## Phase 3: Make TrendPulse Genuinely Useful

Phase 3 goal:

Turn TrendPulse into a real market intelligence product that discovers new trends, maps them to possible ticker impact, explains the signal, reduces false positives, and learns from past outcomes.

## Phase 3 Task 1: Add Real Trend Discovery

### Plan

Move beyond seeded brands.

The system should discover trending topics dynamically, then match those topics against the ticker universe.

### Code

Relevant areas:

- new trend discovery service
- `backend/app/ingestion/social.py`
- `backend/app/ingestion/poller.py`
- `backend/app/models.py`

Implementation actions:

- Add `DiscoveredTopic` model.
- Ingest trending terms from multiple sources.
- Normalize and deduplicate topics.
- Track first-seen time, last-seen time, and source count.
- Feed discovered topics into matching.

Potential sources:

- Google Trends daily trends
- Reddit hot and rising posts
- StockTwits trending symbols
- finance news RSS feeds
- GDELT
- Apify
- YouTube or TikTok trend provider
- X/Twitter provider, if available

### Tests

Add tests for:

- new topic discovery
- topic normalization
- duplicate topic merging
- source-specific failures
- discovered topic to ticker matching

### Edge Cases

Handle:

- duplicate topics from multiple sources
- spam topics
- generic words
- non-English topics
- ticker symbols that are normal words
- source returns too many topics

### Verify

Acceptance criteria:

- New topics can enter the system without manual seeding.
- Discovered topics are stored with source evidence.
- Bad or generic topics are filtered.
- No unnecessary ingestion complexity added.
- Tests pass.

## Phase 3 Task 2: Expand Ticker Universe

### Plan

Add broad ticker coverage across target markets.

### Code

Relevant areas:

- ticker import script
- `backend/app/models.py`
- `backend/seed.py`
- admin/config tooling later

Implementation actions:

- Import NASDAQ and NYSE symbols.
- Import NSE and BSE symbols.
- Store sector, industry, exchange, market cap, float, average volume, and active status.
- Refresh ticker universe periodically.

### Tests

Add tests for:

- import parser
- duplicate symbols
- exchange suffix handling
- inactive ticker handling
- phonetic key generation

### Edge Cases

Handle:

- same symbol on multiple exchanges
- missing company name
- missing market cap
- delisted ticker
- symbols with dots, dashes, or suffixes

### Verify

Acceptance criteria:

- Scanner can compare trends against a broad ticker universe.
- Exchange-specific filtering works.
- Bad ticker rows do not break ingestion.
- Tests pass.

## Phase 3 Task 3: Add False Positive Filters

### Plan

Reduce weak alerts caused by name similarity alone.

### Code

Relevant files:

- `backend/app/analytics/matching.py`
- `backend/app/analytics/scorer.py`
- `backend/app/models.py`

Implementation actions:

- Add stronger stopword handling.
- Add industry mismatch penalty.
- Add liquidity threshold.
- Add ambiguity score.
- Add known false positive list.
- Require stronger evidence for weak name matches.

### Tests

Add tests for:

- generic term rejection
- industry mismatch penalty
- ambiguous brand handling
- weak match rejection
- strong match acceptance

### Edge Cases

Handle:

- company names that are common words
- brands that match many tickers
- acronyms
- short brand names
- tickers that are also words

### Verify

Acceptance criteria:

- Weak matches are filtered or downgraded.
- Strong matches still pass.
- Filters are explainable.
- Tests pass.

## Phase 3 Task 4: Add Explainable Alert Reasoning

### Plan

Make every alert understandable to a non-developer.

### Code

Relevant files:

- `backend/app/api/routes.py`
- `backend/app/schemas.py`
- `frontend/src/components/AlertCard.jsx`

Implementation actions:

- Add structured reasoning fields.
- Include top evidence points.
- Explain trend, match, market validation, confidence, and risk.
- Avoid investment advice language.

### Tests

Add tests for:

- full explanation
- partial explanation
- missing evidence explanation
- unsafe wording prevention

### Edge Cases

Handle:

- high hype but low confidence
- weak match but strong social trend
- strong match but no market confirmation
- stale evidence

### Verify

Acceptance criteria:

- Alert reasoning is clear.
- Reasoning is based on stored evidence.
- UI avoids unsupported claims.
- Tests pass.

## Phase 3 Task 5: Add Trend Timeline

### Plan

Show how a signal evolved over time.

### Code

Relevant areas:

- trend observation models
- alert API
- frontend timeline component

Implementation actions:

- Store time-series observations.
- Add API endpoint for alert timeline.
- Display first seen, spike time, market confirmation, and alert creation.

### Tests

Add tests for:

- timeline ordering
- missing events
- multiple source events
- stale event filtering

### Edge Cases

Handle:

- topic disappears
- source outages
- multiple spikes
- delayed market confirmation

### Verify

Acceptance criteria:

- Users can see whether an alert is early, mid-cycle, or late.
- Timeline uses stored evidence.
- Tests pass.

## Phase 3 Task 6: Add News Corroboration

### Plan

Add news context to separate social-only chatter from catalyst-backed events.

### Code

Relevant areas:

- news ingestion service
- evidence models
- alert scoring
- frontend evidence panel

Implementation actions:

- Ingest from RSS, GDELT, NewsAPI, or other providers.
- Match news articles to topics and tickers.
- Store article title, source, URL, published time, and summary.
- Add news-backed confidence boost.

### Tests

Add tests for:

- article ingestion
- topic/article matching
- duplicate article handling
- stale article filtering
- source failure handling

### Edge Cases

Handle:

- syndicated duplicate articles
- unrelated articles with same keyword
- old news resurfacing
- paywalled sources
- misleading titles

### Verify

Acceptance criteria:

- Alerts can show whether they are social-only or news-backed.
- Article links are stored safely.
- Tests pass.

## Phase 3 Task 7: Add Watchlists and Notifications

### Plan

Let users monitor specific symbols, topics, sectors, and exchanges.

### Code

Relevant areas:

- user/watchlist models
- alert filtering
- notification services
- frontend settings

Implementation actions:

- Add watchlist model.
- Add alert threshold settings.
- Add notification integrations such as email, Telegram, Discord, or desktop notifications.
- Add notification history.

### Tests

Add tests for:

- watchlist filtering
- threshold matching
- notification send success
- notification failure handling
- duplicate notification prevention

### Edge Cases

Handle:

- notification provider outage
- duplicate alerts
- user changes threshold
- invalid destination
- rate-limited notification channel

### Verify

Acceptance criteria:

- Users receive only relevant alerts.
- Notification failures are logged and recoverable.
- Secrets are not exposed.
- Tests pass.

## Phase 3 Task 8: Add Risk Dashboard

### Plan

Make risk obvious.

### Code

Relevant files:

- `backend/app/analytics/scorer.py`
- `backend/app/schemas.py`
- `frontend/src/components/AlertCard.jsx`
- dashboard components

Implementation actions:

- Add risk flags.
- Add liquidity risk.
- Add microcap risk.
- Add spread risk.
- Add pump-risk caution language.
- Add market cap and float context.

### Tests

Add tests for:

- risk flag generation
- low-liquidity warning
- microcap warning
- missing risk data
- frontend risk rendering

### Edge Cases

Handle:

- missing float
- missing market cap
- foreign exchange ticker
- market data unavailable
- high volatility but strong liquidity

### Verify

Acceptance criteria:

- UI clearly shows risk.
- Risk does not imply investment advice.
- Tests pass.

## Phase 3 Task 9: Add Backtesting

### Plan

Measure whether alerts historically worked.

### Code

Relevant areas:

- backtesting module
- historical market data ingestion
- scoring reports
- test fixtures

Implementation actions:

- Store alert outcomes.
- Replay historical trends and market data.
- Measure 1-hour, 1-day, 3-day, 7-day, and 30-day outcomes.
- Track precision, recall, average return, drawdown, and false positives.

### Tests

Add tests for:

- historical replay
- outcome calculation
- missing historical data
- scoring weight comparison
- regression report generation

### Edge Cases

Handle:

- market holidays
- missing candles
- delisted symbols
- split adjustments
- survivorship bias

### Verify

Acceptance criteria:

- Scoring model can be evaluated historically.
- Reports identify false positives and weak score weights.
- Tests pass.

## Phase 3 Task 10: Add Admin Panel

### Plan

Allow operators to configure and monitor the system without editing code.

### Code

Relevant areas:

- backend admin endpoints
- frontend admin screens
- config models
- source health views

Implementation actions:

- Add source health page.
- Add API key status page without exposing secrets.
- Add scoring weight configuration.
- Add tracked topic and ticker management.
- Add threshold management.

### Tests

Add tests for:

- admin auth
- settings update
- source health rendering
- invalid config rejection
- secret masking

### Edge Cases

Handle:

- invalid API key format
- admin saves bad threshold
- concurrent config edits
- missing source health
- unauthorized access

### Verify

Acceptance criteria:

- Admin actions are protected.
- Secrets are masked.
- Invalid settings are rejected.
- Tests pass.

## Suggested Implementation Order

### Phase 2 Order

1. Strict no-random mode
2. Evidence storage
3. Source health tracking
4. Social ingestion reliability
5. Real market validation
6. Confidence score
7. Historical baselines
8. Alert explanation UI

### Phase 3 Order

1. Real trend discovery
2. Larger ticker universe
3. False positive filters
4. Explainable alert reasoning
5. Trend timeline
6. News corroboration
7. Watchlists and notifications
8. Risk dashboard
9. Backtesting
10. Admin panel

## Final Acceptance Criteria

TrendPulse should not be considered reliable until these are true:

- Alerts are backed by real source evidence.
- Simulated data cannot silently create production alerts.
- Every alert explains what is trending, what stock matched, why it matched, and what evidence supports it.
- Confidence score is separate from hype score.
- Source failures are visible.
- Market data is real or explicitly unavailable.
- Trend velocity is based on historical baseline.
- False positives are filtered or downgraded.
- Tests cover success paths, failure paths, and edge cases.
- Security-sensitive values are never exposed in logs, API responses, or frontend UI.

## Final Target State

Every TrendPulse alert should answer:

1. What exactly is trending?
2. Which stock may be affected or confused with it?
3. What real evidence supports this signal?
4. How confident is the system?
5. What are the main risks?

Until Phase 2 is complete, TrendPulse should be treated as a prototype scanner, not a reliable real future-trend analyzer.
