# Finance Manager Report — Mekong CLI
*Role: Finance Manager | Date: 2026-03-11*

---

## Revenue Model Overview

Mekong CLI monetizes via RaaS (Revenue as a Service) — a credit-based subscription
model processed exclusively through Polar.sh. Credits (MCU) are deducted only on
successful task delivery, aligning revenue with customer value.

---

## Pricing & Unit Economics

| Tier       | Credits/mo | Price/mo | Annual ACV | Gross Margin Est. |
|------------|-----------|----------|------------|-------------------|
| Starter    | 200       | $49      | $588       | ~92%              |
| Pro        | 1,000     | $149     | $1,788     | ~90%              |
| Enterprise | Unlimited | $499     | $5,988     | ~85%              |

**Gross margin drivers:**
- Infrastructure: Cloudflare Workers/Pages/D1/KV/R2 = $0 at current scale
- LLM cost per MCU: ~$0.01–$0.05 depending on model (DeepSeek cheapest)
- Polar.sh payment fee: ~2.9% + $0.30 per transaction
- At $49/mo, payment fee = ~$1.72 (3.5% effective rate)

---

## Cost Structure

### Fixed Costs (Monthly)
| Item | Cost |
|------|------|
| Cloudflare Workers (free tier) | $0 |
| Cloudflare D1 / KV / R2 (free tier) | $0 |
| GitHub (public repo) | $0 |
| Polar.sh (payment processing) | % of revenue only |
| Domain (agencyos.network) | ~$3/mo amortized |
| **Total fixed** | **~$3/mo** |

### Variable Costs (per active user/mo)
| Item | Cost per User |
|------|--------------|
| LLM API calls (avg 50 calls/mo at $0.001) | ~$0.05 |
| Cloudflare bandwidth overage | ~$0.00 |
| Support overhead (async, Discord) | ~$0.50 |
| **Total variable** | **~$0.55/user/mo** |

At $49 Starter: ~98.8% contribution margin before support.

---

## Revenue Projections (12-Month)

Assumptions: 8% free-to-paid conversion, 20% Starter→Pro upgrade, 10% Pro→Enterprise.

| Month | Starter | Pro | Enterprise | MRR | MoM Growth |
|-------|---------|-----|------------|-----|-----------|
| Apr   | 20      | 5   | 1          | $1,774 | — |
| Jun   | 60      | 15  | 3          | $5,322 | +74% |
| Sep   | 150     | 40  | 8          | $13,596 | +34% |
| Dec   | 300     | 80  | 20         | $31,500 | +27% |

**12-month ARR target: ~$250K**

---

## Break-Even Analysis

Monthly fixed costs: ~$3 (near zero infra)
Variable cost per user: ~$0.55
Break-even at: **1 paying Starter user** (month 1)

This is the core financial advantage — zero infra cost means every dollar of revenue
after Polar.sh fees is effectively profit until significant scale (>10K users).

---

## Polar.sh Revenue Recognition

- Webhooks trigger credit grants on successful payment
- HTTP 402 blocks execution when balance = 0 (no credit risk)
- Revenue recognized at subscription start (prepaid credits)
- Refund policy: unused credits not refundable (standard SaaS)

---

## LLM Cost Sensitivity

The largest variable cost risk is LLM API pricing changes.

| Scenario | LLM cost/MCU | Margin at $49 |
|----------|-------------|---------------|
| DeepSeek ($0.001/call) | $0.20 | 99.2% |
| Claude Sonnet ($0.003/call) | $0.60 | 98.8% |
| GPT-4o ($0.01/call) | $2.00 | 95.9% |
| Worst case ($0.05/call) | $10.00 | 79.6% |

Mitigation: Local Ollama path has $0 LLM cost. Encourage DeepSeek/Qwen for cost-conscious users.

---

## Chart of Accounts (Simplified)

```
Revenue
  4000 - Subscription Revenue (Polar.sh)
  4010 - Enterprise Revenue
Expenses
  5000 - Payment Processing (Polar.sh fees)
  5100 - LLM API Costs (OpenRouter/DeepSeek)
  5200 - Infrastructure (Cloudflare overages)
  5300 - Domain & Tooling
  6000 - Personnel (founders, future hires)
```

---

## Key Financial Risks

1. **Polar.sh dependency** — single payment provider; add Stripe fallback at $50K ARR
2. **LLM price volatility** — hedge with DeepSeek/local model defaults
3. **Unlimited Enterprise abuse** — add fair-use clause at 10,000 MCU/mo
4. **Free tier cost** — Ollama users = $0 cost, no concern until cloud features added

---

## Q2 Financial Actions

- [ ] Set up Polar.sh MRR dashboard with Stripe-equivalent reporting
- [ ] Track LLM cost per user via Cloudflare Analytics
- [ ] Model churn scenarios at 5%, 10%, 20% monthly churn
- [ ] Establish $10K MRR milestone as hiring trigger
