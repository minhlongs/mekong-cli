# Apex-OS — Console.log/debug Cleanup (Mission 3)

**Date:** 2026-02-11
**Scope:** `apps/apex-os/` production code (src/, backend/, mobile/src/, supabase/functions/)
**Rule:** Max 5 files per mission

## Scan Results

| Area | console.log/debug | console.error/warn | Total |
|------|-------------------|-------------------|-------|
| `src/` | 0 (logger only) | 0 | 0 |
| `backend/services/` | 5 | 5 | 10 |
| `mobile/src/` | 22 | 79 | 101 |
| `supabase/functions/` | 4 | 1 | 5 |
| `scripts/` (excluded) | 195+ | - | - |
| **Total production** | **31** | **85** | **116** |

## 5 Files Đã Sửa

### 1. `backend/services/agent-execution.ts`
**Trước:** 4 console.log + 3 console.error (raw)
**Sau:** 0 console — tất cả chuyển sang `Logger` class từ `../utils/logger`
**Chi tiết:** Import Logger, tạo instance, replace 7 console calls → logger.info/logger.error

### 2. `mobile/src/shared/lib/viral-economics/cron-jobs.ts`
**Trước:** 4 console.log (progress logs cho cron jobs)
**Sau:** 0 console — xóa hoàn toàn, cron jobs chạy silent
**Chi tiết:** Removed monthly commission log, daily tier check log, hourly metrics log, unused `promotedCount` variable

### 3. `mobile/src/shared/lib/services/exchange-verification.ts`
**Trước:** 3 console.log + 2 console.error
**Sau:** 0 console.log, 2 console.error giữ (decrypt failure + referral link error)
**Chi tiết:** Removed verification start log, credential decryption success log, mock mode log

### 4. `mobile/src/shared/lib/market-maker/bot.ts`
**Trước:** 3 console.log + 1 console.error
**Sau:** 0 console.log, 1 console.error giữ (MM loop error catch)
**Chi tiết:** Removed bot start/stop lifecycle logs, removed bid/ask price logging

### 5. `mobile/src/shared/lib/binance-feed.ts`
**Trước:** 2 console.log + 3 console.error
**Sau:** 0 console.log, 3 console.error giữ (WebSocket error handling)
**Chi tiết:** Removed connected/disconnected lifecycle logs

## Build Verification
```
npx tsc --noEmit → 1 pre-existing error (CheckoutModal.test.tsx — unrelated)
0 new errors introduced ✅
```

## Issues Còn Lại (console.log/debug trong production code)

### Mobile — 11 files remaining (11 console.log/debug)
1. `mobile/src/shared/lib/ai/smart-router.ts` — 2
2. `mobile/src/shared/lib/trading/data-pipeline.ts` — 2
3. `mobile/src/shared/lib/analytics-mock.ts` — 2
4. `mobile/src/shared/lib/usage-tracking.ts` — 1
5. `mobile/src/shared/lib/notifications.ts` — 1
6. `mobile/src/shared/lib/agent/event-bus.ts` — 1
7. `mobile/src/shared/lib/monitoring/sentry.ts` — 1

### Supabase Functions — 2 files (4 console.log)
8. `supabase/functions/reverify-scheduler/index.ts` — 2
9. `supabase/functions/verify-exchange-mock/index.ts` — 2

### Backend — 1 file (1 console.log)
10. `backend/services/trading.ts` — 1

### Console.error/warn (production — cần chuyển sang logger)
- `mobile/src/shared/lib/` — 79 console.error/warn across 19 files
- Mobile hiện chưa có shared logger utility — cần tạo trước khi migrate

### Pre-existing TS Error
- `src/components/payments/__tests__/CheckoutModal.test.tsx:134` — `isOpen` prop không tồn tại trên `CheckoutModalProps`

## Unresolved Questions
1. Mobile cần shared logger utility tương tự `src/lib/logger.ts`?
2. `analytics-mock.ts` — có cần giữ console cho mock analytics không?
3. `sentry.ts` — Sentry init logging có nên giữ?
