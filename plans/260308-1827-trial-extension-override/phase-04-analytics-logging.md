---
title: "Phase 4: Analytics Logging"
priority: P2
status: pending
effort: 0.75h
---

# Phase 4: Analytics Logging

## Overview

Add audit trail logging for trial extension checks, grants, and revocations.

## Events to Log

| Event | Trigger | Log Level | Data |
|-------|---------|-----------|------|
| `trial.extension_check` | Every request with trial check | INFO | tenantId, hasExtension, expiresIn |
| `trial.extension_granted` | Admin grants extension | INFO | tenantId, extendedBy, period, reason |
| `trial.extension_revoked` | Admin revokes extension | INFO | tenantId, revokedBy |
| `trial.expired` | Extension expires | WARN | tenantId, expiredAt |

## Files to Create

### `src/kv-trial-analytics.js`

**Functions:**

1. `logTrialEvent(env, eventType, data)` → Log trial event
   - Uses `console.log()` for Cloudflare Workers log aggregation
   - Structured JSON format for parsing

2. `buildTrialEventData(eventType, data)` → Build event object
   - Returns: `{ event_type, timestamp, tenant_id, ...data }`

## Implementation Pattern

```javascript
// Structured logging for Cloudflare Workers
function logTrialEvent(env, eventType, data) {
  const event = {
    event_type: `trial.${eventType}`,
    timestamp: new Date().toISOString(),
    tenant_id: data.tenantId,
    ...data
  };
  console.log(JSON.stringify(event));
}
```

## Files to Modify

### `src/kv-trial-extension.js`

Add logging calls to:

1. `checkTrialExtension()` → Log `trial.extension_check`
2. `grantTrialExtension()` → Log `trial.extension_granted`
3. `revokeTrialExtension()` → Log `trial.extension_revoked`

### `index.js`

Add logging for expiration detection (optional):
```javascript
if (trialResult.hasExtension && trialResult.expiresIn < 0) {
  logTrialEvent(env, 'expired', { tenantId, extendedUntil: trialResult.extendedUntil });
}
```

## Implementation Steps

- [ ] Create `src/kv-trial-analytics.js` with logging functions
- [ ] Add import to `src/kv-trial-extension.js`
- [ ] Add log calls in grant/revoke/check functions
- [ ] Test log output format

## Success Criteria

```bash
# Analytics module exists
ls -la src/kv-trial-analytics.js

# Log calls in trial extension functions
grep "logTrialEvent" src/kv-trial-extension.js
# Should have 3+ calls

# Structured JSON format
grep "event_type" src/kv-trial-analytics.js
```

## Log Output Example

```json
{
  "event_type": "trial.extension_granted",
  "timestamp": "2026-03-08T18:30:00.000Z",
  "tenant_id": "tenant-123",
  "extended_by": "admin-456",
  "extension_period_days": 7,
  "reason": "Payment plan upgrade",
  "extended_until": "2026-03-15T18:30:00.000Z"
}
```

## Dependencies

- Phase 1 complete (trial extension functions exist)

## Integration with Existing Analytics

This logs to Cloudflare Workers console. For integration with external analytics:

- Option A: Use `analytics.bindings` in wrangler.toml
- Option B: Webhook to external analytics service
- Option C: Forward to algo-trader analytics module

**Recommendation:** Start with console.log, upgrade to analytics binding later.
