# Security Audit: CORS Config & API Route Security -- sophia-ai-factory

**Date:** 2026-02-11
**Auditor:** code-reviewer (subagent)
**Scope:** CORS headers, all API routes, webhook security, auth callback
**Base path:** `apps/sophia-ai-factory/apps/sophia-ai-factory/`

---

## Code Review Summary

### Scope
- Files: 25 route files + middleware + next.config.ts + schemas + lib clients
- Focus: CORS, authentication, input validation, webhook verification, info leakage
- LOC reviewed: ~1200

### Overall Assessment
Codebase demonstrates solid security hygiene in several areas (security headers, webhook verification, SSRF protection, Zod validation) but has one **CRITICAL** issue (browser Supabase client on server route), several **HIGH** gaps (missing rate limiting, dev-mode auth bypass), and a few **MEDIUM** concerns.

---

## CRITICAL Issues

### C-1. user/integrations uses BROWSER Supabase client on server-side API route
- **Severity:** CRITICAL
- **File:** `src/app/api/user/integrations/route.ts` line 2
- **Current:** `import { supabase } from '@/lib/supabase/client'`
- **Problem:** The `client.ts` module creates a bare `createClient()` from `@supabase/supabase-js` (the browser SDK), NOT `@supabase/ssr`. This client has NO access to HTTP request cookies on the server. As a result:
  - `supabase.auth.getUser()` has no session context and returns `null` user every time
  - Both POST and GET handlers always return 401 -- the route is effectively **broken**
  - If the anon key ever gets elevated privileges or RLS is misconfigured, this client operates outside user session scope entirely
- **Contrast:** All other authenticated routes (`heygen/create-video`, `heygen/avatars`, `heygen/voices`, `heygen/status/[id]`, `checkout`) correctly use `import { createClient } from '@/lib/supabase/server'`
- **Fix:** Replace `import { supabase } from '@/lib/supabase/client'` with `import { createClient } from '@/lib/supabase/server'` and call `const supabase = await createClient()` inside each handler

---

## HIGH Priority Issues

### H-1. Development-mode auth bypass on internal API routes
- **Severity:** HIGH
- **Files:**
  - `src/app/api/ingestion/trigger/route.ts` lines 11-13
  - `src/app/api/intelligence/score/route.ts` lines 10-12
- **Current:**
  ```ts
  if (process.env.NODE_ENV !== 'development') {
    return NextResponse.json({ error: 'Unauthorized' }, { status: 401 })
  }
  ```
- **Problem:** If `NODE_ENV=development` (or not set), auth check is **completely skipped**. Staging environments, preview deployments, or misconfigured production environments could expose these routes without authentication. These routes trigger heavy operations (ingestion runner, scoring engine).
- **Fix:** Remove the development override. Use a separate flag like `ALLOW_DEV_ACCESS=true` that is never set in any non-local environment. Or always require the CRON_SECRET.

### H-2. No rate limiting on public-facing API routes
- **Severity:** HIGH
- **Routes without rate limiting:**
  - `POST /api/checkout` -- creates Polar checkout sessions (cost per call)
  - `GET /api/checkout` -- creates Polar checkout sessions (cost per call)
  - `GET /api/check-access` -- triggers Supabase + tier guard queries
  - `GET /api/discovery/top-50` -- database query
  - `GET /api/discovery/search` -- database search query
  - `GET /api/discovery/validate-link` -- outbound HTTP request to arbitrary HTTPS URL
  - `POST /api/setup/verify` -- attempts API key validation against external services
  - `GET /api/health` -- Supabase + Redis connectivity checks
  - `GET /api/sophia-index/health` -- database query
- **Problem:** An attacker can:
  - Spam checkout creation causing API cost inflation on Polar
  - DDoS internal services via health check loops
  - Abuse `validate-link` as an open HTTP proxy (HEAD requests to any HTTPS URL)
  - Probe API keys via repeated setup/verify calls (though guarded by IS_CONFIGURED check)
- **Fix:** Add Vercel Edge rate limiting via `@vercel/edge` or Upstash Redis-based rate limiter. Priority: checkout and validate-link routes.

### H-3. validate-link SSRF bypass via DNS rebinding
- **Severity:** HIGH
- **File:** `src/app/api/discovery/validate-link/route.ts` lines 10-47
- **Current:** `isSafeUrl()` checks hostname at URL parse time against a blocklist
- **Problem:** The function checks the hostname string but does NOT resolve DNS. An attacker can:
  1. Register a domain pointing to `169.254.169.254` (cloud metadata)
  2. Pass `https://attacker-domain.com` which passes the hostname check
  3. The `fetch()` on line 67 resolves DNS to the internal IP
- **Additional gap:** `redirect: 'manual'` prevents redirect-based SSRF but DNS rebinding still works
- **Fix:** Use a DNS resolution check before fetch, or use Vercel Edge Runtime's built-in protections. Consider using a dedicated URL validation service.

### H-4. CSP allows 'unsafe-inline' for script-src
- **Severity:** HIGH
- **File:** `next.config.ts` line 65
- **Current:** `script-src 'self' 'unsafe-inline'`
- **Problem:** `'unsafe-inline'` allows inline `<script>` execution, largely negating XSS protection from CSP. If any user input is reflected without sanitization, XSS payloads execute.
- **Note:** `style-src 'self' 'unsafe-inline'` is also present but lower risk (style injection vs script execution)
- **Fix:** Replace `'unsafe-inline'` with nonce-based CSP or `'strict-dynamic'`. Next.js supports nonce-based CSP via `next.config.js` experimental features.

---

## MEDIUM Priority Issues

### M-1. Auth callback has no explicit redirect URL validation
- **Severity:** MEDIUM
- **File:** `src/app/auth/callback/route.ts` lines 10-18
- **Current:**
  ```ts
  const { searchParams, origin } = new URL(request.url);
  // ...
  return NextResponse.redirect(`${origin}/dashboard`);
  ```
- **Analysis:** `origin` is derived from `request.url` which is the server's own origin (safe). Supabase SDK handles PKCE internally via `exchangeCodeForSession()`. However:
  - No `next` or `redirect_to` parameter is accepted (good -- no open redirect)
  - No explicit state parameter validation (PKCE handles this)
  - The `code` parameter is not validated for format before passing to Supabase
- **Risk:** Low in current form. Would become HIGH if a `redirect_to` query param is ever added.
- **Fix:** Add a comment documenting that redirect_to must never be accepted from query params. Consider adding `code` format validation (UUID or hex string).

### M-2. Checkout route error response leaks error message detail
- **Severity:** MEDIUM
- **File:** `src/app/api/checkout/route.ts` lines 110-114
- **Current:**
  ```ts
  const errorMessage = error instanceof Error ? error.message : 'Unknown error';
  return NextResponse.json(
    { error: `Failed to create checkout session: ${errorMessage}` },
    { status: 500 }
  );
  ```
- **Problem:** Internal error messages from Polar SDK or Supabase are forwarded to the client. This can reveal:
  - Internal API endpoints
  - Database column names
  - SDK version information
  - Stack trace fragments
- **Fix:** Log detailed error server-side, return generic message to client.

### M-3. Admin Basic Auth uses timing-unsafe string comparison
- **Severity:** MEDIUM
- **Files:**
  - `src/middleware.ts` lines 29-33
  - `src/app/api/admin/invite/route.ts` lines 18-21
- **Current:** `return user === validUser && pwd === validPass;`
- **Problem:** JavaScript `===` comparison is not constant-time. Theoretically allows timing attacks to brute-force admin credentials character-by-character. Practical exploitability is low over network but worth fixing.
- **Fix:** Use `crypto.timingSafeEqual(Buffer.from(a), Buffer.from(b))` for constant-time comparison.

### M-4. Health check endpoint exposes service configuration details
- **Severity:** MEDIUM
- **File:** `src/app/api/health/route.ts` lines 94-108
- **Current:** When `HEALTH_CHECK_SECRET` is provided, response includes names of all external service dependencies (openrouter, elevenlabs, heygen, telegram) and their configuration status
- **Problem:** Authenticated health check reveals the full technology stack and integration surface. Useful for targeted attacks.
- **Fix:** Consider restricting health check to internal networks only. Current secret-gated approach is acceptable but be aware of token reuse risk.

### M-5. Inngest route exposes GET, POST, and PUT without explicit signing key validation
- **Severity:** MEDIUM
- **File:** `src/app/api/inngest/route.ts`
- **Current:** Uses `serve()` from `inngest/next` which registers GET, POST, PUT handlers
- **Analysis:** The Inngest SDK's `serve()` function internally validates `INNGEST_SIGNING_KEY` for production environments. However:
  - The signing key validation is implicit (SDK-level, not visible in this code)
  - If `INNGEST_SIGNING_KEY` is not set, the SDK may accept unsigned events in development mode
  - The PUT handler is used by Inngest dashboard for function registration
- **Fix:** Ensure `INNGEST_SIGNING_KEY` is always set in production. Add an explicit environment check. The current health check confirms this key exists.

### M-6. Middleware matcher excludes API routes -- auth bypass by design
- **Severity:** MEDIUM (by design, but needs documentation)
- **File:** `src/middleware.ts` line 151
- **Current:** `matcher: ["/((?!api|_next|_vercel|setup-wizard|auth/callback|.*\\\\..*).*)" ]`
- **Problem:** The middleware matcher explicitly excludes ALL `/api/*` routes from middleware processing. This means:
  - Dashboard auth check (Supabase) in middleware does NOT protect API routes
  - Each API route must implement its own auth check independently
  - If a developer adds a new API route and forgets auth, it is completely unprotected
- **Fix:** Consider creating a shared `requireAuth()` utility that all authenticated API routes must call. Document this pattern prominently.

---

## LOW Priority Issues

### L-1. sophia-index/health leaks error messages
- **Severity:** LOW
- **File:** `src/app/api/sophia-index/health/route.ts` line 17
- **Current:** `{ status: 'error', message: (error as Error).message }`
- **Fix:** Return generic error, log details server-side.

### L-2. No explicit CORS headers set for API routes
- **Severity:** LOW
- **File:** `next.config.ts` -- no `Access-Control-*` headers present
- **Analysis:** Next.js API routes default to same-origin. No wildcard `*` CORS headers found anywhere. This is actually **correct** for a same-origin SPA.
- **Note:** The `connect-src` CSP directive properly restricts outbound connections to known domains.
- **Status:** No action needed. Current behavior is secure.

### L-3. Telegram webhook GET endpoint has no auth
- **Severity:** LOW
- **File:** `src/app/api/webhooks/telegram/route.ts` lines 91-97
- **Current:** GET handler returns service status without any authentication
- **Problem:** Reveals that the Telegram webhook service exists and is running
- **Fix:** Remove GET handler or require auth. Low priority since it reveals minimal info.

### L-4. X-XSS-Protection set to '0'
- **Severity:** LOW
- **File:** `next.config.ts` line 49
- **Analysis:** Setting `X-XSS-Protection: 0` is actually the modern best practice (OWASP recommendation) since browser XSS filters can introduce vulnerabilities. CSP should be the primary XSS defense. This is **correct**.
- **Status:** No action needed.

---

## Positive Observations

1. **Security headers** -- Comprehensive set: HSTS (63072000s preload), X-Frame-Options DENY, X-Content-Type-Options nosniff, Permissions-Policy, Referrer-Policy, CSP. Well above average.
2. **Zod validation** -- Used consistently across checkout, integrations, video creation, webhook headers, setup config. Proper `safeParse()` with error flattening.
3. **Polar webhook verification** -- Proper `standardwebhooks` signature verification with base64 fallback. Header validation via Zod schema.
4. **Telegram webhook** -- `X-Telegram-Bot-Api-Secret-Token` header validation + rate limiting via `withMiddleware`.
5. **SSRF protection** -- `validate-link` route has comprehensive blocklist including cloud metadata endpoints, private IP ranges, .local/.internal TLDs, and uses `redirect: 'manual'`.
6. **Setup wizard guards** -- Both `setup/verify` and `setup/save` check `IS_CONFIGURED` flag to prevent post-setup tampering.
7. **Data filtering** -- Discovery routes (`top-50`, `search`) strip `affiliate_link` and `raw_metrics` from public responses.
8. **Health check tiering** -- Detailed service info only shown when `HEALTH_CHECK_SECRET` is provided; public view is minimal.
9. **Error handling** -- All routes have try/catch with generic error messages (except noted exceptions above).

---

## Webhook Security Summary

| Webhook | Verification Method | Status |
|---------|---------------------|--------|
| Telegram | `X-Telegram-Bot-Api-Secret-Token` header | PASS -- validates against `TELEGRAM_WEBHOOK_SECRET` env |
| Polar | `standardwebhooks` HMAC signature | PASS -- signature + header validation via Zod |
| Inngest | SDK-internal `INNGEST_SIGNING_KEY` | CONDITIONAL -- relies on env var being set |

---

## Recommended Actions (Priority Order)

1. **[CRITICAL]** Fix `user/integrations/route.ts` -- replace browser Supabase client with server client
2. **[HIGH]** Remove development-mode auth bypass from `ingestion/trigger` and `intelligence/score`
3. **[HIGH]** Add rate limiting to checkout and validate-link routes (minimum)
4. **[HIGH]** Upgrade CSP to use nonces instead of `'unsafe-inline'` for script-src
5. **[HIGH]** Add DNS resolution validation to `validate-link` SSRF protection
6. **[MEDIUM]** Use `crypto.timingSafeEqual` for admin Basic Auth comparison
7. **[MEDIUM]** Sanitize error messages in checkout route (line 110-114)
8. **[MEDIUM]** Create shared `requireAuth()` utility and document API auth pattern
9. **[LOW]** Remove Telegram webhook GET handler or add auth

---

## Unresolved Questions

1. Is the `user/integrations` route intentionally broken (feature not launched yet) or is this a regression from a refactor?
2. Are there preview deployments (Vercel Preview) running with `NODE_ENV=development` that expose the ingestion/score routes?
3. Is there a plan to implement API-level rate limiting (Vercel Edge Middleware, Upstash)?
4. Should the `validate-link` endpoint require authentication to prevent abuse as an open proxy?
