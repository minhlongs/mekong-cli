# Sophia AI Factory — Runtime Errors Audit & Fix Report

**Date:** 2026-02-11
**Scope:** Runtime errors, unhandled rejections, console warnings
**Project:** `apps/sophia-ai-factory/apps/sophia-ai-factory`

## Tổng Kết

| Severity | Tìm thấy | Đã sửa |
|----------|----------|--------|
| CRITICAL | 3 | 3 |
| HIGH | 7 | 2 |
| MEDIUM | 8 | 0 |
| LOW | 5 | 0 |
| **Total** | **23** | **5** |

## 5 File Đã Sửa (Mission Này)

### 1. `src/app/actions/admin.ts` — CRITICAL
**Vấn đề:** Hardcoded mock admin user (`admin_user_001`, tier ENTERPRISE) bypass toàn bộ auth
**Fix:** Thay bằng `supabase.auth.getUser()` thực, check tier từ `user_metadata`

### 2. `src/lib/clients/polar-client.ts` — CRITICAL
**Vấn đề:** `verifyWebhook()` stub luôn return `true` — dead code nhưng gây hiểu nhầm
**Fix:** Implement real verification bằng `standardwebhooks` library (đã installed)
**Note:** Route `/api/webhooks/polar` đã có verification riêng, stub này cho callers khác

### 3. `src/lib/telegram/telegram-client.ts` — CRITICAL
**Vấn đề:** `setTelegramWebhook()` không có try-catch, không guard env vars, crash silently
**Fix:** Thêm env var guards, try-catch, response.ok check, trả structured error

### 4. `src/lib/ai/text-to-speech-generator-elevenlabs.ts` — HIGH
**Vấn đề:** Empty catch block `catch (error) { }` nuốt lỗi ElevenLabs API
**Fix:** Log error message trước khi fallback sang mock audio

### 5. `src/lib/supabase/client.ts` — HIGH
**Vấn đề:** Module-level `throw new Error()` crash toàn bộ app khi env vars thiếu (build time, test)
**Fix:** Lazy initialization qua `getSupabaseClient()`, backward-compatible `supabase` export

## Build Verification

```
npx tsc --noEmit → EXIT_CODE=0 ✅
```

## 18 Issues Còn Lại (Cần Mission Tiếp)

### HIGH (5 remaining)

| ID | File | Vấn đề |
|----|------|--------|
| C1-03 | `src/app/[locale]/(admin)/admin/settings/integrations/page.tsx` | Empty catch block trong fetchIntegrations useEffect |
| C2-01 | `src/app/actions/automation.ts` | Unsafe `formData.get() as string` cast |
| C2-02 | `src/app/[locale]/dashboard/components/create-project-form.tsx` | Unsafe `formData.get() as string` cast |
| C2-03 | `src/app/actions/campaigns.ts` | Unsafe `rawData.platforms as string[]` cast |
| C2-04 | Multiple API routes | `(error as Error).message` pattern crash nếu error không phải Error |
| C2-05 | `src/lib/heygen/heygen-client.ts` | `data.data.avatars` không null check |
| C5-01 | `src/app/api/user/integrations/route.ts` | Browser Supabase client trong API route |

### MEDIUM (8 remaining)

| ID | File | Vấn đề |
|----|------|--------|
| C1-04 | `src/app/actions/settings.ts` | getUserProfile() throws thay vì return structured error |
| C1-05 | `src/lib/heygen/heygen-client.ts` | listAvatars/listVoices nuốt error return `[]` |
| C2-06 | `src/app/actions/campaigns.ts` | Non-null assertion `userId!` |
| C2-07 | `src/lib/inngest/functions/generate-campaign.ts` | Unsafe script type assertion |
| C2-08 | `src/lib/telegram/telegram-bot.ts` | Multiple `as unknown as` casts |
| C3-03 | Multiple files | 8 `@ts-expect-error` (Supabase Json typing) |
| C4-02 | `src/app/setup-wizard/page.tsx` | Không có error boundary |
| C5-02 | `src/app/api/admin/invite/route.ts` | Không có Zod validation |
| C5-03 | `src/app/api/ingestion/trigger/route.ts` | Body không validated |

### LOW (5 remaining)

| ID | File | Vấn đề |
|----|------|--------|
| C1-06 | `src/app/auth/callback/route.ts` | Silent redirect không log error |
| C1-07 | `src/app/actions/campaign-export-actions.ts` | Generic error message |
| C3-04 | `src/app/actions/templates.ts` | File-level eslint-disable |
| C4-03 | `src/app/actions/templates.ts` | getSession() thay vì getUser() |
| C5-04 | `src/app/api/setup/save/route.ts` | Env var key không whitelist |
