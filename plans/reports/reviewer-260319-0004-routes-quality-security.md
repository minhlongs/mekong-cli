# Code Review Report — packages/mekong-engine/src/routes/

**Date:** 2026-03-19
**Reviewer:** code-reviewer agent
**Scope:** 15 route files (~2,100 LOC)
**Focus:** Security, authentication, input validation, type safety, error handling

---

## Executive Summary

| Metric | Value | Status |
|--------|-------|--------|
| Files Reviewed | 15 | - |
| Critical Issues | 2 | 🔴 Requires immediate fix |
| High Priority | 5 | 🟠 Should fix before production |
| Medium Priority | 8 | 🟡 Technical debt |
| Low Priority | 4 | 🟢 Nice-to-have |

**Overall Assessment:** Routes demonstrate solid security patterns (HMAC verification, auth middleware) but have gaps in webhook replay protection, inconsistent Zod validation coverage, and missing type guards on dynamic SQL.

---

## Critical Issues

### 1. MISSING AUTH — `chat.ts` Webhooks (CRITICAL)

**File:** `packages/mekong-engine/src/routes/chat.ts`
**Lines:** 11, 93

**Issue:** Zalo and Facebook webhook endpoints are PUBLIC (no `authMiddleware`). While webhooks inherently cannot use bearer auth, there is NO rate limiting or replay attack prevention.

```typescript
// Line 11: Zalo webhook — NO auth, NO rate limit
chatRoutes.post('/webhook/zalo', async (c) => { ... })

// Line 93: Facebook webhook — NO auth, NO rate limit
chatRoutes.post('/webhook/facebook', async (c) => { ... })
```

**Impact:**
- Attacker can spam webhooks to drain credits (calls `processMessage` → LLM → credit deduction)
- Replay attacks possible (no timestamp window check)
- DoS vector (no rate limiting)

**Fix:**
```typescript
// Add rate limiting middleware
import { rateLimit } from 'hono-rate-limit'

chatRoutes.post('/webhook/zalo',
  rateLimit({ limit: 100, window: 60 }), // 100 req/min per IP
  async (c) => { ... }
)

// Add replay attack prevention (like billing.ts line 104-114)
const timestamp = body.timestamp
if (timestamp && Date.now() - new Date(timestamp).getTime() > 5 * 60 * 1000) {
  return c.json({ error: 'Webhook timestamp too old' }, 401)
}
```

---

### 2. WEBHOOK REPLAY ATTACK — `billing.ts` Timestamp Check Weakness (CRITICAL)

**File:** `packages/mekong-engine/src/routes/billing.ts`
**Lines:** 103-114

**Issue:** Timestamp validation exists but uses client-provided `event.timestamp` which can be manipulated. Also, no nonce tracking for replay prevention.

```typescript
const timestamp = event.timestamp ?? event.created_at  // Trusts client input
if (age > 5 * 60 * 1000) { ... }  // 5-minute window
```

**Impact:** Attacker can capture valid webhook and replay with modified timestamp within 5-minute window.

**Fix:**
```typescript
// Track processed webhook IDs to prevent replay
const webhookId = event.id  // Polar.sh provides unique event ID
const seen = await db.prepare('SELECT 1 FROM webhook_events WHERE event_id = ?').bind(webhookId).first()
if (seen) return c.json({ error: 'Duplicate webhook', code: 'REPLAY' }, 409)

await db.prepare('INSERT INTO webhook_events (event_id, tenant_id, processed_at) VALUES (?, ?, datetime("now"))')
  .bind(webhookId, tenantId).run()
```

---

## High Priority Issues

### 3. INCOMPLETE ZOD VALIDATION — `ledger.ts`, `funding.ts`, `revenue.ts` (HIGH)

**Files:**
- `ledger.ts` — Lines 24-27 (manual type annotation, no Zod)
- `funding.ts` — Lines 40, 56, 69 (no validation)
- `revenue.ts` — Lines 24-28 (no validation)

**Issue:** These routes parse JSON directly without schema validation:

```typescript
// ledger.ts line 24
const body = await c.req.json<{ from_code: string; to_code: string; amount: number }>()

// funding.ts line 69
const body = await c.req.json<{ project_id: string; stakeholder_id: string; amount: number }>()
```

**Impact:**
- No validation of amount bounds (could be negative, overflow)
- No string length limits (DoS via large payloads)
- Type coercion vulnerabilities

**Fix:** Add Zod schemas:
```typescript
const transferSchema = z.object({
  from_code: z.string().min(1).max(100),
  to_code: z.string().min(1).max(100),
  amount: z.number().positive().max(1_000_000_000),
  description: z.string().max(500).optional(),
})
```

---

### 4. SQL INJECTION RISK — `equity.ts` Dynamic Query (HIGH)

**File:** `packages/mekong-engine/src/routes/equity.ts`
**Lines:** 72-82, 153

**Issue:** String interpolation in SQL query (line 153):

```typescript
// Line 153 — Uses string division in SQL calculation
const capShares = Math.floor((safe.principal_amount as number) /
  ((safe.valuation_cap as number) / (entity?.total_authorized_shares as number || 10000000)))
```

Also, `GROUP_CONCAT` query (lines 116-118) uses raw SQL with template literals (safe in this case, but pattern is risky).

**Impact:** If `entity?.total_authorized_shares` is manipulated to 0, division by zero. Not SQL injection but arithmetic vulnerability.

**Fix:**
```typescript
// Add null/zero guards
const totalAuthorized = entity?.total_authorized_shares as number || 10000000
if (totalAuthorized === 0) return c.json({ error: 'Invalid share configuration' }, 400)
if (!(safe.valuation_cap as number) > 0) return c.json({ error: 'Invalid valuation cap' }, 400)
```

---

### 5. MISSING ERROR HANDLING — `chat.ts` `processMessage` (HIGH)

**File:** `packages/mekong-engine/src/routes/chat.ts`
**Lines:** 166-206

**Issue:** `processMessage` function has no try-catch around critical operations:

```typescript
// Line 191-196: LLM call can fail silently
const { LLMClient } = await import('../core/llm-client')
const llm = new LLMClient({ ... })
const response = await llm.chat(messages, { max_tokens: 300, temperature: 0.7 })
```

**Impact:**
- Unhandled promise rejection crashes worker
- No fallback if LLM fails (user message lost)
- No error logging for debugging

**Fix:**
```typescript
async function processMessage(...) {
  try {
    // ... existing code
    const response = await llm.chat(messages, { max_tokens: 300, temperature: 0.7 })
    reply = response.content
  } catch (error) {
    console.error('LLM generation failed:', error)
    reply = 'Xin lỗi, tôi đang gặp sự cố. Vui lòng thử lại sau.' // Fallback message
  }
  // ... rest of code
}
```

---

### 6. HARDCODED SECRETS IN FALLBACK — `chat.ts` (HIGH)

**File:** `packages/mekong-engine/src/routes/chat.ts`
**Lines:** 12-13, 88

```typescript
// Line 12-13
const secret = c.env.ZALO_APP_SECRET || c.env.ZALO_SECRET

// Line 88
const verifyToken = c.env.FB_VERIFY_TOKEN || 'mekong_verify'  // HARDCODED FALLBACK!
```

**Impact:** Default verify token `'mekong_verify'` is public knowledge — anyone can verify Facebook webhook.

**Fix:**
```typescript
const verifyToken = c.env.FB_VERIFY_TOKEN
if (!verifyToken) {
  console.warn('FB_VERIFY_TOKEN not configured — Facebook webhook verification disabled')
  return c.text('Forbidden', 403)  // Fail closed, not open
}
```

---

### 7. NO TENANT ISOLATION CHECK — `agents.ts` (HIGH)

**File:** `packages/mekong-engine/src/routes/agents.ts`
**Lines:** 21-35

**Issue:** Agent execution endpoint accepts any command without validation of what the agent can access:

```typescript
agentRoutes.post('/:name/run', authMiddleware, async (c) => {
  const body = await c.req.json<{ command: string; params?: Record<string, unknown> }>()
  // No validation of command content
  // No sandbox for shell agent
  return c.json({ status: 'accepted', ... })
})
```

**Impact:** If `shell` agent executes arbitrary commands, tenant could escape sandbox.

**Fix:**
- Add allowlist for permitted commands
- Validate `params` schema
- Add audit logging for agent execution

---

## Medium Priority Issues

### 8. INCONSISTENT ERROR FORMAT (MEDIUM)

**Files:** All route files

**Issue:** Error responses use different formats:

| File | Format |
|------|--------|
| `billing.ts` | `{ error: string, code?: string }` |
| `governance.ts` | `{ error: string, code: string, details: [] }` |
| `crm.ts` | `{ error: string }` |
| `ledger.ts` | `{ error: string, balance?: number }` |

**Impact:** Frontend error handling is inconsistent.

**Fix:** Standardize on:
```typescript
interface ApiError {
  error: string
  code: 'BAD_REQUEST' | 'UNAUTHORIZED' | 'FORBIDDEN' | 'NOT_FOUND' | 'CONFLICT' | 'SERVICE_UNAVAILABLE'
  details?: Array<{ field: string; message: string }>
}
```

---

### 9. MISSING RATE LIMITS — `/v1/tasks` (MEDIUM)

**File:** `packages/mekong-engine/src/routes/tasks.ts`
**Lines:** 27-41

**Issue:** Mission creation deducts credits but has no rate limiting:

```typescript
taskRoutes.post('/', creditMeteringMiddleware, async (c) => {
  // Deducts credits, creates mission
  // No rate limit on mission creation frequency
})
```

**Impact:** Attacker with valid API key can rapidly create missions to exhaust credits.

**Fix:** Add rate limiting per tenant:
```typescript
import { rateLimit } from 'hono-rate-limit'

taskRoutes.post('/',
  rateLimit({ limit: 10, window: 60 }), // 10 missions/min
  creditMeteringMiddleware,
  async (c) => { ... }
)
```

---

### 10. WEAK EMAIL VALIDATION — `governance.ts` (MEDIUM)

**File:** `packages/mekong-engine/src/routes/governance.ts`
**Line:** 16

```typescript
email: z.string().email().optional().or(z.literal('')),
```

**Issue:** Allows empty string as valid email.

**Fix:**
```typescript
email: z.string().email().optional().refine((val) => !val || val.length > 0, 'Email cannot be empty string'),
// Or simply:
email: z.string().email().optional().nullable(),
```

---

### 11. NO ESCAPING — `onboarding.ts` LLM Prompt (MEDIUM)

**File:** `packages/mekong-engine/src/routes/onboarding.ts`
**Lines:** 147-148

```typescript
const faqPrompt = `Given this cafe menu: ${JSON.stringify(body.menu_data).slice(0, 1000)}
Generate 5 FAQ Q&A pairs...`
```

**Issue:** `JSON.stringify` prevents injection but truncation at 1000 chars could break JSON structure.

**Fix:**
```typescript
const menuJson = JSON.stringify(body.menu_data).slice(0, 900) + '...[truncated]'
const faqPrompt = `Given this cafe menu: ${menuJson}\nGenerate...`
```

---

### 12. ASYNC RACE CONDITION — `crm.ts` Upsert (MEDIUM)

**File:** `packages/mekong-engine/src/routes/crm.ts`
**Lines:** 104-138

**Issue:** Check-then-insert pattern is not atomic:

```typescript
const existing = await db.prepare('SELECT id, visit_count FROM contacts WHERE ...').first()
if (existing) {
  await db.prepare('UPDATE contacts SET visit_count = ...').run()  // Race condition
} else {
  await db.prepare('INSERT INTO contacts ...').run()
}
```

**Impact:** Concurrent requests create duplicate contacts.

**Fix:** Use `INSERT ... ON CONFLICT DO UPDATE`:
```typescript
const id = `ct_${tenant.id}_${body.external_id}`
await db.prepare(`
  INSERT INTO contacts (id, tenant_id, external_id, platform, name, visit_count, last_contact_at)
  VALUES (?, ?, ?, ?, ?, 1, datetime('now'))
  ON CONFLICT(external_id, platform, tenant_id) DO UPDATE
  SET visit_count = contacts.visit_count + 1, last_contact_at = datetime('now')
`).bind(id, tenant.id, body.external_id, body.platform, body.name).run()
```

---

### 13. MISSING CONTENT-TYPE VALIDATION — `content.ts` (MEDIUM)

**File:** `packages/mekong-engine/src/routes/content.ts`
**Lines:** 100-135

**Issue:** PATCH endpoint doesn't validate that `scheduled_at` is valid ISO date:

```typescript
if (body.scheduled_at) { fields.push('scheduled_at = ?'); values.push(body.scheduled_at) }
```

**Fix:**
```typescript
if (body.scheduled_at) {
  const date = new Date(body.scheduled_at)
  if (isNaN(date.getTime())) return c.json({ error: 'Invalid scheduled_at date format' }, 400)
  fields.push('scheduled_at = ?')
  values.push(body.scheduled_at)
}
```

---

### 14. NO MAX LIMIT — `reports.ts` (MEDIUM)

**File:** `packages/mekong-engine/src/routes/reports.ts`
**Lines:** 82, 86

**Issue:** No pagination limits on aggregate queries (potential DoS via large tenant data).

**Fix:** Add explicit limits even for COUNT queries (D1 optimization).

---

### 15. HARDCODED MAGIC NUMBERS — `billing.ts` (MEDIUM)

**File:** `packages/mekong-engine/src/routes/billing.ts`
**Lines:** 30-31, 53-69

```typescript
await addCredits(c.env.DB, tenant.id, 10, 'welcome: free tier bonus')  // Magic number 10
const POLAR_PRODUCT_CREDITS: Record<string, number> = { ... }  // Magic numbers
```

**Fix:** Move to config file:
```typescript
// config/credits.ts
export const WELCOME_CREDITS = 10
export const POLAR_PRODUCT_CREDITS = { ... }

// billing.ts
import { WELCOME_CREDITS, POLAR_PRODUCT_CREDITS } from '../config/credits'
await addCredits(c.env.DB, tenant.id, WELCOME_CREDITS, 'welcome: free tier bonus')
```

---

## Low Priority Issues

### 16. CONSOLE.LOG IN PRODUCTION — `payment-vn.ts` (LOW)

**File:** `packages/mekong-engine/src/routes/payment-vn.ts`

**Issue:** No console.log found, but comment says "Mock URL" (lines 211, 224) — should be removed or moved to dev-only config.

---

### 17. DUPLICATE CODE — Webhook Signature Verification (LOW)

**Files:** `billing.ts`, `payment-vn.ts`, `chat.ts`

**Issue:** HMAC verification logic is duplicated 6+ times across files.

**Fix:** Extract to utility:
```typescript
// raas/webhook-verify.ts
export async function verifyWebhookSignature(
  secret: string, rawBody: string, signature: string, algorithm: 'sha256' | 'sha512' = 'sha256'
): Promise<boolean> { ... }
```

---

### 18. TYPE ANY USAGE — Multiple Files (LOW)

**Files:**
- `billing.ts` line 95: `// eslint-disable-next-line @typescript-eslint/no-explicit-any`
- `equity.ts` line 90: `vestingDetails = (detailedGrants.results || []).map((g: any) => ...)`
- `funding.ts` lines 100-113: `results: any[]`

**Fix:** Define proper interfaces:
```typescript
interface EquityGrant { vesting_months?: number; cliff_months?: number; shares: number; ... }
interface FundingResult { id: string; name: string; direct: number; qf_score: number; ... }
```

---

### 19. NO GRACEFUL DEGRADATION — `content.ts` LLM Fallback (LOW)

**File:** `packages/mekong-engine/src/routes/content.ts`
**Lines:** 51-53

```typescript
} catch {
  return c.json({ error: 'LLM generation failed' }, 502)
}
```

**Issue:** Returns 502 but doesn't offer fallback (e.g., save draft with placeholder).

---

## Positive Observations

| Practice | Files | Quality |
|----------|-------|---------|
| ✅ HMAC webhook verification | `billing.ts`, `payment-vn.ts`, `chat.ts` | Excellent |
| ✅ Zod validation (where used) | `billing.ts`, `crm.ts`, `governance.ts`, `tasks.ts`, `settings.ts` | Good |
| ✅ Auth middleware pattern | 12/15 files | Good |
| ✅ Parameterized SQL queries | All files | Excellent |
| ✅ Credit metering middleware | `tasks.ts`, `revenue.ts` | Good |
| ✅ Idempotency keys | `ledger.ts` line 36-39 | Excellent |
| ✅ Atomic batch operations | `ledger.ts`, `equity.ts`, `revenue.ts` | Excellent |
| ✅ Timestamp replay prevention | `billing.ts` (partial) | Good |

---

## Security Score by Layer

| Layer | Score | Notes |
|-------|-------|-------|
| Authentication | 7/10 | Good middleware, missing on chat webhooks |
| Authorization | 8/10 | Tenant isolation consistent |
| Input Validation | 6/10 | Zod used in 5/15 files only |
| SQL Injection | 9/10 | All queries parameterized |
| XSS Prevention | N/A | API-only, no direct DOM |
| CSRF Protection | N/A | API uses bearer tokens |
| Webhook Security | 6/10 | Signature OK, replay gaps |
| Rate Limiting | 3/10 | Missing entirely |
| Error Handling | 6/10 | Inconsistent formats |

---

## Recommended Actions (Prioritized)

### Immediate (Before Next Deploy)
1. **Add rate limiting to `chat.ts` webhooks** — Prevent DoS and credit drain
2. **Fix hardcoded Facebook verify token fallback** — Security vulnerability
3. **Add replay attack prevention to billing webhook** — Track processed event IDs

### Short-term (This Sprint)
4. **Add Zod schemas to `ledger.ts`, `funding.ts`, `revenue.ts`** — Input validation
5. **Extract webhook verification to utility function** — DRY, consistency
6. **Standardize error response format** — Developer experience
7. **Add try-catch to `chat.ts` `processMessage`** — Reliability

### Medium-term (Next Sprint)
8. **Implement rate limiting on `/v1/tasks`** — Credit protection
9. **Fix CRM upsert race condition** — Data integrity
10. **Add type definitions to replace `any`** — Type safety

---

## Metrics

| Metric | Value |
|--------|-------|
| Files with auth middleware | 12/15 (80%) |
| Files with Zod validation | 5/15 (33%) |
| Files with HMAC verification | 3/15 (20%) |
| Type coverage (estimated) | ~85% |
| Parameterized SQL queries | 100% |
| Rate limited endpoints | 0/15 (0%) |

---

## Unresolved Questions

1. **Agent sandboxing**: What prevents the `shell` agent from escaping tenant isolation? Is there a container boundary?
2. **Credit deduction race**: Can concurrent mission creation cause double-spending of credits?
3. **Webhook event storage**: Should webhook events be logged to a `webhook_events` table for audit purposes?
4. **LLM prompt injection**: Has the KB lookup in `chat.ts` been tested against prompt injection attacks?

---

## Report Location
`/Users/macbook/mekong-cli/plans/reports/reviewer-260319-0004-routes-quality-security.md`
