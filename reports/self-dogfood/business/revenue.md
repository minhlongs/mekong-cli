# Revenue Model — Mekong CLI

**Model:** RaaS (Results-as-a-Service) credits | **Payment:** Polar.sh | **Updated:** March 2026

---

## Revenue Model Overview

Mekong CLI is free to install (MIT OSS). Revenue comes from mission execution credits (MCU).

```
Free tier:     pip install mekong-cli  →  0 MCU (manual LLM key required)
Starter:       $49/mo                  →  200 MCU/mo
Pro:           $149/mo                 →  1,000 MCU/mo
Enterprise:    $499/mo                 →  Unlimited MCU
Top-up:        $12 flat               →  50 MCU (one-time)
```

**1 MCU = 1 mission credit.** Complex missions cost 2–5 MCU. Simple commands cost 1.

---

## Why Credits (Not Seats)

| Model | Problem | Our Choice |
|-------|---------|-----------|
| Per-seat | Penalizes team growth | No |
| Per-API-call | Too granular, unpredictable | No |
| Flat subscription | No usage signal, churns faster | Partial |
| Credits (MCU) | Aligns cost with value delivered | Yes |

Credits create a natural upgrade path: power users exhaust Starter → upgrade to Pro without sales friction.

---

## Revenue Streams

### Stream 1: Subscriptions (Primary — 85% of revenue)

| Tier | Price | MCU | Gross Margin | Target Users (Q4 2026) |
|------|-------|-----|-------------|----------------------|
| Starter | $49/mo | 200 | 75% | 250 |
| Pro | $149/mo | 1,000 | 72% | 60 |
| Enterprise | $499/mo | Unlimited | 68% | 8 |

### Stream 2: Credit Top-ups (Secondary — 10% of revenue)

- $12 for 50 MCU (one-time, no subscription required)
- Targets: Starter users who spike usage, free-tier users testing before subscribing
- Low friction: single Polar.sh checkout

### Stream 3: Enterprise Custom (Future — 5% of revenue)

- $999+/mo for dedicated instance + SLA + Slack support
- Invoice billing (not Polar.sh)
- Available Q4 2026 at earliest

---

## Polar.sh Integration

| Feature | Status |
|---------|--------|
| Subscription products created | Done |
| Webhook endpoint (`/v1/webhooks/polar`) | Implemented |
| Credit ledger deduction on mission success | Implemented |
| HTTP 402 on zero balance | Implemented |
| Upgrade/downgrade handling | Needs testing |
| Refund handling | Not implemented |

**Polar.sh fees:** 4% per transaction (drops to 2.9% + $0.30 above $10K/mo volume).

---

## Credit Consumption by Command Layer

| Layer | Avg MCU/mission | Example command |
|-------|----------------|----------------|
| Ops | 1 | `mekong status` |
| Engineer | 2 | `mekong cook "fix bug"` |
| Product | 3 | `mekong plan "new feature"` |
| Business | 3 | `mekong marketing "launch campaign"` |
| Founder | 5 | `mekong annual "company review"` |

Average mission cost: ~2.5 MCU. Starter gets ~80 missions/mo. Pro gets ~400/mo.

---

## Revenue Expansion Mechanics

1. **Natural upgrade:** Starter hits 80% MCU → nudge to Pro
2. **Team expansion:** Solo founder becomes team → Enterprise pitch
3. **Use case expansion:** Started with `/cook` → discovers `/annual`, `/sales`
4. **Credit top-ups:** Occasional spikes covered without full upgrade

---

## Revenue Risks

| Risk | Likelihood | Mitigation |
|------|-----------|-----------|
| LLM API cost spike | Medium | Pass-through model, monitor cost/MCU |
| Polar.sh outage | Low | Manual billing fallback |
| Free tier abuse | Medium | Rate limiting on free installs |
| Competitor undercuts pricing | Medium | Binh Phap moat (289 commands, recipes) |
