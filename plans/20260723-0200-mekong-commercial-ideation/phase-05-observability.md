---
title: "Phase 05 — Observability + Reliability"
status: pending
priority: P0
tags: [observability, gateway, billing, sentry]
---

# Phase 05 — Observability + Reliability
Goal: Ship-to-production readiness.

## Scope
- Gateway `/health` bloom-filter fix + health probes
- MCU billing audit + usage quota alerts
- Error tracking (Sentry) + structured logging

## Deliverables
1. Gateway `/health` fix (bloom filter + gateway health proxies)
2. MCU billing audit endpoints
3. Usage quota alerts
4. Sentry init + sample error routing

## Definition of Done
- `/health` returns HTTP 200 with real component statuses
- `billing status` shows MCU usage and plan limits
- Sentry captures first test error in staging environment

## Dependencies
- Phase 03 (billing flow must be stable first)
