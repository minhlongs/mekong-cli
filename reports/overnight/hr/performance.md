# Performance Framework — March 2026
**Generated:** 2026-03-12 | **Stage:** Pre-Revenue | **Model:** OKR-based

---

## Executive Summary

No employees to evaluate yet. This document establishes the performance framework
for when hiring begins. OKR-based evaluation covering three domains: Engineering
(build health, test coverage, response time), Community (GitHub stars, contributors,
issue resolution), and Business (MRR, customer satisfaction, churn).

---

## Philosophy

Performance at Mekong CLI follows the Binh Pháp principle of 始計 (Initial Calculations):
measure what matters, measure it objectively, and act on data. No annual reviews —
continuous OKR cycles (quarterly) with monthly check-ins.

Core beliefs:
- **Output over hours:** Results matter, not time spent
- **Async-first:** Performance metrics should not require synchronous meetings
- **Transparent:** All OKRs visible to all team members
- **Data-driven:** Every KR has a numeric target and measurement method

---

## OKR Framework

### Cadence
- **Annual:** Company-level OKRs (founder sets in January)
- **Quarterly:** Team/individual OKRs (aligned to company OKRs)
- **Monthly:** KR progress check-in (async, written)
- **Weekly:** Personal TODO alignment (no formal review)

### Scoring
- 1.0: Fully achieved
- 0.7: Strong progress (acceptable)
- 0.5: Partial (needs discussion)
- 0.0: Not started / abandoned

Target average: 0.7 (stretch goals by design)

---

## Domain 1: Engineering OKRs

### Q2 2026 Engineering Objectives

**Objective 1: Maintain production-grade build health**

| Key Result                           | Target  | Measurement               |
|--------------------------------------|---------|---------------------------|
| CI build pass rate                   | >99%    | GitHub Actions dashboard  |
| Test suite pass rate                 | 100%    | pytest CI output          |
| TypeScript/Python type errors        | 0       | mypy / tsc output         |
| PR review turnaround                 | <48h    | GitHub PR timestamps      |
| Critical bug resolution              | <24h    | Issue close timestamps    |

**Objective 2: Improve test coverage**

| Key Result                           | Target  | Measurement               |
|--------------------------------------|---------|---------------------------|
| Unit test coverage (src/core/)       | >90%    | pytest-cov report         |
| Unit test coverage (src/agents/)     | >80%    | pytest-cov report         |
| Integration test scenarios           | 20+     | tests/ file count         |
| No @ts-ignore / # type: ignore       | 0       | grep in CI                |
| No TODO/FIXME in codebase            | 0       | grep in CI                |

**Objective 3: API performance**

| Key Result                           | Target  | Measurement               |
|--------------------------------------|---------|---------------------------|
| /v1/missions p50 response time       | <200ms  | CF Worker analytics       |
| /v1/missions p99 response time       | <2000ms | CF Worker analytics       |
| Cold start time (Workers)            | <100ms  | CF dashboard              |
| Uptime                               | >99.5%  | CF uptime monitoring      |
| Error rate (5xx)                     | <0.1%   | CF analytics              |

### Engineering Anti-Metrics (Do NOT optimize for these)

- Lines of code written (quality > quantity)
- Number of PRs merged (correctness > velocity)
- Hours worked (output > input)
- Features shipped without tests (never ship untested)

---

## Domain 2: Community OKRs

### Q2 2026 Community Objectives

**Objective 1: Build a thriving GitHub presence**

| Key Result                           | Target  | Measurement               |
|--------------------------------------|---------|---------------------------|
| GitHub stars                         | 500     | github.com/[org]/mekong   |
| GitHub forks                         | 50      | GitHub insights           |
| External contributors (PRs merged)   | 10      | GitHub contributors graph |
| Issues triaged within 24h            | 100%    | Issue timestamps          |
| README quality score (HN front page) | 1       | Product Hunt / HN launch  |

**Objective 2: Discord community health**

| Key Result                           | Target  | Measurement               |
|--------------------------------------|---------|---------------------------|
| Discord members                      | 200     | Discord member count      |
| Weekly active members                | 50+     | Discord analytics         |
| Average response time in #help       | <4h     | Manual tracking           |
| Monthly office hours held            | 4       | Calendar events           |
| Community-reported bugs (Discord)    | 5+      | Issues tagged "community" |

**Objective 3: Content and awareness**

| Key Result                           | Target  | Measurement               |
|--------------------------------------|---------|---------------------------|
| Blog posts published                 | 12      | Website/GitHub blog       |
| Twitter/X impressions                | 50K     | Twitter analytics         |
| HackerNews Show HN                   | 1 front page | HN submission        |
| Product Hunt launch                  | Top 5 of day | PH ranking            |
| YouTube tutorial views               | 5K      | YouTube analytics         |

---

## Domain 3: Business OKRs

### Q2 2026 Business Objectives

**Objective 1: First revenue**

| Key Result                           | Target  | Measurement               |
|--------------------------------------|---------|---------------------------|
| First paying customer                | 1       | Polar.sh dashboard        |
| MRR end of Q2                        | $5,000  | Polar.sh MRR              |
| Customer count                       | 30+     | Polar.sh subscriptions    |
| Net Revenue Retention                | >90%    | Churn tracking            |
| NPS score (first 10 customers)       | >50     | Email survey              |

**Objective 2: Product-market fit signals**

| Key Result                           | Target  | Measurement               |
|--------------------------------------|---------|---------------------------|
| "Would be very disappointed" (PMF survey)| >40% | Sean Ellis survey       |
| Organic signups (no paid marketing)  | 80%+    | Signup source tracking    |
| Daily active MCU usage (per user)    | >5 MCU  | D1 ledger analytics       |
| Support tickets / customer / month   | <2      | Support ticket count      |
| Feature requests from customers      | 10+     | GitHub Discussions        |

---

## Individual Performance Review Template

For use when first employee hired:

```markdown
## Quarterly Performance Review — [Name] — Q[N] 2026

**Role:** [Title] | **Manager:** [Founder] | **Period:** [dates]

### OKR Scorecard
| Objective | KR | Target | Actual | Score |
|-----------|-----|--------|--------|-------|
| [O1]      | [KR1]| [T]  | [A]    | [S]   |

**Average Score:** [X.X] / 1.0

### Strengths (observed this quarter)
1. [Specific example]
2. [Specific example]

### Growth Areas
1. [Specific, actionable]
2. [Specific, actionable]

### Next Quarter Focus
- [Top 3 priorities for Q[N+1]]

### Compensation Review
- Current: $[X]
- Market range: $[X]–$[X]
- Recommendation: [maintain/increase by N%/equity refresh]

### Employee Self-Assessment
[Written by employee before review meeting]
```

---

## Founder Self-Accountability (Current — Solo Stage)

| Weekly Check-in                      | This Week Target   |
|--------------------------------------|--------------------|
| Tests passing (CI green)             | 100%               |
| GitHub issues responded              | All within 24h     |
| Discord messages answered            | All within 4h      |
| Blog post drafted                    | 1                  |
| Customer conversations               | 3+ (even pre-revenue) |
| Code shipped                         | At least 1 meaningful PR |

---

## Performance Improvement Plan (PIP) Template

For underperforming employees (post-hire):

1. **Trigger:** Two consecutive quarters below 0.5 average OKR score
2. **Duration:** 60-day PIP period
3. **Structure:** Weekly written check-ins, clear measurable targets
4. **Outcome:** Return to good standing OR separation with respect
5. **Support:** Founder meets weekly during PIP (not just async)

---

*Next framework review: At first hire. Adapt to actual team needs.*
