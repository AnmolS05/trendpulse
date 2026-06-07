Success Metrics — TrendPulse

1. North Star Metric

Metric: Actionable Alert Lead Time (AALT)

Formula:

\text{AALT} = T_{\text{VolumePeak}} - T_{\text{Alert}}

Where:

  - T_{\text{Alert}} is the timestamp of the system-generated alert (defined by
    a calculated \text{Meme Score} \ge 85 and a validated market volume anomaly
    \ge 2\sigma above the historical baseline).
  - T_{\text{VolumePeak}} is the timestamp of the local 24-hour peak trading
    volume for that flagged ticker.
  - This metric is exclusively computed for validated True Positives (i.e.,
    stocks where actual trading volume reaches \ge 3\sigma within 24 hours of
    the alert).

Target:

\text{AALT} \ge 45 \text{ minutes on } \ge 75\% \text{ of validated alerts.}

Why this matters:

For retail momentum traders, timing is everything. If our system flags a
mistaken identity stock (such as Parle Industries [1.1.1, 1.1.6]) after it has
already locked into an upper circuit or peaked in daily volume, the signal is
useless.

AALT measures our lead-time advantage. A positive AALT of 45 minutes or more
gives users a realistic window to identify the trend, evaluate the
phonetic/semantic confusion, and execute trades before retail volume reaches its
peak saturation point.

2. Product Metrics

Acquisition

  - Metric: Weekly New User Signups (attributed by source).
  - Target: \ge 120 signups per week during the first 60 days post-launch.
  - Tracking Method: PostHog user registration event tracking, filtered by
    referral source parameter (utm_source tracking for platforms like X, Reddit,
    or hacker communities).

Activation

  - Metric: Scored Trend Detail Views (First 48 Hours).
  - Target: \ge 65\% of new signups view the full "Meme Score Breakdown" of at
    least one alert within 48 hours of account creation.
  - Tracking Method: PostHog event logging for the view_alert_details backend
    API call.

Engagement

  - Metric: Weekly Active Users to Monthly Active Users Ratio (WAU/MAU).
  - Target: \ge 35\% (Standard for utility-centric financial tracking
    platforms).
  - Tracking Method: Segmented analytics in PostHog calculating daily active
    interactions (logins, watchlist edits, alert updates) over 7-day and 30-day
    windows.

Retention

  - Metric: Cohort-based Week 4 (W4) User Retention.
  - Target: \ge 20\% retention by Week 4.
  - Tracking Method: PostHog cohort retention table measuring weekly returning
    users who query the active dashboard.
  - Trade-off: We prioritize active dashboard queries over email click-throughs
    to ensure we are retaining users who value our primary live data feed.

Referral

  - Metric: Shared Metric Link Click-Through Rate.
  - Target: \ge 12\% of active users sharing an alert card screenshot or link to
    external trading forums (Reddit, Telegram, X), generating at least 1.5
    click-backs per share.
  - Tracking Method: Dynamic short-URL tracking on shared link payloads
    (domain.com/share/{share_id}).

Revenue (Premium Alert Tier)

  - Metric: Free-to-Paid Conversion Rate (SMS/Telegram instant push
    notifications).
  - Target: \ge 1.5\% conversion rate of active users within 60 days of
    introducing the paywall.
  - Tracking Method: Stripe API billing events (customer.subscription.created)
    correlated with user IDs in our SQLite/PostgreSQL database.

3. Technical Metrics

The system's integrity relies on keeping low-cost VPS instances stable without
crashing during social trend spikes.

| Metric                                      | Target                         | Alert Threshold             | Tracking / Measurement Method                            |
| :------------------------------------------ | :----------------------------- | :-------------------------- | :------------------------------------------------------- |
| **Page Load Time (First Contentful Paint)** | $< 1.2 \text{ seconds}$        | $> 2.5 \text{ seconds}$     | PostHog Web Vitals monitoring on dashboard.              |
| **API Latency (REST endpoints)**            | $< 150 \text{ ms}$             | $> 400 \text{ ms}$          | Prometheus middleware timers in FastAPI backend.         |
| **Error Rate (HTTP 5xx)**                   | $< 0.1\%$                      | $> 1.0\%$                   | Sentry issue tracking & Loguru server logs.              |
| **System Uptime**                           | $\ge 99.9\%$                   | $< 99.0\%$                  | UptimeRobot external ping checking every 60 seconds.     |
| **Build Success Rate**                      | $\ge 95\%$                     | $< 80\%$                    | GitHub Actions CI/CD pipeline history.                   |
| **Cost per Active User**                    | $< \$0.05 \text{ / month}$     | $> \$0.15 \text{ / month}$  | Monthly AWS/Hetzner server costs divided by MAU.         |
| **AI/NLP Inference Cost**                   | $\$0.00 \text{ / month (MVP)}$ | $> \$10.00 \text{ / month}$ | Tracking serverless execution or API key usage.          |
| **Infrastructure Cost**                     | $< \$30.00 \text{ / month}$    | $> \$50.00 \text{ / month}$ | Hard cost limits on VPS, SQLite DB storage, and proxies. |
| **E2E Pipeline Latency**                    | $< 15 \text{ minutes}$         | $> 30 \text{ minutes}$      | Time elapsed from social scraper execution to API write. |

Trade-off: To maintain a < \$30/month infrastructure cost, we sacrifice deep
video processing and complex multi-node orchestration, accepting the risk of
missing silent, non-text visual memes in favor of operational sustainability.

4. AI & Heuristic Metrics

Note: For our cost-sparing MVP, "AI" refers to our localized NLP models (Double
Metaphone, Levenshtein Distance, VADER sentiment) and the mathematical heuristic
of the Meme Score.

| Metric                         | Formula                                                                                 | Target         | Why this matters                                                                                                            |
| :----------------------------- | :-------------------------------------------------------------------------------------- | :------------- | :-------------------------------------------------------------------------------------------------------------------------- |
| **Phonetic Mapping Precision** | $\frac{\text{True Positives}}{\text{True Positives} + \text{False Positives}}$          | $\ge 80\%$     | Prevents system-wide alert fatigue by ensuring matched names (e.g., "Parle") are genuinely confused with the target ticker. |
| **Meme Score Calibration**     | $R^2 \text{ correlation between Meme Score & } 24\text{h Peak Vol}$                     | $R^2 \ge 0.60$ | Confirms that our score calculation accurately predicts actual market trading volume changes.                               |
| **Entity Extraction Recall**   | $\frac{\text{Correctly Tagged Entities}}{\text{Total True Entities in Scraped Corpus}}$ | $\ge 85\%$     | Ensures our system doesn't miss viral brand names due to scraping issues or typos.                                          |
| **Fallback LLM Trigger Rate**  | $\frac{\text{LLM API Queries}}{\text{Total Social Ingestion Items}}$                    | $< 5\%$        | Keeps API compute costs low by ensuring local, cheap regex/metaphone algorithms handle $\ge 95\%$ of cases.                 |
| **Sentiment Accuracy**         | $\frac{\text{Accurate Sentiment Classifications}}{\text{Total Evaluated Comments}}$     | $\ge 75\%$     | Confirms our VADER/RoBERTa engine correctly identifies hype vs. panic in comment sections.                                  |

5. Business Metrics

Monthly Active Users (MAU)

  - Target: 1,000 MAUs within 90 days of launch.
  - Measurement: Distinct logged-in or API-key authenticated users query our API
    over a rolling 30-day window.

Weekly Active Users (WAU)

  - Target: 350 WAUs.
  - Measurement: Distinct active users query our API over a rolling 7-day
    window.

Conversion Rate (Free to Paid)

  - Target: \ge 1.5\% conversion to premium alert subscriptions.
  - Measurement: Active paid subscriptions in Stripe divided by total
    authenticated accounts.

Churn Rate

  - Target: < 8\% monthly churn.
  - Measurement: Percentage of paid subscribers who cancel their accounts or
    fail to renew within a given calendar month.

Customer Acquisition Cost (CAC)

  - Target: < \$2.50 per acquired user (focused entirely on organic distribution
    channels).
  - Measurement: Total marketing spend + scraper infrastructure costs allocated
    for acquisition divided by the number of new signups.

Lifetime Value (LTV)

  - Target: \ge \$30.00 per converted customer.
  - Measurement: Average monthly subscription revenue per paid user divided by
    user churn rate.

6. Launch Success Criteria

       30 DAYS POST-LAUNCH                    60 DAYS POST-LAUNCH                    90 DAYS POST-LAUNCH
┌──────────────────────────────────────┐┌──────────────────────────────────────┐┌──────────────────────────────────────┐
│ GREEN  : MAU >= 300; Precision >= 75%││ GREEN  : MAU >= 700; Ret. W4 >= 20%  ││ GREEN  : MAU >= 1k; Pay-Conv >= 1.5% │
│ YELLOW : MAU 150-299; Prec 60-74%    ││ YELLOW : MAU 350-699; Ret. W4 15-19% ││ YELLOW : MAU 500-999; Conv 0.8-1.4%  │
│ RED    : MAU < 150; Pivot / Rebuild  ││ RED    : MAU < 350; High Churn       ││ RED    : MAU < 500; Flat growth/High Cost│
└──────────────────────────────────────┘└──────────────────────────────────────┘└──────────────────────────────────────┘

30 Days Post-Launch (Platform Stability & Precision)

  - GREEN (Success): \ge 300 MAU, phonetic mapping precision \ge 75\%, average
    pipeline latency < 15 mins, monthly infrastructure cost managed under \$30.
  - YELLOW (Continue Iterating): 150 - 299 MAU, phonetic precision between
    60\% - 74\%, pipeline latency between 15 - 30 mins. Action: Fine-tune
    Levenshtein thresholds and phonetic string preprocessing.
  - RED (Pivot): < 150 MAU, phonetic precision < 60\%, system crashes
    frequently, infrastructure costs exceed \$50. Action: Halt user acquisition,
    rebuild mapping algorithms locally, or review source quality.

60 Days Post-Launch (User Retention & Initial Traction)

  - GREEN (Success): \ge 700 MAU, Week-4 retention \ge 20\%, referral link share
    rate \ge 8\%.
  - YELLOW (Continue Iterating): 350 - 699 MAU, Week-4 retention between
    15\% - 19\%. Action: Introduce email digests of missed alerts, improve
    onboarding tooltips.
  - RED (Pivot): < 350 MAU, retention < 15\%, high user drop-off. Action: Survey
    users to find if they are receiving alerts too late (AALT) or if our
    interface is too complex.

90 Days Post-Launch (Economic Viability)

  - GREEN (Success): \ge 1,000 MAU, paid conversion rate \ge 1.5\% (Stripe
    active), monthly system run-rate remains below \$40.
  - YELLOW (Continue Iterating): 500 - 999 MAU, paid conversion rate
    0.8\% - 1.4\%. Action: Experiment with alert delivery options (Telegram vs.
    Email).
  - RED (Pivot): < 500 MAU, paid conversion < 0.5\%, running out of
    infrastructure budget. Action: Shut down continuous ingestion, shift to
    purely on-demand search, or re-evaluate monetization.

7. Instrumentation Plan

To avoid slowing down the system, all custom product metrics are pushed
asynchronously to PostHog, while infrastructure metrics are monitored via
Prometheus/Grafana.

Event: User Signup

  - Tool: PostHog
  - Event Name: user_signed_up
  - Properties:
      - signup_method: "email" | "oauth"
      - utm_source: "reddit" | "twitter" | "indiehackers" | "organic"
      - device_type: "mobile" | "desktop"

Event: Alert Details Viewed

  - Tool: PostHog
  - Event Name: view_alert_details
  - Properties:
      - ticker_symbol: "PARLE.NS" [1.1.1]
      - meme_score: 88
      - matched_brand: "Melody Chocolate" [1.1.1]
      - confusion_type: "phonetic" | "parent_company" | "semantic"

Event: Share Triggered

  - Tool: PostHog
  - Event Name: share_alert_generated
  - Properties:
      - ticker_symbol: "SIGL"
      - platform: "twitter" | "telegram" | "clipboard"
      - calculated_score_at_share: 91

Event: Pipeline Completion

  - Tool: Prometheus / Grafana (Server-Side logs)
  - Event Name: pipeline_run_completed
  - Properties:
      - ingested_items_count: 142
      - execution_duration_seconds: 42.5
      - identified_triggers: [{"ticker": "PARLE", "score": 89}]
      - database_write_status: "success"

8. Dashboard Layouts

To keep information organized, we maintain four distinct internal dashboard
views:

I. Executive Dashboard (The Big Picture)

  - Target Audience: Core stakeholders, solo developer.
  - Visualizations:
      - Single Value Cards: Monthly Active Users (MAU), Total Alerts Triggered,
        Active Paid Subscriptions (MRR).
      - Line Chart: Daily Signup Growth vs. Paid Conversion Rate (30-day trend).
      - Funnel Chart: Acquisition \rightarrow Signup \rightarrow View Alert
        Details \rightarrow Set Custom Alert.

II. Product Dashboard (User Behavior)

  - Target Audience: Designer, Product Engineer.
  - Visualizations:
      - Heatmap Table: User retention cohorts (Week 1 through Week 8).
      - Bar Chart: Most active alert triggers (attributing which tickers
        generate the most detail clicks).
      - Pie Chart: Referral sources of inbound traffic.

III. Engineering Dashboard (Performance & Stability)

  - Target Audience: Solo Developer / DevOps.
  - Visualizations:
      - Gauge Indicator: API Latency (ms) & E2E Pipeline Latency (minutes).
      - Line Chart: RAM and CPU utilization of our $15 VPS node over time.
      - Bar Chart: System error logs categorizing API HTTP status codes
        (2xx, 4xx, 5xx).
      - Counter Card: SQLite active lock queue duration and API scraper
        rate-limit hits.

IV. Growth Dashboard (Marketing & Funnel Optimization)

  - Target Audience: Solo Developer / Growth Hacker.
  - Visualizations:
      - Single Value Cards: Customer Acquisition Cost (CAC), Share-link
        Clickback Rate.
      - Line Chart: Daily clicks coming from specific social channels (Reddit
        /r/wallstreetbets vs. X posts).
      - Table View: Real-time feedback and NPS survey responses.
