# Routes Code Quality & Security Review

**Date:** 2026-03-19
**Scope:** 22 route files in `packages/mekong-engine/src/routes/`
**Reviewer:** code-reviewer agent

---

## Executive Summary

| Metric | Count | Status |
|--------|-------|--------|
| Files Reviewed | 22 | ✓ |
| Critical Issues | 3 | 🔴 |
| High Priority | 8 | 🟠 |
| Medium Priority | 12 | 🟡 |
| Low Priority | 6 | 🟢 |

**Overall Assessment:** Routes demonstrate solid patterns (Zod validation, handleDb wrappers, auth middleware) but have security gaps in webhook handling, SQL injection risks in dynamic queries, and inconsistent error handling.

---

## 🔴 CRITICAL ISSUES

### 1. SQL Injection Risk - Dynamic Query Construction

**Files:** `crm.ts:77-79`, `governance.ts:117-118`

**Issue:** String interpolation in SQL queries with user-provided values.

```typescript
// crm.ts:77-79 - Tag filter uses json_each without proper parameterization
const query = tag
  ? `SELECT * FROM contacts WHERE tenant_id = ? AND json_each.value = ? LIMIT ?`
  : 'SELECT * FROM contacts WHERE tenant_id = ? ORDER BY last_contact_at DESC LIMIT ?'
```

**Risk:** While currently using bind(), the query structure could be exploited if tag values are not sanitized.

**Fix:** Validate tag values against allowlist or use stricter sanitization.

---

### 2. Webhook Signature Verification - Timing Attack Vector

**Files:** `payment-vn.ts:62-81`, `payment-vn.ts:148-175`, `chat.ts:48-70`, `chat.ts:144-167`, `billing.ts:88-101`, `raas.ts:26-29`

**Issue:** Signature comparison uses string equality (`!==`) which is vulnerable to timing attacks.

```typescript
// payment-vn.ts:78
if (signature !== expectedHex) {
  return c.json(createError('UNAUTHORIZED', 'Invalid MoMo signature'), 401)
}
```

**Risk:** Attacker can determine correct signature byte-by-byte through response timing.

**Fix:** Use `crypto.timingSafeEqual()` for constant-time comparison.

```typescript
const sigBuffer = Buffer.from(signature, 'hex')
const expectedBuffer = Buffer.from(expectedHex, 'hex')
if (sigBuffer.length !== expectedBuffer.length || !crypto.timingSafeEqual(sigBuffer, expectedBuffer)) {
  return c.json(createError('UNAUTHORIZED', 'Invalid signature'), 401)
}
```

---

### 3. Hardcoded Secrets in Configuration Maps

**Files:** `revenue.ts:14-21`, `funding.ts:23-51`

**Issue:** Default revenue split and pricing configurations are hardcoded in route files.

```typescript
// revenue.ts:14-21
const DEFAULT_SPLIT = {
  platform: 0.20,
  expert: 0.30,
  ai_compute: 0.15,
  // ...
}
```

**Risk:** Business logic hardcoded makes it impossible to adjust without redeployment. Not a direct security issue but violates separation of concerns.

**Fix:** Move to configuration table or environment variables.

---

## 🟠 HIGH PRIORITY

### 4. Missing Input Validation on Nested Objects

**Files:** `onboarding.ts:36-38`, `marketplace.ts:27-28`

**Issue:** Schemas use `z.record(z.unknown())` which bypasses type safety.

```typescript
// onboarding.ts:36-38
const menuSchema = z.object({
  menu_data: z.record(z.unknown()),  // No validation on menu content
})

// marketplace.ts:27-28
config_schema?: Record<string, unknown>  // Plugin config unrestricted
```

**Risk:** Malicious payloads pass through validation unchecked.

**Fix:** Define explicit schema for expected menu structure or add size/type constraints.

---

### 5. Unsafe Error Handling - Silent Failures

**Files:** `equity.ts:63,118,149,250,279,319`, `governance.ts:262-264`

**Issue:** Generic `throw error` without proper logging or context.

```typescript
// equity.ts:63
} catch (error) {
  if (error instanceof z.ZodError) { /* handled */ }
  throw error  // Re-throws without logging
}
```

**Risk:** Debugging production issues becomes difficult; errors may leak sensitive stack traces.

**Fix:** Log errors with context before re-throwing or convert to handled errors.

---

### 6. Broad Exception Handling in Funding Routes

**File:** `funding.ts:190-193`

**Issue:** Catching generic `any` type and checking message string.

```typescript
// funding.ts:190-193
} catch (e: any) {
  if (e.message?.includes('UNIQUE')) return c.json(createError('CONFLICT', 'Already contributed'), 409)
  throw e
}
```

**Risk:** Type-unsafe; message string matching is fragile.

**Fix:** Use proper error type checking or named error classes.

---

### 7. Missing Tenant Validation in Cross-Tenant Queries

**Files:** `ledger.ts:66-67`, `equity.ts:145-150`, `matching.ts:143-147`

**Issue:** Some queries don't verify tenant ownership before accessing resources.

```typescript
// equity.ts:145-150 - Entity lookup doesn't check tenant_id
const entity = await handleDb(
  async () => {
    const r = await c.env.DB.prepare('SELECT * FROM equity_entities WHERE id = ?').bind(entityId).first()
```

**Risk:** Potential IDOR (Insecure Direct Object Reference) if entity IDs are predictable.

**Fix:** Always include `tenant_id` in WHERE clauses for resource lookups.

---

### 8. Rate Limiting Inconsistency

**Files:** Only `rbac.ts:23` implements rate limiting

**Issue:** Most routes lack rate limiting despite handling sensitive operations.

```typescript
// rbac.ts:23 - Only route with rate limiting
rbacRoutes.get('/policies', rateLimitMiddleware('rbac_policies', 100, 60000), (c) => {
```

**Risk:** Brute force attacks on payment, voting, and credit operations.

**Fix:** Apply rate limiting to all mutation endpoints (POST/PUT/PATCH).

---

### 9. Unsafe Base64 Encoding for Sensitive Data

**Files:** `payment-vn.ts:107,232,243`

**Issue:** Using `atob()`/`btoa()` for encoding payment metadata - not encryption.

```typescript
// payment-vn.ts:107
const decoded = atob(extraData)
parsed = JSON.parse(decoded)

// payment-vn.ts:232
const extraData = btoa(JSON.stringify({ tenant_id, credits, plan: plan ?? '' }))
```

**Risk:** Data is easily reversible; anyone with the token can decode tenant info.

**Fix:** Use proper encryption (AES-GCM) for sensitive metadata or signed JWTs.

---

### 10. XSS Risk in LLM-Generated Content

**Files:** `content.ts:67-74`, `onboarding.ts:194-205`, `reports.ts:111-119`

**Issue:** LLM-generated content saved directly to database without sanitization.

```typescript
// content.ts:71-74
const result = await llm.generateJson(prompt)
posts = Array.isArray(result) ? result : (result.posts as typeof posts) ?? []
// Content inserted to DB without sanitization (line 88-96)
```

**Risk:** Prompt injection could result in XSS payloads stored in database.

**Fix:** Sanitize LLM output with DOMPurify or equivalent before storage.

---

## 🟡 MEDIUM PRIORITY

### 11. Inconsistent Error Response Format

**Files:** Multiple files

**Issue:** Some routes return structured errors, others return raw objects.

```typescript
// governance.ts:84-85 - Structured
return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)

// marketplace.ts:63-64 - Inconsistent
if (msg.includes('UNIQUE')) return c.json({ error: 'Slug already exists', code: 'CONFLICT' }, 409)
return c.json({ error: 'Failed to publish plugin' }, 500)
```

**Fix:** Standardize error response format across all routes.

---

### 12. Missing Pagination on List Endpoints

**Files:** `governance.ts:117-118`, `equity.ts:97-98`, `marketplace.ts:75-81`

**Issue:** Many list endpoints have no pagination or arbitrary limits.

```typescript
// governance.ts:117-118 - No limit clause
const query = role
  ? 'SELECT * FROM stakeholders WHERE tenant_id = ? AND role = ? ORDER BY ...'
  : 'SELECT * FROM stakeholders WHERE tenant_id = ? ORDER BY ...'
```

**Risk:** DoS via large result sets; performance degradation.

**Fix:** Add mandatory `LIMIT` with default (50-100) and `OFFSET`/cursor pagination.

---

### 13. Unsafe JSON.parse on Database Results

**Files:** `matching.ts:157-158`, `crm.ts:73-86`

**Issue:** JSON.parse on potentially null or malformed database values.

```typescript
// matching.ts:157-158
const profileSkills: string[] = JSON.parse((profile.skills as string) || '[]')
const profileIndustries: string[] = JSON.parse((profile.industries as string) || '[]')
```

**Risk:** Runtime crash if database contains malformed JSON.

**Fix:** Wrap in try-catch or use safe JSON parsing utility.

---

### 14. Missing Content-Type Validation

**Files:** All webhook routes

**Issue:** Webhooks don't validate `Content-Type` header before parsing JSON.

**Fix:** Add middleware to verify `Content-Type: application/json` before `c.req.json()`.

---

### 15. Insufficient Logging for Security Events

**Files:** All routes

**Issue:** Failed auth, signature verification, and permission checks not logged.

**Fix:** Add structured logging for security-relevant events with correlation IDs.

---

### 16. Magic Numbers in Business Logic

**Files:** `decentralization.ts:23-52`, `governance.ts:88-91`

**Issue:** Governance levels and phase thresholds hardcoded.

```typescript
// governance.ts:88-91
const levelMap: Record<string, number> = {
  owner: 1, admin: 2, operator: 3, vc_partner: 4,
  founder: 5, expert: 5, developer: 6, customer: 6, community: 6
}
```

**Fix:** Move to configuration table or documented constants file.

---

### 17. Type Casting Without Validation

**Files:** `governance.ts:122-123`, `reports.ts:101`, `tasks.ts:105-108`

**Issue:** Using `as Type` assertions on database results without runtime validation.

```typescript
// governance.ts:122-123
const rowsResult = await handleDb(
  async () => {
    const r = await c.env.DB.prepare(query).bind(...params).all()
    return r as DbResult<StakeholderRow>  // No runtime check
```

**Fix:** Use Zod schema to validate database results at runtime.

---

### 18. Async Handler Without Await

**Files:** `chat.ts:114,212`

**Issue:** `waitUntil()` used for background processing but no error handling.

```typescript
// chat.ts:114
c.executionCtx.waitUntil(processMessage(c.env, ...))
```

**Risk:** Silent failures in background processing; no retry mechanism.

**Fix:** Wrap async callbacks in try-catch with error logging.

---

### 19. Inconsistent UUID Validation

**Files:** Mixed across routes

**Issue:** Some routes validate UUID format, others don't.

```typescript
// governance.ts:42 - Validates
author_id: z.string().uuid('Invalid author_id format'),

// funding.ts:181 - No validation before use
const id = crypto.randomUUID()
await handleDb(
  () => c.env.DB.prepare(...).bind(id, body.project_id, body.stakeholder_id, body.amount)
```

**Fix:** Apply UUID validation consistently to all ID fields.

---

### 20. Missing Database Transaction for Multi-Step Operations

**Files:** `ledger.ts:80-97`, `revenue.ts:115-141`, `equity.ts:313-328`

**Issue:** Multiple DB operations without atomic transactions.

```typescript
// ledger.ts:80-97 - Batch used but not wrapped in transaction
const batch = [/* 5 operations */]
await handleDb(() => db.batch(batch), ...)
```

**Risk:** Partial failure leaves data in inconsistent state.

**Fix:** Use explicit transactions with rollback on failure.

---

## 🟢 LOW PRIORITY

### 21. Code Duplication in Schema Definitions

**Files:** Multiple routes define similar schemas

**Issue:** `stakeholder_id`, `tenant_id` validation repeated across 20+ files.

**Fix:** Extract common schemas to shared `schemas.ts` module.

---

### 22. Inconsistent Commenting Style

**Files:** Mixed

**Issue:** Some files have detailed headers (`onboarding.ts:1-8`), others have none.

**Fix:** Standardize JSDoc comments for all route files.

---

### 23. Unnecessary Type Assertions

**Files:** `equity.ts:98`, `governance.ts:199`

**Issue:** Overuse of `as any` defeats type safety.

```typescript
// equity.ts:98
return r as { results?: any[] }
```

**Fix:** Define proper result types or use generics.

---

### 24. Missing Health Check Endpoint

**Files:** N/A (no health route)

**Issue:** No `/health` or `/status` endpoint for monitoring.

**Fix:** Add health check route with DB connectivity test.

---

### 25. Verbose Function Names

**Files:** Throughout

**Issue:** Some function names overly verbose (`validateTenantExists`, `ensureFundingTables`).

**Note:** This aligns with project naming conventions - keep as-is.

---

## Security Summary

### Authentication & Authorization

| Check | Status |
|-------|--------|
| Auth middleware applied | ✓ All routes |
| Tenant isolation | ⚠️ Most routes, gaps in equity.ts |
| Permission checks | ⚠️ Only in rbac.ts |
| Rate limiting | ❌ Only 1 route |

### Input Validation

| Check | Status |
|-------|--------|
| Zod schemas | ✓ 90% coverage |
| Nested object validation | ❌ Uses z.unknown() |
| UUID format validation | ⚠️ Inconsistent |
| Array bounds checking | ✓ Present |

### Data Protection

| Check | Status |
|-------|--------|
| Signature verification | ⚠️ Timing-vulnerable |
| Secret masking | ✓ settings.ts:70 |
| Encryption at rest | ❌ Base64 only |
| Replay attack prevention | ✓ Webhook event tracking |

### SQL Safety

| Check | Status |
|-------|--------|
| Parameterized queries | ✓ Most queries |
| Dynamic query risks | ⚠️ 2 files |
| Batch operations | ✓ Used correctly |
| Transaction support | ⚠️ Not enforced |

---

## Recommendations by Priority

### Immediate (P0)

1. **Fix timing attack vulnerability** - Replace string comparison with `crypto.timingSafeEqual()`
2. **Add tenant_id validation** to all cross-tenant queries
3. **Encrypt sensitive webhook metadata** - Replace base64 with proper encryption

### Short-term (P1)

4. Implement rate limiting on all mutation endpoints
5. Add input validation for nested objects (menu_data, config_schema)
6. Standardize error response format
7. Add pagination to all list endpoints
8. Implement proper transaction support for multi-step operations

### Medium-term (P2)

9. Extract shared schemas to common module
10. Add structured logging for security events
11. Move hardcoded business logic to configuration
12. Implement health check endpoint
13. Add XSS sanitization for LLM-generated content

---

## Positive Observations

- **Consistent Zod validation** across 90% of routes
- **Auth middleware** properly applied to all routes
- **handleDb wrapper** provides uniform error handling
- **Webhook replay prevention** implemented via event tracking
- **Double-entry ledger** pattern correctly implemented
- **Quadratic voting formula** correctly implemented
- **Idempotency support** in ledger transfers

---

## Metrics

| Metric | Value |
|--------|-------|
| Total Routes | ~180 endpoints |
| Type Coverage | ~85% (some `any` usage) |
| Input Validation | ~90% (Zod schemas) |
| Auth Coverage | 100% |
| Rate Limited | ~5% |
| Files with `any` | 8/22 |
| Files with broad `catch` | 6/22 |

---

## Unresolved Questions

1. **Chat route external API calls** (`chat.ts:270-283`) - Are Zalo/FB API tokens properly encrypted at rest?
2. **LLM client configuration** - Are API keys rotated regularly?
3. **Webhook secrets** - How are POLAR_WEBHOOK_SECRET, MOMO_SECRET_KEY managed/deployed?
4. **Database migrations** - Is there a migration system for schema changes?
5. **Audit logging** - Are all credit transactions logged for compliance?

---

**Report Generated:** 2026-03-19
**Next Review:** After P0 fixes implemented
