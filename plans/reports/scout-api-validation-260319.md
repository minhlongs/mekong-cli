# API Validation Audit Report - mekong-engine

**Date:** 2026-03-19
**Scope:** All API routes in `packages/mekong-engine/src`

---

## Routes Scanned

| Route File | Routes | Validation Status | Issues |
|------------|--------|-------------------|--------|
| `index.ts` | `GET /`, `GET /health`, `POST /cmd`, `GET /ai/test` | ⚠️ Partial | `/cmd` has minimal validation (only checks `goal` exists) |
| `tasks.ts` | `POST /`, `GET /`, `GET /:id`, `GET /:id/stream`, `POST /:id/cancel` | ✅ Good | Uses Zod schema for POST body, query param validation could be stricter |
| `billing.ts` | `POST /tenants`, `POST /tenants/regenerate-key`, `POST /webhook`, `GET /pricing`, `GET /credits`, `GET /credits/history` | ✅ Good | Zod schemas, webhook signature validation, replay attack prevention |
| `settings.ts` | `POST /llm`, `GET /llm`, `DELETE /llm` | ✅ Good | Zod schema with provider enum validation |
| `chat.ts` | `POST /webhook/zalo`, `GET /webhook/facebook`, `POST /webhook/facebook` | ✅ Good | Zod schemas, HMAC signature verification, replay attack prevention |
| `content.ts` | `POST /generate`, `GET /`, `PATCH /:id` | ✅ Good | Zod schemas with proper constraints |
| `crm.ts` | `GET /contacts`, `POST /contacts`, `POST /contacts/auto`, `GET /campaigns`, `POST /campaigns` | ✅ Good | Zod schemas, email validation |
| `payment-vn.ts` | `POST /momo/ipn`, `GET /vnpay/ipn`, `POST /create`, `GET /pricing-vn` | ✅ Good | Zod schemas, HMAC verification, amount validation |
| `agents.ts` | `GET /`, `POST /:name/run` | ⚠️ Partial | Basic Zod schema, no param validation on agent name |
| `governance.ts` | All governance routes | ✅ Good | Comprehensive Zod schemas with UUID validation, enum constraints |
| `equity.ts` | All equity routes | ✅ Good | UUID validation, numeric constraints, enum types |
| `revenue.ts` | `POST /split`, `GET /split-config`, `GET /summary` | ✅ Good | Complex schema with sum validation |
| `funding.ts` | All funding routes | ✅ Good | UUID validation, numeric constraints |
| `ledger.ts` | `POST /transfer`, `POST /topup`, `GET /balance`, `GET /history` | ✅ Good | Zod schemas, idempotency support |

---

## Validation Gaps Identified

### 1. `/cmd` Endpoint (index.ts:133) - MEDIUM PRIORITY

**Current:**
```typescript
const body = await c.req.json<{ goal: string }>()
if (!body.goal) return c.json({ error: 'Missing goal' }, 400)
```

**Issues:**
- No Zod schema for structured validation
- No max length check on `goal` (could be abused for DoS)
- No optional `params` validation

**Fix:**
```typescript
const cmdSchema = z.object({
  goal: z.string().min(1, 'Goal is required').max(5000, 'Goal must be ≤5000 characters'),
  params: z.record(z.unknown()).optional(),
})
```

### 2. Query Parameter Validation - LOW PRIORITY

Multiple routes have loose query parameter validation:

**Example (tasks.ts:51):**
```typescript
const limit = Math.min(Math.max(parseInt(c.req.query('limit') ?? '20', 10) || 20, 1), 100)
```

**Issues:**
- Manual parsing without Zod
- Silent fallback to defaults (could hide bugs)

**Fix:**
```typescript
const listQuerySchema = z.object({
  limit: z.coerce.number().int().min(1).max(100).optional().default(20),
  offset: z.coerce.number().int().min(0).optional().default(0),
})
```

### 3. Route Parameter Validation - LOW PRIORITY

Routes using `:id` params don't validate UUID format:

**Example (tasks.ts:64):**
```typescript
const id = c.req.param('id')
```

**Fix:**
```typescript
const idParamSchema = z.object({
  id: z.string().uuid('Invalid ID format'),
})
```

### 4. `agents.ts` Agent Name Validation - LOW PRIORITY

```typescript
const name = c.req.param('name')
const agent = AVAILABLE_AGENTS.find((a) => a.name === name)
```

**Issues:**
- No validation that agent name is one of the allowed values
- Returns 404 for unknown agents (correct but could be more descriptive)

**Fix:**
```typescript
const agentNameSchema = z.object({
  name: z.enum(['git', 'file', 'shell', 'lead-hunter', 'content-writer', 'recipe-crawler']),
})
```

---

## Existing Validation Strengths

The codebase already has excellent validation patterns:

1. **Zod schemas** - Used consistently across most routes
2. **HMAC signature verification** - Webhooks (Zalo, Facebook, MoMo, VNPAY, Polar)
3. **Replay attack prevention** - Webhook events table with duplicate detection
4. **Timestamp validation** - Polar webhooks (5-minute window)
5. **UUID validation** - Governance, equity, funding routes
6. **Numeric constraints** - Positive checks, max limits
7. **Enum validation** - Provider types, status values
8. **Payload size limit middleware** - Global 10KB limit
9. **Error handling utilities** - `handleAsync`, `handleDb`, `validateJsonBody`, `createError`

---

## Recommendations

### Priority 1: Fix `/cmd` Endpoint
- Add Zod schema with max length
- Validate optional `params` object

### Priority 2: Add Query Param Utility
- Create `validateQuery` helper using Zod
- Apply to all pagination endpoints

### Priority 3: Add Route Param Validation
- Validate UUID format on all `:id` params
- Validate enum values on `:name` params

### Priority 4: Export and Reuse `validateBody`
The `validation.ts` file already exports good utilities:
- `validateBody<T>()` - Parse + validate request body
- `validateQuery<T>()` - Validate query params
- `validateParam<T>()` - Validate route params

These should be used more consistently across routes.

---

## Unresolved Questions

1. Should the `/cmd` endpoint support a max_tokens or timeout parameter?
2. Should query param validation be strict (return error) or lenient (use default)?
3. Should we add rate limiting specific to the `/cmd` endpoint given its LLM cost?
