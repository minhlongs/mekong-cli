# Security Audit Report — sophia-ai-factory

**Date:** 2026-02-11 12:39
**Scope:** CSP headers, XSS vectors, exposed secrets, CORS config
**Method:** 4 parallel subagents (code-reviewer x3, debugger x1)

## Executive Summary

| Category | Before | After |
|----------|--------|-------|
| CRITICAL | 1 | **0** |
| HIGH | 7 | 4 (remaining) |
| MEDIUM | 6 | 5 (remaining) |
| LOW | 4 | 4 (unchanged) |

## 5 Files Fixed (This Mission)

### Fix 1: `next.config.ts` — CSP Missing Directives [HIGH → FIXED]
- Added `base-uri 'self'` — prevents `<base href>` injection
- Added `form-action 'self'` — prevents form submission hijacking
- Added `object-src 'none'` — blocks plugin-based attacks

### Fix 2: `src/app/api/user/integrations/route.ts` — Browser Supabase on Server [CRITICAL → FIXED]
- Changed `import { supabase } from '@/lib/supabase/client'` → `import { createClient } from '@/lib/supabase/server'`
- Both POST and GET now use `await createClient()` for proper cookie-based auth
- Route was **completely broken** before (always returned 401)

### Fix 3: `src/lib/export-utils.ts` — CSV Injection [HIGH → FIXED]
- Fixed escaping: `\"` → `""` (RFC 4180 compliant)
- Added formula injection protection: strips `=`, `+`, `-`, `@`, `\t`, `\r` prefixes

### Fix 4: `src/components/guide/youtube-embed.tsx` — videoId Validation [MEDIUM → FIXED]
- Added regex validation: `/^[a-zA-Z0-9_-]{11}$/`
- Returns `null` for invalid IDs (prevents URL injection)

### Fix 5: `src/app/api/ingestion/trigger/route.ts` — Dev Auth Bypass [HIGH → FIXED]
- Removed `NODE_ENV === 'development'` bypass
- Auth now **always required** via `Bearer ${CRON_SECRET}` — no environment exceptions

## Remaining Issues (Chưa Fix)

### HIGH (4 remaining)

| # | Issue | File | Reason Not Fixed |
|---|-------|------|------------------|
| 1 | `'unsafe-inline'` in CSP script-src | next.config.ts | Next.js cần nonce-based CSP setup — thay đổi lớn, cần plan riêng |
| 2 | No rate limiting trên 21 API routes | Multiple routes | Cần Upstash/Vercel Edge middleware — architectural change |
| 3 | Dummy fallback tokens (Redis, Telegram) | redis.ts, telegram-bot-instance.ts | Cần validate env startup — risk: break staging |
| 4 | validate-link SSRF bypass (DNS rebinding) | discovery/validate-link | Cần DNS resolution check — complex implementation |

### MEDIUM (5 remaining)

| # | Issue | File |
|---|-------|------|
| 1 | Overly permissive `img-src https:` | next.config.ts |
| 2 | Incomplete Permissions-Policy (3/20+ features) | next.config.ts |
| 3 | Admin Basic Auth without lockout/MFA | middleware.ts |
| 4 | Dynamic `<a href>` without protocol validation | 3 component files |
| 5 | intelligence/score auth bypass (same as ingestion) | intelligence/score/route.ts |

### LOW (4 remaining)

| # | Issue | File |
|---|-------|------|
| 1 | NEXT_PUBLIC_ADMIN_USER in client bundle | middleware.ts |
| 2 | Duplicate Redis client modules | 2 files |
| 3 | Health endpoint info disclosure (gated) | health/route.ts |
| 4 | Pre-existing eslint warning (unused var) | integrations/route.ts |

## Positive Observations

- `.env*` files properly gitignored
- NEXT_PUBLIC_* vars không chứa secrets
- Encryption utility (AES-256-GCM) implement đúng chuẩn
- Polar webhook: HMAC signature verification via standardwebhooks
- Telegram webhook: secret token validation + rate limiting
- SSRF protection trên validate-link có blocklist IP nội bộ
- Zero `dangerouslySetInnerHTML` trong toàn bộ codebase
- Zod validation trên mọi API endpoint
- `rel="noopener noreferrer"` trên mọi external link

## Lint Result

```
0 errors, 1 warning (pre-existing unused var in catch block)
```

## Detailed Sub-Reports

- `code-reviewer-260211-1240-sophia-security-headers-audit.md`
- `debugger-260211-1240-sophia-exposed-secrets-scan.md`
- `code-reviewer-260211-1240-sophia-xss-vectors-analysis.md`
- `code-reviewer-260211-1240-sophia-cors-api-security-audit.md`
