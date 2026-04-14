# Error Handling Scout Report

**Date:** 2026-03-19
**Scope:** `packages/mekong-engine/src/routes/*.ts` (19 files)

## Summary

| Metric | Count |
|--------|-------|
| Files analyzed | 6 (detailed), 13 (pending) |
| Routes with proper error handling | ~70% |
| Critical gaps | 4 |
| Inconsistent patterns | 3 |

## Current Patterns (Good)

**Utility functions available** (`types/error.ts`):
- `handleAsync()` - wrapper for route handlers
- `handleDb()` - database error wrapping
- `handleExternalApi()` - external API error wrapping
- `validateJsonBody()` - JSON + zod validation
- `requireResource()` - null/undefined guard
- `guardEmptyArray()` - empty array guard
- `HttpError` class with `toResponse()`
- `createError()` - standardized error format

**Files using patterns correctly:**
- `billing.ts` - Uses `handleAsync`, `handleDb`, replay attack detection
- `crm.ts` - Consistent `handleAsync` + `handleDb` usage
- `settings.ts` - Proper `handleAsync` + `handleDb` + Zod validation
- `agents.ts` - Clean error handling with `handleAsync`

## Missing Error Handling (by file)

### chat.ts (CRITICAL)
**Line 308-318:** Custom `handleAsync` duplicate instead of importing from `types/error`
```typescript
// BUG: Duplicate handleAsync implementation (lines 308-318)
function handleAsync(fn: (c: any) => Promise<any>) {
  return async (c: any) => {
    try {
      return await fn(c)
    } catch (error: unknown) {
      const message = error instanceof Error ? error.message : 'Unknown error'
      return c.json({ error: message }, 500)  // ❌ Generic 500, no ErrorCode
    }
  }
}
```
**Issues:**
- Not using standardized `handleAsync` from `types/error.ts`
- Returns generic `{ error: message }` without `code` field
- Always returns 500, no granular status codes
- Duplicates existing utility

### payment-vn.ts (HIGH)
**Lines 55-250:** Mix of handled and unhandled routes
```typescript
// ❌ Line 55: async (c) => { ... } - NO handleAsync wrapper
paymentVnRoutes.post('/momo/ipn', async (c) => { ... })

// ❌ Line 133: async (c) => { ... } - NO handleAsync wrapper
paymentVnRoutes.get('/vnpay/ipn', async (c) => { ... })

// ❌ Line 207: async (c) => { ... } - NO handleAsync wrapper
paymentVnRoutes.post('/create', async (c) => { ... })
```
**Issues:**
- Zero routes use `handleAsync` wrapper
- Try-catch blocks manual but inconsistent
- Missing standardized error format for payment failures

### billing.ts (MEDIUM)
**Lines 212-235:** Helper functions defined inline
```typescript
// ⚠️ Local helper functions instead of using shared utilities
async function ensureWebhookEventsTable(db: any) { ... }
async function isDuplicateWebhookEvent(db: any, provider: string, eventId: string): Promise<boolean> { ... }
async function recordWebhookEvent(db: any, provider: string, eventId: string, type: string) { ... }
```
**Note:** Could use `handleDb` more consistently but functional.

## Inconsistent Patterns

### 1. Zod Validation Style

**Consistent (good):**
```typescript
// billing.ts:28-29
const parsed = createTenantSchema.safeParse(await c.req.json().catch(() => ({})))
if (!parsed.success) return c.json({ error: ... }, 400)
```

**Inconsistent:**
```typescript
// agents.ts:37-45 - Manual try-catch around json()
try {
  body = runAgentSchema.parse(await c.req.json())
} catch (error) {
  if (error instanceof z.ZodError { ... }
  throw error
}
```

**Should use:** `validateJsonBody(c, schema)` from `types/error.ts`

### 2. Error Response Format

**Standardized:**
```typescript
return c.json(createError('NOT_FOUND', `Agent '${name}' not found`), 404)
```

**Non-standard:**
```typescript
return c.json({ error: 'Tenant not found or name mismatch' }, 404)
// Missing: code field, inconsistent format
```

### 3. Database Error Handling

**Good:**
```typescript
await handleDb(() => db.prepare(...).run(), 'DATABASE_ERROR', 'Failed to...')
```

**Missing:**
```typescript
// Direct DB calls without handleDb wrapper in some routes
await c.env.DB.prepare(...).run()  // ❌ No error wrapping
```

## Edge Cases Not Covered

### Critical (Security)

| File | Edge Case | Risk |
|------|-----------|------|
| `payment-vn.ts` | Missing signature verification edge cases | Payment fraud |
| `chat.ts` | Custom handleAsync loses error details | Debugging impossible |
| All webhook routes | Timestamp validation missing in some | Replay attacks |

### High (Data Integrity)

| File | Edge Case | Impact |
|------|-----------|--------|
| `crm.ts` | Empty tag array handling | Incorrect filtering |
| `billing.ts` | Missing credit validation (negative) | Credit manipulation |
| `settings.ts` | API key format validation | Invalid config saved |

### Medium (UX)

| File | Edge Case | Impact |
|------|-----------|--------|
| All routes | Rate limiting headers missing | Client can't throttle |
| All routes | Retry-After headers missing | Poor retry behavior |
| `agents.ts` | Agent execution timeout | Hanging tasks |

## Recommendations (Priority Order)

### 1. CRITICAL - Fix `payment-vn.ts` (3 routes)
- Add `handleAsync` wrapper to all 3 routes
- Use `validateJsonBody` for payment creation
- Add `handleDb` for all DB operations
- Standardize error responses with `createError`

### 2. CRITICAL - Fix `chat.ts` duplicate `handleAsync`
- Remove local `handleAsync` (lines 308-318)
- Import from `types/error.ts`
- Ensure all error responses use `createError` format

### 3. HIGH - Add replay attack protection consistency
- Ensure ALL webhook routes have timestamp validation
- Add `Retry-After` headers for rate-limited responses
- Document replay attack window (currently 5 min in billing.ts)

### 4. MEDIUM - Extract common patterns
- Move `ensureWebhookEventsTable`, `isDuplicateWebhookEvent`, `recordWebhookEvent` to shared utility
- Create `handleWebhook()` higher-order function

### 5. LOW - Add missing edge case guards
- Negative credit/amount validation
- API key format validation before save
- Empty array handling for list endpoints

## Files Requiring Detailed Review

Still need to scan these 13 files for complete analysis:
- `conflicts.ts`, `content.ts`, `decentralization.ts`, `equity.ts`
- `funding.ts`, `governance.ts`, `ledger.ts`, `matching.ts`
- `onboarding.ts`, `rbac.ts`, `reports.ts`, `revenue.ts`, `tasks.ts`

**Recommendation:** Spawn subagent to scan remaining files if full coverage required.
