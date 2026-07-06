---
status: pending
created: 2026-07-06T12:43:00Z
track: Phase C
title: Revenue Layer — Stripe, Trials, CRM, VietQR, Usage Metering
owner: engineering
depends_on: [Phase B — Agentic Core Complete]
---

# Phase C Revenue Layer

## Goal
Wire the complete revenue stack: tier config → Stripe checkout → trial provisioning → CRM sync → VietQR payment → usage metering → unit economics.

## Acceptance Checklist

| # | Criterion | Proof |
|---|-----------|-------|
| 1 | Unified tier config (single source of truth) | `TierConfig` enum, no duplicate maps |
| 2 | Stripe Checkout + Webhook → MCU credit provisioning | `POST /v1/webhooks/stripe` provisions credits |
| 3 | 14-day trial system | New signups get `TRIAL` tier, auto-expires |
| 4 | HubSpot CRM sync | Contact creation + status sync on signup/convert |
| 5 | VietQR + Usage metering + Unit economics | VietQR webhook works; usage per command tracked; CAC/LTV visible |

## Phases

- **C1** — Unified Tier Config (consolidate duplicates into `src/seed/config/tiers.py`)
- **C2** — Stripe Checkout + Webhook (14-day trial → paid conversion)
- **C3** — Trial System (14-day expiry, grace period, auto-downgrade)
- **C4** — HubSpot CRM Integration (contact + deal sync)
- **C5** — VietQR Fix + Usage Metering + Unit Economics
