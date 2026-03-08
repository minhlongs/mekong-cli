---
title: "Phase 2: Auth Middleware Integration"
priority: P1
status: pending
effort: 1h
---

# Phase 2: Auth Middleware Integration

## Overview

Integrate trial extension check into the RaaS Gateway request flow, positioned after suspension check and before rate limiting.

## Request Flow Change

### Current Flow (index.js line 225-256)
```
authenticate() → suspension check → rate limit → route handler
```

### New Flow
```
authenticate() → suspension check → TRIAL EXTENSION CHECK → rate limit → route handler
```

## Files to Modify

### `index.js`

**Changes:**

1. Import trial extension functions (line 10):
```javascript
import { checkTrialExtension, buildTrialStatusHeader } from './src/kv-trial-extension.js';
```

2. Add trial check after suspension check (after line 244):
```javascript
// --- TRIAL EXTENSION CHECK: Allow trial if extended ---
const trialResult = await checkTrialExtension(env, tenantId);
```

3. Update `/v1/auth/validate` response (line 262-287):
```javascript
return jsonResponse({
  valid: true,
  tenant_id: tenantId,
  role,
  features,
  suspension: { ... },
  trial: {
    hasExtension: trialResult.hasExtension,
    extendedUntil: trialResult.extendedUntil,
    expiresIn: trialResult.expiresIn
  },
  rateLimit: { ... }
}, 200, {
  ...corsHeaders,
  ...rlHeaders,
  ...buildSuspensionStatusHeader(suspensionResult),
  ...buildTrialStatusHeader(trialResult)
});
```

## Integration Points

| Location | Change |
|----------|--------|
| Line 10 | Add import for `checkTrialExtension`, `buildTrialStatusHeader` |
| Line 245 | Add trial check after suspension check |
| Line 262+ | Include `trial` object in `/v1/auth/validate` response |
| Line 286 | Add trial headers to response |

## Response Headers

```
X-Trial-Status: active|expired|none
X-Trial-Expires: <ISO date or empty>
```

## Implementation Steps

- [ ] Read `index.js` to understand current flow
- [ ] Add import statement at top
- [ ] Add trial check after suspension check (line ~245)
- [ ] Update `/v1/auth/validate` response to include trial status
- [ ] Add response headers
- [ ] Verify syntax with `node --check index.js`

## Success Criteria

```bash
# Import added
grep "kv-trial-extension" index.js

# Trial check in request flow
grep -A2 "TRIAL EXTENSION" index.js

# Trial status in validate response
grep -A5 "trial:" index.js | head -10

# No syntax errors
node --check index.js
```

## Dependencies

- Phase 1 complete (`src/kv-trial-extension.js` exists)
- KV namespace `TRIAL_EXTENSIONS` created

## Risks

- Breaking existing auth flow → Mitigation: Keep trial check isolated, fail-open
- Response size increase → Mitigation: Only add essential fields
