# Sophia AI Factory -- Core Web Vitals Audit

**Date:** 2026-02-11
**Agent:** debugger
**Project:** `apps/sophia-ai-factory/apps/sophia-ai-factory`
**Stack:** Next.js (App Router) + React + TypeScript + Tailwind CSS + PWA

---

## Executive Summary

| Metric | Risk Assessment | Score |
|--------|----------------|-------|
| **LCP** | NEEDS IMPROVEMENT | 6/10 |
| **CLS** | GOOD | 9/10 |
| **INP** | GOOD | 8/10 |
| **Loading States** | GOOD | 9/10 |
| **Metadata & Head** | NEEDS IMPROVEMENT | 6/10 |

**Overall CWV Readiness: 7.6/10** -- solid foundation, 3 medium-priority fixes needed.

---

## 1. LCP (Largest Contentful Paint)

### Current State: NEEDS IMPROVEMENT

#### What's Good

- **Font loading** -- Uses `next/font/google` (Geist, Geist_Mono) with CSS variable strategy. Fonts are self-hosted by Next.js, eliminating external font request latency. No FOIT/FOUT risk.
  - File: `src/app/[locale]/layout.tsx:20-28`

- **Hero is NOT dynamically imported** -- Directly imported in page.tsx, ensuring it's in the initial bundle.
  - File: `src/app/[locale]/page.tsx:2` (`import { Hero } from ...`)

- **Below-fold sections are all `dynamic()`** -- 8 sections (Workflow, Features, SocialProof, PricingSection, AffiliateDiscovery, ROICalculator, FAQ, Footer) use `next/dynamic` with skeleton loading states. Reduces initial JS bundle significantly.
  - File: `src/app/[locale]/page.tsx:41-72`

- **`reactCompiler: true`** in next.config.ts -- React Compiler auto-memoizes, reducing unnecessary re-renders.
  - File: `next.config.ts:20`

- **Image optimization** configured with `formats: ['image/avif', 'image/webp']`
  - File: `next.config.ts:22`

#### Issues Found

**[P1] Hero section is a client component blocking SSR of LCP element**

The Hero section has `"use client"` directive. The LCP element (the `<h1>` tag with gradient text) requires client-side hydration before being meaningfully rendered. Since there are no images above the fold, the h1 text IS the LCP element.

- File: `src/app/components/sections/hero.tsx:1` (`"use client"`)
- Impact: Hero text renders only after JS hydration completes
- The `"use client"` is needed because of `useTranslations()` hook from `next-intl`

**Fix:** Convert Hero to server component using `getTranslations()` from `next-intl/server` instead of `useTranslations()`. The `FadeInView` children can remain client-side (they're visual enhancement, not LCP).

**Estimated impact:** 200-500ms LCP improvement on slow 3G.

**[P2] No `<link rel="preconnect">` for external domains**

CSP header reveals 7 external domains that the app connects to, but NONE have preconnect hints:

- `*.supabase.co` (auth, database)
- `api.polar.sh` (payments)
- `api.heygen.com` (AI video)
- `api.openai.com` (AI)
- `openrouter.ai` (AI)
- `api.elevenlabs.io` (voice)
- `api.inngest.com` (job queue)

- File: `src/app/[locale]/layout.tsx` -- no `<head>` preconnect links
- Impact: First connection to these domains requires DNS + TCP + TLS handshake (~200-400ms each)

**Fix:** Add preconnect in layout.tsx `<head>` for domains used on initial load:
```html
<link rel="preconnect" href="https://<project>.supabase.co" />
<link rel="preconnect" href="https://api.polar.sh" />
```

**Estimated impact:** 100-300ms reduction on first API call.

**[P3] `framer-motion` is dead dependency (35KB+ gzipped)**

`framer-motion` v12.31.0 exists in `package.json` but is NOT imported anywhere in production code. All animations use the custom `FadeInView` (IntersectionObserver + CSS transitions). If tree-shaking fails or if any transitive dependency pulls it in, it inflates the JS bundle.

- File: `package.json:39` (`"framer-motion": "^12.31.0"`)
- Evidence: grep shows only comment references like "replaces framer-motion"
- The `animated-counter-with-framer-motion.tsx` filename is misleading -- it does NOT import framer-motion.

**Fix:** Remove `framer-motion` from `package.json` and run `npm install`.

**Estimated impact:** Potential 35KB bundle reduction (if tree-shaking wasn't complete).

**[P4] NextIntlClientProvider sends ALL messages to client**

`getMessages()` returns the entire translation file and sends it via `NextIntlClientProvider`. If translation files are large, this adds to the HTML payload.

- File: `src/app/[locale]/layout.tsx:83` (`const messages = await getMessages()`)
- Impact: Increases HTML document size, delays FCP/LCP

**Fix:** Use `getMessages({ namespace: 'landing' })` or split messages by route using `next-intl`'s built-in namespace filtering.

**Estimated impact:** Variable -- depends on translation file size.

---

## 2. CLS (Cumulative Layout Shift)

### Current State: GOOD

#### What's Good

- **No raw `<img>` tags found** -- All images use `next/image` with `fill` + `sizes` props, which automatically reserves space.
  - Files: `src/components/video-preview.tsx:106-112`, `src/components/discovery/product-card.tsx:23-29`

- **FadeInView uses composited properties only** -- `opacity` and `transform` do NOT trigger layout recalculation. `willChange: "opacity, transform"` promotes to GPU layer.
  - File: `src/components/ui/fade-in-view.tsx:70-75`

- **Dynamic imports have matching skeletons** -- Each `dynamic()` call includes a `loading:` component that matches the final layout dimensions.
  - File: `src/app/[locale]/page.tsx:41-72`

- **Font loading prevents FOUT** -- `next/font` injects CSS variables that apply immediately. No flash of unstyled/fallback text.
  - File: `src/app/[locale]/layout.tsx:20-28`

- **Navbar is `fixed` positioned** -- Does not participate in document flow, cannot cause CLS.
  - File: `src/app/components/layout/navbar.tsx:40`

- **FAQ accordion uses `gridTemplateRows`** -- Animates from `0fr` to `1fr`, which is a contained transform that doesn't shift surrounding content.
  - File: `src/app/components/sections/faq.tsx:58-59`

- **Mobile menu uses `max-h` + `opacity`** -- No layout shift during open/close.
  - File: `src/app/components/layout/navbar.tsx:98-100`

- **`disableTransitionOnChange`** on ThemeProvider -- prevents layout shift during theme toggle.
  - File: `src/app/[locale]/layout.tsx:98`

#### Minor Issues

**[P3] Skeleton height mismatches possible in `SectionSkeleton`**

Generic `SectionSkeleton` uses fixed heights (`h-96`, `h-80`, `h-64`) which may not exactly match the rendered section heights, causing a minor shift when content loads.

- File: `src/app/[locale]/page.tsx:5-21`
- Impact: Minor CLS (~0.01-0.05) when dynamic sections replace skeletons

**Fix:** Measure actual rendered section heights and update skeleton `height` props to match. Low priority.

---

## 3. INP (Interaction to Next Paint)

### Current State: GOOD

#### What's Good

- **ROI Calculator uses `useMemo`** -- Revenue calculation is memoized, preventing redundant computation on every render.
  - File: `src/app/components/sections/roi-calculator.tsx:15-22`

- **React Compiler enabled** -- Auto-memoizes components and callbacks, reducing re-render overhead.
  - File: `next.config.ts:20`

- **FAQ toggle is lightweight** -- Single `setOpenIndex` call, CSS animation handles the visual transition.
  - File: `src/app/components/sections/faq.tsx:41`

- **Settings form uses `useTransition`** -- Properly defers expensive form submission.
  - File: `src/components/settings/settings-form.tsx:23`

- **Pricing checkout uses async/await with loading state** -- UI remains responsive during API call.
  - File: `src/components/pricing-section.tsx:174-196`

#### Minor Issues

**[P3] Affiliate filter re-renders full grid without virtualization**

Clicking category filters triggers `setFilter()` which re-renders ALL affiliate program cards. If the list grows large (50+), this could cause frame drops.

- File: `src/app/components/sections/affiliate-discovery.tsx:22`
- Impact: Currently manageable with ~20 items. Risk increases with data growth.

**Fix:** Add `useDeferredValue(filter)` or virtualize the grid with `react-window` if list exceeds 50 items. Low priority now.

**[P3] `handleScrollClick` uses `scrollIntoView` synchronously**

Navbar smooth scroll handler calculates `getBoundingClientRect()` + `window.scrollTo()` on click. These trigger forced reflow.

- File: `src/app/components/layout/navbar.tsx:26-37`
- Impact: ~5-10ms per click on modern devices. Negligible.

---

## 4. Loading States

### Current State: GOOD (9/10)

#### Loading.tsx Coverage

| Route Segment | Has loading.tsx? | Quality |
|--------------|-----------------|---------|
| `[locale]/` | YES | Skeleton grid, h-screen centered |
| `[locale]/dashboard/` | YES | EXCELLENT -- matches DashboardStats + CampaignList layout |
| `dashboard/support/` | YES | animate-pulse grid |
| `dashboard/api-docs/` | YES | -- |
| `dashboard/analytics/` | YES | -- |
| `dashboard/settings/` | YES | -- |
| `dashboard/create/` | YES | -- |
| `dashboard/system-health/` | YES | -- |
| `dashboard/campaigns/` | YES | -- |
| `dashboard/campaigns/[id]/` | YES | -- |
| `[locale]/pricing/` | NO | Uses PricingSection directly (server component, acceptable) |
| `[locale]/login/` | NO | Lightweight client component, fast render |
| `[locale]/guide/` | NO | Static content, acceptable |

**Coverage: 10/13 route segments** -- excellent.

#### Suspense Usage

- Only `dashboard/settings/page.tsx` uses explicit `<Suspense>` boundary.
- Other dashboard pages rely on `loading.tsx` (which is functionally equivalent in App Router).
- No streaming SSR detected (no nested `<Suspense>` in server components).

**[P3] Consider adding `<Suspense>` in dashboard page for campaign list**

Dashboard page fetches campaigns server-side via `await supabase.from("campaigns")` which blocks the entire page. Wrapping `CampaignList` in `Suspense` would allow stats to render immediately.

- File: `src/app/[locale]/dashboard/page.tsx:27-49`
- Impact: Dashboard perceived load time could decrease by ~200-500ms

---

## 5. Metadata & Head

### Current State: NEEDS IMPROVEMENT

#### What's Good

- **Viewport meta** -- Correctly exported via `viewport` constant with `width: device-width, initialScale: 1, maximumScale: 5`
  - File: `src/app/[locale]/layout.tsx:68-73`

- **PWA manifest** -- `manifest.json` linked in metadata
  - File: `src/app/[locale]/layout.tsx:43`

- **OpenGraph + Twitter cards** -- Properly configured
  - File: `src/app/[locale]/layout.tsx:50-65`

- **Security headers** -- HSTS, X-Frame-Options, CSP all configured in `next.config.ts:34-74`

- **DNS prefetch enabled** -- `X-DNS-Prefetch-Control: on`
  - File: `next.config.ts:40-42`

#### Issues Found

**[P1] Missing `<link rel="preconnect">` for critical external domains**

(Same as LCP issue P2 above. Listed here for completeness.)

No preconnect hints for Supabase or Polar despite being critical for dashboard and checkout flows.

**[P2] No OG image configured**

OpenGraph metadata has title and description but no `images` property. Social shares will have no preview image.

- File: `src/app/[locale]/layout.tsx:50-56`

**Fix:** Add `images: [{ url: '/og-image.png', width: 1200, height: 630 }]` to the OpenGraph config. Create a branded OG image.

---

## 6. Middleware Performance

### Current State: ACCEPTABLE

#### Analysis

- **Supabase auth check on every `/dashboard` request** -- `supabase.auth.getUser()` makes a network call to Supabase on every dashboard navigation. This adds ~100-200ms to TTFB.
  - File: `src/middleware.ts:83-106`

- **Multiple path checks** -- Sequential if/else chain is O(1) per request, negligible overhead.

- **Admin Basic Auth** -- Only activated for `/admin` paths, no impact on normal users.

**[P3] Consider caching auth session in middleware**

The `getUser()` call validates the JWT with Supabase on every request. If tokens are short-lived, this is necessary. If using refresh tokens, consider caching the validated session for a few minutes.

---

## Priority Fix List

### Quick Wins (< 1 hour each)

| # | Fix | Metric | Impact | File(s) |
|---|-----|--------|--------|---------|
| 1 | Remove `framer-motion` from package.json | LCP | ~35KB bundle reduction | `package.json` |
| 2 | Add `<link rel="preconnect">` for Supabase + Polar | LCP/TTFB | 100-300ms first-call | `layout.tsx` |
| 3 | Add OG image to metadata | SEO/Social | Social share previews | `layout.tsx` |

### Medium Effort (1-4 hours)

| # | Fix | Metric | Impact | File(s) |
|---|-----|--------|--------|---------|
| 4 | Convert Hero to server component | LCP | 200-500ms on slow networks | `hero.tsx`, `page.tsx` |
| 5 | Filter `getMessages()` by namespace | LCP | Reduce HTML payload | `layout.tsx` |
| 6 | Add Suspense boundary for campaign data | Loading | 200-500ms perceived speed | `dashboard/page.tsx` |

### Architectural Changes (4+ hours)

| # | Fix | Metric | Impact | File(s) |
|---|-----|--------|--------|---------|
| 7 | Streaming SSR for dashboard pages | LCP/Loading | Progressive rendering | Multiple dashboard pages |
| 8 | Virtualize affiliate grid | INP | Future-proof for growth | `affiliate-discovery.tsx` |

---

## Architecture Highlights (Positive)

1. **FadeInView is a masterclass replacement for framer-motion** -- ~78 lines of IntersectionObserver + CSS transitions vs 35KB+ library. Zero CLS, zero layout thrashing.
2. **Aggressive code splitting on landing page** -- 8 dynamic imports with matching skeletons.
3. **React Compiler enabled** -- auto-memoization eliminates common INP regressions.
4. **No `<img>` tags** -- all images use `next/image` with proper `sizes` attributes.
5. **Loading.tsx coverage at 77%** (10/13 routes) -- above average for Next.js apps.
6. **CSS-only animations** -- gradient-shift, bounce-slow, arrow-bounce, shimmer all defined in globals.css with `@keyframes`, no JS runtime cost.

---

## Unresolved Questions

1. **Translation file size** -- How large are `en.ts` and `vi.ts`? If >50KB, namespace filtering in `getMessages()` becomes critical.
2. **Bundle analyzer output** -- No `ANALYZE=true` build was run. Actual framer-motion tree-shaking status is unverified. Recommend running `ANALYZE=true npm run build` to confirm.
3. **Real-world CWV data** -- No field data (CrUX, Vercel Analytics) available. Lab-only assessment. Recommend enabling Vercel Speed Insights or web-vitals reporting.
4. **Middleware auth latency** -- Actual `getUser()` round-trip time to Supabase is unknown. Needs measurement in production.
