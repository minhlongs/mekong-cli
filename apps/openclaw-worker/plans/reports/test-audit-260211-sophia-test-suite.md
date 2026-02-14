# Test Suite Audit Report — Sophia AI Factory

**Date:** 2026-02-11 | **Mode:** Auto | **Scope:** Full test suite, failures, coverage gaps

---

## Kết Quả Test Suite

| Metric | Value |
|--------|-------|
| Test Files | 32 |
| Total Tests | 241 |
| Passed | 241 (100%) |
| Failed | 0 |
| Runtime | 4.45s |
| Framework | Vitest |

---

## ĐÃ FIX (1 file)

### 1. `src/app/api/check-access/route.test.ts` — TypeScript Error Fix
- **Vấn đề:** `TS2352` — Mock object cast trực tiếp sang `SupabaseClient` type không đủ overlap
- **Line:** 44-50
- **Fix:** Thêm `as unknown` intermediate cast: `} as unknown as ReturnType<...>`
- **Verify:** 0 TS errors, 4/4 tests pass

---

## Coverage Analysis

### Overall: 20% lines (LOW)

| Metric | Coverage |
|--------|----------|
| Statements | 19.85% |
| Branches | 17.88% |
| Functions | 14.48% |
| Lines | 20.39% |

### Modules với Coverage TỐT (>80%)

| Module | Lines | Notes |
|--------|-------|-------|
| `src/lib/schemas/settings.ts` | 100% | Schema validation |
| `src/lib/validation/services.ts` | 100% | Service validation |
| `src/lib/intelligence/normalization.ts` | 100% | Score normalization |
| `src/lib/intelligence/runner.ts` | 100% | Intelligence runner |
| `src/lib/ingestion/runner.ts` | 100% | Ingestion runner |
| `src/utils/encryption.ts` | 96% | AES-256-GCM |
| `src/lib/gateway/adapters/*` | 97.5% | Channel adapters |
| `src/lib/ingestion/base-adapter.ts` | 93% | Base adapter |
| `src/lib/services/real/payment-service.ts` | 91% | Polar payments |

### Coverage GAPS Nghiêm Trọng (0%)

| Module | Files | Impact | Fix Recommendation |
|--------|-------|--------|-------------------|
| `src/lib/inngest/functions/` | 2 files (affiliates, campaign) | **HIGH** — Core business logic | Unit tests cho Inngest functions (mock `step.run`) |
| `src/lib/payments/` | 4 files (calculator, service, types, webhook) | **HIGH** — Revenue critical | Test webhook handler, commission calculator |
| `src/lib/services/mock/` | 4 files | LOW — Mock services | Skip — not production code |
| `src/lib/middleware/` | 1 file (auth) | MEDIUM — Auth middleware | Test auth flow, token validation |
| `src/lib/telegram/` (trừ bot) | 7 files (handlers, client, state, keyboard, formatter, setup, rate-limit) | MEDIUM — Telegram bot | Test command handlers, rate limiting |
| `src/lib/ingestion/adapters/` | 2 files (clickbank, shareasale) | MEDIUM — Data ingestion | Test adapter-specific parsing |
| `src/types/` | 3 files | N/A — Type-only files | No tests needed |
| `src/lib/supabase/` (trừ sophia-index) | 4 files | LOW — Supabase client wrappers | Minimal value — thin wrappers |
| `src/lib/utils/` | 1 file (timer-utility) | LOW | Test utility functions |
| `src/lib/templates/` | 1 file | LOW | Test template loading |

### Modules Cần Cải Thiện (~50-85%)

| Module | Lines | Gap Areas |
|--------|-------|-----------|
| `src/lib/gateway/smart-resume-engine.ts` | 59% | Lines 149-177 (edge cases) |
| `src/lib/intelligence/scoring.ts` | 83% | Lines 26-29 (error handling) |
| `src/lib/heygen/heygen-client.ts` | 86% | Lines 65-69 (error path) |
| `src/lib/telegram/telegram-bot.ts` | 73% | Lines 279-301 (error handlers) |

---

## Điểm Tích Cực

- 241 tests ALL PASS — zero flaky tests
- Runtime 4.45s — fast feedback loop
- Core business logic (scoring, ingestion, gateway) well-tested
- Encryption utility has 96% coverage
- Channel adapters (TikTok, YouTube, Telegram) at 97.5%
- Payment service (Polar) at 91%

## Priority Fix Order (Next Missions)

1. **Inngest functions** — Chứa toàn bộ campaign pipeline + affiliate scraping logic
2. **Payment webhook handler** — Revenue critical, validates Polar webhook signatures
3. **Commission calculator** — Tính toán revenue, phải chính xác
4. **Auth middleware** — Security critical
5. **Telegram command handlers** — User-facing bot logic

---

**Test Health Score: 8/10** (100% pass, 20% coverage → cần tăng coverage các module critical)
