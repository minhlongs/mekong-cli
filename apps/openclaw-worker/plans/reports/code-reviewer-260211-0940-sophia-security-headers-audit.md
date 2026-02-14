# Security Headers Audit -- sophia-ai-factory

**Date:** 2026-02-11
**Agent:** code-reviewer-a8ae602
**Scope:** CSP + Security Headers configuration
**Status:** RESEARCH ONLY -- no files modified

---

## Critical Findings Summary

| Severity | Count | Description |
|----------|-------|-------------|
| CRITICAL | 1 | Hardcoded Supabase service_role key in committed scripts |
| High | 2 | `unsafe-inline` in CSP script-src/style-src |
| Medium | 2 | X-XSS-Protection deprecated value, X-Frame-Options SAMEORIGIN instead of DENY |
| Low | 1 | No CORS headers in API routes (acceptable for same-origin Next.js) |

---

## Header-by-Header Analysis

### Header: Content-Security-Policy (CSP)

- **Status:** Partially configured
- **File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/next.config.ts`
- **Line:** 64-65
- **Value:**
  ```
  default-src 'self';
  img-src 'self' https: data: blob:;
  script-src 'self' 'unsafe-inline';
  style-src 'self' 'unsafe-inline';
  font-src 'self' data:;
  connect-src 'self' https:;
  worker-src 'self';
  frame-ancestors 'none';
  ```
- **Issues:**
  1. **HIGH -- `'unsafe-inline'` in `script-src`**: Defeats XSS protection purpose of CSP entirely. Attackers can inject inline `<script>` tags. Next.js requires nonce-based approach or `'strict-dynamic'` instead.
  2. **HIGH -- `'unsafe-inline'` in `style-src`**: Allows inline style injection. Less severe than script-src but still weakens CSP.
  3. Missing `base-uri 'self'` directive -- allows base tag injection.
  4. Missing `form-action 'self'` directive -- allows form redirect to external domains.
  5. Missing `object-src 'none'` directive -- should explicitly block plugins.
  6. `connect-src 'self' https:` is overly broad -- allows connection to ANY https domain. Should whitelist specific domains (supabase, polar, heygen, inngest, etc.).
  7. `img-src 'self' https: data: blob:` is also overly broad.
- **Recommendation:**
  - Replace `'unsafe-inline'` with nonce-based CSP using Next.js `nonce` support
  - Add `base-uri 'self'`, `form-action 'self'`, `object-src 'none'`
  - Whitelist `connect-src` to specific domains only

---

### Header: Strict-Transport-Security (HSTS)

- **Status:** Configured correctly
- **File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/next.config.ts`
- **Line:** 44-45
- **Value:** `max-age=63072000; includeSubDomains; preload`
- **Assessment:** Excellent. 2-year max-age, includes subdomains, preload-ready.
- **Recommendation:** None -- this is best practice.

---

### Header: X-Content-Type-Options

- **Status:** Configured correctly
- **File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/next.config.ts`
- **Line:** 57-58
- **Value:** `nosniff`
- **Assessment:** Correct. Prevents MIME type sniffing.
- **Recommendation:** None.

---

### Header: X-Frame-Options

- **Status:** Configured -- MEDIUM concern
- **File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/next.config.ts`
- **Line:** 52-53
- **Value:** `SAMEORIGIN`
- **Assessment:** Allows same-origin framing. The CSP `frame-ancestors 'none'` is stricter and takes precedence in modern browsers. However, the mismatch between `SAMEORIGIN` (X-Frame-Options) and `'none'` (CSP frame-ancestors) may confuse legacy browsers.
- **Recommendation:** Change to `DENY` to align with CSP `frame-ancestors 'none'`. Or change CSP to `frame-ancestors 'self'` if same-origin framing is needed.

---

### Header: X-XSS-Protection

- **Status:** Configured -- MEDIUM concern
- **File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/next.config.ts`
- **Line:** 48-49
- **Value:** `1; mode=block`
- **Assessment:** This header is deprecated and the `mode=block` value has known vulnerabilities in some browsers (information leakage via timing attacks). Modern best practice is to set `0` (disabled) and rely on CSP instead.
- **Recommendation:** Change value to `0`. The XSS Auditor was removed from Chrome 78+ and Edge. Setting `1; mode=block` can cause more harm than good.

---

### Header: Referrer-Policy

- **Status:** Configured correctly
- **File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/next.config.ts`
- **Line:** 60-61
- **Value:** `origin-when-cross-origin`
- **Assessment:** Good. Sends full URL for same-origin, only origin for cross-origin. Could be stricter with `strict-origin-when-cross-origin` but current value is acceptable.
- **Recommendation:** Consider upgrading to `strict-origin-when-cross-origin` for marginally better privacy (no referrer on HTTPS-to-HTTP downgrade).

---

### Header: Permissions-Policy

- **Status:** Configured -- minimal
- **File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/next.config.ts`
- **Line:** 68-69
- **Value:** `camera=(), microphone=(), geolocation=()`
- **Assessment:** Blocks camera, microphone, geolocation. Good baseline but missing several features.
- **Recommendation:** Add more restrictive permissions:
  ```
  camera=(), microphone=(), geolocation=(), payment=(), usb=(), magnetometer=(), gyroscope=(), accelerometer=()
  ```

---

### Header: X-DNS-Prefetch-Control

- **Status:** Configured
- **File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/next.config.ts`
- **Line:** 40-41
- **Value:** `on`
- **Assessment:** Performance optimization, not security-relevant. Having DNS prefetching `on` can leak browsing intent but is generally acceptable for production apps.
- **Recommendation:** None.

---

## Middleware Security Analysis

**File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/src/middleware.ts`

### Findings:

1. **Admin Basic Auth (Line 23-37):** Uses HTTP Basic Auth for admin routes. Credentials compared via `===` (constant-time comparison NOT used). Timing attack possible but low risk since Basic Auth is already weak.
   - Credentials sourced from env vars (`ADMIN_USER`, `ADMIN_PASS`) -- correct.
   - No rate limiting on admin auth attempts.

2. **No security headers set in middleware:** All security headers are set via `next.config.ts` `headers()` function, not middleware. This is acceptable for Next.js but means API routes excluded by the matcher pattern may not receive headers.

3. **Matcher pattern (Line 151):**
   ```
   /((?!api|_next|_vercel|setup-wizard|auth/callback|.*\\..*).*)
   ```
   This EXCLUDES API routes from middleware processing. The `next.config.ts` headers apply to `/:path*` which covers all routes including API, so security headers should still be present on API responses.

---

## API Routes CORS Analysis

- **Status:** No explicit CORS headers found
- **Assessment:** Next.js API routes do not set `Access-Control-Allow-Origin` or other CORS headers. This means:
  - Same-origin requests: work normally
  - Cross-origin requests: blocked by browser (default deny)
  - This is CORRECT for a Next.js app serving its own frontend
- **Recommendation:** None needed unless third-party integrations require cross-origin access.

---

## CRITICAL: Hardcoded Secrets in Committed Files

### File 1: `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/scripts/check-migration.ts`

- **Line:** 9-11
- **Content:** Hardcoded Supabase URL + **SERVICE_ROLE KEY** (full admin access)
- **Severity:** CRITICAL
- **Key type:** `service_role` (bypasses RLS, full database admin)
- **Git status:** NOT gitignored (confirmed via `git check-ignore`)
- **Impact:** Anyone with repo access has full Supabase admin access. Can read/write/delete ALL data bypassing Row Level Security.

### File 2: `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/scripts/run-migration-007.ts`

- **Line:** 9-11
- **Content:** Same hardcoded Supabase URL + SERVICE_ROLE KEY
- **Severity:** CRITICAL
- **Impact:** Same as above -- duplicate exposure

### Immediate Actions Required:
1. **Rotate the Supabase service_role key immediately** (Dashboard -> Settings -> API)
2. Remove hardcoded keys from scripts, use `process.env.SUPABASE_SERVICE_ROLE_KEY`
3. Add `scripts/*.ts` to `.gitignore` or refactor to use env vars
4. Run `git filter-branch` or BFG Repo Cleaner to purge key from git history

---

## .env.example Analysis

**File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/.env.example`

- **Status:** Properly formatted with placeholder values
- **Assessment:** Uses `your_*` and `prod_...` placeholder patterns. No real secrets exposed.
- **Recommendation:** None -- follows best practices.

---

## Webhook Security Analysis

### Polar Webhook (`/api/webhooks/polar/route.ts`)
- Uses `standardwebhooks` library for signature verification
- Validates headers with Zod schema (`webhookHeaderSchema`)
- Verifies HMAC signature before processing
- **Assessment:** Properly secured

### Telegram Webhook (`/api/webhooks/telegram/route.ts`)
- Validates `X-Telegram-Bot-Api-Secret-Token` header
- Returns 401 on invalid token
- **Assessment:** Properly secured

---

## Score Card

| Header | Status | Grade |
|--------|--------|-------|
| Content-Security-Policy | Has `unsafe-inline` | C |
| Strict-Transport-Security | Excellent | A+ |
| X-Content-Type-Options | Correct | A |
| X-Frame-Options | SAMEORIGIN (should be DENY) | B |
| X-XSS-Protection | Deprecated value | C |
| Referrer-Policy | Good | A- |
| Permissions-Policy | Minimal | B |
| CORS | N/A (same-origin app) | A |
| Webhook Auth | Properly secured | A |
| Secrets Management | CRITICAL -- hardcoded keys | F |

**Overall Security Headers Score: 6.5/10**
**Overall Security Posture: 5/10** (dragged down by hardcoded service_role key)

---

## Priority Fix List

1. **CRITICAL** -- Rotate Supabase service_role key, remove hardcoded credentials from `scripts/check-migration.ts` and `scripts/run-migration-007.ts`, purge from git history
2. **HIGH** -- Replace `'unsafe-inline'` in CSP `script-src` with nonce-based or `strict-dynamic` approach
3. **HIGH** -- Replace `'unsafe-inline'` in CSP `style-src` with nonce-based approach
4. **MEDIUM** -- Change `X-XSS-Protection` from `1; mode=block` to `0`
5. **MEDIUM** -- Align `X-Frame-Options: DENY` with CSP `frame-ancestors 'none'`
6. **LOW** -- Add missing CSP directives: `base-uri`, `form-action`, `object-src`
7. **LOW** -- Expand `Permissions-Policy` to cover more features
8. **LOW** -- Tighten `connect-src` to whitelist specific domains

---

## Unresolved Questions

1. Has the Supabase service_role key been pushed to a public/shared remote? If so, the key rotation is even more urgent.
2. Is the Next.js app using any inline scripts that would break with nonce-based CSP? Need to test before removing `unsafe-inline`.
3. Does the app use `next/script` with `strategy="afterInteractive"`? This may require `unsafe-eval` for certain analytics -- needs verification.
