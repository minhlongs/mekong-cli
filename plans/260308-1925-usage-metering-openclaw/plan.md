---
title: "Usage Metering Integration: OpenClaw Worker + RaaS Gateway"
description: "Integrate OpenClaw Worker with RaaS Gateway for JWT + mk_ API key authentication and KV-based usage metering"
status: pending
priority: P2
effort: 6h
branch: main
tags: [raas, usage-metering, openclaw, cloudflare-workers, kv]
created: 2026-03-08
---

# Usage Metering Integration Plan

## Overview

Connect OpenClaw Worker to RaaS Gateway for centralized authentication and usage tracking. RaaS Gateway already has production-ready KV-based metering — OpenClaw needs to forward requests with proper API keys.

## Architecture Summary

```
Telegram User
    ↓ (message with mk_ API key or service token)
OpenClaw Worker (src/index.ts)
    ↓ (Authorization: Bearer mk_xxx)
RaaS Gateway (raas.agencyos.network)
    ↓ (tracks usage in RAAS_USAGE_KV, adds X-Tenant-Id headers)
FastAPI Backend (BRIDGE_URL)
```

## Key Findings from Research

| Component | Status | Action Needed |
|-----------|--------|---------------|
| RaaS Gateway auth (JWT + mk_) | ✅ Production-ready | None |
| RaaS KV usage meter | ✅ Implemented | None |
| RaaS rate limiting | ✅ Per-tier limits | None |
| OpenClaw → RaaS integration | ❌ Missing | Add API key forwarding |
| OpenClaw usage tracking | ❌ Not needed | RaaS handles tracking |
| KV namespace config | ⚠️ Placeholder IDs | Update wrangler.toml |

## Phases

| Phase | Description | Status | Files |
|-------|-------------|--------|-------|
| 1. Setup & Configuration | KV namespaces, env vars | Pending | wrangler.toml, .dev.vars |
| 2. OpenClaw Worker Integration | Add RaaS Gateway forwarding | Pending | src/index.ts |
| 3. RaaS Gateway Enhancement | Optional: OpenClaw-specific endpoints | Pending | index.js |
| 4. KV Namespace Configuration | Create/verify KV bindings | Pending | Cloudflare Dashboard |
| 5. Testing & Verification | End-to-end flow | Pending | tests/ |
| 6. Documentation | Update docs | Pending | docs/ |

## Dependencies

- RaaS Gateway deployed at `raas.agencyos.network`
- OpenClaw Worker has `RAAS_GATEWAY_URL` env var
- mk_ API keys configured in RaaS Gateway `MK_API_KEYS` secret

## Success Criteria

1. OpenClaw Worker forwards requests to RaaS Gateway with `Authorization: Bearer mk_xxx`
2. Usage appears in `RAAS_USAGE_KV` under correct license key
3. Rate limiting enforced per tenant tier
4. Suspension checks block unauthorized tenants

## Unresolved Questions

1. Does OpenClaw need to support user-provided mk_ keys, or use single SERVICE_TOKEN?
2. Should Telegram user IDs map to tenant IDs, or use service-level auth?

---

## Phase Details

- [Phase 1](./phase-01-setup-configuration.md) — Setup & Configuration
- [Phase 2](./phase-02-openclaw-integration.md) — OpenClaw Worker Integration
- [Phase 3](./phase-03-raas-enhancement.md) — RaaS Gateway Enhancement
- [Phase 4](./phase-04-kv-configuration.md) — KV Namespace Configuration
- [Phase 5](./phase-05-testing-verification.md) — Testing & Verification
- [Phase 6](./phase-06-documentation.md) — Documentation
