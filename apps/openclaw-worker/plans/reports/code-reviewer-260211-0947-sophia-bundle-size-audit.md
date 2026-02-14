# Sophia AI Factory - Bundle Size Audit

**Date:** 2026-02-11
**Agent:** code-reviewer
**Scope:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory/`
**Type:** Research only - no files modified

---

## Overall Assessment

Bundle hygiene is ABOVE AVERAGE. Landing page uses `next/dynamic` for code splitting. `FadeInView` wisely replaces framer-motion with IntersectionObserver + CSS. However, `framer-motion` (5.3MB) is installed as a dependency and its 2 consumer files are **dead code** (never imported). `recharts` (8MB) is loaded for a single analytics page. Total static chunks: 2.3MB (pre-gzip).

**Build chunks (top 5 by size):**

| Chunk | Size | Contains |
|-------|------|----------|
| `a867763516bad40e.js` | 355KB | react-hook-form deep utilities |
| `eb8b87b348967caf.js` | 266KB | Zod v4 schema library |
| `9bbae971a85c340e.js` | 219KB | Next.js framework internals |
| `a8c6e5b324e59153.js` | 177KB | Cookie/SSR auth layer |
| `a6dad97d9634a72d.js` | 110KB | Unknown shared module |

---

## CRITICAL: Dead Code with framer-motion

- **Files:** `/src/components/ui/floating-element-background-animation.tsx`, `/src/components/ui/staggered-grid-with-framer-motion.tsx`
- **Issue:** Both files import `motion` from `framer-motion` but are NEVER imported anywhere in the codebase. Grep for `floating-element-background` and `staggered-grid-with-framer` across all src/ returns zero import matches.
- **Impact:** HIGH - framer-motion (5.3MB installed, ~35KB gzipped client bundle) may still be included as a dependency even though its consumers are dead code. Turbopack/webpack might pull it in due to the dependency graph.
- **Estimated savings:** ~35KB gzipped if framer-motion removed entirely
- **Fix:** Delete both dead files. If no other file imports from `framer-motion`, remove `framer-motion` from `package.json` dependencies.

---

## Heavy Dependencies Analysis

### In package.json (37 dependencies + 18 devDependencies)

| Dependency | Installed Size | gzip Client Bundle | Usage Count | Server-only? |
|------------|---------------|-------------------|-------------|-------------|
| `framer-motion` | 5.3MB | ~35KB | 2 files (DEAD CODE) | No |
| `recharts` | 8.0MB | ~45KB | 1 file (charts.tsx) | No |
| `@polar-sh/sdk` | 38MB | N/A | 2 files | Yes |
| `inngest` | 10MB | N/A | 2 files | Yes |
| `airtable` | 2.3MB | N/A | 1 file | Yes |
| `telegraf` | 1.1MB | N/A | 2 files | Yes |
| `jszip` | 880KB | N/A | 1 file | Yes |
| `react-markdown` | 80KB | ~12KB | 1 file | Mixed |
| `@supabase/supabase-js` | Large | ~20KB | Multiple | Mixed |
| `zod` v4 | Moderate | ~25KB | Multiple | Both |
| `react-hook-form` | Moderate | ~25KB | Multiple | No |
| `@tanstack/react-query` | Moderate | ~15KB | 4 files | No |

---

## Findings by Category

### 1. Dead Dependencies (framer-motion)

- **File:** `/src/components/ui/floating-element-background-animation.tsx`
  - Issue: Dead code - exports `FloatingElement` and `FloatingBackground` but ZERO imports found in project
  - Impact: HIGH
  - Estimated savings: ~35KB gzipped (entire framer-motion)
  - Fix: Delete file. Remove `framer-motion` from package.json if confirmed no other consumers.

- **File:** `/src/components/ui/staggered-grid-with-framer-motion.tsx`
  - Issue: Dead code - exports `StaggeredGrid` but ZERO imports found in project
  - Impact: HIGH (same dependency)
  - Fix: Delete file.

- **File:** `/src/components/ui/animated-counter-with-framer-motion.tsx`
  - Issue: Misleading filename - does NOT use framer-motion, only React state. Name should be `animated-counter.tsx`
  - Impact: Low (no bundle impact, just naming confusion)
  - Fix: Rename file to `animated-counter.tsx`

- **File:** `/src/components/ui/typewriter-effect-animation.tsx`
  - Issue: Misleading filename - no animation library used, just static render
  - Impact: Low
  - Fix: Rename to `typewriter-text.tsx`

### 2. recharts - Single Consumer

- **File:** `/src/app/[locale]/dashboard/analytics/components/charts.tsx`
  - Issue: recharts (8MB installed, ~45KB gzipped client) imported for 3 chart components (PieChart, BarChart)
  - Impact: Medium - already dynamically imported via `analytics-view.tsx`
  - Fix: Already mitigated by `next/dynamic`. Consider replacing with lightweight alternative (e.g., `chart.js/auto` at ~15KB or CSS-based charts for simple pie/bar).

### 3. react-markdown + remark-gfm

- **File:** `/src/components/guide/guide-content-renderer.tsx`
  - Issue: react-markdown (~12KB) + remark-gfm + unified ecosystem pulled in for guide pages. Not "use client" itself, but guide layout IS "use client"
  - Impact: Medium - loaded for 6 guide sub-pages only
  - Estimated savings: ~15KB gzipped if lazy-loaded
  - Fix: Dynamically import `GuideContentRenderer` in each guide page, or convert guide pages to server components (they render static markdown).

### 4. Server-only Libraries (OK)

The following heavy libraries are server-only (API routes, server components). They do NOT affect client bundle:

| Library | File(s) | Status |
|---------|---------|--------|
| `telegraf` | `lib/telegram/*.ts` | OK - server only |
| `inngest` | `lib/inngest/client.ts`, `api/inngest/route.ts` | OK - server only |
| `airtable` | `lib/airtable.ts` | OK - server only |
| `jszip` | `lib/ingestion/adapters/clickbank-adapter.ts` | OK - server only |
| `@polar-sh/sdk` | `lib/polar.ts`, `lib/clients/polar-client.ts` | OK - server only |
| `@upstash/redis` | `lib/redis.ts`, `lib/clients/upstash-redis-client.ts` | OK - server only |
| `bottleneck` | `lib/ingestion/base-adapter.ts` | OK - server only |

### 5. Barrel Exports

- **File:** `/src/types/index.ts`
  - Issue: Barrel export but types-only (no runtime code). `export type` statements are erased at compile time.
  - Impact: None
  - Status: OK

- **File:** `/src/lib/gateway/index.ts`
  - Issue: Barrel re-export of OpenClawGateway, adapters, types
  - Impact: None - all gateway code is server-only (API routes)
  - Status: OK

**No other barrel exports found.** Components import directly from their file paths.

### 6. Client Components ("use client")

**Total: 47 files** with "use client" directive.

**Justified "use client"** (uses hooks, state, events):
- `hero.tsx` - uses `useTranslations`, click handlers
- `pricing-section.tsx` - uses hooks
- `login/page.tsx` - form interactions
- All `dashboard/components/*.tsx` - interactive forms/lists
- `navbar.tsx`, `mobile-nav.tsx` - menu state
- UI primitives: `dropdown-menu.tsx`, `switch.tsx`, `label.tsx`

**Questionable "use client":**

- **File:** `/src/components/ui/label.tsx`
  - Issue: Simple wrapper over Radix Label. If no event handlers needed, could be server component.
  - Impact: Low
  - Fix: Verify if hooks/events used; if not, remove "use client"

- **File:** `/src/components/ui/animated-counter-with-framer-motion.tsx`
  - Issue: Marked "use client" but only renders static JSX (no hooks, no state, no effects). The animation was stripped but directive remains.
  - Impact: Low
  - Fix: Remove "use client" - this is a pure render component now

- **File:** `/src/components/ui/typewriter-effect-animation.tsx`
  - Issue: Same - marked "use client" but no hooks/state/effects. Pure render.
  - Impact: Low
  - Fix: Remove "use client"

### 7. Import Patterns

**Wildcard imports (`import * as`):**

| Pattern | Count | Status |
|---------|-------|--------|
| `import * as React` | 10 files | OK - Turbopack/webpack optimizes React namespace |
| `import * as Primitives` (Radix) | 4 files | OK - Radix re-exports specific primitives |
| `import * as` in test files | 3 files | OK - test-only, not bundled |

**lucide-react imports:**
- 45+ files import from `lucide-react` using named imports: `{ Icon1, Icon2 }`
- lucide-react v0.563 is tree-shakeable with named imports
- Status: OK - proper tree-shaking pattern used

**No problematic barrel imports from large libraries.**

### 8. next.config.ts Optimization

| Setting | Value | Assessment |
|---------|-------|------------|
| `reactCompiler` | `true` | GOOD - React Compiler enabled |
| `images.formats` | `['avif', 'webp']` | GOOD - modern formats |
| Bundle Analyzer | Installed, env-gated | GOOD |
| PWA | `@ducanh2912/next-pwa` | OK - disabled in dev |
| `experimental.optimizeCss` | Not set | MISSING - could reduce CSS bundle |
| `experimental.optimizePackageImports` | Not set | MISSING - could help with large packages |

### 9. i18n Messages

- `en.json`: 17KB
- `vi.json`: 20KB
- Total: 37KB raw, ~8KB gzipped
- All messages sent to client via `NextIntlClientProvider messages={messages}`
- Impact: Medium - consider splitting messages per page namespace
- Fix: Use `getMessages({ namespace })` to send only page-relevant messages

---

## Prioritized Recommendations

### CRITICAL (do first, biggest impact)

1. **Delete dead framer-motion files + remove dependency**
   - Delete: `src/components/ui/floating-element-background-animation.tsx`
   - Delete: `src/components/ui/staggered-grid-with-framer-motion.tsx`
   - Run: `npm uninstall framer-motion`
   - Savings: ~35KB gzipped from client bundle
   - Risk: Zero (files are not imported anywhere)

### HIGH

2. **Add `optimizePackageImports` to next.config.ts**
   ```ts
   experimental: {
     optimizePackageImports: ['lucide-react', '@radix-ui/react-dropdown-menu'],
   }
   ```
   - Savings: ~5-10KB gzipped (lucide-react optimization)

3. **Consider recharts alternative for simple charts**
   - Current: recharts at ~45KB gzipped for 3 chart components
   - Alternative: lightweight chart lib or SVG-based
   - Already mitigated: dynamically imported, so only analytics page affected
   - Savings: ~30KB gzipped on analytics page

### MEDIUM

4. **Split i18n messages per namespace**
   - Current: All 37KB messages sent to every page
   - Fix: `getMessages({ namespace: 'landing' })` for landing, `{ namespace: 'dashboard' }` for dashboard
   - Savings: ~4-8KB per page load

5. **Remove stale "use client" from static components**
   - `animated-counter-with-framer-motion.tsx` - no hooks/state
   - `typewriter-effect-animation.tsx` - no hooks/state
   - Savings: Minimal direct, improves SSR coverage

6. **Rename misleading files**
   - `animated-counter-with-framer-motion.tsx` -> `animated-counter.tsx`
   - `typewriter-effect-animation.tsx` -> `typewriter-text.tsx`
   - Impact: Developer clarity only

### LOW

7. **Add `experimental.optimizeCss: true`** (if using Tailwind v4, may already be optimized)

8. **Dynamically import `GuideContentRenderer`** to lazy-load react-markdown on guide pages

---

## Positive Observations

- Landing page sections ALL dynamically imported with skeleton loading (excellent code splitting)
- Hero section uses CSS animations instead of framer-motion (intentional optimization)
- `FadeInView` component is a lightweight IntersectionObserver replacement for framer-motion (~0.5KB vs ~35KB)
- lucide-react icons use proper named imports (tree-shakeable)
- Server-heavy libraries (telegraf, inngest, airtable, jszip, polar, upstash) correctly isolated in server-only files
- Bundle analyzer installed and ready (`ANALYZE=true npm run build`)
- Security headers properly configured in next.config.ts
- React Compiler enabled for automatic memoization

## Estimated Total Savings

| Action | Estimated Savings (gzipped) |
|--------|---------------------------|
| Remove framer-motion | ~35KB |
| optimizePackageImports | ~5-10KB |
| Split i18n messages | ~4-8KB per page |
| recharts -> lightweight | ~30KB (analytics only) |
| **Total potential** | **~74-83KB** |

---

## Unresolved Questions

1. Is the 355KB chunk (`a867763516bad40e.js`) loaded on initial page? Need `ANALYZE=true` build to map chunks to routes.
2. Does `@ducanh2912/next-pwa` service worker add significant overhead? Need to measure SW script size.
3. Is `zod` v4 (266KB chunk) tree-shaken effectively by Turbopack? Zod v4 is new and may have different module structure than v3.
4. Are the Supabase client libraries (`@supabase/ssr`, `@supabase/supabase-js`) pulled into client bundle? They have both server and client usage patterns.
