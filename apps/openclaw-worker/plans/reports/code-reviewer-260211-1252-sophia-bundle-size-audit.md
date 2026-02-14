# Bundle Size & Tree-Shaking Audit -- sophia-ai-factory

**Date:** 2026-02-11
**Agent:** code-reviewer-260211-1252
**Project:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/`
**Scope:** All production dependencies, import patterns, dynamic loading, barrel exports

---

## Overall Assessment

The codebase shows **mature bundle optimization patterns** -- landing page uses `next/dynamic` extensively, charts are lazy-loaded with `ssr: false`, and server-heavy deps (telegraf, airtable, inngest, jszip, bottleneck) are correctly isolated to server-only code paths. One **critical dead dependency** (`framer-motion`) inflates `node_modules` and can affect install time. Several minor optimizations remain.

---

## 1. Dependency Size Inventory (Non-Dev)

| Package | Est. Size (gzipped) | Used In | Client Bundle? | Notes |
|---------|---------------------|---------|----------------|-------|
| `next` 16.1.6 | Framework | -- | Yes | Core |
| `react` / `react-dom` 19.2.3 | ~45KB | -- | Yes | Core |
| `framer-motion` ^12.31.0 | **~160KB** | **NOWHERE** | **Dead weight** | **REMOVE** |
| `recharts` ^3.7.0 | ~200KB | 1 file (charts.tsx) | Lazy (dynamic, ssr:false) | OK |
| `react-markdown` ^10.1.0 | ~40KB | 1 file (guide-content-renderer) | Server only | OK |
| `remark-gfm` ^4.0.1 | ~20KB | 1 file (guide-content-renderer) | Server only | OK |
| `lucide-react` ^0.563.0 | ~1-2KB/icon | ~50 files, 80+ icons | Yes, tree-shaken | OK |
| `@tanstack/react-query` ^5.90.20 | ~40KB | Root layout (QueryProvider) | **Global** | Acceptable |
| `next-intl` ^4.8.2 | ~15KB | Root layout | **Global** | Unavoidable |
| `@polar-sh/sdk` ^0.42.5 | ~80KB | 2 server files | No | OK |
| `@polar-sh/nextjs` ^0.9.3 | ~15KB | Middleware/webhooks | No | OK |
| `@supabase/supabase-js` ^2.94.1 | ~50KB | Server + 2 client files | Partial | Review |
| `@supabase/ssr` ^0.8.0 | ~10KB | Server + 2 client files | Partial | OK |
| `inngest` ^3.50.0 | ~50KB | API routes only | No | OK |
| `telegraf` ^4.16.3 | ~50KB | Server lib only | No | OK |
| `airtable` ^0.12.2 | ~30KB | Server lib only | No | OK |
| `jszip` ^3.10.1 | ~70KB | Server adapter only | No | OK |
| `bottleneck` ^2.19.5 | ~10KB | Server adapter only | No | OK |
| `sonner` ^2.0.7 | ~10KB | Root layout (dynamic) | Lazy | OK |
| `react-hook-form` ^7.71.1 | ~20KB | Settings pages only | Code-split | OK |
| `@hookform/resolvers` ^5.2.2 | ~5KB | Settings pages only | Code-split | OK |
| `zod` ^4.3.6 | ~15KB | Settings form resolver | Code-split | OK |
| `@upstash/redis` ^1.36.2 | ~15KB | Server lib only | No | OK |
| `standardwebhooks` ^1.0.0 | ~5KB | API route only | No | OK |
| `next-themes` ^0.4.6 | ~3KB | Root layout | Global (tiny) | OK |
| `@ducanh2912/next-pwa` ^10.2.9 | Build-time | Service worker | SW only | OK |
| `class-variance-authority` | ~2KB | UI components | Yes (tiny) | OK |
| `clsx` / `tailwind-merge` | ~2KB each | Utilities | Yes (tiny) | OK |
| `tailwindcss-animate` | Build-time | CSS only | No runtime | OK |
| `@radix-ui/*` (3 packages) | ~5KB each | UI primitives | Code-split | OK |
| `@swc/helpers` | ~2KB | Runtime helpers | Yes (tiny) | OK |

---

## 2. Critical Issues

### 2.1 CRITICAL: `framer-motion` is a Phantom Dependency (~160KB)

**Impact:** ~160KB gzipped dead weight in `node_modules`. Does NOT affect client bundle (not imported), but inflates install time and `node_modules` size.

**Evidence:**
- Listed in `package.json` line 39: `"framer-motion": "^12.31.0"`
- Zero imports found: `from 'framer-motion'` and `from 'motion'` both return 0 results
- The file `src/components/ui/animated-counter-with-framer-motion.tsx` was **refactored to remove framer-motion** but the filename was never updated. It only uses `React` and `cn()` -- no animation library.
- Comments throughout codebase confirm migration away: "CSS transition instead of framer-motion", "replaces framer-motion's whileInView", "Lightweight replacement for framer-motion"

**Fix:** Remove `framer-motion` from `package.json` dependencies. Rename `animated-counter-with-framer-motion.tsx` to `animated-counter.tsx`.

---

## 3. High Priority

### 3.1 `react-markdown` + `remark-gfm` NOT Dynamically Imported in Guide Pages

**Impact:** ~60KB combined. Currently renders server-side (guide pages are server components) so it does NOT inflate client JS. However, `GuideContentRenderer` is statically imported in 6 guide pages with no lazy boundary.

**Current state:** Acceptable because:
- Guide page files (`guide/page.tsx`, `guide/faq/page.tsx`, etc.) are server components
- `GuideContentRenderer` is also a server component (no `'use client'`)
- react-markdown renders to HTML on server, zero client JS

**Recommendation:** No action needed. The current pattern is correct. If the guide ever needs client-side markdown rendering, wrap with `dynamic()`.

### 3.2 Root Layout Global Client Bundle

**Impact:** Every page visitor downloads these immediately:
- `@tanstack/react-query` QueryProvider (~40KB)
- `next-intl` NextIntlClientProvider (~15KB)
- `next-themes` ThemeProvider (~3KB)
- Navbar component (lucide-react Menu + X icons, ~4KB)

**Assessment:** This is a reasonable trade-off. React Query is used on multiple pages (system-health, discovery, analytics). next-intl and next-themes are genuinely global.

**Good patterns observed:**
- `Toaster` (sonner) -- dynamically imported
- `FloatingHelpButton` -- dynamically imported

---

## 4. Medium Priority

### 4.1 `animated-counter-with-framer-motion.tsx` Misleading Filename

**File:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/src/components/ui/animated-counter-with-framer-motion.tsx`

The file name says "with-framer-motion" but the component is a simple `<span>` renderer with zero animation library usage. This is confusing and may prevent future developers from removing the dependency.

**Fix:** Rename to `animated-counter.tsx` and update the single import in `dashboard-stats.tsx`.

### 4.2 Duplicate Supabase Client Initialization

**Files with `createClient` from `@supabase/supabase-js`:**
- `src/lib/supabase/client.ts` (browser client)
- `src/lib/supabase/admin.ts` (admin client)
- `src/lib/services/template-service.ts` (creates own client)
- `src/lib/gateway/checkpoint-supabase-persistence.ts` (creates own client)
- `src/lib/telegram/telegram-bot.ts` (creates own client)
- `src/lib/inngest/functions/generate-campaign.ts` (creates own client)
- `src/lib/inngest/functions/auto-discover-affiliates.ts` (creates own client)
- `src/app/actions/campaigns.ts` (creates own client)
- `src/app/actions/templates.ts` (creates own client)

**Impact:** Multiple `createClient()` calls may create separate instances, increasing memory usage. Not a bundle issue per se, but a code quality concern. Server-side files should ideally share a singleton admin client.

### 4.3 Barrel Export in `lib/gateway/index.ts`

Re-exports 8 classes/types. Since all consumers are server-side, no client bundle impact. However, if any client component ever imports from this barrel, it would pull in the entire gateway module.

**Risk:** Low (currently all server-side). Monitor if gateway code is ever referenced from client components.

---

## 5. Positive Observations

### 5.1 Excellent Dynamic Import Usage on Landing Page

The home page (`src/app/[locale]/page.tsx`) uses `next/dynamic` for **all 8 below-the-fold sections**, each with custom Skeleton fallbacks:
- Workflow, Features, SocialProof, PricingSection, AffiliateDiscovery, ROICalculator, FAQ, Footer
- Only `Hero` is statically imported (above the fold) -- correct pattern

### 5.2 Recharts Properly Isolated

Charts are triple-lazy:
1. `analytics/page.tsx` dynamically imports `AnalyticsView`
2. `AnalyticsView` dynamically imports each chart component with `ssr: false`
3. Charts are only visible to authenticated users on the analytics page

### 5.3 Server Components Well Utilized

Heavy server-only dependencies are correctly isolated:
- `inngest` -- API routes only
- `telegraf` -- Server lib only
- `airtable` -- Server lib only
- `jszip` -- Server adapter only
- `bottleneck` -- Server adapter only
- `@polar-sh/sdk` -- Server lib only
- `standardwebhooks` -- API route only

### 5.4 `lucide-react` Tree-Shaking

All 50+ files use named imports: `import { Menu, X } from 'lucide-react'`. lucide-react v0.563 supports ESM tree-shaking, so only used icons ship to client. No barrel re-export of all icons detected.

### 5.5 React Compiler Enabled

`next.config.ts` line 20: `reactCompiler: true` -- automatically optimizes React component re-renders, reducing unnecessary client-side work.

### 5.6 Bundle Analyzer Available

`@next/bundle-analyzer` is configured and activatable via `ANALYZE=true npm run build`.

---

## 6. Dynamic Import Coverage

| Page/Component | Dynamic? | Notes |
|---------------|----------|-------|
| Landing: Workflow | Yes | Skeleton fallback |
| Landing: Features | Yes | Skeleton fallback |
| Landing: SocialProof | Yes | Skeleton fallback |
| Landing: PricingSection | Yes | Skeleton fallback |
| Landing: AffiliateDiscovery | Yes | Skeleton fallback |
| Landing: ROICalculator | Yes | Skeleton fallback |
| Landing: FAQ | Yes | Skeleton fallback |
| Landing: Footer | Yes | Skeleton fallback |
| Layout: Toaster (sonner) | Yes | Good |
| Layout: FloatingHelpButton | Yes | Good |
| Analytics: AnalyticsView | Yes | Skeleton fallback |
| Analytics: Charts (3x) | Yes | `ssr: false`, Loader2 fallback |
| Settings: SettingsForm | Yes | Via dynamic page import |
| Affiliate Discovery: Dashboard | Yes | Via dynamic page import |
| Dashboard: Campaign-related | Yes | Multiple dynamic imports |
| **Navbar** | **No** | Static in root layout (acceptable) |
| **Hero** | **No** | Static on landing page (correct: above fold) |
| **Guide: GuideContentRenderer** | **No** | Server component (no client JS) |
| **System Health page** | **No** | Could benefit from dynamic import |

---

## 7. Prioritized Fix Recommendations

| # | Priority | Action | Est. Impact | Effort |
|---|----------|--------|-------------|--------|
| 1 | **CRITICAL** | Remove `framer-motion` from `package.json` | -160KB node_modules, faster install | 5 min |
| 2 | **LOW** | Rename `animated-counter-with-framer-motion.tsx` to `animated-counter.tsx` | Code clarity | 5 min |
| 3 | **LOW** | Consolidate Supabase admin client instances into shared singleton | Memory optimization | 30 min |
| 4 | **INFO** | Run `ANALYZE=true npm run build` and capture actual bundle sizes | Data-driven next steps | 10 min |

---

## 8. Client Component Count

**64 files** with `'use client'` directive. Breakdown:
- UI primitives (dropdown-menu, switch, label, fade-in-view, etc.): ~10 files
- Landing sections (hero, features, workflow, etc.): ~8 files
- Dashboard components (stats, lists, forms, etc.): ~18 files
- Settings sections: ~5 files
- Admin pages: ~6 files
- Error boundaries: ~8 files
- Providers: 2 files
- Guide layout: 1 file
- Misc (theme-toggle, language-switcher, etc.): ~6 files

**Assessment:** Ratio is reasonable for a dashboard-heavy SaaS app. Error boundaries must be client components by Next.js design.

---

## 9. `next.config.ts` Review

| Setting | Status | Assessment |
|---------|--------|------------|
| `reactCompiler: true` | Enabled | Excellent -- auto-memoization |
| Bundle analyzer | Configured | `ANALYZE=true` activatable |
| Image formats | `avif, webp` | Optimal |
| Security headers | Comprehensive | HSTS, CSP, X-Frame-Options, etc. |
| PWA | Production only | `disable: true` in dev |
| Webpack custom config | None | Clean -- relies on Next.js defaults |

**Missing config that could help:**
- `modularizeImports` for further tree-shaking (e.g., `lucide-react` deep imports)
- `experimental.optimizePackageImports` for auto-barrel optimization

---

## Unresolved Questions

1. What is the actual production bundle size? Recommend running `ANALYZE=true npm run build` to get precise data from the bundle analyzer.
2. Was `framer-motion` intentionally kept for future use, or is it truly dead? Comments in code suggest full migration away.
3. Is `@ducanh2912/next-pwa` service worker caching configured optimally? The default config may cache aggressively.
