---
title: "Phase 3: Suspension Bypass Prevention"
priority: P0
status: pending
effort: 0.5h
---

# Phase 3: Suspension Bypass Prevention

## Overview

**CRITICAL SECURITY**: Ensure suspended/revoked accounts CANNOT use trial extensions to bypass suspension.

## Security Rule

```
SUSPENDED/REVOKED → BLOCK (regardless of trial extension)
TRIAL EXTENSION → ALLOW (only if NOT suspended)
```

## Check Order Enforcement

The check order in `index.js` MUST be:

```javascript
// 1. Authentication (line 225)
const { authenticated, tenantId, role } = authenticate(request, env);
if (!authenticated) return 401;

// 2. Suspension Check (line 236) ← FIRST
const suspensionResult = await checkSuspensionStatus(env, tenantId);
if (suspensionResult.blocked) return 403;

// 3. Trial Extension Check (line 245) ← SECOND (only reached if NOT suspended)
const trialResult = await checkTrialExtension(env, tenantId);
// Trial extension does NOT override suspension

// 4. Rate Limit (line 247) ← THIRD
const rlResult = await checkRateLimit(env, tenantId, role);
```

## Why This Works

- Suspension check returns 403 immediately if blocked
- Trial check only runs if suspension check passes
- No additional code needed in trial extension module
- **The order of checks is the security control**

## Verification

### Test Cases

```javascript
// Case 1: Suspended tenant with trial extension → BLOCK
// suspensionResult.blocked = true → returns 403 before trial check

// Case 2: Active tenant with trial extension → ALLOW
// suspensionResult.blocked = false → proceeds to trial check → allowed

// Case 3: Active tenant without trial extension → Normal rate limit
// suspensionResult.blocked = false → trialResult.hasExtension = false → rate limit
```

## Implementation Steps

- [ ] Verify check order in `index.js` is: auth → suspension → trial → rate
- [ ] Add comment documenting security order (line 235):
  ```javascript
  // --- SUSPENSION CHECK: MUST run before trial check (security) ---
  ```
- [ ] Add comment at trial check (line 244):
  ```javascript
  // --- TRIAL CHECK: Only reached if NOT suspended (bypass prevention) ---
  ```

## Files to Modify

- `index.js` (add security comments, verify order)

## Success Criteria

```bash
# Check order verified
grep -n "SUSPENSION CHECK\|TRIAL CHECK" index.js
# Should show suspension before trial

# Security comments present
grep -c "bypass prevention" index.js
# Should be >= 1
```

## Dependencies

- Phase 2 complete (trial check integrated)

## Risks

- Future code changes could reorder checks → Mitigation: Add clear comments
- Someone might add "suspension override" feature → Mitigation: Document in plan.md
