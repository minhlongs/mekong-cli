# Security Audit: Exposed Secrets Scan -- sophia-ai-factory

**Date:** 2026-02-11
**Agent:** debugger
**Scope:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/src/`
**Status:** RESEARCH ONLY -- no code changes made

---

## Executive Summary

No hardcoded real secrets found in source code. Environment variable handling follows reasonable patterns. Several **MEDIUM** and **HIGH** findings related to dummy fallback tokens, unauthenticated setup API, and admin Basic Auth.

**Verdict:** 7/10 -- good baseline, 4 items need attention.

---

## Findings

### FINDING 1: Dummy Fallback Tokens in Production Code Path

**Severity:** HIGH
**Exposure:** Server-side

| File | Line | Code |
|------|------|------|
| `src/lib/redis.ts` | 4 | `process.env.UPSTASH_REDIS_REST_TOKEN \|\| 'dummy_token'` |
| `src/lib/redis.ts` | 3 | `process.env.UPSTASH_REDIS_REST_URL \|\| 'https://dummy-url.upstash.io'` |
| `src/lib/clients/upstash-redis-client.ts` | 16-17 | Same pattern -- `'dummy_token'` and `'https://dummy-url.upstash.io'` |
| `src/lib/telegram/telegram-bot-instance.ts` | 3 | `process.env.TELEGRAM_BOT_TOKEN \|\| 'dummy_token_for_build'` |

**Risk:** If env vars are missing in production, app silently connects to dummy URLs or creates invalid bot instances. `redis.ts` does NOT guard `NODE_ENV !== 'production'` on the fallback path (the check on line 6 has empty body). The `upstash-redis-client.ts` has no guard at all.

**Recommendation:**
- Throw Error in production if env vars missing, instead of falling back to dummy values
- Or use `getEnvironmentConfig()` from `environment-config.ts` which already has zod validation

---

### FINDING 2: Setup Wizard API -- No Authentication

**Severity:** HIGH
**Exposure:** Public network endpoint

| File | Route |
|------|-------|
| `src/app/api/setup/save/route.ts` | `POST /api/setup/save` |
| `src/app/api/setup/verify/route.ts` | `POST /api/setup/verify` |

**Detail:** Both endpoints are guarded ONLY by `NEXT_PUBLIC_IS_CONFIGURED` flag. Before initial setup, these endpoints are **completely unauthenticated** and accept API keys in the POST body:

- `/api/setup/verify` -- accepts `{ service, key }` and validates keys against external services (OpenRouter, ElevenLabs, D-ID, Airtable). An attacker could use this as an API key validation oracle.
- `/api/setup/save` -- writes arbitrary key-value pairs to `.env.local` on disk. On Vercel, file write is blocked but key names leak in response.

**Middleware confirms:** `src/middleware.ts` lines 47-54 explicitly allow `/api/setup` without auth when not configured.

**Recommendation:**
- Add rate limiting on `/api/setup/*` routes
- Add CSRF token validation
- Consider a one-time setup token or IP-based restriction
- After first setup, these routes already return 403 (good)

---

### FINDING 3: Admin Panel Uses Basic Auth with Env Credentials

**Severity:** MEDIUM
**Exposure:** Server-side (middleware)

| File | Line | Detail |
|------|------|--------|
| `src/middleware.ts` | 23-37 | `isAdminAuthorized()` reads `ADMIN_USER` + `ADMIN_PASS` from env |

**Detail:** Admin auth uses HTTP Basic Auth which transmits credentials in base64 (not encrypted) on every request. HSTS is configured in `next.config.ts` which mitigates this for HTTPS, but:

- No account lockout after failed attempts
- No MFA
- Credentials stored as plain text env vars (standard practice, but single-factor)

**Recommendation:**
- Acceptable for internal admin given HSTS enforcement
- Consider upgrading to session-based auth with rate limiting for production at scale

---

### FINDING 4: `NEXT_PUBLIC_ADMIN_USER` Exposed to Client Bundle

**Severity:** LOW
**Exposure:** Client-side

| File | Line | Code |
|------|------|------|
| `src/app/[locale]/(admin)/admin/settings/page.tsx` | 69 | `process.env.NEXT_PUBLIC_ADMIN_USER \|\| "admin"` |

**Detail:** This is a `"use client"` component. `NEXT_PUBLIC_ADMIN_USER` would be embedded in the client JS bundle if set. Currently harmless (displays username as label, not password), but reveals admin username to anyone inspecting the bundle.

**Recommendation:**
- Fetch admin username from server action instead of embedding in client bundle
- Or accept the risk since username alone is not secret

---

### FINDING 5: Health Check Endpoint Info Leak (Controlled)

**Severity:** LOW
**Exposure:** Depends on `HEALTH_CHECK_SECRET`

| File | Line | Detail |
|------|------|--------|
| `src/app/api/health/route.ts` | 9-13 | Token/Bearer auth gates detailed service info |

**Detail:** Without `HEALTH_CHECK_SECRET`, public gets only `{ status, timestamp }`. With the secret, service names and latency are exposed. This is **well-designed** -- detailed info is gated behind auth. Only risk: if `HEALTH_CHECK_SECRET` is a weak value.

**Recommendation:** Ensure `HEALTH_CHECK_SECRET` is a strong random value (32+ chars). Already handled well.

---

### FINDING 6: Duplicate Redis Client Modules

**Severity:** LOW (code quality, not security)

| File | Purpose |
|------|---------|
| `src/lib/redis.ts` | Bare Redis client with dummy fallback |
| `src/lib/clients/upstash-redis-client.ts` | Singleton with helpers, also dummy fallback |

**Detail:** Two Redis client files with duplicate dummy token patterns. Inconsistent initialization logic.

**Recommendation:** Consolidate to single client. Remove `src/lib/redis.ts` if `upstash-redis-client.ts` is the canonical source.

---

## .gitignore Verification

| Pattern | Status | Note |
|---------|--------|------|
| `.env*` | PRESENT (line 34) | Catches all .env files |
| `.env*.local` | PRESENT (line 42) | Redundant but safe |
| `*.pem` | PRESENT (line 25) | Good |

**Git tracking check:** `.env.local` and `.env.production.local` are NOT tracked by git (confirmed via `git ls-files --error-unmatch`).

---

## NEXT_PUBLIC_* Audit

| Variable | Contains Secret? | Verdict |
|----------|-----------------|---------|
| `NEXT_PUBLIC_SUPABASE_URL` | No (public URL) | OK |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | No (public anon key by design) | OK |
| `NEXT_PUBLIC_APP_URL` | No (app URL) | OK |
| `NEXT_PUBLIC_MOCK_AI_SERVICES` | No (feature flag) | OK |
| `NEXT_PUBLIC_IS_CONFIGURED` | No (boolean flag) | OK |
| `NEXT_PUBLIC_ADMIN_USER` | Marginal (username) | LOW risk -- see Finding 4 |
| `NEXT_PUBLIC_FEATURE_*` | No (feature flags) | OK |

No secrets leak via `NEXT_PUBLIC_*` variables.

---

## Server-Side Env Var Audit

All sensitive env vars are accessed ONLY in server-side code (API routes, server actions, middleware, lib/). Confirmed patterns:

| Env Var | Used In | Server-Only? |
|---------|---------|-------------|
| `SUPABASE_SERVICE_ROLE_KEY` | admin.ts, actions/*.ts, inngest functions, telegram-bot.ts | YES |
| `POLAR_ACCESS_TOKEN` | polar.ts, polar-client.ts | YES |
| `POLAR_WEBHOOK_SECRET` | polar-client.ts | YES |
| `OPENROUTER_API_KEY` | script-generator.ts, niche-enhancer.ts | YES |
| `ELEVENLABS_API_KEY` | text-to-speech-generator-elevenlabs.ts | YES |
| `HEYGEN_API_KEY` | heygen-client.ts | YES |
| `TELEGRAM_BOT_TOKEN` | telegram-*.ts | YES |
| `TELEGRAM_WEBHOOK_SECRET` | telegram webhook route | YES |
| `API_ENCRYPTION_KEY` | encryption.ts | YES |
| `INNGEST_EVENT_KEY` | health route (existence check only) | YES |
| `INNGEST_SIGNING_KEY` | health route (existence check only) | YES |
| `ADMIN_USER` / `ADMIN_PASS` | middleware.ts | YES |
| `HEALTH_CHECK_SECRET` | health route | YES |

---

## Encryption Review

`src/utils/encryption.ts` uses AES-256-GCM with random IV and auth tag. Implementation is correct:
- Key from env (`API_ENCRYPTION_KEY`) as hex
- Random 16-byte IV per encryption
- Auth tag appended for integrity
- Format: `iv:authTag:encryptedContent`

No issues found.

---

## Security Headers (Bonus)

`next.config.ts` has strong security headers:
- HSTS with preload (2-year max-age)
- X-Frame-Options: DENY
- X-Content-Type-Options: nosniff
- CSP configured with allowed connect-src
- Permissions-Policy restricts camera/microphone/geolocation

**Note:** CSP uses `'unsafe-inline'` for script-src and style-src, typical for Next.js but weakens XSS protection.

---

## Summary Table

| # | Finding | Severity | Action Required |
|---|---------|----------|-----------------|
| 1 | Dummy fallback tokens in Redis/Telegram | HIGH | Throw in production |
| 2 | Unauthenticated setup API endpoints | HIGH | Add rate limiting + CSRF |
| 3 | Admin Basic Auth (no lockout/MFA) | MEDIUM | Acceptable with HSTS |
| 4 | NEXT_PUBLIC_ADMIN_USER in client bundle | LOW | Consider server-side fetch |
| 5 | Health endpoint info leak (gated) | LOW | Already well-designed |
| 6 | Duplicate Redis client modules | LOW | Consolidate |

**Total CRITICAL:** 0
**Total HIGH:** 2
**Total MEDIUM:** 1
**Total LOW:** 3

---

## Unresolved Questions

1. Are `.env.local` and `.env.production.local` values rotated regularly? (Cannot verify -- privacy-protected)
2. Is `HEALTH_CHECK_SECRET` a strong value? (Cannot verify)
3. Is there rate limiting configured at Vercel/CDN level for `/api/setup/*`?
4. Does CSP `unsafe-inline` for script-src expose any real XSS vectors given Next.js server rendering?
