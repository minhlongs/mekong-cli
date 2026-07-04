# 05. Business Model

> Date: 2026-07-04
> Status: Framework + Targets (Not Yet Implemented)

---

## 1. Model: SaaS B2B (Self-serve PLG + Direct Sales)

Mekong CLI follows a dual-path go-to-market model:

| Path | Target | Mechanics |
|------|--------|-----------|
| **Self-serve PLG** | Individual developers, small teams | Sign up, credit card, immediate access. No sales call. |
| **Direct Sales** | Mid-market agencies, enterprises | Demo + POC, custom onboarding, dedicated agent, negotiated annual contracts. |

The product is developer-centric enough for PLG to work (CLI tool, no implementation project required), but the value to a team of 20+ justifies a sales conversation.

### 1.1 Why PLG First

- CLI tools have zero switching costs -- adoption must be frictionless or it does not happen.
- Developers self-educate and self-buy. A sales-led process for a command-line tool does not convert.
- PLG builds a usage base that trains the product. Feature requests from self-serve users improve the enterprise product.

### 1.2 Why Direct Sales Matters

- No self-serve dashboard converts a team of 50+ engineers without procurement questions (security review, invoice, PO).
- Enterprise buyers need SLA guarantees, SSO, audit logs, and a named contact.
- The Pro tier ($499/mo) is high enough that a sales conversation pays for itself.

---

## 2. Unit Economics (Target)

| Metric | Target | Notes |
|--------|--------|-------|
| ARPU (blended) | $99/mo | Mix of Starter ($49), Growth ($149), Pro ($499) |
| LTV | $1,188 | 12-month average retention |
| CAC | $198 | 2 months payback |
| Gross margin | 85% | Cloud API costs (LLM inference, storage, compute) |
| MRR target | $99,000 | 1,000 customers |
| ARR target | $1,188,000 | Before churn |

### 2.1 Payback Period

CAC of $198 on $99/mo ARPU = 2-month payback. This is well within the SaaS benchmark of < 12 months and gives room to spend on acquisition.

- PLG CAC (ad-supported): $50-100 (self-serve funnel, content marketing)
- Direct Sales CAC: $500-1,000 (SDR time, demos, trial support)
- Blended CAC target: $198

### 2.2 LTV / CAC Ratio

$1,188 / $198 = 6.0x

Industry benchmark for healthy SaaS is 3x+. At 6x, the model supports aggressive acquisition spend.

### 2.3 Gross Margin Drivers

At 85%, the primary cost is LLM inference tokens per MCU credit consumed. Other costs (hosting, storage, bandwidth) are near zero for a CLI product.

| Cost Item | % of Revenue |
|-----------|-------------|
| LLM API costs | 10-12% |
| Infrastructure (D1, R2, Workers) | 2-3% |
| Payment processing | 2-3% |
| Total COGS | ~15% |

---

## 3. Pricing Tiers

### 3.1 Starter -- $49/mo

| Attribute | Value |
|-----------|-------|
| MCU credits | 200 / month |
| Departments | 22 |
| Support | Community (Discord) |
| Concurrent sessions | 1 |
| API rate limit | Standard |
| Best for | Solo developers, freelancers, evaluation |

**Positioning:** Low enough to be an impulse buy for a developer solving a real problem. 200 MCU credits cover roughly 200 agent runs per month.

### 3.2 Growth -- $149/mo

| Attribute | Value |
|-----------|-------|
| MCU credits | 1,000 / month |
| Departments | 22 (unlimited? -- policy TBD) |
| Support | Priority response (4h SLA) |
| Concurrent sessions | 3 |
| API rate limit | 2x standard |
| Best for | Small teams, growing agencies |

**Positioning:** The sweet spot. 5x the credits for 3x the price. Catches teams whose usage exceeds Starter. Priority support is the key differentiator.

### 3.3 Pro -- $499/mo

| Attribute | Value |
|-----------|-------|
| MCU credits | 5,000 / month |
| Departments | Unlimited |
| Support | Dedicated agent (1h SLA) |
| Concurrent sessions | 10 |
| API rate limit | 5x standard |
| SSO / Audit logs | Yes |
| Best for | Mid-market teams, enterprises |

**Positioning:** Enterprise tier with a named support contact. SSO + audit logs unlock procurement approval. Custom contract negotiable for annual commit.

### 3.4 Enterprise (Custom)

For >$5,000/mo commit: custom pricing, dedicated infrastructure option, SLA negotiation, on-premise or VPC deployment option.

---

## 4. MCU Credit System

### 4.1 What is an MCU Credit?

Mekong Compute Unit (MCU) is the billing primitive. 1 MCU = roughly 1 agent run of moderate complexity (3-5 tool calls, moderate context window).

MCU consumption scales with:
- **Model cost tier** -- GPT-4 class models consume more MCU per call than Haiku-class models
- **Context size** -- longer sessions consume more compute
- **Tool call volume** -- each external tool call (GitHub, database, deploy) adds MCU cost

### 4.2 Rollover Policy (Proposed)

- Unused credits roll over for 1 billing cycle (monthly cap: 2x plan limit)
- Enterprise: unlimited rollover within annual contract

### 4.3 Overage (Proposed)

- Starter: hard cap at 200 MCU. User must upgrade.
- Growth: $0.15 per additional MCU, or upgrade to Pro (whichever the user prefers).
- Pro: $0.10 per additional MCU, or custom enterprise contract.

### 4.4 MCU vs. Traditional Seats

Mekong CLI does NOT charge per seat. MCU billing aligns cost with usage, not headcount. This is deliberate:

- A team of 20 light users pays less than a team of 5 power users.
- Encourages broad adoption within an organization (no marginal cost per added developer).
- Avoids the "seat audit" friction that kills expansion revenue in traditional B2B SaaS.

---

## 5. Revenue Model Details

### 5.1 Revenue Streams

| Stream | % of Revenue (Target) | Notes |
|--------|----------------------|-------|
| Subscription (monthly) | 60% | Core MCU-based tiers |
| Subscription (annual) | 25% | 2 months free on annual commit |
| Usage overage | 10% | MCU overage charges |
| Professional services | 5% | Custom integration, migration, training |

### 5.2 Annual Discount

Annual billing = 10 months paid (2 months free):

| Tier | Monthly | Annual (per month) | Annual (total) | Savings |
|------|---------|-------------------|----------------|---------|
| Starter | $49 | $41 | $490 | 17% |
| Growth | $149 | $124 | $1,490 | 17% |
| Pro | $499 | $416 | $4,990 | 17% |

### 5.3 Expansion Revenue Drivers

- **Natural usage growth:** As teams adopt Mekong CLI for more workflows, MCU consumption rises.
- **Department expansion:** More departments within an organization means more agents running.
- **Tier upgrades:** Starter -> Growth -> Pro as needs scale.
- **Multi-project:** Single user on multiple projects = additive MCU consumption.

---

## 6. Go-to-Market Channels

| Channel | Target | CAC | Timeline |
|---------|--------|-----|----------|
| Content marketing (blog, docs) | Developers | $50 | 0-6 months |
| Open-source community (GitHub) | Contributors | $30 | ongoing |
| Developer tool directories | Indie devs | $80 | 3-12 months |
| Paid search (developer keywords) | Active buyers | $150 | 6-12 months |
| Direct sales (outbound) | Agencies, enterprises | $800 | 6+ months |
| Partnerships (dev tool ecosystem) | Shared audiences | $100 | 9+ months |

### 6.1 Initial Focus (0-6 months)

1. **Content marketing** -- "How to build an AI agent CLI" guides, comparison posts, architecture deep-dives
2. **GitHub presence** -- Open-source the core engine, grow stars, capture inbound interest
3. **Discord community** -- Free support channel that also serves as product feedback loop

---

## 7. Key Metrics & Targets

| Metric | Monthly Target | Annual Target |
|--------|---------------|---------------|
| New signups | 200 | 2,400 |
| Conversion rate (trial -> paid) | 5% | 5% |
| Paid customers | 10 (month 1) -> 200 (month 12) | 1,000 |
| MRR | $1K (month 1) -> $20K (month 12) | $99K |
| Monthly churn | <5% | -- |
| Net revenue retention | >110% | >120% |
| NPS | 40+ | 50+ |

### 7.1 Monthly Churn Tolerance

At $99K MRR target:
- At 5% monthly churn: need $5K/mo in new MRR just to stay flat
- At 3% monthly churn: need $3K/mo in new MRR
- At 1% monthly churn: need $1K/mo in new MRR

Churn is the single biggest risk to the model. A CLI tool has low switching costs -- users can leave overnight. Product quality, API reliability, and constant value delivery are existential, not nice-to-haves.

---

## 8. Current Reality

| Item | Status | Notes |
|------|--------|-------|
| MCU billing | CONCEPT only | Not implemented anywhere in the codebase |
| Payment processor | Not connected | No Stripe, NOWPayments, or any processor integrated |
| Subscription tiers | Defined on paper only | No tier enforcement, no gating logic |
| Usage tracking | None | No counter, no rate limiter tied to billing |
| Zero revenue | Confirmed | No paying customers |
| Product shipped | Yes | CLI is functional and usable |

### 8.1 Implementation Gaps

The product is built. The billing system is not.

| Build vs. Buy | Decision |
|---------------|----------|
| Payment processor | Buy (Stripe, Paddle, or NOWPayments) |
| Subscription portal | Build (simple dashboard with tier selection) |
| MCU tracking middleware | Build (hook into CLI execution pipeline) |
| Tier gating | Build (check subscription status before running commands) |

### 8.2 Priority Order for Billing Implementation

1. **MCU counter middleware** -- instrument the CLI execution path to count MCU per run
2. **Stripe checkout** -- self-serve subscription page with 3 tiers
3. **Webhook handler** -- listen for subscription changes, activate/deactivate access
4. **Tier gating** -- check active tier before executing paid features
5. **Usage dashboard** -- show MCU consumption, remaining credits, upgrade prompt
6. **Overage billing** -- charge for extra MCU beyond plan limit

---

## 9. Risks & Mitigations

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Low conversion rate | Revenue miss | Medium | Improve trial UX, offer free tier with limited MCU |
| High churn | MRR decay | High | Continuous product improvement, support quality, feature depth |
| LLM API cost spikes | Margin compression | Medium | Model routing (use cheaper models where possible), caching |
| Price sensitivity | Low ARPU | Low | $49 entry point is below pain threshold for developers |
| Competitor undercuts | Churn | Medium | Differentiation via department-level agent orchestration |

---

## 10. Unit Economics Sensitivity Analysis

### 10.1 What if ARPU is $49 (all Starter)?

| Metric | Value |
|--------|-------|
| MRR @ 1,000 customers | $49,000 |
| ARR | $588,000 |
| CAC payback | 4 months (at $198 CAC) |
| LTV | $588 (12 mo) |
| LTV/CAC | 3.0x |

Still healthy. The product needs 2x the customers to reach the same MRR target.

### 10.2 What if churn is 8% monthly?

| Metric | Value |
|--------|-------|
| Average lifetime | 12.5 months |
| LTV | $1,238 |
| New MRR needed to grow | $7,920/mo (to offset 8% of $99K) |
| Implied new customers | 80/mo at blended $99 |

8% churn is not fatal but requires aggressive acquisition. At less than 80 new paid customers per month, MRR declines.

### 10.3 What if gross margin drops to 70%?

- $0.30 of every $1.00 goes to COGS instead of $0.15
- At $99K MRR: COGS goes from $14,850/mo to $29,700/mo
- Remaining gross profit: $69,300/mo instead of $84,150/mo
- Still profitable, but less room for G&A and R&D spend

| MAR | $220,000 | Venture Tech $10-20M ARR |
| GP% | 75%+ | High, but MCU model adds COGS |
| CAC Payback | <12mo | 2mo target is well inside |

---

## 11. Open Questions

1. Should there be a free tier? (e.g., 50 MCU/month, no credit card) -- drives adoption but adds cost.
2. Are seats really the wrong model? Some enterprise buyers expect per-seat pricing by convention.
3. Is Stripe or Paddle better for B2B SaaS with global customers? (Paddle handles VAT globally.)
4. Do we want to support crypto payments (NOWPayments) given the current payment integration is NOWPayments for Sophia?
5. Should annual contracts be required for SSO / audit log features?
6. Is the MCU abstraction too complex for non-technical buyers? Should we simplify to flat per-seat pricing?
