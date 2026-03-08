---
title: "Phase 1: KV Trial Extension Schema"
priority: P1
status: pending
effort: 1h
---

# Phase 1: KV Trial Extension Schema

## Overview

Create KV helper functions for trial extension storage and retrieval, following the existing pattern from `kv-suspension-checker.js`.

## KV Schema

### Key Format
```
trial:{tenantId}
```

### Value Structure
```json
{
  "extendedUntil": "2026-03-15T18:00:00.000Z",
  "reason": "Manual extension by admin",
  "extendedBy": "admin-user-id",
  "createdAt": "2026-03-08T18:00:00.000Z",
  "extensionPeriodDays": 7
}
```

### TTL Strategy
```
TTL = (extendedUntil - now) + 24h buffer
Example: 7-day extension = 8 days TTL
```

## Files to Create

### `src/kv-trial-extension.js`

**Functions:**

1. `checkTrialExtension(env, tenantId)` → Check if tenant has valid trial extension
   - Returns: `{ hasExtension: boolean, extendedUntil: string|null, expiresIn: number|null }`
   - Fail-open: KV errors return `hasExtension: false`

2. `grantTrialExtension(env, tenantId, extensionPeriodDays, extendedBy, reason)` → Grant extension
   - Writes to KV with appropriate TTL
   - Returns: `{ success: boolean, extendedUntil: string }`

3. `revokeTrialExtension(env, tenantId)` → Revoke extension
   - Deletes from KV
   - Returns: `{ success: boolean }`

4. `getTrialExtension(env, tenantId)` → Get full extension details
   - Returns: `{ extension: object|null, expiresIn: number|null }`

5. `buildTrialStatusHeader(trialResult)` → Build response headers
   - Returns: `{ 'X-Trial-Status': string, 'X-Trial-Expires': string }`

## Implementation Steps

- [ ] Create `src/kv-trial-extension.js` with all helper functions
- [ ] Follow existing pattern from `kv-suspension-checker.js`
- [ ] Add JSDoc comments for all functions
- [ ] Handle KV not configured (fail-open)
- [ ] Handle KV read/write errors gracefully

## Success Criteria

```bash
# KV namespace created
wrangler kv:namespace create "TRIAL_EXTENSIONS"

# Functions exported correctly
grep -E "^export (async )?function" src/kv-trial-extension.js
# Expected: checkTrialExtension, grantTrialExtension, revokeTrialExtension, getTrialExtension, buildTrialStatusHeader

# No syntax errors
node --check src/kv-trial-extension.js
```

## Related Files

- Create: `src/kv-trial-extension.js`
- Reference: `src/kv-suspension-checker.js` (pattern)
- Update: `wrangler.toml` (add KV namespace)

## Risks

- KV read latency could slow down auth flow → Mitigation: Keep queries simple, TTL-based
- TTL miscalculation → Mitigation: Add 24h buffer, test edge cases
