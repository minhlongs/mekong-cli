# Pricing Analysis — Mekong CLI RaaS Credits

**Date:** March 2026 | **Author:** Product + Finance
**Context:** Pre-public launch pricing validation
**Reference tiers:** Starter ($49/200 MCU), Pro ($149/1,000 MCU), Enterprise ($499/unlimited)

---

## The Core Pricing Question

What is the right price per MCU credit, and does the current tier structure generate sustainable margin while remaining competitive against alternatives?

---

## Unit Economics: Cost Per MCU

### LLM API Cost Breakdown

MCU (Mission Credit Unit) is an abstraction over LLM API calls. One MCU ≠ one LLM call — it represents the total compute budget for one meaningful unit of work.

**Cost mapping by command type:**

| Command type | Avg tokens (in+out) | Avg LLM cost | MCU assigned | Revenue per MCU |
|-------------|--------------------|--------------|-----------|--------------------|
| Quick ops (health, status, clean) | ~500 | $0.0005 | 0 MCU (free) | — |
| Simple commands (brainstorm, code snippet) | ~2,000 | $0.002 | 1 MCU | $0.049 (Starter) |
| Standard commands (cook, plan, sprint) | ~8,000 | $0.008 | 2 MCU | $0.098 (Starter) |
| Complex commands (deploy, security audit) | ~20,000 | $0.020 | 3 MCU | $0.147 (Starter) |
| Heavy commands (fundraise, annual planning) | ~50,000 | $0.050 | 5 MCU | $0.245 (Starter) |

LLM API costs assume OpenRouter routing to Claude Haiku/Sonnet mix (primary model), OpenAI GPT-4o-mini fallback. Weighted average: **$0.001 per 1,000 tokens**.

### Margin Analysis by Tier

**Starter tier: $49/month for 200 MCU**

| Item | Value |
|------|-------|
| Revenue | $49.00 |
| LLM cost (200 MCU × avg 2 MCU/command × $0.004/command) | ~$3.20 |
| Infrastructure (API, DB, CDN per account) | ~$2.00 |
| Support (email, no SLA) | ~$1.00 |
| Payment processing (Polar.sh ~3%) | ~$1.47 |
| **Total COGS** | **~$7.67** |
| **Gross margin** | **~$41.33 (84%)** |

**Pro tier: $149/month for 1,000 MCU**

| Item | Value |
|------|-------|
| Revenue | $149.00 |
| LLM cost (1,000 MCU × avg $0.004/command avg) | ~$16.00 |
| Infrastructure | ~$3.00 |
| Support (async, occasional) | ~$5.00 |
| Payment processing | ~$4.47 |
| **Total COGS** | **~$28.47** |
| **Gross margin** | **~$120.53 (81%)** |

**Enterprise tier: $499/month, unlimited MCU**

| Item | Value |
|------|-------|
| Revenue | $499.00 |
| LLM cost (est. 3,000–8,000 MCU/month — usage capped by workflow needs, not hard limit) | ~$24–$64 |
| Infrastructure | ~$5.00 |
| Support (Slack SLA, 2hr/mo) | ~$100.00 |
| Payment processing | ~$14.97 |
| **Total COGS (midpoint)** | **~$168** |
| **Gross margin** | **~$331 (66%)** |

**Summary:** All tiers healthy. Starter and Pro at 80%+ gross margin is excellent for a SaaS at this stage. Enterprise at 66% is lower but justified by the support commitment; scales as support amortizes over more customers.

---

## Price-Per-MCU Analysis

| Tier | Price/MCU | Price/command (avg 2 MCU) |
|------|-----------|--------------------------|
| Starter | $0.245 | $0.49 |
| Pro | $0.149 | $0.30 |
| Enterprise (est. 5,000 MCU avg) | ~$0.10 | $0.20 |

**Volume discount curve:** Pro is 39% cheaper per MCU than Starter. Enterprise (at 5K MCU) is 59% cheaper. This is a standard SaaS volume discount structure — encourages upgrading without making Starter unprofitable.

---

## Competitive Pricing Comparison

### Direct Competitors

| Tool | Price | What you get | Effective cost per task |
|------|-------|-------------|------------------------|
| Mekong Starter | $49/mo | 200 MCU, 5 layers, 289 commands | $0.49/command |
| Mekong Pro | $149/mo | 1,000 MCU, full access | $0.30/command |
| ChatGPT Plus | $20/mo | Unlimited GPT-4o, manual prompting | ~$0.20/prompt (but you write the prompt + do the work) |
| Cursor Pro | $20/mo | Code-only AI, no business layer | N/A (different category) |
| Devin | $500/mo | AI software engineer (1 task type) | ~$50/task (10 tasks/month assumed) |
| GitHub Copilot | $10/mo | Code autocomplete only | N/A |
| Factory | $custom | Enterprise AI coding workflow | $50–200/user/mo |

### The Comparison That Matters

**Mekong vs. ChatGPT Plus at $20/mo:**
- ChatGPT: $20 for unlimited prompts where YOU are the execution engine
- Mekong: $49 for 200 tasks where the CLI is the execution engine
- Net: +$29 for the work actually getting done, not just suggested

The framing is: "ChatGPT helps you think. Mekong does the work."

**Mekong vs. Devin at $500/mo:**
- Devin: $500 for AI software engineering only
- Mekong Enterprise: $499 for all 5 business layers including engineering
- Net: Same price, dramatically broader coverage

The framing: "Devin handles your code. Mekong handles your entire company."

---

## Free Tier Strategy

### Current position: No free tier

Rationale for no free tier at launch:
1. LLM API costs are real — even 10 free MCU per user would burn $0.04/user in LLM costs
2. Free tier users dilute support bandwidth without revenue offset
3. At 0 customers, we don't yet know which free tier feature drives conversion

### Recommended free tier (post-launch, after 100 paying customers)

**"Mekong Free"** — 10 MCU/month, no credit card required

| Command | Free tier |
|---------|-----------|
| `mekong cook` (simple tasks) | Yes (1 MCU each, up to 10/mo) |
| `mekong plan` | Yes |
| `mekong health`, `mekong status` | Yes (0 MCU, always free) |
| DAG workflow recipes | No (minimum 3 MCU per recipe) |
| `mekong deploy` | No |
| `mekong fundraise`, `mekong pitch` | No |

**Why 10 MCU:** Enough to complete 5–10 real tasks and experience the core value loop. Not enough to run a business on for free.

**Conversion hypothesis:** Users who complete their first `mekong cook` within 10 MCU will want more. Starter ($49) feels cheap after experiencing the value.

**Free → Paid conversion target:** 8% (industry standard for developer tools is 5–15%; we target 8% as conservative baseline).

---

## MCU Pricing Sensitivity Analysis

### What happens if we raise prices?

**Scenario: Starter → $79/mo (same 200 MCU)**

- Revenue per customer: +$30/mo (+61%)
- Price-per-MCU: $0.395 (vs. $0.245 now)
- Gross margin: ~87% (vs. 84%)
- Risk: loses price comparison vs. ChatGPT Plus ($20 × 4 = $80/mo for 4 AI tools)
- Verdict: Too aggressive at launch. Revisit at 500 customers if churn is low.

**Scenario: Reduce Starter credits to 100 MCU at $49**

- Revenue per MCU: $0.49 (2x current)
- Gross margin: ~90%
- Risk: power users churn immediately; "200 MCU feels generous" becomes "100 MCU feels like a trap"
- Verdict: Do not reduce credits. MCU generosity at Starter builds trust.

**Scenario: Add a $19/mo "Lite" tier (50 MCU)**

- New entry point below $49
- Could capture price-sensitive solo founders in emerging markets
- Risk: cannibalizes Starter signups
- Verdict: Interesting for international expansion (Vietnam, India, LATAM), deferred to v5.2

---

## Annual Discount Structure

| Tier | Monthly | Annual | Discount | Effective monthly |
|------|---------|--------|----------|------------------|
| Starter | $49/mo | $470/yr | 2 months free (20%) | $39/mo |
| Pro | $149/mo | $1,430/yr | 2 months free (20%) | $119/mo |
| Enterprise | $499/mo | $5,000/yr | ~16% | $417/mo |

**Annual rationale:**
- 20% discount for Starter/Pro is market standard (Notion, Linear, etc.)
- Enterprise at 16% discount — slightly less because Enterprise already has support costs; floor margin at 60%
- Annual subscriptions reduce churn exposure and improve cash flow predictability

**Cash impact of 10 annual subscribers per tier:**
- Starter: 10 × $470 = $4,700 upfront vs. $490/mo monthly
- Pro: 10 × $1,430 = $14,300 upfront vs. $1,490/mo monthly

For a bootstrapped product, annual revenue is highly valuable for hiring and infrastructure investment.

---

## Pricing Page Copy Recommendations

**Starter — headline:** "For solo founders moving fast"
- Not "Basic" or "Lite" (feels limited)
- "Starter" communicates growth path

**Pro — headline:** "For agencies that bill by results"
- Not "Business" (too generic)
- Agency framing justifies $149/mo as COGS, not personal expense

**Enterprise — headline:** "Your AI operating system, unlimited"
- Not "Custom" (implies uncertainty)
- "Unlimited" is the key differentiator vs. Pro

---

## Pricing Review Cadence

| Milestone | Review trigger |
|-----------|---------------|
| 50 paying customers | Check churn rate by tier — if Starter churn > 15%/mo, pricing or value problem |
| 100 paying customers | A/B test $59 vs. $49 Starter with new signups |
| $10K MRR | Evaluate free tier introduction |
| 500 paying customers | Full pricing review — volume, competition, margin |
