# 15. AARRR + Lean Analytics

> Metrics-driven growth framework for mekong-cli. Tracks the full customer lifecycle from first touch through referral flywheel.

## North Star Metric

**Active workflows per day** — the single metric that best captures delivered value. Every other metric feeds into this.

---

## A — Acquisition

How users find and start using mekong-cli.

| Metric | Current Baseline | Target | Notes |
|--------|-----------------|--------|-------|
| Website visitors (unique / month) | TBD | 10,000 | Organic + content marketing |
| Install script downloads (monthly) | TBD | 2,500 | `curl -fsSL https://mekong.sh/install` |
| GitHub stars | 0 | 500 | Growth via open-source utility |
| Docs page views / month | TBD | 5,000 | README + docs.mekong.sh |
| Referral traffic % | TBD | 25% | Word-of-mouth from shipped projects |
| Cost per acquisition (CPA) | TBD | < $5 | Focus on organic, minimal paid |

**Key questions:**
- Which channels drive the highest-quality installs?
- What is the conversion rate from visitor to script download?

---

## A — Activation

First meaningful experience — the moment a user realizes mekong-cli saves them time.

| Metric | Current Baseline | Target | Notes |
|--------|-----------------|--------|-------|
| First agent configured | TBD | 80% of installs | Setup wizard completion |
| First workflow executed | TBD | 60% of installs | Default "hello-world" workflow |
| Time to first value (TTFV) | TBD | < 10 min | From install to first successful run |
| Help command usage | TBD | < 3 tries | Users find answers without docs |
| First project scaffolded | TBD | 40% of installs | `mekong init` conversion |
| Activation rate (visited → value) | TBD | > 40% | Lean Analytics benchmark |

**Key questions:**
- Where do users drop off between install and first workflow?
- Can TTFV be reduced to under 5 minutes with better defaults?
- Is the install + configure experience too manual?

---

## R — Retention

Users who come back are users who ship.

| Metric | Current Baseline | Target | Notes |
|--------|-----------------|--------|-------|
| Daily active users (DAU) | TBD | 500 | Core engagement metric |
| Weekly active users (WAU) | TBD | 2,000 | Broader usage signal |
| Weekly workflow count | TBD | 5 per user | Habit formation threshold |
| 7-day retention rate | TBD | > 40% | Day-7 cohort analysis |
| 30-day retention rate | TBD | > 20% | Long-term stickiness |
| Median sessions per week | TBD | 3 | Frequency of use |
| Feature adoption (per release) | TBD | > 50% | Update → try rate |

**Key questions:**
- What is the primary workflow loop that drives daily returns?
- Do power users use different commands than casual users?
- What triggers the "aha moment" that converts a trial user into a daily user?

---

## R — Revenue

Monetization through tiered access (free / pro / team).

| Metric | Current Baseline | Target | Notes |
|--------|-----------------|--------|-------|
| Monthly recurring revenue (MRR) | $0 | $10,000 | Target: 200 pro users x $50 |
| Average revenue per user (ARPU) | $0 | $25 | Blended across tiers |
| Conversion rate (trial → paid) | TBD | > 5% | Industry benchmark for dev tools |
| Monthly churn rate | TBD | < 5% | Net negative churn target |
| Customer acquisition cost (CAC) | TBD | < $50 | Self-serve / organic heavy |
| LTV / CAC ratio | TBD | > 3x | Healthy unit economics |
| Time to payback (CAC) | TBD | < 6 months | Cash flow efficiency |
| Expansion MRR (upgrades) | TBD | > 10% of MRR | Team tier upgrades |

**Key questions:**
- What feature cluster drives the free-to-pro conversion?
- Is pricing perceived as fair relative to value delivered?
- What is the biggest reason for churn among paid users?

---

## R — Referral

Happy users bring users. Measure the flywheel.

| Metric | Current Baseline | Target | Notes |
|--------|-----------------|--------|-------|
| Net Promoter Score (NPS) | TBD | > 40 | World-class for dev tools |
| Referral sources tracked | TBD | 3+ | GitHub, Twitter, direct word-of-mouth |
| Viral coefficient (K-factor) | TBD | > 0.3 | Each user brings 0.3 new users |
| Referral conversion rate | TBD | > 10% | Referred → installed |
| Share rate (workflows shared / total) | TBD | > 15% | Social proof loop |
| Community contributions (PRs/issues) | TBD | 50 / month | Open-source leverage |

**Key questions:**
- What would make users naturally share mekong-cli with their team?
- Is the sharing friction low enough (one command, one link)?
- Can we turn shipped projects into implicit endorsements?

---

## Lean Analytics One-Metric-That-Matters (OMTM) by Stage

| Stage | OMTM | Why |
|-------|------|-----|
| Empathy (pre-launch) | Problem interview completion | Validate pain before building |
| Stickiness (0-500 users) | 7-day retention | Product must be habit-forming |
| Virality (500-5,000) | Viral coefficient | Growth must become self-sustaining |
| Revenue (5,000+) | MRR growth rate | Business viability |

**Current stage:** Pre-launch / Empathy — validate that developers feel the "CLI fatigue" pain we are solving.

---

## Data Sources

- **Product analytics:** PostHog self-hosted (DAU, retention, funnels)
- **Revenue:** Stripe billing dashboard (MRR, churn, ARPU)
- **Referral:** UTM-tagged links + PostHog source attribution
- **NPS:** In-app survey (triggered after 10th workflow run)
- **Install tracking:** Post-install telemetry (opt-in via `mekong telemetry enable`)

---

## Review Cadence

- **Weekly:** DAU, installs, activation rate, top commands
- **Monthly:** MRR, churn, retention cohorts, NPS
- **Quarterly:** Full AARRR review, OMTM stage reassessment, forecast vs actual
- **Trigger:** Any metric > 20% deviation from target triggers a deep-dive

---

*Last updated: 2026-07-04*
