# Runway Analysis — March 2026
**Generated:** 2026-03-12 | **Stage:** Pre-Revenue Bootstrap | **Model:** Zero-Burn

---

## Executive Summary

Current runway is effectively infinite. Zero external capital raised, zero monthly burn rate,
zero salaries drawn. The Cloudflare-only infrastructure stack eliminates platform costs entirely.
This report models current state and two forward scenarios: continued bootstrap and post-raise.

---

## Current State: Zero-Burn Bootstrap

| Metric               | Value      | Notes                                 |
|----------------------|------------|---------------------------------------|
| Cash in bank         | $0         | No external capital                   |
| Monthly burn         | ~$6        | Dev LLM usage only                    |
| Monthly revenue      | $0         | Pre-customer                          |
| Net cash flow        | (~$6/mo)   | Negligible                            |
| Runway (cash-based)  | Infinite   | No cash to exhaust                    |
| Runway (time-based)  | Indefinite | Founder sustains via other means      |
| Break-even MRR       | $6         | 1 Starter customer covers all costs   |

**Interpretation:** With ~$6/mo total burn, even a single Starter customer ($49/mo) creates
positive cash flow of $43/mo. The project can operate indefinitely in bootstrap mode.

---

## Burn Rate Breakdown

### Fixed Monthly Costs
| Item           | Cost   |
|----------------|--------|
| Cloudflare     | $0     |
| GitHub         | $0     |
| Domain(s)      | $1     |
| **Fixed Total**| **$1** |

### Variable Monthly Costs
| Item                | Cost Range | Notes                        |
|---------------------|------------|------------------------------|
| Dev LLM (OpenRouter)| $3–$10     | Internal testing, dev work   |
| Monitoring tools    | $0         | Free tiers sufficient        |
| **Variable Total**  | **$3–$10** |                              |

### Total Burn
| Scenario    | Monthly Burn | Annual Burn |
|-------------|-------------|-------------|
| Minimal     | $1          | $12         |
| Typical     | $6          | $72         |
| Maximum     | $21         | $252        |

---

## Scenario 1: Bootstrap to $25K MRR (Recommended Path)

Target: Reach $25K MRR before considering external capital.

| Milestone           | Target Date | MRR     | Action                                |
|---------------------|-------------|---------|---------------------------------------|
| First customer      | Apr 2026    | $49     | Product Hunt launch                   |
| 10 customers        | May 2026    | $490    | HackerNews Show HN                    |
| $1K MRR             | Jun 2026    | $1,000  | Begin content marketing               |
| $5K MRR             | Aug 2026    | $5,000  | Hire community manager                |
| $10K MRR            | Oct 2026    | $10,000 | Founder draws $3K/mo salary           |
| $25K MRR            | Jan 2027    | $25,000 | Evaluate raise vs. continued bootstrap|

**Runway at each stage:** Infinite (costs stay near $0 until $5K MRR hires)

**Burn increase schedule:**
- $5K MRR: +$4,000/mo (community manager salary)
- $10K MRR: +$3,000/mo (founder salary)
- $15K MRR: +$2,000/mo (infra upgrades, tooling)

**Cash runway after hiring at $5K MRR:** Revenue-funded, no external capital needed.

---

## Scenario 2: Seed Raise (Post-$25K MRR)

Raise only after proving $25K MRR to maximize leverage and minimize dilution.

### Raise Parameters
| Parameter           | Value         | Notes                              |
|---------------------|---------------|------------------------------------|
| Raise amount        | $500K–$1.5M   | Pre-seed / seed range              |
| Valuation           | $3M–$8M       | 3–5x ARR multiple                  |
| Dilution target     | <20%          | Founder maintains control          |
| Use of funds        | 18 months     | Runway target                      |

### Post-Raise Burn Model ($500K raise)

| Category            | Monthly Cost  | Annualized    |
|---------------------|---------------|---------------|
| Engineering (2 FTE) | $16,000       | $192,000      |
| Marketing           | $5,000        | $60,000       |
| Infrastructure      | $500          | $6,000        |
| Legal/Admin         | $1,000        | $12,000       |
| Founder salary      | $8,000        | $96,000       |
| Buffer (10%)        | $3,050        | $36,600       |
| **Total Burn**      | **$33,550**   | **$402,600**  |

**Runway at $500K raise:** ~15 months (needs revenue growth to extend)
**Runway at $1.5M raise:** ~45 months (comfortable to Series A)

### Recommended Raise Timing
- Raise ONLY after $25K MRR (strong position)
- Target: $1M raise at $5M–$8M valuation
- Achieves 18+ months runway with growth headroom
- Investor profile: Operator-angels, developer-tools funds

---

## Scenario 3: Revenue-Funded Scale (Preferred if possible)

If $25K MRR reached with sustainable growth rate (20%+ MoM), consider no raise:

| MRR         | Date     | Action                                      |
|-------------|----------|---------------------------------------------|
| $25K        | Jan 2027 | Evaluate raise vs bootstrap                 |
| $50K        | Apr 2027 | 4 FTE team, profitable                      |
| $100K       | Sep 2027 | Series A from position of strength          |

**Advantage:** No dilution. Full founder control. Build toward profitability first.

---

## Key Decisions

| Trigger                    | Decision                                    |
|----------------------------|---------------------------------------------|
| $5K MRR                    | Hire community manager (revenue-funded)     |
| $10K MRR                   | Founder salary begins                       |
| $25K MRR + strong growth   | Evaluate seed raise                         |
| $25K MRR + slowing growth  | Raise to accelerate                         |
| Any enterprise deal >$20K  | Raise immediately (leverage moment)         |

---

## Risk Factors

| Risk                        | Probability | Mitigation                              |
|-----------------------------|-------------|-----------------------------------------|
| Founder fatigue (no salary) | Medium      | First salary at $10K MRR               |
| LLM cost spike (internal)   | Low         | BYOK model shields from cost            |
| Cloudflare pricing change   | Low         | Migrate to Fly.io/Railway if needed     |
| Competitor launch           | Medium      | Speed to $1K MRR before copycat         |
| Polar.sh outage             | Low         | Revenue held in Polar, not Mekong       |

---

## Summary

**Today:** Infinite runway. $6/mo burn. Pre-revenue.
**Target:** Bootstrap to $25K MRR before any capital decision.
**Raise scenario:** $1M seed at $25K MRR = 18+ months runway, <20% dilution.
**Philosophy:** Revenue is the best funding.

---

*Next runway review: 2026-04-01 or upon first customer acquisition.*
