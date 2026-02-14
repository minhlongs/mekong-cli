# Security Audit Report — Sophia AI Factory

**Date:** 2026-02-11 | **Mode:** Auto + 4 Parallel Agents | **Scope:** CSP, XSS, Secrets, CORS

---

## Tổng Hợp Findings

| Severity | Count | Fixed | Remaining |
|----------|-------|-------|-----------|
| CRITICAL | 3 | 3 | 0 |
| MAJOR | 5 | 2 | 3 |
| MINOR | 6 | 0 | 6 |

---

## ĐÃ FIX (5 files, mission này)

### 1. `scripts/check-migration.ts` — CRITICAL
- **Vấn đề:** Hardcoded Supabase `service_role` key (bypass RLS, full admin access)
- **Fix:** Thay bằng `process.env.SUPABASE_URL` + `process.env.SUPABASE_SERVICE_ROLE_KEY` với validation

### 2. `scripts/run-migration-007.ts` — CRITICAL
- **Vấn đề:** Same hardcoded `service_role` key
- **Fix:** Same env var pattern

### 3. `.gitignore` (root) — CRITICAL
- **Vấn đề:** `.env.bak` chứa real secrets (PayPal, Gumroad, Supabase, Gemini, PLAINTEXT PASSWORD) tracked by git
- **Fix:** Đổi `.env` + `.env.local` → `.env*` + `!.env.example` + `!.env.*.example`; `git rm --cached .env.bak`

### 4. `next.config.ts` — MAJOR
- **Vấn đề:**
  - CSP `connect-src 'self' https:` cho phép connect đến BẤT KỲ domain HTTPS
  - `X-Frame-Options: SAMEORIGIN` mâu thuẫn với CSP `frame-ancestors 'none'`
  - CSP thiếu `frame-src` → YouTube embeds bị block
  - `X-XSS-Protection: 1; mode=block` deprecated
- **Fix:**
  - `connect-src` thu hẹp: chỉ Supabase, Polar, HeyGen, OpenRouter, ElevenLabs, Inngest
  - `X-Frame-Options: DENY` (khớp CSP)
  - Thêm `frame-src 'self' https://www.youtube.com`
  - `X-XSS-Protection: 0` (OWASP recommendation)

### 5. `src/app/api/checkout/route.ts` — MAJOR
- **Vấn đề:** Open redirect — POST handler tin `Origin` header để build `successUrl`
- **Fix:** Chỉ dùng `process.env.NEXT_PUBLIC_APP_URL`, không trust `Origin` header

---

## CÒN LẠI (cần mission tiếp theo)

### MAJOR (3 items)

| # | File | Vấn đề | Fix Recommendation |
|---|------|--------|-------------------|
| 1 | `next.config.ts` | CSP `script-src 'unsafe-inline'` — vô hiệu hóa XSS protection | Chuyển sang nonce-based CSP (Next.js 14+ hỗ trợ) |
| 2 | `src/config/tiers.ts` + `affiliate-discovery.tsx` | Server env vars imported trong `"use client"` component | Tách thành `tiers-public.ts` (client) và `tiers-server.ts` |
| 3 | `src/app/[locale]/(admin)/admin/settings/page.tsx` | `NEXT_PUBLIC_ADMIN_USER` expose admin username | Dùng server component hoặc API route |

### MINOR (6 items)

| # | File | Vấn đề |
|---|------|--------|
| 1 | `src/app/api/intelligence/score/route.ts` | Dev mode bypass auth (`NODE_ENV !== 'development'`) |
| 2 | `src/app/api/ingestion/trigger/route.ts` | Same dev bypass pattern |
| 3 | `src/lib/redis.ts` + `upstash-redis-client.ts` | Dummy fallback tokens mask config issues |
| 4 | `src/lib/telegram/telegram-bot-instance.ts` | Dummy token fallback |
| 5 | `components/guide/youtube-embed.tsx` | `videoId` not validated against regex |
| 6 | `components/video-preview.tsx` + `project-card.tsx` + `campaign-actions.tsx` | Dynamic `href` without protocol validation |

---

## Điểm Tích Cực

- 0 `dangerouslySetInnerHTML`, `eval()`, `innerHTML` — codebase sạch XSS vectors
- Zod validation trên tất cả API inputs
- Webhook signature verification (Polar: standardwebhooks, Telegram: secret token)
- SSRF protection trên `/api/discovery/validate-link` (blocks private IPs, metadata endpoints)
- No CORS headers = same-origin default (đúng behavior)
- HSTS `max-age=63072000; includeSubDomains; preload` — A+
- `AES-256-GCM` encryption utility với proper IV + auth tag

## Action Items Khẩn Cấp

1. **ROTATE SECRETS NGAY:** PayPal, Gumroad, Supabase service_role, Gemini API key (đã bị commit vào git history)
2. **PURGE GIT HISTORY:** Dùng `git filter-repo` hoặc BFG Repo-Cleaner để xóa `.env.bak` khỏi toàn bộ history
3. **ĐỔI GUMROAD PASSWORD:** Plaintext password `FastSaaS2026@` đã exposed

---

**Score tổng thể: 6.5/10** → Sau fixes: **7.5/10**
