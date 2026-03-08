---
phase: 6
title: "Documentation"
status: pending
effort: 30m
---

# Phase 6: Documentation

## Overview

Document the OpenClaw + RaaS Gateway integration for future reference and onboarding.

## Key Insights

Documentation needed:
1. Architecture overview
2. Configuration guide
3. Usage tracking API reference
4. Troubleshooting guide

## Requirements

### Functional
1. Create integration documentation
2. Update system architecture diagram
3. Document KV schema

### Non-Functional
1. Keep docs under 200 lines each
2. Use Vietnamese for user-facing docs

## Related Files

### Files to Create
- `apps/raas-gateway/docs/openclaw-integration.md` — Integration guide
- `docs/usage-metering-architecture.md` — Architecture overview

### Files to Update
- `apps/raas-gateway/README.md` — Add usage tracking section
- `docs/system-architecture.md` — Update diagram

## Documentation Structure

### openclaw-integration.md

```markdown
# OpenClaw + RaaS Gateway Integration

## Overview

OpenClaw Worker forwards requests to RaaS Gateway for centralized authentication
and usage tracking.

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| RAAS_GATEWAY_URL | Yes | RaaS Gateway URL |
| RAAS_SERVICE_TOKEN | Yes | Service-level API key |

### KV Namespaces

| Namespace | Purpose | TTL |
|-----------|---------|-----|
| RAAS_USAGE_KV | Usage metrics | 24h |
| SUSPENSION_CACHE | Tenant status | 1h |

## Usage Tracking

### Key Format

```
Key: usage:{licenseKey}:{hourBucket}
Example: usage:mk_test123:2026-03-08-19
```

### Value Structure

```json
{
  "licenseKey": "mk_test123",
  "tenantId": "tenant1",
  "tier": "free",
  "endpoint": "extension",
  "method": "POST",
  "requestCount": 1,
  "payloadSize": 150,
  "timestamp": "2026-03-08T19:30:00.000Z",
  "hourBucket": "2026-03-08-19"
}
```

## API Reference

### GET /v1/usage

Retrieve usage metrics for a license key.

**Query Parameters:**
- `start_hour` (optional): Start hour bucket
- `end_hour` (optional): End hour bucket
- `limit` (optional): Max results (default: 100)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "license_key": "mk_test123",
  "metrics": [...],
  "pagination": { "limit": 100, "offset": 0, "total": 50 }
}
```

## Troubleshooting

### Usage Not Tracking

1. Check `RAAS_USAGE_KV` binding exists
2. Verify API key format (must start with `mk_`)
3. Check worker logs for KV errors

### Rate Limit Errors

1. Check tenant tier limits
2. Verify `RATE_LIMIT_KV` binding
3. Wait 60s for sliding window reset
```

### system-architecture.md Update

Add to architecture diagram:

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Telegram   │ ──→ │  OpenClaw    │ ──→ │ RaaS Gateway│
│   Users     │     │   Worker     │     │  (Edge)     │
└─────────────┘     └──────────────┘     └──────────────┘
                                              │
                          ┌───────────────────┤
                          │                   │
                   ┌──────▼──────┐    ┌───────▼───────┐
                   │ RAAS_USAGE  │    │ RATE_LIMIT_KV │
                   │     KV      │    │               │
                   └─────────────┘    └───────────────┘
                          │
                          ▼
                   ┌──────────────┐
                   │ FastAPI      │
                   │ Backend      │
                   └──────────────┘
```

## Success Criteria

- [ ] Integration guide created
- [ ] Architecture diagram updated
- [ ] KV schema documented
- [ ] API reference complete
- [ ] Troubleshooting guide helpful

## Next Steps

After documentation complete:
1. Update project roadmap with completed status
2. Add changelog entry
3. Mark plan as completed
