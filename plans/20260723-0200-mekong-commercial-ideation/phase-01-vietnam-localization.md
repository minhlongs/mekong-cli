---
title: "Phase 01 — Vietnam Localization"
status: in_progress
priority: P0
tags: [i18n, vietnam, payments, onboarding]
---

# Phase 01 — Vietnam Localization
Goal: Make Mekong CLI usable by Vietnamese founders and teams.

## Scope
- Vietnamese language support across CLI (`tiếng Việt`)
- VN payment methods: VietQR, MoMo
- VN-localized docs + onboarding flow

## Deliverables
1. `src/cli/i18n/__init__.py` — shared i18n helper (done)
2. `mekong company init` locale selector wired to VN defaults (scaffold ready)
3. VietQR + MoMo checkout routes in `src/api/vn_payments_routes.py` (existing)

## Definition of Done
- `mekong --locale vi` renders Vietnamese UI via shared helper
- VietQR checkout returns 200 + QR payload
- MoMo sandbox payment succeeds end-to-end

## Dependencies
- Phase 03 pricing checkout must expose VN price list first

## Risks
- MoMo sandbox rate limits
- VietQR bank coverage not universal
