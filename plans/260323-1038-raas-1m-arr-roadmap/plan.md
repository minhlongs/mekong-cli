---
title: "RaaS $1M ARR Roadmap"
description: "12-month plan from first revenue to $83K MRR across RaaS + algo-trading"
status: in-progress
priority: P1
effort: 12mo
branch: main
tags: [raas, revenue, growth, roadmap]
created: 2026-03-23
---

# RaaS $1M ARR Roadmap

**Target:** $1M ARR ($83K MRR) by Q1 2027
**Dual Revenue:** RaaS subscriptions + algo-trading passive income
**Margin:** ~99% on RaaS (LLM cost ~$0.01-0.10/MCU)

## Revenue Math

| Milestone | MRR | Customers | Timeline |
|-----------|-----|-----------|----------|
| First Revenue | $49-149 | 1-3 | Week 1-2 |
| Post-PH Launch | $2-5K | 20-50 | Week 3-4 |
| PLG Engine | $5-10K | 50-100 | Week 5-8 |
| Scale | $10-25K | 100-250 | Week 9-12 |
| $1M ARR | $83K | 600-800 | Month 4-12 |

Blended ARPU ~$120/mo (mix of $49/$149/$499 tiers)

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | First Revenue (Week 1-2) | In Progress (97%) | [phase-01](phase-01-first-revenue.md) |
| 2 | ProductHunt Launch (Week 3-4) | In Progress (26%) | [phase-02](phase-02-producthunt-launch.md) |
| 3 | PLG Growth Engine (Week 5-8) | In Progress (80%) | [phase-03](phase-03-plg-growth-engine.md) |
| 4 | Scale to $10K MRR (Week 9-12) | In Progress (75%) | [phase-04](phase-04-scale-10k-mrr.md) |
| 5 | Path to $1M ARR (Month 4-12) | Pending | [phase-05](phase-05-path-to-1m-arr.md) |
| 6 | Algo-Trading Revenue Stream | In Progress (10%) | [phase-06](phase-06-algo-trading-stream.md) |

## Key Metrics Dashboard

| Metric | Week 2 | Week 4 | Week 8 | Week 12 | Month 12 |
|--------|--------|--------|--------|---------|----------|
| MRR | $149 | $3K | $8K | $15K | $83K |
| Customers | 2 | 30 | 80 | 150 | 700 |
| Churn | - | <5% | <5% | <4% | <3% |
| CAC | $0 | $10 | $50 | $80 | $100 |
| LTV | - | $500 | $1K | $1.5K | $3K |

## Critical Dependencies

1. Polar.sh checkout E2E verified working
2. API gateway stable at api.agencyos.network (v5.0.0, eeb00860)
3. Free tier functional (50 MCU) for PLG
4. M1 Max running algo-trader for passive income
5. PEV engine fixed — MissionExecutor wired into scheduled-handler.ts

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Checkout broken | Blocks all revenue | E2E test in Phase 1 day 1 |
| PH launch flop | Delays growth 4 weeks | Have backup channels ready |
| High churn | Revenue leaks | Onboarding + usage alerts |
| LLM costs spike | Margin erosion | Rate limiting + model routing |
| Solo founder burnout | Everything stops | Automate, hire CS at $10K MRR |
