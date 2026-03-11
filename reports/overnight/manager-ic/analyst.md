# Data Analyst Report — Mekong CLI
*Role: Data Analyst | Date: 2026-03-11*

---

## Analytics Architecture

Current state: No instrumentation confirmed. This is the highest-priority gap for
a data-driven growth motion. Recommended stack:

```
Event Collection: PostHog (self-hosted on CF Pages/Workers, free)
Storage: Cloudflare D1 (SQLite — already in stack)
Dashboards: PostHog UI + custom CF Worker queries
Alerting: CF Worker cron → Slack webhook on anomalies
```

---

## Metrics Framework

### North Star Metric
**Weekly Active Cooks (WAC)** — unique users who ran ≥1 `mekong cook` in past 7 days.
Rationale: captures both acquisition (new users) and retention (returning users) in one number.

### L1 Metrics (CEO/Founder dashboard)
| Metric | Definition | Cadence |
|--------|-----------|---------|
| WAC | Weekly active cook users | Weekly |
| MRR | Monthly recurring revenue (Polar.sh) | Monthly |
| Free → Paid conversion | % activated users who purchase credits | Monthly |
| Net Revenue Retention | MRR expansion from existing customers | Monthly |
| GitHub stars (weekly) | New stars as acquisition proxy | Weekly |

### L2 Metrics (Product/Growth dashboard)
| Metric | Definition | Cadence |
|--------|-----------|---------|
| Time to First Cook (TTFC) | pip install → first successful cook | Per cohort |
| Cook success rate | % cooks that pass Verifier | Daily |
| Avg MCU per active user | Credits consumed / active user / week | Weekly |
| Command diversity | Avg distinct commands used per user | Weekly |
| Day-7 / Day-30 retention | Cohort retention curves | Per cohort |

### L3 Metrics (Engineering dashboard)
| Metric | Definition | Cadence |
|--------|-----------|---------|
| PEV step failure rate | % steps that fail Verifier | Daily |
| Rollback trigger rate | % cooks that trigger rollback | Daily |
| LLM latency P50/P95 | Per provider, per command type | Real-time |
| CF Worker error rate | 5xx / total requests | Real-time |
| Test suite pass rate | pytest pass/fail in CI | Per commit |

---

## Funnel Analysis

### Acquisition → Revenue Funnel
```
GitHub Stars (weekly)
    │  ~40% pip install rate
    ▼
pip installs (weekly)
    │  ~62% activation rate
    ▼
First Cook Completed
    │  ~12% conversion rate
    ▼
Credit Purchase (Polar.sh)
    │  ~75% retention rate
    ▼
Month-2 Renewal
```

Key ratios to track:
- Star → Install: measures README quality + SEO
- Install → Cook: measures onboarding friction (TTFC)
- Cook → Purchase: measures value demonstration
- Purchase → Renewal: measures product stickiness

---

## Cohort Analysis Plan

Group users by:
1. **Acquisition week** — measure retention curves week over week
2. **LLM provider** — do Ollama users retain better than OpenRouter users?
3. **First command type** — do `cook` users retain better than `plan` users?
4. **Tier** — do Starter users upgrade more if they hit credit limit in week 1?

Example cohort query (D1 SQLite):
```sql
SELECT
  strftime('%Y-W%W', first_cook_at) as cohort_week,
  COUNT(DISTINCT user_id) as cohort_size,
  COUNT(DISTINCT CASE WHEN last_cook_at >= first_cook_at + 7 THEN user_id END) as d7_retained,
  ROUND(100.0 * COUNT(DISTINCT CASE WHEN last_cook_at >= first_cook_at + 7 THEN user_id END)
    / COUNT(DISTINCT user_id), 1) as d7_retention_pct
FROM user_activity
GROUP BY cohort_week
ORDER BY cohort_week DESC;
```

---

## Key Dashboards to Build

### Dashboard 1: Growth Overview
- WAC trend (line chart, 12 weeks)
- GitHub stars/week (bar chart)
- pip installs/week (bar chart)
- Free → Paid funnel (funnel chart)

### Dashboard 2: Product Health
- Cook success rate by command type (table)
- TTFC distribution (histogram)
- Top 20 most-used commands (bar chart)
- LLM provider distribution (pie chart)

### Dashboard 3: Revenue
- MRR by tier (stacked area chart)
- Polar.sh churn by tier (line chart)
- MCU consumption heatmap (calendar view)
- Credit refill timing (days before expiry histogram)

### Dashboard 4: Infrastructure
- CF Worker error rate (time series)
- LLM latency P50/P95 per provider (multi-line)
- D1 query latency (histogram)
- Queue depth — Tôm Hùm (time series)

---

## Anomaly Detection Rules

Implement as CF Worker cron jobs → Slack alerts:

| Anomaly | Threshold | Alert Channel |
|---------|-----------|--------------|
| Cook success rate drop | <80% (vs 7-day avg) | #eng-alerts |
| CF Worker error spike | >1% error rate | #eng-alerts |
| MRR drop | >10% week-over-week | #founders |
| Credit exhaustion spike | >20% users at 0 MCU | #product |
| LLM latency spike | P95 > 10s | #eng-alerts |

---

## Data Retention Policy

| Data Type | Retention | Reason |
|-----------|-----------|--------|
| Raw events (PostHog) | 90 days | Storage cost |
| Aggregated metrics (D1) | 2 years | Trend analysis |
| User credit balance | Indefinite | Billing audit |
| LLM prompt content | 0 days | Privacy (don't store) |
| Error logs (Sentry) | 30 days | Debug window |

---

## Q2 Analytics Actions

- [ ] Instrument `src/main.py` with PostHog events (opt-out flag required)
- [ ] Set up PostHog self-hosted on CF Workers
- [ ] Build L1 metrics dashboard (CEO view) in PostHog
- [ ] Write D1 cohort retention query and schedule weekly report
- [ ] Set up Slack alerting via CF Worker cron for anomaly detection
- [ ] Define baseline metrics from first 30 days of instrumentation
