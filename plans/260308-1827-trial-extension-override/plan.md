---
title: "Trial Extension Override Implementation"
description: "KV-based trial extension system with admin API and suspension bypass prevention"
status: pending
priority: P1
effort: 6h
branch: master
tags: [raas, gateway, trial, kv, admin-api]
created: 2026-03-08
---

# Trial Extension Override System

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RaaS Gateway (Cloudflare Worker)                     │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  Request → [1] Auth Middleware → [2] Suspension Check → [3] Trial Check │
│                   ↓                        ↓                    ↓       │
│            JWT/API Key valid?      SUSPENDED/REVOKED?    extendedUntil? │
│                   ↓                        ↓                    ↓       │
│            ┌──────┴──────┐          ┌─────┴─────┐       ┌───┴───┐       │
│           YES           NO        ACTIVE      BLOCKED   VALID EXPIRED   │
│            ↓                       ↓          ↓        ↓       ↓        │
│    [4] Rate Limit Check       ALLOW     BLOCK   ALLOW   BLOCK          │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│  KV Namespaces:                                                         │
│  - RATE_LIMIT_KV: Rate limiting counters                                │
│  - SUSPENSION_CACHE: Suspension status (suspended:{tenantId})           │
│  - TRIAL_EXTENSIONS: Trial extensions (trial:{tenantId}) ← NEW          │
├─────────────────────────────────────────────────────────────────────────┤
│  Admin API Endpoints:                                                   │
│  - POST /api/admin/trial/extend      → Grant extension                  │
│  - GET /api/admin/trial/:tenantId    → Get status                       │
│  - DELETE /api/admin/trial/:tenantId → Revoke extension                 │
└─────────────────────────────────────────────────────────────────────────┘
```

## Check Order (CRITICAL)

```
1. Suspension Status (BLOCK if SUSPENDED/REVOKED)
2. Trial Extension (ALLOW if extendedUntil > now)
3. Rate Limit (Apply normal rate limiting)
```

## Phase Files

| Phase | File | Status | Effort |
|-------|------|--------|--------|
| 1 | `phase-01-kv-trial-extension.md` | [ ] | 1h |
| 2 | `phase-02-auth-middleware-integration.md` | [ ] | 1h |
| 3 | `phase-03-suspension-bypass-prevention.md` | [ ] | 0.5h |
| 4 | `phase-04-analytics-logging.md` | [ ] | 0.75h |
| 5 | `phase-05-admin-api.md` | [ ] | 1.5h |
| 6 | `phase-06-testing.md` | [ ] | 1.25h |

## TODO Checklist

### Setup
- [ ] Create KV namespace: `wrangler kv:namespace create "TRIAL_EXTENSIONS"`
- [ ] Update `wrangler.toml` with new KV binding
- [ ] Deploy test environment

### Implementation
- [ ] Phase 1: Create `src/kv-trial-extension.js`
- [ ] Phase 2: Integrate into `index.js` request flow
- [ ] Phase 3: Verify suspension bypass prevention (check order)
- [ ] Phase 4: Add analytics logging
- [ ] Phase 5: Add admin API endpoints
- [ ] Phase 6: Write and run tests

### Verification
- [ ] All tests pass
- [ ] Manual testing with curl commands
- [ ] Deploy to production
- [ ] Verify production health check

## Success Criteria

```bash
# KV namespace created
wrangler kv:key list --namespace-id=<TRIAL_EXTENSIONS_ID>

# Module exports correct functions
grep "^export" src/kv-trial-extension.js
# Expected: checkTrialExtension, grantTrialExtension, revokeTrialExtension, getTrialExtension, buildTrialStatusHeader

# Admin API endpoints respond
curl -X GET https://raas.agencyos.network/api/admin/trial/test-tenant \
  -H "Authorization: Bearer $SERVICE_TOKEN"

# Suspension bypass prevention verified
# (suspended tenant with trial extension → 403 BLOCK)

# All tests pass
vitest run tests/kv-trial-extension*.test.js
```

## Dependencies

- Cloudflare Workers KV (already configured)
- Existing suspension checker pattern (`kv-suspension-checker.js`)
- Existing auth middleware (`edge-auth-handler.js`)
- SERVICE_TOKEN configured in environment

## Unresolved Questions

1. **Default extension period**: Recommend 7 days (configurable via admin API)
2. **Max extensions per tenant**: Recommend tracking in extension metadata, no hard limit
3. **Trial visibility in /v1/auth/validate**: YES, include `trial` object in response
