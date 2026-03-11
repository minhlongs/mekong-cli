# Quarterly Business Review — Mekong CLI

## Overview
The quarterly business review (QBR) is a structured assessment of all five business layers: revenue, product, engineering, operations, and people. Executed via `mekong business-quarterly-review` and `mekong quarterly`, the QBR produces a board-ready summary, retrospective findings, and the next quarter's OKRs.

---

## QBR Structure (command: `mekong business-quarterly-review`)

### Inputs Required
- Financial close data: `mekong business-financial-close` (run week before QBR)
- Engineering metrics: PRs merged, tests passing, command count growth
- Customer metrics: MRR, churn, NPS, activation rate
- Sales metrics: pipeline volume, conversion rates, deal velocity
- Retrospective notes: `mekong retrospective` from each month of quarter

### QBR Agenda (3-hour block, async-first)

```
Part 1: LOOK BACK (90 min)
  1.1 Financial review (30 min)
      → mekong business-financial-close output
      → MRR waterfall: new + expansion − churn
      → P&L vs budget variance

  1.2 Product & engineering review (30 min)
      → Commands shipped this quarter
      → Test coverage, build health, tech debt eliminated
      → PEV engine improvements

  1.3 Customer & go-to-market review (30 min)
      → Acquisition: installs, signups, conversions
      → Retention: churn rate, NPS, health scores
      → Sales pipeline: deals closed, average deal size

Part 2: RETROSPECTIVE (30 min)
  → mekong retrospective → structured What Went Well / Delta / Actions
  → Three wins to celebrate
  → Three failures to learn from
  → Root cause analysis on biggest miss

Part 3: LOOK FORWARD (60 min)
  3.1 OKR review (15 min)
      → Score last quarter's OKRs (0.0 – 1.0)
      → mekong okr → draft next quarter OKRs

  3.2 Next quarter planning (30 min)
      → Top 3 bets for the quarter
      → Resource allocation
      → Risk register: top 5 risks + mitigations

  3.3 Decisions & owners (15 min)
      → Explicit decisions made in this QBR
      → Owner assigned to each initiative
      → Next QBR date set
```

---

## Q1 2026 Baseline QBR (Reference)

### Financial
| Metric | Q1 Actual | Q1 Target | Variance |
|--------|----------|----------|---------|
| MRR end of Q1 | $4,938 | $5,000 | -1.2% |
| New customers | 62 | 60 | +3.3% |
| Churn rate | 4.2% | <5% | Pass |
| Gross margin | 86% | >85% | Pass |
| Runway | >12 months | >12 months | Pass |

### Product & Engineering
| Metric | Q1 Actual | Q1 Target | Status |
|--------|----------|----------|--------|
| Commands in library | 289 | 250 | Exceeded |
| Test suite pass rate | 62/62 (100%) | 100% | Pass |
| New agents shipped | 2 | 2 | Pass |
| PEV engine improvements | Rollback + self-heal | Planned | Pass |
| Open bug count | 12 | <20 | Pass |

### Customer
| Metric | Q1 Actual | Q1 Target | Status |
|--------|----------|----------|--------|
| Activation rate (week 1) | 58% | >60% | Miss |
| Day 30 retention | 71% | >70% | Pass |
| NPS | 47 | >50 | Miss |
| Support tickets open | 8 | <10 | Pass |

### Retrospective Findings (Q1 2026)
**What Went Well:**
- MIT open source launch drove 800+ GitHub stars organically
- PEV rollback engine shipped on time — zero production incidents
- Polar.sh integration seamless — zero payment failures
- Cloudflare infra: $0 hosting cost at current scale

**What Failed:**
- Activation rate 58% vs 60% target: LLM setup confusing for new users
- NPS 47 vs 50 target: Enterprise wants dedicated onboarding support
- Content cadence: 1.5 posts/week vs 2/week target

**Actions for Q2:**
1. Ship `mekong init` with guided LLM setup wizard → fix activation gap
2. Add 45-min onboarding call for Enterprise $499 tier → fix NPS
3. Schedule content via `mekong marketing-content-engine` weekly → fix cadence

---

## Q2 2026 OKRs (command: `mekong okr`)

### Objective 1: Reach $20K MRR
- KR1: Grow to 300 paying customers (from 62)
- KR2: Upgrade 30 Starter → Pro via usage-triggered upsell emails
- KR3: Close 5 Enterprise accounts at $499/mo
- KR4: Reduce churn to <3% (from 4.2%)

### Objective 2: Product-Market Fit Signals
- KR1: Activation rate >70% (from 58%)
- KR2: NPS >55 (from 47)
- KR3: 5 published customer case studies
- KR4: Daily active commands >500/day

### Objective 3: Engineering Excellence
- KR1: Ship 100 new commands (289 → 389)
- KR2: Maintain 100% test pass rate
- KR3: `mekong daemon` (Tôm Hùm) autonomous dispatch in production
- KR4: P50 command execution latency <2s

### Objective 4: Distribution & Brand
- KR1: 3,000 GitHub stars (from ~800)
- KR2: Listed on Homebrew + 2 additional package managers
- KR3: 2 active LLM provider co-marketing partnerships
- KR4: 1,000 "OpenClaw Weekly" newsletter subscribers

---

## Business Financial Close (command: `mekong business-financial-close`)

### End-of-Quarter Close Checklist
```
Week 12, Day 1:  mekong accounting-daily        → Final month reconciliation
Week 12, Day 2:  mekong finance-collections     → Chase outstanding invoices
Week 12, Day 3:  mekong finance-monthly-close   → Final month P&L
Week 12, Day 4:  mekong business-financial-close→ Quarter P&L + balance sheet
Week 12, Day 5:  mekong business-quarterly-review inputs ready
QBR Day:         Full QBR → produce next quarter plan
```

### Financial Close Deliverables
1. Quarter P&L (revenue, COGS, gross margin, OpEx, net income)
2. MRR waterfall (new, expansion, churn, contraction, net new MRR)
3. Cash flow statement (operating, investing, financing)
4. Customer cohort retention table by signup month
5. Unit economics update (LTV, CAC, LTV:CAC per tier)
6. Budget vs actuals variance analysis
7. Next quarter financial model with three scenarios (bear/base/bull)

---

## Annual Financial Targets (command: `mekong annual`)

| Quarter | MRR Target | Cumulative ARR | Key Milestone |
|---------|-----------|----------------|--------------|
| Q1 2026 | $5,000 | $60K run-rate | Launch + first 50 customers |
| Q2 2026 | $20,000 | $240K run-rate | PMF signals, Enterprise tier live |
| Q3 2026 | $50,000 | $600K run-rate | $50K MRR = hire sales lead |
| Q4 2026 | $120,000 | $1.44M ARR | Series A conversation ready |

---

## QBR Cadence Calendar

| Quarter | QBR Date | Financial Close Deadline | OKR Lock |
|---------|---------|--------------------------|---------|
| Q1 2026 | Apr 7, 2026 | Apr 4, 2026 | Apr 8, 2026 |
| Q2 2026 | Jul 7, 2026 | Jul 4, 2026 | Jul 8, 2026 |
| Q3 2026 | Oct 6, 2026 | Oct 3, 2026 | Oct 7, 2026 |
| Q4 2026 | Jan 6, 2027 | Jan 3, 2027 | Jan 7, 2027 |

---

## Decision Log (updated each QBR)

| Quarter | Decision | Rationale | Owner |
|---------|---------|-----------|-------|
| Q1 2026 | MIT open source launch | Fastest distribution, no revenue risk | Founder |
| Q1 2026 | Polar.sh only payments | Simplicity, developer-friendly, no PayPal | Founder |
| Q1 2026 | Cloudflare-only infra | Zero cost, edge performance, D1 database | Eng |
| Q1 2026 | MCU deduct on delivery only | Fairness, aligns incentives | Product |
| Q2 2026 | Add guided init wizard | Fix 58% activation rate miss | Product |
| Q2 2026 | Enterprise onboarding call | Fix NPS 47 miss, high LTV justifies cost | CS |
| Q2 2026 | Weekly content schedule | Fix 1.5/wk cadence miss via automation | Marketing |
