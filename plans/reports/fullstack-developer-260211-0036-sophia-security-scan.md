# Security Audit Report: Sophia AI Factory

**Date:** 2026-02-11
**Auditor:** fullstack-developer (CTO auto-pilot)
**Scope:** CSP headers, XSS vectors, exposed secrets, CORS config, auth, input validation, dependencies
**Project:** `apps/sophia-ai-factory/apps/sophia-ai-factory/`

---

## Summary

| Category | Score | Status |
|----------|-------|--------|
| CSP Headers | 9/10 | Pre-existing, well configured |
| XSS Prevention | 10/10 | No dangerouslySetInnerHTML, no eval() |
| Exposed Secrets | 8/10 | **FIXED** hardcoded admin creds |
| CORS Config | 8/10 | No explicit CORS issues |
| Security Headers | 9/10 | HSTS, X-Frame, X-Content-Type, Referrer-Policy, Permissions-Policy |
| Auth Security | 8/10 | **FIXED** tier spoofing, HeyGen unauthed routes |
| Input Validation | 9/10 | Zod schemas on all POST routes |
| Dependencies | 10/10 | 0 vulnerabilities (npm audit) |
| SSRF | 8/10 | **FIXED** validate-link SSRF vector |
| Setup Endpoints | 8/10 | **FIXED** env content leak, added config guard |

**Overall: 87/100** (Production Ready)

---

## Findings & Fixes Applied

### CRITICAL

#### 1. Hardcoded Default Admin Credentials
- **File:** `src/app/api/admin/invite/route.ts`
- **Issue:** `ADMIN_USER || "admin"` and `ADMIN_PASS || "sophia2024"` — if env vars not set, anyone could access admin API with known defaults
- **Fix:** Removed fallback values; returns `false` when env vars missing
- **Severity:** CRITICAL

### HIGH

#### 2. SSRF Vulnerability in validate-link
- **File:** `src/app/api/discovery/validate-link/route.ts`
- **Issue:** Took arbitrary URLs from query params and made server-side fetch requests. Could access internal services (metadata endpoints, localhost)
- **Fix:** Added `isSafeUrl()` guard that blocks private IPs, non-HTTPS, cloud metadata endpoints, .local/.internal TLDs. Added `redirect: 'manual'` to prevent SSRF via redirect chains
- **Severity:** HIGH

### MEDIUM

#### 3. Tier Spoofing via Query Params in Production
- **File:** `src/app/api/check-access/route.ts`
- **Issue:** When auth failed, fell back to query params for tier/userId in ALL environments — allowing unauthenticated users to claim any tier
- **Fix:** Query param fallback now restricted to `NODE_ENV === 'development'` only
- **Severity:** MEDIUM

#### 4. HeyGen Routes Missing Auth
- **Files:** `src/app/api/heygen/avatars/route.ts`, `voices/route.ts`, `status/[id]/route.ts`
- **Issue:** No authentication check — anyone could list avatars, voices, and check video status
- **Fix:** Added Supabase auth guard to all three routes
- **Severity:** MEDIUM

#### 5. Setup Endpoints Leaked Env Content
- **File:** `src/app/api/setup/save/route.ts`
- **Issue:** On Vercel/read-only, returned full `envContent` (including API keys/secrets) in HTTP response body
- **Fix:** Returns only key names (not values) on Vercel. Added `isConfigured` guard to reject calls after setup complete
- **Severity:** MEDIUM

#### 6. Setup Verify Accessible After Configuration
- **File:** `src/app/api/setup/verify/route.ts`
- **Issue:** Could be used to probe/validate API keys even after app fully configured
- **Fix:** Added `isConfigured` guard to reject calls post-setup
- **Severity:** MEDIUM

### LOW

#### 7. Error Details Leaked in Discovery Routes
- **Files:** `src/app/api/discovery/search/route.ts`, `top-50/route.ts`
- **Issue:** `(error as Error).message` exposed in HTTP responses
- **Fix:** Removed `details` field from error responses
- **Severity:** LOW

---

## Pre-Existing (Good)

| Item | Status | Details |
|------|--------|---------|
| CSP Header | OK | `default-src 'self'; frame-ancestors 'none'; ...` |
| HSTS | OK | `max-age=63072000; includeSubDomains; preload` |
| X-Frame-Options | OK | `SAMEORIGIN` |
| X-Content-Type-Options | OK | `nosniff` |
| Referrer-Policy | OK | `origin-when-cross-origin` |
| Permissions-Policy | OK | `camera=(), microphone=(), geolocation=()` |
| dangerouslySetInnerHTML | OK | 0 instances |
| eval() / Function() | OK | 0 instances |
| console.log in src | OK | 0 instances |
| Polar webhook | OK | Signature verification via standardwebhooks |
| Telegram webhook | OK | Secret token header validation |
| Checkout route | OK | Zod validation on POST body |
| HeyGen create-video | OK | Auth check + Zod validation |
| User integrations | OK | Auth check + Zod validation |
| .env.example files | OK | No real values, only placeholders |
| npm audit | OK | 0 vulnerabilities |

---

## Files Modified

| File | Change |
|------|--------|
| `src/app/api/admin/invite/route.ts` | Remove hardcoded default credentials |
| `src/app/api/discovery/validate-link/route.ts` | Add SSRF protection (isSafeUrl guard) |
| `src/app/api/check-access/route.ts` | Restrict tier query param to dev only |
| `src/app/api/heygen/avatars/route.ts` | Add Supabase auth guard |
| `src/app/api/heygen/voices/route.ts` | Add Supabase auth guard |
| `src/app/api/heygen/status/[id]/route.ts` | Add Supabase auth guard |
| `src/app/api/setup/save/route.ts` | Add config guard + remove env content leak |
| `src/app/api/setup/verify/route.ts` | Add config guard |
| `src/app/api/discovery/search/route.ts` | Remove error.message from response |
| `src/app/api/discovery/top-50/route.ts` | Remove error.message from response |

---

## Build Status

- TypeScript compilation: **PASS** (my changes introduce 0 new errors)
- Pre-existing TS error in `generate-campaign.ts:84` (Supabase typing issue, unrelated)
- npm audit: **0 vulnerabilities**

---

## Remaining Items (Manual Review Recommended)

1. **CSP `script-src 'unsafe-inline'`** — required by Next.js/React but ideally should use nonce-based CSP in future
2. **Ingestion/Score routes** use `CRON_SECRET` but bypass auth in development mode — acceptable for dev but ensure `CRON_SECRET` is always set in production
3. **Admin Basic Auth over HTTP** — relies on HSTS for HTTPS enforcement; consider migrating to Supabase-based admin auth long-term
4. **Rate limiting** — Telegram webhook has rate limiting via `withMiddleware`, but API routes (discovery, checkout) have no rate limiting; consider adding
5. **Pre-existing TS error** in `generate-campaign.ts:84` should be fixed separately
