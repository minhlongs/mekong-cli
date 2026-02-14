# Sophia AI Factory -- Lazy Loading & Code Splitting Audit

**Date:** 2026-02-11
**Scope:** `/apps/sophia-ai-factory/apps/sophia-ai-factory/src/`
**Total source files:** ~24,600 LOC across TSX/TS
**Tech:** Next.js 16.1.6 (App Router), React 19.2.3, reactCompiler: true

---

## 1. next/dynamic Usage Audit

### Currently Using dynamic() (11 instances) -- GOOD

| File | Component | SSR | Fallback | Verdict |
|------|-----------|-----|----------|---------|
| `src/app/[locale]/layout.tsx` | Toaster (sonner) | yes (default) | none | OK -- lightweight toast |
| `src/app/[locale]/layout.tsx` | FloatingHelpButton | yes (default) | none | OK -- conditionally visible |
| `src/app/[locale]/page.tsx` | Workflow, Features, SocialProof, PricingSection, AffiliateDiscovery, ROICalculator, FAQ, Footer | yes | Skeleton fallbacks | EXCELLENT -- all below-fold sections lazy |
| `src/app/[locale]/dashboard/page.tsx` | CampaignList | yes | Skeleton | OK |
| `src/app/[locale]/dashboard/analytics/page.tsx` | AnalyticsView | yes | Skeleton | OK |
| `src/app/[locale]/dashboard/settings/page.tsx` | SettingsForm | yes | Skeleton | OK |
| `src/app/[locale]/dashboard/create/page.tsx` | CreateProjectFormWithTemplates | yes | Skeleton | OK |
| `src/app/[locale]/dashboard/campaigns/page.tsx` | CampaignList | yes | Skeleton | OK |
| `src/app/[locale]/dashboard/campaigns/[id]/page.tsx` | VideoPreview | yes | Skeleton | OK |
| `src/app/[locale]/dashboard/analytics/components/analytics-view.tsx` | StatusDistributionChart, CompletionTimeChart, CampaignsByTypeChart | ssr: false | Spinner | EXCELLENT -- recharts ~200KB lazy + SSR disabled |
| `src/app/[locale]/dashboard/components/dashboard-stats.tsx` | AnimatedCounter | ssr: false | `<span>0</span>` | OK |
| `src/app/[locale]/affiliate-discovery/page.tsx` | DiscoveryDashboard | yes | Skeleton | OK |

### Should Use dynamic() But Don't -- MISSING

| Component | File | Why Dynamic | Est. Savings |
|-----------|------|-------------|--------------|
| **PricingSection** (on `/pricing` page) | `src/app/[locale]/pricing/page.tsx` | Imported statically. Same component is lazy on landing but eager on `/pricing`. The component is 293 lines with client state | ~5-8 KB |
| **GuideContentRenderer** | `src/components/guide/guide-content-renderer.tsx` | Imports `react-markdown` + `remark-gfm` (~40KB gzipped). Only used on guide pages but imported statically | ~15-20 KB |
| **AdminSidebar** | `src/app/components/admin/admin-sidebar.tsx` | Client component imported directly in admin layout. Admin routes rarely visited | ~2-3 KB |
| **DiscoveryDashboard sub-components** | `src/components/discovery/dashboard.tsx` | The dashboard itself is lazy, but it statically imports FilterPanel + ProductCard. FilterPanel is a `'use client'` component | ~2-3 KB |
| **SettingsForm sections** | `src/components/settings/sections/*` | 4 section components (appearance, api-keys, profile, notifications) all `'use client'`, imported statically by SettingsForm | ~3-5 KB |

---

## 2. React.lazy / Suspense Audit

### React.lazy Usage: **NONE**

No `React.lazy` calls found. This is fine -- `next/dynamic` is the idiomatic replacement in Next.js App Router.

### Suspense Boundaries

**Existing (1 explicit):**
- `src/app/[locale]/dashboard/settings/page.tsx` -- wraps SettingsForm in `<Suspense fallback={<SettingsSkeleton />}>`

**loading.tsx Files (10 total -- automatic route-level Suspense):**
- `[locale]/loading.tsx` -- root
- `dashboard/loading.tsx` -- dashboard root
- `dashboard/analytics/loading.tsx`
- `dashboard/campaigns/loading.tsx`
- `dashboard/campaigns/[id]/loading.tsx`
- `dashboard/create/loading.tsx`
- `dashboard/settings/loading.tsx`
- `dashboard/support/loading.tsx`
- `dashboard/api-docs/loading.tsx`
- `dashboard/system-health/loading.tsx`

**Missing loading.tsx files:**
| Route | Impact |
|-------|--------|
| `(admin)/admin/` | Admin pages have no loading.tsx -- full-page flash on navigation |
| `(admin)/admin/affiliates/` | No loading state |
| `(admin)/admin/features/` | No loading state |
| `(admin)/admin/settings/` | No loading state |
| `(admin)/admin/settings/integrations/` | No loading state |
| `guide/` sub-routes (faq, how-it-works, screens, etc.) | No loading.tsx for guide child routes |
| `login/` | No loading.tsx |
| `pricing/` | No loading.tsx |
| `affiliate-discovery/` | No loading.tsx |

---

## 3. 'use client' Boundary Analysis

### All 'use client' Components (62 files)

#### JUSTIFIED -- Needs Client APIs (useState, useEffect, event handlers, browser APIs)

| # | File | Reason | Could Be Server? |
|---|------|--------|-------------------|
| 1 | `components/theme-toggle.tsx` | Theme switching (useTheme) | No |
| 2 | `components/language-switcher.tsx` | Dropdown interaction | No |
| 3 | `components/dashboard/health-indicator.tsx` | useQuery, polling | No |
| 4 | `components/discovery/filter-panel.tsx` | useState for filters | No |
| 5 | `components/discovery/dashboard.tsx` | useState, useQuery | No |
| 6 | `components/video-preview.tsx` | Video player interaction | No |
| 7 | `components/settings/settings-form.tsx` | Form state | No |
| 8 | `components/settings/sections/appearance-section.tsx` | useTheme | No |
| 9 | `components/settings/sections/api-keys-section.tsx` | Form state | No |
| 10 | `components/settings/sections/profile-section.tsx` | Form state | No |
| 11 | `components/settings/sections/notifications-section.tsx` | Form state | No |
| 12 | `components/pricing-section.tsx` | useState, checkout flow | No |
| 13 | `components/providers/query-provider.tsx` | QueryClientProvider | No |
| 14 | `components/providers/theme-provider.tsx` | ThemeProvider | No |
| 15 | `components/ui/dropdown-menu.tsx` | Radix UI (requires client) | No |
| 16 | `components/ui/mobile-nav.tsx` | usePathname, navigation | No |
| 17 | `components/ui/switch.tsx` | Radix Switch | No |
| 18 | `components/ui/fade-in-view.tsx` | IntersectionObserver | No |
| 19 | `components/ui/typewriter-effect-animation.tsx` | Animation state | No |
| 20 | `components/ui/animated-counter-with-framer-motion.tsx` | Client rendering (despite name, no framer import) | No |
| 21 | `components/ui/label.tsx` | Radix Label | No |
| 22 | `components/guide/floating-help-button.tsx` | useState, click handlers | No |
| 23 | `app/components/layout/navbar.tsx` | useState, usePathname, scroll handling | No |
| 24 | `app/components/admin/admin-sidebar.tsx` | usePathname | No |
| 25 | `app/components/affiliate/program-grid.tsx` | Client rendering | No |
| 26 | `app/components/affiliate/program-card.tsx` | Client interactions | No |
| 27 | `app/components/affiliate/filter-sidebar.tsx` | Filter state | No |
| 28 | `app/components/sections/hero.tsx` | useTranslations | Partially* |
| 29 | `app/components/sections/workflow.tsx` | useTranslations | Partially* |
| 30 | `app/components/sections/features.tsx` | useTranslations | Partially* |
| 31 | `app/components/sections/social-proof.tsx` | IntersectionObserver + useTranslations | No |
| 32 | `app/components/sections/faq.tsx` | useState (accordion) + useTranslations | No |
| 33 | `app/components/sections/roi-calculator.tsx` | useState (sliders) | No |
| 34 | `app/components/sections/affiliate-discovery.tsx` | useTranslations, filters | No |
| 35 | `app/[locale]/login/page.tsx` | Form state, auth | No |
| 36 | `app/[locale]/error.tsx` | Error boundary (required client) | No |
| 37 | `app/[locale]/guide/layout.tsx` | useState, usePathname | No |
| 38 | `app/[locale]/(admin)/admin/affiliates/page.tsx` | useState, filter | No |
| 39 | `app/[locale]/(admin)/admin/features/page.tsx` | useState, toggles | No |
| 40 | `app/[locale]/(admin)/admin/settings/page.tsx` | Client page | Partially** |
| 41 | `app/[locale]/(admin)/admin/settings/integrations/page.tsx` | useState, form | No |
| 42 | `app/[locale]/(admin)/admin/users/admin-users-client.tsx` | Client state | No |
| 43 | `app/[locale]/dashboard/analytics/components/analytics-view.tsx` | useMemo, client charts | No |
| 44 | `app/[locale]/dashboard/analytics/components/charts.tsx` | Recharts (client-only) | No |
| 45 | `app/[locale]/dashboard/components/dashboard-stats.tsx` | useTranslations | No |
| 46 | `app/[locale]/dashboard/components/onboarding-welcome-banner.tsx` | Client interaction | No |
| 47 | `app/[locale]/dashboard/components/project-card.tsx` | Client interaction | No |
| 48 | `app/[locale]/dashboard/components/project-grid.tsx` | Client state | No |
| 49 | `app/[locale]/dashboard/components/campaign-list.tsx` | Client state, filters | No |
| 50 | `app/[locale]/dashboard/components/create-project-form.tsx` | Form state | No |
| 51 | `app/[locale]/dashboard/components/campaign-export-control.tsx` | Client interaction | No |
| 52 | `app/[locale]/dashboard/components/campaign-creation-form-with-template-selector.tsx` | Form state | No |
| 53 | `app/[locale]/dashboard/system-health/page.tsx` | useQuery, polling | No |
| 54-62 | Error boundaries (8 files) | Required by Next.js | No |

#### COULD POTENTIALLY BE SERVER COMPONENTS

**(*) Landing sections using only `useTranslations`:**

These components (hero, workflow, features) are `'use client'` solely because they use `useTranslations` from `next-intl`. If refactored to accept translated strings as props from a server parent, they could become server components. However, this is a tradeoff: `useTranslations` is the idiomatic next-intl pattern, and with React Compiler enabled, the perf impact is minimal.

**Est. savings if converted:** ~3-5 KB per section (JSX only, no heavy deps)
**Recommendation:** LOW priority. React Compiler already optimizes these.

**(**) Admin settings page:**

`app/[locale]/(admin)/admin/settings/page.tsx` is marked `'use client'` but contains no interactive state. It only renders static cards with `process.env` values and links. Could be a server component.

**Est. savings:** ~1-2 KB

---

## 4. Third-Party Script Loading

### next/script Usage: **NONE**

No `<Script>` from `next/script` found anywhere. No `<script>` tags found either.

**Assessment:** This is acceptable for current state (no analytics/tracking scripts). When adding analytics (GA, Vercel Analytics, Hotjar, etc.), MUST use `next/script` with `strategy="lazyOnload"`.

---

## 5. Route-Level Code Splitting

### App Router Automatic Splitting -- VERIFIED

Next.js App Router automatically code-splits per route segment. The route structure provides natural boundaries:

| Route Group | Separate Chunk? | Notes |
|------------|----------------|-------|
| Landing (`/`) | Yes | `page.tsx` has all sections lazy via dynamic() |
| Dashboard (`/dashboard/**`) | Yes | Separate layout.tsx creates boundary |
| Admin (`/(admin)/admin/**`) | Yes | Route group `(admin)` with own layout |
| Guide (`/guide/**`) | Yes | Own layout.tsx |
| Login (`/login`) | Yes | Standalone page |
| Pricing (`/pricing`) | Yes | Standalone page |
| Affiliate Discovery (`/affiliate-discovery`) | Yes | Standalone page |
| Setup Wizard (`/setup-wizard`) | Yes | Separate root layout (no shared providers) |

**Concern:** Admin pages are full `'use client'` pages without dynamic imports. Each admin page (affiliates 162 LOC, features 106 LOC, settings 113 LOC, integrations 121 LOC, users 189 LOC) ships all code eagerly within its chunk.

---

## 6. Font Loading Audit

### Current Setup

**File: `src/app/[locale]/layout.tsx`**
```typescript
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});
const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});
```

**File: `src/app/setup-wizard/layout.tsx`**
```typescript
const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});
```

### Issues Found

| Issue | Severity | Detail |
|-------|----------|--------|
| Missing `display` property | MEDIUM | No `display: 'swap'` set. Next.js defaults to `display: 'swap'` for `next/font/google`, so this is implicitly correct. But explicit is better. |
| Duplicate font instantiation | LOW | `Geist` font is instantiated in both `[locale]/layout.tsx` and `setup-wizard/layout.tsx`. Next.js may deduplicate, but should use shared instance. |
| Vietnamese subset missing | MEDIUM | Only `["latin"]` subset configured. For Vietnamese locale (`vi`), `latin-ext` should be added to support diacritics properly. |
| No preload hint | LOW | `next/font` auto-handles preload. No action needed. |

**Estimated savings from adding `latin-ext` subset:** No savings -- adds ~2-5 KB for proper i18n support. This is a correctness fix, not a perf fix.

---

## 7. Dead Dependency -- framer-motion

**CRITICAL FINDING:** `framer-motion` (v12.31.0, ~130KB minified) is in `package.json` but **ZERO imports** exist in the codebase. All framer-motion patterns have been replaced with:

- `fade-in-view.tsx` -- IntersectionObserver replacement
- CSS transitions -- in hero, roi-calculator
- Native IntersectionObserver -- in social-proof

**Action:** Remove `framer-motion` from `package.json` dependencies.

**Estimated savings:** While tree-shaking should eliminate it if unused, removing it:
- Reduces `node_modules` size
- Speeds up `npm install` by ~3-5s
- Prevents accidental future imports
- Estimated bundle savings: ~0 KB (tree-shaking) but eliminates risk

---

## 8. Heavy Dependencies Analysis

| Package | Size (min+gzip) | Where Imported | Lazy? | Action |
|---------|-----------------|----------------|-------|--------|
| `recharts` v3.7.0 | ~200 KB | `charts.tsx` only | YES (dynamic, ssr:false) | EXCELLENT |
| `framer-motion` v12.31.0 | ~130 KB | NOWHERE | N/A | REMOVE from package.json |
| `react-markdown` v10.1.0 | ~40 KB | `guide-content-renderer.tsx` | NO | Should be dynamic |
| `remark-gfm` v4.0.1 | ~15 KB | `guide-content-renderer.tsx` | NO | Comes with react-markdown |
| `sonner` v2.0.7 | ~10 KB | `layout.tsx` (Toaster) | YES (dynamic) | OK |
| `jszip` v3.10.1 | ~45 KB | Server-only (clickbank-adapter) | N/A (server) | OK -- never in client bundle |
| `airtable` v0.12.2 | ~30 KB | Server-only (lib/airtable.ts) | N/A (server) | OK |
| `inngest` v3.50.0 | ~50 KB | Server-only (API routes) | N/A (server) | OK |
| `telegraf` v4.16.3 | ~80 KB | Server-only (telegram-bot) | N/A (server) | OK |

---

## Summary: Prioritized Recommendations

### CRITICAL (Do Now)

| # | Action | Est. Savings | File(s) |
|---|--------|-------------|---------|
| 1 | Remove `framer-motion` from `package.json` | Risk elimination, ~3-5s install time | `package.json` |

### HIGH Priority

| # | Action | Est. Savings | File(s) |
|---|--------|-------------|---------|
| 2 | Dynamic import `GuideContentRenderer` (react-markdown + remark-gfm) | ~15-20 KB | Guide pages that use it |
| 3 | Add `loading.tsx` to admin routes | Perceived perf improvement | `(admin)/admin/`, `(admin)/admin/affiliates/`, etc. |
| 4 | Add `loading.tsx` to `/login`, `/pricing`, `/affiliate-discovery` | Perceived perf improvement | Respective route dirs |
| 5 | Add `latin-ext` font subset for Vietnamese support | Correctness fix | Both layout.tsx files |

### MEDIUM Priority

| # | Action | Est. Savings | File(s) |
|---|--------|-------------|---------|
| 6 | Convert admin settings page to server component | ~1-2 KB | `(admin)/admin/settings/page.tsx` |
| 7 | Add `display: 'swap'` explicitly to font configs | Explicit clarity | Both layout.tsx files |
| 8 | Add `loading.tsx` to guide sub-routes | Better UX | `guide/faq/`, `guide/how-it-works/`, etc. |

### LOW Priority

| # | Action | Est. Savings | File(s) |
|---|--------|-------------|---------|
| 9 | Dynamic import PricingSection on `/pricing` page (already lazy on landing) | ~5-8 KB on pricing route | `pricing/page.tsx` |
| 10 | Extract shared Geist font instantiation to avoid duplication | Code cleanliness | `layout.tsx` files |
| 11 | Dynamic import settings form sections individually | ~3-5 KB | Settings sections |

---

## Overall Assessment

**Score: 8/10** -- The project demonstrates strong lazy loading practices.

**Strengths:**
- Landing page has ALL below-fold sections lazy loaded via `next/dynamic` with skeleton fallbacks
- Recharts (heaviest client lib) properly lazy-loaded with `ssr: false`
- Comprehensive `loading.tsx` coverage for dashboard routes
- Server components used correctly for data-fetching pages (dashboard, analytics, campaigns, create, settings)
- AnimatedCounter lazy loaded with `ssr: false`
- `sonner` Toaster lazy loaded in root layout
- No unnecessary third-party scripts
- `@next/bundle-analyzer` available for analysis

**Weaknesses:**
- `framer-motion` in package.json but unused (dead dep)
- `react-markdown` (~40KB) not lazy loaded
- Admin routes missing `loading.tsx`
- Some landing sections are `'use client'` only for `useTranslations`
- Vietnamese font subset missing (`latin-ext`)

---

## Unresolved Questions

1. Is there a plan to add analytics (GA, Vercel Analytics)? If so, `next/script` with `strategy="lazyOnload"` should be prepared
2. Could `next-intl`'s `getTranslations` (server-side) be used in landing sections instead of `useTranslations` to make hero/workflow/features server components? This depends on whether those sections need any client interactivity
3. The `animated-counter-with-framer-motion.tsx` file name is misleading -- it no longer uses framer-motion. Consider renaming to `animated-counter.tsx` for clarity
