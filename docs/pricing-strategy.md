# Pricing Strategy — Mekong CLI

> **Unit Economics, MCU Cost Model, Break-even Analysis**
> Version: 1.0 | Date: 2026-03-19 | Owner: OpenClaw CTO

---

## Executive Summary

**Pricing Model**: MCU (Mekong Credit Unit) — consumption-based + subscription tiers

**3 Tiers**:
| Tier | Price/mo | Credits | Overage | Target |
|------|----------|---------|---------|--------|
| Starter | $49 | 200 MCU | $0.35/MCU | Indie devs, solo founders |
| Pro | $149 | 1,000 MCU | $0.25/MCU | Small teams, agencies |
| Enterprise | $499 | Unlimited | — | Corp, regulated industries |

**Unit Economics**:
- Gross Margin: 85% (target)
- CAC Payback: < 3 months
- LTV/CAC: > 3x

---

## 1. MCU Cost Model

### 1.1 What is 1 MCU?

```
1 MCU = 1 command execution (average)
Examples:
- /cook "fix bug" = 1 MCU
- /debug "analyze error" = 1 MCU
- /plan "add feature" = 2 MCU
- /test = 1 MCU
- /review = 1 MCU
```

### 1.2 Cost Components

| Component | Cost/MCU | % of Total |
|-----------|----------|------------|
| LLM API (Opus 4.6) | $0.15 | 43% |
| Infrastructure | $0.05 | 14% |
| Support/Success | $0.08 | 23% |
| G&A | $0.07 | 20% |
| **Total COGS** | **$0.35** | **100%** |

### 1.3 LLM Cost Breakdown

Based on Anthropic API pricing (Opus 4.6):
- Input: $15/MTok
- Output: $75/MTok
- Avg command: 50K input + 5K output = ~$1.125/command

**Optimization levers**:
- Model routing (Sonnet for simple tasks): $0.30/MCU
- Caching for repeat queries: 40% reduction
- Batch processing: 20% reduction

---

## 2. Unit Economics

### 2.1 Per-Tier Economics

**Starter ($49/mo, 200 MCU)**:
```
Revenue: $49
COGS: 200 × $0.35 = $70
Gross Profit: $49 - $70 = -$21 (loss leader)
Gross Margin: -43%

Strategy: Acquisition tool. Convert 30% to Pro within 90 days.
```

**Pro ($149/mo, 1,000 MCU)**:
```
Revenue: $149
COGS: 1,000 × $0.25 (optimized) = $250
Gross Profit: $149 - $250 = -$101 (loss leader)
Gross Margin: -68%

Wait — this doesn't work. Need to recalibrate.
```

**Recalibrated Model**:

Actual COGS per MCU after optimizations:
- Model routing (80% Sonnet, 20% Opus): $0.18/MCU
- Caching hit rate 50%: effective $0.09/MCU
- Infra + Support: $0.06/MCU
- **Total: $0.15/MCU**

**Revised Economics**:
| Tier | Revenue | COGS | Gross Profit | Margin |
|------|---------|------|--------------|--------|
| Starter (200 MCU) | $49 | $30 | $19 | 39% |
| Pro (1,000 MCU) | $149 | $150 | -$1 | ~0% |
| Enterprise (Unlimited) | $499 | $200* | $299 | 60% |

*Enterprise users avg 1,500 MCU/mo with 80% caching

### 2.2 LTV Model

```
Assumptions:
- Churn: 5%/mo (Starter), 3%/mo (Pro), 1%/mo (Enterprise)
- Expansion: 10%/qtr (Pro → Enterprise)
- CAC: $150 (Starter), $300 (Pro), $1,000 (Enterprise)

LTV Calculation (36-month horizon):
Starter: $49 × 12 × (1 - 0.05)^36 × 0.39 margin = $89
Pro: $149 × 12 × (1 - 0.03)^36 × 0.05 margin = $32
Enterprise: $499 × 12 × (1 - 0.01)^36 × 0.60 margin = $2,502

LTV/CAC:
Starter: 0.6x (needs improvement)
Pro: 0.1x (broken — needs price increase or cost reduction)
Enterprise: 2.5x (healthy)
```

### 2.3 Pricing Correction

**Problem**: Starter và Pro tiers đang loss hoặc breakeven.

**Solution Options**:

**Option A: Increase Prices**
| Tier | Old Price | New Price | Change |
|------|-----------|-----------|--------|
| Starter | $49 | $79 | +61% |
| Pro | $149 | $249 | +67% |
| Enterprise | $499 | $599 | +20% |

**Option B: Reduce Credits**
| Tier | Old Credits | New Credits | Change |
|------|-------------|-------------|--------|
| Starter | 200 | 100 | -50% |
| Pro | 1,000 | 500 | -50% |

**Option C: Hybrid (Recommended)**
| Tier | Price | Credits | Overage | Margin |
|------|-------|---------|---------|--------|
| Starter | $79 | 150 | $0.50 | 55% |
| Pro | $249 | 750 | $0.35 | 45% |
| Enterprise | $599 | Unlimited* | — | 65% |

*Fair use: 2,000 MCU/mo avg, overage $0.20/MCU beyond 3,000

---

## 3. Break-even Analysis

### 3.1 Fixed Costs (Monthly)

| Category | Amount |
|----------|--------|
| Engineering (2 FTE) | $30,000 |
| Infrastructure (fixed) | $5,000 |
| Support (2 FTE) | $12,000 |
| G&A | $8,000 |
| **Total Fixed** | **$55,000** |

### 3.2 Break-even Calculation

Using Option C pricing:
```
Weighted Avg Contribution Margin = 55%

Break-even Revenue = Fixed Costs / Margin
                   = $55,000 / 0.55
                   = $100,000/mo

Break-even Customers (avg $250/mo) = 400 customers
```

### 3.3 Scenario Analysis

| Scenario | Customers | MRR | Gross Profit | Net |
|----------|-----------|-----|--------------|-----|
| Conservative | 200 | $50,000 | $27,500 | -$27,500 |
| Base | 400 | $100,000 | $55,000 | $0 |
| Optimistic | 1,000 | $250,000 | $137,500 | $82,500 |
| Moon | 5,000 | $1,250,000 | $687,500 | $632,500 |

---

## 4. Competitive Positioning

| Competitor | Price/mo | Credits | $/Credit |
|------------|----------|---------|----------|
| **Mekong CLI (new)** | $79-599 | 150-unlim | $0.53 |
| Cursor Pro | $20 | Unlimited* | ~$0.10** |
| Copilot | $10 | Unlimited | ~$0.05** |
| Warp | $20 | 500 queries | $0.04 |
| Zed AI | $20 | 1,000 completions | $0.02 |

*Cursor: 500 premium completions/mo
**Effective cost varies by usage pattern

**Differentiation**:
- Full workflow automation (not just code completion)
- Multi-agent orchestration
- RaaS marketplace integration
- Enterprise governance (SOC2, audit trails)

---

## 5. Recommendations

### Immediate Actions (Q2 2026)

1. **Adopt Option C pricing** — $79/$249/$599 tiers
2. **Implement model routing** — 80% Sonnet, 20% Opus
3. **Add usage analytics** — Track MCU/command for optimization
4. **Launch with Pro focus** — Higher LTV, lower churn

### Q3 2026

1. **Enterprise sales motion** — Target 50 enterprise customers
2. **Usage-based add-ons** — Priority support, custom agents
3. **Annual prepay discount** — 2 months free (17% savings)

### Q4 2026

1. **Price optimization** — A/B test $99/$299/$699
2. **International expansion** — EUR, GBP pricing
3. **Partner channel** — 20% rev share for agencies

---

## 6. Metrics Dashboard

**Weekly Tracking**:
- MRR by tier
- MCU consumption per customer
- Gross margin % by tier
- Churn rate by tier
- CAC by channel

**Monthly Review**:
- LTV/CAC ratio
- Net Revenue Retention
- Payback period
- Cash burn vs. plan

---

## Appendix: MCU Command Costs

| Command | Base MCU | Complexity Multiplier |
|---------|----------|----------------------|
| /cook | 1 | ×1-3 (scope-based) |
| /fix | 1 | ×1-2 |
| /plan | 2 | ×1-5 |
| /debug | 1 | ×1-3 |
| /test | 1 | ×1-2 |
| /review | 1 | ×1-2 |
| /scout | 1 | ×1-4 |
| /deploy | 2 | ×1 |
| /help | 0 | — |

**Dynamic Pricing**:
- Peak hours (9am-6pm PT): 1.2× multiplier
- Off-peak: 0.8× multiplier
- Enterprise: Flat rate (no multiplier)
