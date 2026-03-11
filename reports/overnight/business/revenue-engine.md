# Revenue Engine — Mekong CLI

## Overview
Mekong CLI monetizes AI-operated business automation via a **credit-based consumption model** (MCU = Mission Credit Unit). Revenue is driven by command usage, tiered subscriptions, and open-source freemium funnel.

---

## Revenue Model

### Primary: RaaS (Revenue as a Service)
Customers submit goals → pay MCU credits → OpenClaw executes → deliver results.

| Tier | Credits/mo | Price/mo | ARR per customer |
|------|-----------|----------|-----------------|
| Starter | 200 MCU | $49 | $588 |
| Pro | 1,000 MCU | $149 | $1,788 |
| Enterprise | Unlimited | $499 | $5,988 |

**MCU cost per command category:**
- Free: `health`, `status`, `clean`, `help` (0 MCU)
- Low (1 MCU): `plan`, `review`, `audit`, `docs-*`
- Medium (3 MCU): `cook`, `fix`, `sales`, `marketing`, `finance`
- High (5 MCU): `deploy`, `founder/vc/cap-table`, `founder/ipo/*`, `fundraise`

### Secondary: Open Source Freemium
- Self-hosted with own LLM key → free (drives adoption)
- Free users → product-qualified leads → convert to paid RaaS
- GitHub stars → social proof → enterprise inbound

---

## Revenue Engine Mechanics

### Acquisition → Activation → Revenue Loop
```
GitHub star / HN post
    → pip install mekong-cli
    → mekong cook "hello world" (free with own key)
    → Hit complex task (>5 steps)
    → Discover RaaS: "let OpenClaw run it"
    → Subscribe Starter $49
    → Hit Pro usage limits
    → Upgrade to Pro $149
    → Agency/team usage
    → Enterprise $499
```

### Credit Burn Rate by Persona
| Persona | Typical Commands/wk | MCU burn/mo | Recommended Tier |
|---------|--------------------|-----------|--------------------|
| Solo dev | `cook` x10, `fix` x5 | ~60 MCU | Starter |
| Founder | `annual`, `sales`, `finance` x20 | ~120 MCU | Starter/Pro |
| Agency | Full suite daily | ~800 MCU | Pro/Enterprise |
| Enterprise team | Multi-user, all layers | Unlimited | Enterprise |

---

## Payment Infrastructure

**Provider: Polar.sh** (sole payment provider — PayPal banned per rule)
- Webhook-driven MCU credit grants on successful payment
- HTTP 402 returned to CLI when balance = 0 (forces upgrade)
- Audit trail per transaction in `src/raas/` billing module

**Billing Flow:**
```
Customer pays Polar.sh
→ Polar webhook → Cloudflare Worker (apps/openclaw-worker/)
→ Credit ledger update (D1 database)
→ CLI checks balance before each command
→ Deduct MCU only on successful delivery
```

---

## Revenue Levers (commands: `revenue`, `business-revenue-engine`)

### Lever 1: Increase ARPU
- Upsell Starter → Pro when burn rate hits 150+ MCU/mo
- Pro → Enterprise at team usage (3+ users)
- `mekong revenue` command tracks ARPU trends

### Lever 2: Increase Conversion Rate
- Free CLI installs = top of funnel
- Activation = first `mekong cook` success
- Conversion = first MCU purchase
- Target: 5% free→paid (industry: 2-4%)

### Lever 3: Reduce Churn
- Sticky usage: `finance-monthly-close`, `hr-performance-cycle` = recurring workflow
- Annual pre-pay: 20% discount → reduces monthly churn
- Enterprise contracts: 12-month terms

### Lever 4: Expand Revenue
- **Affiliate program** (`mekong affiliate`): 20% commission to referrers
- **Agency white-label**: Agencies resell Mekong as their AI ops tool
- **Marketplace**: Custom skills/commands monetized by contributors

---

## Sales Channels (command: `sales`)

1. **PLG (Product-Led Growth)**: GitHub → install → self-serve upgrade
2. **Outbound SDR**: Target founders, CTOs, agency owners (`mekong sdr-prospect`)
3. **Partnerships**: Dev tool ecosystems, LLM provider co-marketing
4. **Content**: Technical blog posts driving `pip install` intent

---

## Key Revenue Metrics to Track

| Metric | Target | Command |
|--------|--------|---------|
| MRR | $50K by Q4 2026 | `mekong finance-monthly-close` |
| ARR growth | 3x YoY | `mekong annual` |
| Churn rate | <3%/mo | `mekong business-revenue-engine` |
| CAC | <$50 | `mekong sales-pipeline-build` |
| LTV:CAC | >10x | `mekong unit-economics` |
| Conversion free→paid | 5% | `mekong forecast` |

---

## Competitive Positioning on Price

| Competitor | Pricing | Mekong Advantage |
|-----------|---------|-----------------|
| GitHub Copilot | $19/mo/user (code only) | Full business ops, 289 commands |
| Cursor | $20/mo (code only) | CLI-first, LLM-agnostic |
| Linear + Notion | $40-50/mo (project mgmt) | AI execution, not just planning |
| Human VA | $500-2000/mo | 10x cheaper, 24/7, no HR cost |

**Core message:** $49/mo replaces $500+/mo in SaaS stack + VA cost.

---

## Revenue Risks & Mitigations

| Risk | Mitigation |
|------|-----------|
| LLM cost spike | Universal provider → switch cheapest |
| Low conversion | Friction-free Starter at $49 |
| Churn on Pro | Lock-in via `finance-monthly-close` habits |
| Enterprise slow sales | Start Starter, let usage pull to Enterprise |
