# Recruiting Department as a Service

> Replace a $20k/hire recruiter with AI agents that source, screen, and advance candidates automatically.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| Recruiter (10 hires/yr × $20k) | $200,000/yr | $49/mo floor |
| LinkedIn Recruiter Lite | $1,680/yr | $1.50/candidate |
| Greenhouse ATS | $6,000/yr | Included |
| **Total replaced** | **$207,680/yr** | **~$3,600/yr** |

## What This Department Does

1. **Candidate Sourcing** — LinkedIn, GitHub, job boards — filtered to ICP match
2. **Resume Screening** — Automated screening against job requirements, ranked shortlist
3. **Outreach** — Personalized recruiter messages with role fit reasoning
4. **Interview Coordination** — Scheduling, scorecards, feedback aggregation
5. **Offer Generation** — Offer letter drafting with comp benchmarks

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Candidate sourced + screened | $3 |
| Job description written | $8 |
| Interview scorecard setup | $5 |
| Offer letter drafted | $10 |
| Sourcing batch (50 candidates) | $25 |

**Monthly floor:** $49.

## Included Commands

```bash
mekong recruiter-screen    # Resume screening + scoring
mekong recruiter-source    # Candidate sourcing pipeline
mekong hr-recruit          # HR-side recruiting integration
mekong business-hiring-sprint  # Sprint-based hiring coordination
```

## Install

```bash
mekong install dept-recruiting
```

## Configuration

```bash
# .mekong/.env.dept-recruiting
DEPT_RECRUITING_ATS=ashby  # ashby|greenhouse|lever
DEPT_RECRUITING_ATS_API_KEY=your_key
DEPT_RECRUITING_LINKEDIN_COOKIE=optional_for_sourcing
DEPT_RECRUITING_GITHUB_TOKEN=optional_for_eng_sourcing
DEPT_RECRUITING_CALENDLY_LINK=https://calendly.com/yourlink
DEPT_RECRUITING_HUMAN_APPROVE_OUTREACH=true
```

## Comparison: Agency Recruiter vs SaS

| Metric | Agency Recruiter | Recruiting Dept SaS |
|--------|-----------------|---------------------|
| Cost per hire | $15,000-25,000 | $200-500 |
| Time to shortlist | 2-3 weeks | 24 hours |
| Sourcing volume | 20-50/search | Unlimited |
| Available hours | Business hours | 24/7 |
