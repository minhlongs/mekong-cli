---
title: "Revenue Execution — Stripe + Conversion Funnel + CRM"
status: completed
created: 2026-07-04
project: mekong-cli
context: plans/reports/revenue-execution-260704-1732-mekong-billing-report.md
---

## Goal

Connect existing billing code → active revenue pipeline: Stripe payments → MCU credit provisioning → customer lifecycle tracking. 3 tracks.

## Phases

| Phase | Description | Files |
|-------|-------------|-------|
| A | Payment Gateway (Stripe webhook + MCU connector) | `src/raas/`, `scripts/` |
| B | Conversion Funnel (signup CLI + trial flow + onboarding) | `.claude/commands/`, `mekong/bootstrap/` |
| C | CRM Setup (HubSpot + pipeline + lead scoring) | `config/`, `scripts/` |

## Build Order

C → A → B (quick win → revenue enabler → conversion optimizer)

## Acceptance

- `mekong subscribe --tier starter` opens Stripe Checkout
- Stripe webhook → MCU credits provisioned in SQLite
- 14-day trial with 50 MCU credits
- `mekong status` shows balance + tier
- HubSpot contacts auto-created on signup
