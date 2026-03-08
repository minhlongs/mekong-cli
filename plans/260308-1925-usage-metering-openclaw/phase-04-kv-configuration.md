---
phase: 4
title: "KV Namespace Configuration"
status: pending
effort: 30m
---

# Phase 4: KV Namespace Configuration

## Overview

Create and configure Cloudflare KV namespaces for usage metering and suspension caching.

## Key Insights

RaaS Gateway uses 3 KV namespaces:
1. `RATE_LIMIT_KV` — Already configured (id: `982a12a5ea414244988a51d743eb14e7`)
2. `RAAS_USAGE_KV` — Placeholder ID (needs creation)
3. `SUSPENSION_CACHE` — Placeholder ID (needs creation)

## Requirements

### Functional
1. Create missing KV namespaces
2. Update wrangler.toml with correct IDs
3. Verify KV access from Workers

### Non-Functional
1. Consistent naming across environments
2. Proper TTL settings for cost optimization

## Related Code Files

### Files to Modify
- `apps/raas-gateway/wrangler.toml` — Update KV IDs

### Files to Verify
- `apps/raas-gateway/src/kv-usage-meter.js` — Uses `RAAS_USAGE_KV`
- `apps/raas-gateway/src/kv-suspension-checker.js` — Uses `SUSPENSION_CACHE`

## Implementation Steps

### Step 1: Create RAAS_USAGE_KV

```bash
cd apps/raas-gateway

# Create namespace
wrangler kv:namespace create "RAAS_USAGE_KV"
# Output: id = "abc123..."

# Update wrangler.toml with the ID
```

### Step 2: Create SUSPENSION_CACHE

```bash
# Create namespace
wrangler kv:namespace create "SUSPENSION_CACHE"
# Output: id = "def456..."

# Update wrangler.toml with the ID
```

### Step 3: Update wrangler.toml

Edit `apps/raas-gateway/wrangler.toml`:

```toml
# KV namespace for RaaS usage metering (hourly aggregated metrics)
[[kv_namespaces]]
binding = "RAAS_USAGE_KV"
id = "abc123_actual_id"
preview_id = "abc123_actual_id"

# KV namespace for tenant suspension cache
[[kv_namespaces]]
binding = "SUSPENSION_CACHE"
id = "def456_actual_id"
preview_id = "def456_actual_id"
```

### Step 4: Verify KV Access

```bash
# Test KV write
wrangler kv:key put --namespace-id=abc123 test:key "test_value"

# Test KV read
wrangler kv:key get --namespace-id=abc123 test:key

# Should return: "test_value"
```

### Step 5: Configure TTL Settings

Verify TTL in `kv-usage-meter.js`:
- Usage metrics: 86400 seconds (24 hours) — ✅ Already set
- Suspension cache: Check `kv-suspension-checker.js` for TTL

## Success Criteria

- [ ] `RAAS_USAGE_KV` created and configured
- [ ] `SUSPENSION_CACHE` created and configured
- [ ] wrangler.toml updated with correct IDs
- [ ] KV read/write test passes
- [ ] Worker deploys with KV bindings

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| Wrong KV ID | High — runtime errors | Double-check IDs in wrangler.toml |
| KV cost overrun | Low — minimal usage | TTL ensures auto-cleanup, keep under free tier |
| Preview vs prod mismatch | Medium — works locally, fails in prod | Use same IDs for preview_id and id |

## Next Steps

Proceed to [Phase 5: Testing & Verification](./phase-05-testing-verification.md)
