# DOs AND DON'Ts — TrendPulse

## Project Goal (1–3 lines)
Build a low-latency pipeline to identify trending brand and theme spikes, map them phonetically or semantically to confused public equities, and validate using market volume indicators to alert traders *before* speculative flows hit their 24-hour peak.

---

# ✅ DO

## Product
*   **Prioritize Text-Only Metadata:** Focus strictly on parsing titles, descriptions, hashtags, and top comments. Text represents 90% of the semantic value for 5% of the compute cost.
*   **Implement Hard Market Validation:** Every generated alert must require an active order-book volume trigger ($\ge 2\sigma$ volume anomaly) before escalation.
*   **Expose Scoring Heuristics:** Clearly present the raw components of the Meme Score (trend velocity, brand similarity, stock liquidity) to the user to foster product trust.

## Engineering
*   **Use SQLite in WAL Mode:** Keep database setup trivial for the solo developer while handling concurrent read-write flows with a defined 30-second connection timeout.
*   **Keep Calculations Deterministic:** Write the matching algorithms (Double Metaphone + Levenshtein Distance) as simple, synchronous, unit-tested Python functions.
*   **Verify API Limits Aggressively:** Implement strict error boundaries and fallbacks on third-party scrapers and market data pullers to gracefully handle rate-limit hits.

## AI / Agent Usage
*   **Scaffold and Boilerplate:** Use AI agents to quickly generate standard FastAPI endpoint structures, database schema definitions, and repetitive Tailwind CSS configurations.
*   **Isolate Code Verification:** Run all agent-generated code locally with isolated test inputs before integrating it into the core pipeline.
*   **Review Scraping Selectors:** Manually review and verify all agent-generated CSS/DOM selectors used in social scraping loops, as these are highly prone to hallucination.

## UX
*   **Maintain a Mobile-First, Single-Page Layout:** Design for fast scanning on mobile browsers, as momentum traders frequently monitor feeds on the go.
*   **Display Liquidity Warnings:** Visually flag low free-float or micro-cap stocks with clear color-coded warning badges to alert users of extreme slippage risk.
*   **Keep the Alert Card Actionable:** Show the core trigger loop immediately: *Trending Brand Name* $\rightarrow$ *Phonetic Conflict* $\rightarrow$ *Confused Ticker Name*.

## Performance
*   **Limit E2E Pipeline Latency:** The pipeline must ingest a trending signal, resolve its ticker target, check volume changes, and publish the alert in **under 15 minutes**.
*   **Minimize Page Load Times:** Keep First Contentful Paint (FCP) below 1.2 seconds by serving static assets with gzip/brotli compression.
*   **Keep Backend Latency Low:** Restrict backend FastAPI endpoint response times to less than 150ms for normal read queries.

## Growth
*   **Evaluate Every Choice by User Value:** Prioritize engineering efforts strictly based on their direct impact on our core metrics:
    *    Activation (viewing a scoring breakdown within 48h)
    *    Retention (users returning weekly to verify alerts)
    *    Revenue (upgrading to premium Telegram alerts)
    *    User value (Actionable Alert Lead Time $\ge 45$ minutes)

---

# ❌ DON'T

## Product
*   **No Raw Video Processing:** Reject automated video downloads, audio transcoding, and Whisper transcribing for the MVP. It increases compute costs beyond our target budget.
*   **No Automated Trading Features:** Do not build brokerage APIs, automated buy/sell routing, or custom trading execution bots in v1.
*   **No Complex Portfolio Tracking:** Avoid building generic investment portfolios, PnL analytics, or performance tracking dashboards.

## Engineering
*   **No Premature Database Scale:** Reject Neo4j Aura Pro or hosted PostgreSQL clusters for launch. Do not spin up managed cloud databases until local SQLite limits are reached.
*   **No Redundant Distributed Queues:** Avoid Celery, Redis, and message broker setups for the MVP. Run asynchronous scraping jobs inside FastAPI's lightweight, in-memory `BackgroundTasks`.
*   **No Heavy Monolithic Packages:** Avoid importing generic, resource-heavy NLP packages (such as large SpaCy models or unquantized PyTorch networks) onto the application server.

## AI
*   **No Blind Code Pasting:** Never copy agent-generated code directly into core directories without a detailed human line-by-line validation.
*   **No Unverified Regular Expressions:** Reject AI-generated scraping regex patterns without running them against at least 10 real-world string inputs.
*   **No Automated Core Math Edits:** Do not let agents edit the mathematical formulas governing the "Meme Score" calculation without explicit developer approval.

## UX
*   **No Multi-Page Wizards:** Do not implement multi-step onboarding processes, registration flows, or interactive profile setups.
*   **No Obscure Dropdowns:** Avoid burying critical calculation metrics or phonetic matching confidence ratings under deeply nested user menus.
*   **No Chat Interface Hype:** Reject adding "AI Conversational Trading Assistants" or conversational search interfaces.

## Analytics
*   **No Vanity Indicators:** Do not optimize for cumulative website page views, overall user registrations, or newsletter subscribers.
*   **No Excessive Tracking Scripts:** Avoid installing multiple, overlapping analytics SDKs that bloat client-side bundle sizes and slow down load speeds.

---

## Decision Filter

Before writing any new feature code, ask yourself:

1. Does this directly help users find speculative brand-to-ticker mix-ups?
2. Will a standard user notice and value this feature within 30 seconds of landing on the site?
3. Can the MVP launch and function successfully without this feature?
4. Does adding this feature increase our monthly database, compute, or maintenance burden?
5. Can an AI coding assistant generate and validate this feature safely in less than one day?

*If you answer **NO** to 3 or more of these questions, reject the feature immediately.*

---

## Red Flags

**Stop development immediately and re-evaluate if:**
*   The system codebase double-counts scope, expanding into a generic social listening or generic trading app.
*   You find yourself repeatedly changing backend configurations or modifying API schemas to support a feature.
*   The core build and containerization packaging step exceeds the 14-day development plan.
*   Our phonetic mapping precision metric drops below 60% during local integration testing.
*   Active beta users log in once to examine the page but do not return within the next 7 days.

---

## Launch Rules

### Must Have:
*   Local SQLite database seeded with at least 5,000 public equities and common unlisted consumer brand associations.
*   Working phonetic mapping engine matching similar sounding strings inside SQLite.
*   Hourly stock market volume anomaly polling service (Alpaca / Upstox API).
*   One-page dashboard UI listing matched alerts sorted by calculated Meme Score.

### Must NOT Have:
*   Live video transcoding or Whisper ASR pipelines.
*   Real-time broker connectivity or order execution triggers.
*   Managed multi-instance cloud deployments (AWS ECS, RDS).

### Definition of Done:
*   Codebase builds cleanly via `docker-compose up --build` on a fresh, clean server instance.
*   Standalone unit tests for the phonetic Metaphone matching engine pass at 100%.
*   A simulated end-to-end event (injecting a mock brand spike and volume trigger) correctly surfaces a formatted alert card in under 1 second.

---

## Final Principle

> "Build less.  
> Launch earlier.  
> Measure faster.  
> Remove aggressively."