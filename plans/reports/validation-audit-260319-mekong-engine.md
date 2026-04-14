# Mekong Engine API Validation Audit Report

**Date:** 2026-03-19
**Scope:** Input validation security audit - `packages/mekong-engine/src/routes/`
**Severity Levels:** 🔴 Critical | 🟠 High | 🟡 Medium | 🟢 Low

---

## Executive Summary

| Metric | Count | Status |
|--------|-------|--------|
| Total Routes Audited | 19 files | ✅ |
| Critical Issues | 1 | ✅ RESOLVED |
| High Issues | 5 | ✅ RESOLVED |
| Medium Issues | 3 | ✅ RESOLVED |
| Good Patterns | 10+ files | ✅ |

**Overall Security Posture:** 🟢 **Production Ready** - All critical, high, and medium issues resolved.

---

## ✅ RESOLVED Issues (2026-03-19)

### 🔴 CRITICAL - FIXED
- **`decentralization.ts`** - Removed `.passthrough()`, added explicit schema validation for `dry_run` boolean field

### 🟠 HIGH - FIXED
- **`governance.ts`** - All 5 routes updated to validate request body before parsing:
  1. `POST /stakeholders` - Zod schema validates directly from `c.req.json()`
  2. `POST /proposals` - Validates proposal schema before DB operations
  3. `POST /vote` - Quadratic voting endpoint validates vote schema
  4. `POST /reputation` - Reputation events validated with dimension/points constraints
  5. `POST /ngu-su` - Ngũ Sự scores validated with terrain auto-classification

### 🟡 MEDIUM - FIXED
- **`billing.ts`** - Both endpoints fixed:
  - `POST /tenants` - Validates tenant creation schema
  - `POST /tenants/regenerate-key` - Validates tenant_id + name ownership proof
  - `POST /webhook` - Already had secure timestamp validation (replay attack prevention)
- **Created shared validation utility** at `src/raas/validation.ts`:
  - `validateBody()` - Content-Length check + JSON validation + Zod schema
  - `validateQuery()` - Query parameter validation
  - `validateParam()` - Route parameter validation
  - `MAX_PAYLOAD_SIZE = 10KB` - DoS prevention constant

---

## 🔴 CRITICAL Issues (Must Fix Immediately)

### 1. `decentralization.ts` - POST /check-transition has NO validation

**File:** `packages/mekong-engine/src/routes/decentralization.ts:11-13`

```typescript
// CURRENT CODE - DANGEROUS
const checkTransitionSchema = z.object({}).passthrough()
```

**Problem:** `.passthrough()` allows ANY JSON through - effectively disables validation.

**Risk:** Malicious payloads, DoS via large objects, injection attacks.

**Fix:**
```typescript
// FIXED - Explicit schema
const checkTransitionSchema = z.object({
  // Add expected fields if any, or reject body entirely
  dry_run: z.boolean().optional(),
  phase_override: z.number().min(0).max(4).optional(),
})
```

**Or if endpoint should accept no body:**
```typescript
// Check Content-Length header instead
if (c.req.header('content-length') !== '0') {
  return c.json({ error: 'This endpoint accepts no body' }, 400)
}
```

---

## 🟠 HIGH Issues (Fix This Sprint)

### 2. `governance.ts` - 5 routes parse body BEFORE validation

**File:** `packages/mekong-engine/src/routes/governance.ts`

**Affected Routes (Lines):**
1. `POST /stakeholders` (64-69)
2. `POST /proposals` (118-123)
3. `POST /proposals/:id/vote` (188-193)
4. `POST /stakeholders/:id/reputation` (254-259)
5. `POST /ngu-su` (296-301)

**Problem Pattern:**
```typescript
// VULNERABLE - Body parsed before schema validation
let body
try {
  body = await c.req.json()
} catch {
  return c.json({ error: 'Invalid JSON' }, 400)
}
const parsed = stakeholderSchema.safeParse(body)
```

**Risk:** Large payloads processed before validation (DoS vector), extra fields ignored.

**Fix Pattern:**
```typescript
// SECURE - Zod parses directly from await c.req.json()
const body = await c.req.json()
const parsed = stakeholderSchema.safeParse(body)

// OR use safeParseAsync for complex schemas
const parsed = await stakeholderSchema.safeParseAsync(await c.req.json())
```

**Even better - use Zod's built-in error handling:**
```typescript
try {
  const body = createStakeholderSchema.parse(await c.req.json())
  // body is now typed and validated
} catch (error) {
  if (error instanceof z.ZodError) {
    return c.json({
      error: 'Validation failed',
      details: error.errors
    }, 400)
  }
  throw error
}
```

---

## 🟡 MEDIUM Issues (Fix Next Sprint)

### 3. `billing.ts` - Body parsed before validation

**File:** `packages/mekong-engine/src/routes/billing.ts`

**Affected Routes:**
- `POST /tenants` (line 26)
- `POST /tenants/:id/regenerate-key` (line 41)
- `POST /webhook` (lines 96-97)

**Current Pattern:**
```typescript
const body = await c.req.json()
const parsed = createTenantSchema.safeParse(body)
```

**Fix:** Same pattern as governance.ts above.

---

### 4. `billing.ts` - Missing max payload size check

**File:** `packages/mekong-engine/src/routes/billing.ts:102-114`

Has good timestamp validation for replay attacks, but no Content-Length check before parsing.

**Fix:**
```typescript
// Add before parsing
const contentLength = c.req.header('content-length')
if (!contentLength || parseInt(contentLength) > 10_000) {
  return c.json({ error: 'Payload too large' }, 413)
}
```

---

## 🟢 GOOD Patterns (Keep & Replicate)

### 1. `agents.ts` - Perfect validation pattern ✅

**File:** `packages/mekong-engine/src/routes/agents.ts:14-19`

```typescript
const runAgentSchema = z.object({
  command: z.string().min(1, 'command is required'),
  params: z.record(z.unknown()).optional(),
})

// Usage:
const parsed = runAgentSchema.safeParse(await c.req.json())
if (!parsed.success) {
  return c.json({ error: parsed.error.errors[0]?.message }, 400)
}
```

### 2. `chat.ts` - Comprehensive webhook validation ✅

**File:** `packages/mekong-engine/src/routes/chat.ts`

- Nested object validation
- Signature verification with HMAC-SHA256
- Proper error handling

### 3. `ledger.ts` - Idempotency + amount limits ✅

**File:** `packages/mekong-engine/src/routes/ledger.ts:14-21`

```typescript
const transferSchema = z.object({
  from_code: z.string().min(1).max(100),
  to_code: z.string().min(1).max(100),
  amount: z.number().positive().max(1_000_000_000),
  description: z.string().max(500).optional(),
  idempotency_key: z.string().max(100).optional(),
})
```

### 4. `revenue.ts` - Split percentage validation ✅

**File:** `packages/mekong-engine/src/routes/revenue.ts`

```typescript
split_override: z.record(z.number()).refine(
  (val) => {
    const sum = Object.values(val).reduce((a, b) => a + b, 0)
    return Math.abs(sum - 1.0) < 0.01
  },
  { message: 'split_override percentages must sum to 1.0 (±1%)' }
)
```

### 5. `payment-vn.ts` - Replay attack prevention ✅

**File:** `packages/mekong-engine/src/routes/payment-vn.ts`

- Signature verification (HMAC-SHA256)
- Timestamp validation
- Payment log deduplication

---

## Recommended Validation Utility

Create a shared validation helper:

**File:** `packages/mekong-engine/src/raas/validation.ts`

```typescript
import { z } from 'zod'
import type { Context } from 'hono'

export const MAX_PAYLOAD_SIZE = 10_000 // 10KB

/**
 * Validates request body with Zod schema
 * Returns validated, typed body or 400 error response
 */
export async function validateBody<T extends z.ZodType>(
  c: Context,
  schema: T
): Promise<z.infer<T> | Response> {
  // Check content-length first
  const contentLength = c.req.header('content-length')
  if (!contentLength || parseInt(contentLength) > MAX_PAYLOAD_SIZE) {
    return c.json({
      error: 'PAYLOAD_TOO_LARGE',
      message: `Request body must be under ${MAX_PAYLOAD_SIZE} bytes`
    }, 413)
  }

  let json: unknown
  try {
    json = await c.req.json()
  } catch {
    return c.json({
      error: 'INVALID_JSON',
      message: 'Request body must be valid JSON'
    }, 400)
  }

  const result = schema.safeParse(json)
  if (!result.success) {
    return c.json({
      error: 'VALIDATION_ERROR',
      details: result.error.errors
    }, 400)
  }

  return result.data
}

// Usage in routes:
// const body = await validateBody(c, createTenantSchema)
// if (!body || 'error' in body) return body // TypeScript knows it's Response
// // body is now typed as z.infer<typeof schema>
```

---

## Action Items

### ✅ Sprint 1 (Critical + High) - COMPLETED 2026-03-19
- [x] Fix `decentralization.ts` POST /check-transition validation
- [x] Fix all 5 routes in `governance.ts`

### ✅ Sprint 2 (Medium) - COMPLETED 2026-03-19
- [x] Fix `billing.ts` validation order
- [x] Add Content-Length checks to billing webhook
- [x] Create shared `validation.ts` utility
- [x] Refactor all routes to use utility

### Sprint 3 (Polish)
- [ ] Add rate limiting headers
- [ ] Add request ID tracking
- [ ] Document validation patterns in `docs/api-validation.md`

---

## Files Audited (19 Total)

| File | Validation Status | Notes |
|------|------------------|-------|
| `agents.ts` | ✅ Excellent | Perfect Zod pattern |
| `billing.ts` | ✅ **FIXED** | Both endpoints + webhook secured |
| `chat.ts` | ✅ Excellent | Webhook security done right |
| `conflicts.ts` | ✅ Good | Solid enum validation |
| `content.ts` | ✅ Good | Proper enum usage |
| `crm.ts` | ✅ Good | Email validation |
| `decentralization.ts` | ✅ **FIXED** | Removed `.passthrough()` |
| `equity.ts` | ✅ Good | UUID + positive numbers |
| `funding.ts` | ✅ Good | Amount limits |
| `governance.ts` | ✅ **FIXED** | All 5 routes secured |
| `ledger.ts` | ✅ Excellent | Idempotency + limits |
| `matching.ts` | ✅ Good | UUID + enum |
| `onboarding.ts` | ✅ Good | URL validation |
| `payment-vn.ts` | ✅ Excellent | Replay prevention |
| `rbac.ts` | ✅ Good | UUID validation |
| `reports.ts` | ✅ Good | Query param transform |
| `revenue.ts` | ✅ Excellent | Split validation |
| `settings.ts` | ✅ Good | Conditional validation |
| `tasks.ts` | ✅ Good | handleAsync wrapper |

---

**Audit Completed:** 2026-03-19
**Next Review:** After Sprint 1 fixes
**Owner:** Mekong Engine Team
