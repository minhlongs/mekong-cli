# Code Review Report: `packages/mekong-engine/src/routes/`

**Date:** 2026-03-19
**Reviewer:** code-reviewer agent
**Scope:** 19 route files (~2,800 LOC total)

---

## Tổng quan

Thư mục chứa 19 file route definitions cho mekong-engine API, xây dựng trên nền tảng **Hono** (Cloudflare Workers). Các routes bao phủ nhiều chức năng: authentication, billing, governance, ledger, content, CRM, onboarding, payments, v.v.

### Files Reviewed

| File | LOC | Purpose |
|------|-----|---------|
| `rbac.ts` | 69 | Role-based access control |
| `settings.ts` | 88 | Tenant LLM settings |
| `content.ts` | 181 | AI content generation |
| `decentralization.ts` | 259 | Governance phases |
| `ledger.ts` | 194 | Double-entry accounting |
| `conflicts.ts` | 231 | Conflict resolution |
| `matching.ts` | 274 | Skill matching |
| `equity.ts` | 333 | Cap table management |
| `funding.ts` | 250 | Quadratic funding |
| `crm.ts` | 225 | Contact management |
| `governance.ts` | 400 | Governance, voting, reputation |
| `onboarding.ts` | 260 | 4-step onboarding |
| `revenue.ts` | 180 | Revenue distribution |
| `payment-vn.ts` | 259 | MoMo/VNPAY integration |
| `tasks.ts` | 166 | Task/mission management |
| `agents.ts` | 64 | Agent execution |
| `billing.ts` | 212 | Billing, Polar webhooks |
| `chat.ts` | 286 | Zalo/FB webhooks |
| `reports.ts` | 234 | Analytics & reporting |

---

## ✅ Điểm Mạnh

### 1. Input Validation với Zod
- Hầu hết routes sử dụng Zod schemas để validate request bodies
- Schema đặt tên rõ ràng: `createContactSchema`, `updatePostSchema`
- Error handling thống nhất: trả về `VALIDATION_ERROR` với chi tiết `error.errors`

### 2. Error Handling Pattern
- Sử dụng `handleAsync` wrapper cho hầu hết handlers
- Custom error types: `createError`, `ERROR_CODES`
- HTTP status codes phù hợp: 400, 404, 402, 409

### 3. Security Controls
- **Authentication**: `authMiddleware` áp dụng cho hầu hết routes
- **Rate Limiting**: `rateLimitMiddleware`, `webhookRateLimit`
- **Payload Limits**: `payloadSizeLimit()` cho POST requests
- **Signature Verification**: Webhook handlers (MoMo, VNPAY, Polar, Zalo, Facebook)
- **Replay Attack Prevention**: `isDuplicateWebhookEvent`, `recordWebhookEvent`

### 4. Database Access Pattern
- `handleDb` wrapper thống nhất
- Atomic batch operations cho double-entry ledger
- Idempotency keys cho transfer operations

### 5. Double-Entry Ledger Implementation
- `ledger.ts` implement proper accounting pattern
- Journal entries + transaction lines
- Balance updates atomic trong batch

---

## ⚠️ Issues & Recommendations

### 🔴 CRITICAL

#### 1. SQL Injection Risk - Dynamic Table Names (funding.ts:38-58)
```typescript
await db.exec(`
  CREATE TABLE IF NOT EXISTS funding_rounds (...)
`).catch(() => {})
```
- **Issue**: `.exec()` với inline SQL strings, catch silence mọi errors
- **Risk**: Nếu có user input lọt vào đây = SQL injection
- **Fix**: Dùng prepared statements, không catch silence

#### 2. Hardcoded Secrets trong Code (payment-vn.ts:39-44)
```typescript
const PRICING_VN = [
  { id: 'free', name: 'Miễn phí', price_vnd: 0, credits: 10 },
  // ...
]
```
- **Issue**: Pricing hardcoded thay vì load từ config/database
- **Risk**: Khó update pricing mà không deploy code mới
- **Fix**: Load từ database table `pricing_tiers`

#### 3. Missing Tenant Validation (nhiều files)
Nhiều routes giả định `tenant.id` từ auth middleware nhưng không verify tenant tồn tại trong DB:
```typescript
const tenant = c.get('tenant')
// ❌ Không check: await db.prepare('SELECT id FROM tenants WHERE id = ?').bind(tenant.id).first()
```
- **Files affected**: `rbac.ts`, `content.ts`, `ledger.ts`, `crm.ts`, v.v.
- **Fix**: Thêm tenant validation helper

#### 4. Duplicate Code - ensureAccount Pattern (ledger.ts:33-46, revenue.ts:58-77)
- **Issue**: Logic similar copy-paste qua `revenue.ts`
- **Fix**: Move vào shared utility `packages/mekong-engine/src/lib/ledger-utils.ts`

---

### 🟡 MEDIUM

#### 5. Inconsistent Error Response Format
```typescript
// Pattern 1 (governance.ts)
return c.json({ error: 'Validation failed', code: 'VALIDATION_ERROR', details: errors }, 400)

// Pattern 2 (hầu hết files khác)
return c.json(createError('VALIDATION_ERROR', 'Validation failed', error.errors), 400)
```
- **Fix**: Thống nhất 1 format trong toàn bộ routes

#### 6. Magic Numbers (decentralization.ts:23-52)
```typescript
export const PHASES = [
  { name: 'foundation', power_distribution: { leadership: 50, founders: 25, community: 25 }, ... },
]
```
- **Issue**: Percentages hardcoded, khó customize per-tenant
- **Fix**: Load từ database config table `decentralization_config`

#### 7. LLM Client Initialization Lặp Lại
- **Files**: `content.ts:60-65`, `onboarding.ts:187-192`, `reports.ts:104-109`
- **Issue**: Code lặp lại 10+ lần
- **Fix**: Tạo factory function `getLLMClient(c: Context)` trong `src/lib/llm-factory.ts`

#### 8. Missing Tests
- Không có test files trong thư mục routes
- **Risk**: Regression bugs khi refactor
- **Fix**: Thêm `packages/mekong-engine/src/routes/__tests__/` với Vitest tests

---

### 🟢 LOW

#### 9. Inconsistent Naming
- `decentralRoutes` vs `ledgerRoutes` - không nhất quán
- **Fix**: Chuẩn hóa `camelCaseRoutes`

#### 10. Type Safety Gaps
```typescript
// governance.ts:98
return r as { results?: any[] }
```
- **Fix**: Define interfaces: `interface QueryResult { results?: Stakeholder[] }`

---

## 🔒 Security Audit Summary

| Category | Status | Notes |
|----------|--------|-------|
| Input Validation | ✅ Good | Zod schemas comprehensive |
| Authentication | ✅ Good | `authMiddleware` consistent |
| Authorization | ⚠️ Partial | Thiếu tenant validation |
| SQL Injection | ⚠️ Risk | `.exec()` trong funding.ts |
| XSS | ✅ Good | React auto-escape (frontend) |
| CSRF | N/A | API stateless, JWT-based |
| Rate Limiting | ✅ Good | Multiple strategies |
| Secrets Management | ⚠️ Fair | Some hardcoded values |
| Webhook Security | ✅ Good | Signature verification |
| Replay Attack Prevention | ✅ Good | Event deduplication |

---

## 📋 Action Items

### Priority 1 (Critical)
- [ ] **funding.ts**: Replace `.exec()` với prepared statements
- [ ] **All routes**: Add tenant existence validation
- [ ] **revenue.ts**: Extract `ensureAcct` vào shared utility

### Priority 2 (High)
- [ ] **All files**: Unify error response format
- [ ] **llm-client**: Create factory function để reduce duplication
- [ ] **pricing**: Move hardcoded tiers vào database

### Priority 3 (Medium)
- [ ] **Tests**: Add unit tests for critical routes (ledger, billing, auth)
- [ ] **Types**: Replace `any` với proper interfaces
- [ ] **Naming**: Standardize route variable naming

---

## 📊 Code Quality Score

| Metric | Score | Notes |
|--------|-------|-------|
| Type Safety | 7/10 | Some `any` usage |
| Error Handling | 8/10 | Consistent but fragmented |
| Security | 7/10 | Good controls, some gaps |
| Maintainability | 6/10 | Duplication, needs refactoring |
| Test Coverage | 0/10 | No tests |
| **Overall** | **5.6/10** | Functional but needs hardening |

---

## ❓ Unresolved Questions

1. **funding.ts:38-58**: Tại sao dùng `.exec()` thay vì migrations?
2. **payment-vn.ts**: Pricing hardcoded có phải intentional design không?
3. **chat.ts:227-267**: `processMessage` function không được export/test - circular dependency?
4. **billing.ts:133-156**: Polar webhook handling - có cần retry logic cho failed credit additions?
