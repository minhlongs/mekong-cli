# Unit Economics & Pricing Model — Mekong CLI

**Date:** March 2026
**Covers:** unit-economics, pricing, tier-pricing, cashflow, runway

---

## Pricing Tiers (Current v5.0)

| Tier | Credits/mo (MCU) | Price/mo | Price/yr | ARPU |
|------|-----------------|----------|----------|------|
| Starter | 200 MCU | $49 | $490 | $49 |
| Pro | 1,000 MCU | $149 | $1,490 | $149 |
| Enterprise | Unlimited | $499 | $4,990 | $499 |

**MCU = Mission Credit Unit** — 1 MCU deducted per successful task delivery.
Zero-balance → HTTP 402. Credits never expire within billing period.

---

## MCU Cost Analysis (Per Credit)

### LLM Cost per MCU

Average task via `mekong cook`:
- Planner call: ~2,000 tokens (input) + 500 tokens (output)
- Executor: 1–3 LLM calls × 1,500 tokens avg
- Verifier: ~1,000 tokens

Total tokens per MCU: ~8,000 tokens (input + output blended)

| Provider | Cost per 1M tokens | Cost per MCU (8K tokens) |
|----------|--------------------|--------------------------|
| DeepSeek V3 | $0.27/M | $0.0022 |
| Qwen-Plus | $0.40/M | $0.0032 |
| Claude Sonnet 4 (via OR) | $3.00/M | $0.024 |
| GPT-4o | $5.00/M | $0.040 |
| Ollama local | $0.00 | $0.000 |

**Blended LLM cost per MCU (assuming 60% DeepSeek, 30% Qwen, 10% Claude):**
= 0.6×$0.0022 + 0.3×$0.0032 + 0.1×$0.024 = **$0.0052/MCU**

### Infrastructure Cost per MCU

Cloudflare Workers: $0.30/1M requests → ~$0.0000003/request (negligible)
Cloudflare D1 (billing DB): $0.001/1M reads → negligible
Polar.sh payment fee: 4% per transaction (amortized over subscription lifetime)

**Total infra cost per MCU: ~$0.001**

### Total COGS per MCU: ~$0.006

---

## Gross Margin Analysis by Tier

### Starter Tier ($49/mo, 200 MCU)

| Item | Value |
|------|-------|
| Revenue | $49.00 |
| LLM cost (200 MCU × $0.0052) | $1.04 |
| Infra cost (200 MCU × $0.001) | $0.20 |
| Payment processing (Polar 4%) | $1.96 |
| **Total COGS** | **$3.20** |
| **Gross Profit** | **$45.80** |
| **Gross Margin** | **93.5%** |

### Pro Tier ($149/mo, 1,000 MCU)

| Item | Value |
|------|-------|
| Revenue | $149.00 |
| LLM cost (1,000 MCU × $0.0052) | $5.20 |
| Infra cost (1,000 MCU × $0.001) | $1.00 |
| Payment processing (4%) | $5.96 |
| **Total COGS** | **$12.16** |
| **Gross Profit** | **$136.84** |
| **Gross Margin** | **91.8%** |

### Enterprise Tier ($499/mo, unlimited MCU)

Assumption: average Enterprise user consumes 5,000 MCU/mo (heavy usage).

| Item | Value |
|------|-------|
| Revenue | $499.00 |
| LLM cost (5,000 MCU × $0.0052) | $26.00 |
| Infra cost | $5.00 |
| Payment processing (4%) | $19.96 |
| **Total COGS** | **$50.96** |
| **Gross Profit** | **$448.04** |
| **Gross Margin** | **89.8%** |

**Blended gross margin (60% Starter, 30% Pro, 10% Enterprise): ~92.5%**

This is SaaS-tier margin. Comparable to Stripe (74%), Datadog (76%), HashiCorp (78%). Mekong's Cloudflare-native infra and cheap LLM routing are the structural advantages.

---

## Customer Acquisition Cost (CAC)

Current acquisition channels and estimated CAC:

| Channel | CAC | Notes |
|---------|-----|-------|
| ProductHunt organic | ~$0 | Time cost only |
| Hacker News Show HN | ~$0 | Time cost only |
| GitHub organic (stars → installs) | ~$5 | Estimated time amortized |
| Vietnamese community (Viblo, TopDev) | ~$10 | Founder time |
| Content marketing (blog/YouTube) | ~$20 | Per converted customer |
| Paid ads (future) | ~$80–150 | Industry benchmark for dev tools |

**Blended CAC (2026, organic-first): ~$15**

---

## LTV Analysis

### LTV Calculation

Average monthly churn target: 5% → average customer lifetime = 20 months

| Tier | ARPU/mo | Gross Margin | Lifetime | LTV |
|------|---------|--------------|---------|-----|
| Starter | $49 | 93.5% | 20 mo | $916 |
| Pro | $149 | 91.8% | 20 mo | $2,736 |
| Enterprise | $499 | 89.8% | 20 mo | $8,962 |
| **Blended** | **$110** | **92.5%** | **20 mo** | **$2,035** |

### LTV:CAC Ratio

| Channel | CAC | Blended LTV | LTV:CAC |
|---------|-----|-------------|---------|
| Organic | $15 | $2,035 | 136:1 |
| Paid ads | $120 | $2,035 | 17:1 |

**Target LTV:CAC > 3:1** (industry standard). Mekong is 136:1 on organic — exceptional.

---

## Cashflow Model 2026

### Monthly Operating Expenses

| Item | Monthly Cost |
|------|-------------|
| Founder salary (deferred) | $0 |
| LLM API costs (at 200 customers, blended) | $500 |
| Cloudflare infrastructure | $0 (free tier) |
| Polar.sh subscription | $0 (% of revenue) |
| GitHub (private repos) | $4 |
| Domain + email | $15 |
| Tools (monitoring, analytics) | $50 |
| **Total monthly burn** | **~$570** |

### Cashflow Projections 2026

| Month | Customers | MRR | COGS | Gross Profit | Burn | Net CF |
|-------|-----------|-----|------|--------------|------|--------|
| Jan | 5 | $245 | $22 | $223 | $570 | -$347 |
| Feb | 8 | $392 | $35 | $357 | $570 | -$213 |
| Mar | 10 | $490 | $44 | $446 | $570 | -$124 |
| Apr | 15 | $735 | $66 | $669 | $570 | +$99 |
| May | 25 | $1,225 | $110 | $1,115 | $570 | +$545 |
| Jun | 40 | $1,960 | $176 | $1,784 | $600 | +$1,184 |
| Jul | 60 | $2,940 | $265 | $2,675 | $600 | +$2,075 |
| Aug | 85 | $4,165 | $375 | $3,790 | $700 | +$3,090 |
| Sep | 110 | $5,390 | $485 | $4,905 | $700 | +$4,205 |
| Oct | 140 | $7,700 | $693 | $7,007 | $900 | +$6,107 |
| Nov | 170 | $9,350 | $842 | $8,508 | $1,200 | +$7,308 |
| Dec | 200 | $11,000 | $990 | $10,010 | $1,500 | +$8,510 |

**Breakeven: April 2026** (month 4, ~15 customers)
**Cumulative cash position by Dec 2026: ~$32K** (from near-zero start)

---

## Runway Analysis

**Current runway (pre-revenue):**
- Monthly burn: $570
- Cash on hand: ~$2,000 (estimated, bootstrap)
- Runway: ~3.5 months

**Post-ProductHunt launch (10 customers):**
- MRR: $490
- Net monthly: -$80 (near-breakeven)
- Runway: effectively infinite at 10 customers

**Key insight:** Mekong CLI reaches cash-flow breakeven at just 10 Starter customers. This is the primary milestone — not fundraising.

---

## Pricing Sensitivity Analysis

| Price Change | Impact on LTV:CAC | Impact on Conversion |
|-------------|-------------------|---------------------|
| Starter $29 (-41%) | LTV drops to $542 | +30% conversion est. |
| Starter $49 (current) | LTV $916 | Baseline |
| Starter $69 (+41%) | LTV $1,284 | -15% conversion est. |
| Pro $99 (-34%) | LTV $1,818 | +20% conversion est. |
| Pro $149 (current) | LTV $2,736 | Baseline |

**Recommendation:** Hold current pricing through Q2. A/B test $29 Starter as "indie developer" tier to lower barrier, measuring conversion lift vs. LTV dilution.

---

## MCU Pricing Optimization

Current: 1 MCU per task, regardless of complexity.
Opportunity: tiered MCU costs by command layer.

| Layer | Current MCU | Proposed MCU | Rationale |
|-------|-------------|--------------|-----------|
| Founder (`mekong annual`) | 1 | 5 | Multi-LLM, complex output |
| Engineer (`mekong cook`) | 3 | 3 | Unchanged |
| Ops (`mekong audit`) | 1 | 1 | Unchanged |
| Business (`mekong sales`) | 2 | 2 | Unchanged |

Proposed tiered MCU pricing = value-based pricing + higher perceived fairness.
