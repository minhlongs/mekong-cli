# Performance Audit Report: Sophia AI Factory

**Date:** 2026-02-11
**Agent:** fullstack-developer (a3e756f)
**Project:** apps/sophia-ai-factory
**Status:** Completed (fixes applied, build compiles)

---

## Audit Scorecard

| Area | Score | Notes |
|------|-------|-------|
| Bundle Size | 8/10 | Good dynamic imports, React Compiler enabled |
| Lazy Loading | 9/10 | Extensive dynamic() usage on landing + dashboard |
| Image Optimization | 8/10 | next/image used, AVIF/WebP formats added |
| Code Splitting | 9/10 | Route-based + component-level splitting |
| Core Web Vitals | 8/10 | Lightweight hero, CSS animations, good font strategy |
| Font Loading | 9/10 | next/font with Geist, proper subsets |
| Third-party Scripts | 9/10 | No external scripts, sonner/lucide tree-shaken |
| Caching | 7/10 | Security headers present, asset caching relies on Next.js defaults |
| **Overall** | **8.4/10** | |

---

## What Was Already Good

1. **Landing page** -- All 8 below-fold sections (Workflow, Features, SocialProof, Pricing, AffiliateDiscovery, ROICalculator, FAQ, Footer) use `next/dynamic` with skeleton loaders
2. **Dashboard pages** -- Charts (recharts), forms, campaign lists all dynamically imported
3. **FadeInView** -- Custom IntersectionObserver + CSS transitions replaces framer-motion (~35KB saved on critical path)
4. **Hero** -- Pure text LCP element, no images/heavy deps, CSS gradient animation
5. **Fonts** -- `next/font/google` with Geist Sans + Mono, latin subset only
6. **No raw `<img>` tags** -- All images use `next/image` with proper `sizes` + `fill`
7. **Loading.tsx** -- Present on 10 routes (root, dashboard, analytics, campaigns, create, settings, support, api-docs, system-health, campaign detail)
8. **React Compiler** -- `reactCompiler: true` eliminates manual memoization
9. **Bundle Analyzer** -- Available via `ANALYZE=true npm run build`
10. **PWA** -- Configured with `@ducanh2912/next-pwa`, disabled in dev
11. **MockModeIndicator** -- Zero-cost: returns null in production (env check)

---

## Issues Found & Fixes Applied

### Fix 1: Image Format Optimization (P1)
**File:** `next.config.ts`
**Issue:** Missing `formats` in images config -- defaults to WebP only, missing AVIF
**Fix:** Added `formats: ['image/avif', 'image/webp']`
**Impact:** ~20-30% smaller images with AVIF for supported browsers

### Fix 2: Dynamic Import Toaster & FloatingHelpButton (P2)
**File:** `src/app/[locale]/layout.tsx`
**Issue:** `sonner` Toaster and FloatingHelpButton eagerly imported in root layout, adding to initial JS bundle for every page
**Fix:** Converted to `next/dynamic` imports -- code-split into separate chunks loaded async
**Impact:** Reduced initial bundle for all pages (~5-10KB savings)

### Fix 3: Remove framer-motion from ProgramCard (P3)
**File:** `src/app/components/affiliate/program-card.tsx`
**Issue:** Used `motion.div` for simple fade-in animation, pulling in framer-motion (~35KB)
**Fix:** Replaced with `FadeInView` component (IntersectionObserver + CSS, ~1KB)
**Impact:** Prevents framer-motion from being bundled if this component gets used

### Fix 4: Remove framer-motion from FilterSidebar (P3)
**File:** `src/app/components/affiliate/filter-sidebar.tsx`
**Issue:** Same as above -- `motion.div` for slide-in animation
**Fix:** Replaced with `FadeInView` component with `direction="left"`
**Impact:** Same as above

---

## Dead Code Identified (Not Fixed -- Flagged Only)

These components exist but are NOT imported by any route:

| File | Dep | Status |
|------|-----|--------|
| `components/ui/floating-element-background-animation.tsx` | framer-motion | Unused |
| `components/ui/staggered-grid-with-framer-motion.tsx` | framer-motion | Unused |
| `app/components/affiliate/program-grid.tsx` | -- | Unused (imports ProgramCard) |

**Recommendation:** Delete these files or add `// @deprecated` comments. They won't affect bundle size (tree-shaking), but add codebase confusion.

---

## Pre-existing Issue (Not My Change)

**File:** `src/lib/inngest/functions/generate-campaign.ts:84`
**Error:** `Argument of type 'Partial<CampaignRow>' is not assignable to parameter of type 'never'`
**Cause:** Supabase type mismatch -- likely `types.ts` was regenerated but `generate-campaign.ts` wasn't updated
**Status:** Pre-existing, unrelated to perf audit

---

## Remaining Optimizations (Future Work)

1. **Static asset caching headers** -- Add `Cache-Control: public, max-age=31536000, immutable` for `/_next/static/` in next.config.ts headers
2. **react-markdown lazy load** -- `GuideContentRenderer` eagerly imports react-markdown + remark-gfm (~40KB). Could dynamic-import on guide page only. Currently only used on `/guide` which is already a separate route, so impact is contained.
3. **framer-motion dependency** -- Can be removed from `package.json` once the 2 unused components are deleted (floating-element, staggered-grid)
4. **Preconnect hints** -- Add `<link rel="preconnect">` for Supabase API domain if used on initial load
5. **Fix TS error** -- `generate-campaign.ts` type error blocks `npm run build` from completing cleanly

---

## Files Modified

| File | Change |
|------|--------|
| `apps/sophia-ai-factory/next.config.ts` | Added `formats: ['image/avif', 'image/webp']` |
| `apps/sophia-ai-factory/src/app/[locale]/layout.tsx` | Dynamic imports for Toaster + FloatingHelpButton |
| `apps/sophia-ai-factory/src/app/components/affiliate/program-card.tsx` | framer-motion -> FadeInView |
| `apps/sophia-ai-factory/src/app/components/affiliate/filter-sidebar.tsx` | framer-motion -> FadeInView |

---

## Build Status

- Compilation: PASS (15.7s)
- TypeScript: FAIL (pre-existing error in generate-campaign.ts, unrelated)
- Changes verified: All 4 modified files compile without errors
