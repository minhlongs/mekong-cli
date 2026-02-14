# Sophia AI Factory -- Image Optimization Audit

**Date:** 2026-02-11
**Agent:** code-reviewer
**Project:** `/Users/macbookprom1/mekong-cli/apps/sophia-ai-factory/apps/sophia-ai-factory`
**Scope:** All image usage across codebase (tsx, public/, remote, CSS, metadata)

---

## Overall Assessment

The codebase has a **CSS-first design** with minimal image usage. Landing page, hero, features, workflow, social proof sections all use CSS gradients + Lucide icons -- no raster images. Only 2 components use `<Image>` from next/image, both correctly configured. However, there are **3 critical issues**: missing OG images, git-tracked screenshots bloating the repo, and incomplete `remotePatterns` coverage.

---

## 1. next/image Usage Audit

### Components Using `<Image>` (2 found)

| File | Line | Props | Status |
|------|------|-------|--------|
| `src/components/video-preview.tsx` | 106 | `fill`, `sizes="(max-width: 672px) 100vw, 672px"`, `alt` | PASS |
| `src/components/discovery/product-card.tsx` | 23 | `fill`, `sizes="64px"`, `alt` | PASS |

### `<img>` HTML Tags

**0 found.** No raw `<img>` tags exist in any .tsx file. All image rendering goes through next/image.

### `priority` Prop

**Not used anywhere.** This is CORRECT because the landing page has zero images above the fold (hero is pure CSS text + gradients). The `<Image>` components only appear in dashboard views (video-preview, product-card) which are below-the-fold or behind auth.

### `loading="lazy"` Explicit

**Not on any `<Image>` component.** Found only on a YouTube `<iframe>` in `src/components/guide/youtube-embed.tsx:16` which is correct (iframe lazy-loading is not automatic).

### `unoptimized` Prop

**Not used anywhere.** All images go through Next.js optimization pipeline.

**Verdict: next/image usage is clean and correct.**

---

## 2. Public Directory Audit

### File Inventory

| File | Size | Used? | Action |
|------|------|-------|--------|
| `public/file.svg` | 391 B | NO | Delete (Next.js starter default) |
| `public/globe.svg` | 1,035 B | NO | Delete (Next.js starter default) |
| `public/next.svg` | 1,375 B | NO | Delete (Next.js starter default) |
| `public/vercel.svg` | 128 B | NO | Delete (Next.js starter default) |
| `public/window.svg` | 385 B | NO | Delete (Next.js starter default) |
| `public/icons/icon-192x192.png` | 1,169 B | YES (PWA manifest) | OK |
| `public/icons/icon-512x512.png` | 2,957 B | YES (PWA manifest) | OK |
| `public/manifest.json` | ~300 B | YES (layout metadata) | OK |

**Issue [MEDIUM]:** 5 unused SVG files from Next.js `create-next-app` template. Zero references in codebase. Grep for `file.svg`, `globe.svg`, `next.svg`, `vercel.svg`, `window.svg` returned no matches.

**Fix:** Delete all 5 files. Total savings: 3.3KB (trivial, but removes dead assets).

### SVG Inline Conversion

Not applicable -- the 5 SVGs are unused defaults. PWA icons are properly PNG (required by manifest spec). No SVG-to-component conversion needed.

---

## 3. Git-Tracked Screenshots [CRITICAL]

**11 PNG files in project root**, all tracked by git (`git ls-files` confirmed):

| File | Size (KB) | Purpose |
|------|-----------|---------|
| `checkout-verify-01-landing.png` | 393 | Browser verification screenshot |
| `checkout-verify-02-pricing.png` | 169 | Browser verification screenshot |
| `checkout-verify-03-starter-polar.png` | 128 | Browser verification screenshot |
| `checkout-verify-04-growth-polar.png` | 127 | Browser verification screenshot |
| `checkout-verify-05-premium-polar.png` | 126 | Browser verification screenshot |
| `checkout-verify-06-master-polar.png` | 129 | Browser verification screenshot |
| `polar-payout-setup-complete.png` | 159 | Payout setup proof |
| `vi-landing-features.png` | 26 | Landing page screenshot |
| `vi-landing-hero.png` | 412 | Landing page screenshot |
| `vi-landing-fullpage.png` | **3,534** | Full-page screenshot |
| `vi-landing-pricing.png` | 276 | Landing page screenshot |
| **Total** | **~5,479** | |

**Impact:** 5.5MB of binary blobs in git history. Not served to users but permanently inflates repo clone size.

**Fix:**
1. Add to `.gitignore`: `checkout-verify-*.png`, `vi-landing-*.png`, `polar-payout-*.png`
2. Remove from tracking: `git rm --cached *.png` (root-level only)
3. Optionally `git filter-branch` or BFG Repo Cleaner to purge from history

---

## 4. Remote Images -- remotePatterns Gaps [HIGH]

### Current Configuration (`next.config.ts` lines 23-32)

```ts
remotePatterns: [
  { protocol: 'https', hostname: 'v5.airtableusercontent.com' },
  { protocol: 'https', hostname: '*.public.blob.vercel-storage.com' },
]
```

### Missing Domains

| Domain | Source | Impact |
|--------|--------|--------|
| `commondatastorage.googleapis.com` | Mock video service (`src/lib/services/mock/video-service.ts:13`) | Image optimization fails in dev/mock mode |
| HeyGen CDN (varies) | `heygen-client.ts` returns `thumbnail_url` from API | `video-preview.tsx` renders these via `<Image>` -- **will throw runtime error if domain not whitelisted** |
| Affiliate product thumbnail domains | `product-card.tsx` renders `product.thumbnail_url` from DB | `<Image>` component will reject any domain not in remotePatterns |

**Risk Analysis:**
- `video-preview.tsx` (line 106) renders `thumbnailUrl` prop through `<Image fill>`. If HeyGen returns a thumbnail from an unlisted domain, Next.js will throw: `Error: Invalid src prop ... hostname "xxx" is not configured under images in your next.config.ts`
- `product-card.tsx` (line 23) renders `product.thumbnail_url` through `<Image fill>`. Affiliate products from ClickBank/ShareASale could have thumbnails from ANY domain.

**Fix options:**
1. **Targeted:** Add known domains: `*.heygen.com`, `commondatastorage.googleapis.com`
2. **Wildcard for user content:** Add `{ protocol: 'https', hostname: '**' }` (bypasses domain restriction but still optimizes). Risk: allows any domain.
3. **Proxy pattern (recommended):** Create an API route `/api/image-proxy?url=...` that fetches and caches remote images. Product-card and video-preview fetch through this proxy. Keeps remotePatterns locked down.

---

## 5. CSS Background Images

**0 found.** No `background-image: url()` or `bg-[url(...)]` patterns in any .tsx, .ts, or .css file. All visual effects use:
- CSS gradients (`bg-gradient-to-r`, `bg-[linear-gradient(...)]`)
- CSS blur/opacity effects
- Tailwind utility classes

**Verdict: No bypass of Next.js image optimization via CSS.**

---

## 6. Favicon & App Icons

| File | Size | Format | Status |
|------|------|--------|--------|
| `src/app/favicon.ico` | 25.9 KB | ICO (16x16 + 32x32, 32bpp) | OK -- standard multi-size ICO |
| `public/icons/icon-192x192.png` | 1.1 KB | PNG | OK -- PWA requirement |
| `public/icons/icon-512x512.png` | 2.9 KB | PNG | OK -- PWA requirement |

**No apple-touch-icon found.** iOS users adding to home screen will get a fallback screenshot instead of the branded icon.

**Fix:** Add `src/app/apple-icon.png` (180x180 PNG) -- Next.js App Router auto-serves it as `<link rel="apple-touch-icon">`.

---

## 7. OG (OpenGraph) Images [CRITICAL]

### Current State

`src/app/[locale]/layout.tsx` lines 50-61:

```ts
openGraph: {
  title: "...",
  description: "...",
  type: "website",
  locale: "en_US",
  siteName: "Sophia AI Factory",
  // NO images property!
},
twitter: {
  card: "summary_large_image",  // Declares large image but provides NONE
  title: "...",
  description: "...",
  // NO images property!
},
```

**Impact:**
- Social media shares (Facebook, LinkedIn, Twitter/X, Telegram) show NO preview image
- `summary_large_image` Twitter card declared but no image = broken card rendering
- SEO penalty for missing structured data image

**Fix options:**
1. **Static OG image:** Create `src/app/opengraph-image.png` (1200x630) and `src/app/twitter-image.png` (1200x600). Next.js App Router auto-discovers these files.
2. **Dynamic OG image (recommended):** Create `src/app/opengraph-image.tsx` using Next.js `ImageResponse` API for dynamic generation with brand colors/text.

---

## 8. Unused Assets Summary

| Category | Count | Total Size | Action |
|----------|-------|------------|--------|
| Unused SVGs in public/ | 5 | 3.3 KB | Delete |
| Git-tracked screenshots | 11 | 5,479 KB | .gitignore + git rm --cached |
| **Total recoverable** | 16 | **5,482 KB** | |

---

## Prioritized Fix List

### CRITICAL (P0)

1. **Add OG images** -- Social sharing completely broken. No preview image for any link share.
   - Create `src/app/opengraph-image.png` (1200x630) or dynamic `opengraph-image.tsx`
   - Create `src/app/twitter-image.png` (1200x600)

2. **Add missing remotePatterns** -- Runtime errors when HeyGen/affiliate thumbnails render
   - Add HeyGen CDN domains to `next.config.ts` remotePatterns
   - Decide strategy for arbitrary affiliate product thumbnails

### HIGH (P1)

3. **Stop tracking screenshots in git** -- 5.5MB of binary waste
   - `.gitignore`: `*.png` at root level (or specific patterns)
   - `git rm --cached checkout-verify-*.png vi-landing-*.png polar-payout-*.png`

4. **Add apple-touch-icon** -- iOS PWA home screen shows no icon
   - Create `src/app/apple-icon.png` (180x180)

### MEDIUM (P2)

5. **Delete unused public/ SVGs** -- Dead Next.js starter template assets
   - Remove: `public/file.svg`, `public/globe.svg`, `public/next.svg`, `public/vercel.svg`, `public/window.svg`

### LOW (P3)

6. **Mock service domain** -- `commondatastorage.googleapis.com` not in remotePatterns
   - Only affects dev/mock mode. Low priority but causes console errors during development.

---

## Positive Observations

- CSS-first landing page design eliminates LCP image bottleneck entirely
- Both `<Image>` usages have correct `fill` + `sizes` props
- No raw `<img>` tags anywhere in the codebase
- No `unoptimized` prop usage
- No CSS background images bypassing optimization
- PWA manifest and icons properly configured
- next.config.ts has AVIF + WebP formats enabled (optimal)
- favicon is properly multi-size ICO format

---

## Unresolved Questions

1. What domain(s) does HeyGen return for `thumbnail_url`? Need to check actual API responses to determine exact remotePatterns entries needed.
2. Are affiliate product thumbnails currently rendering in production, or is the discovery feature behind a feature flag? If behind flag, the remotePatterns gap is deferred risk.
3. Should the checkout-verify screenshots be kept in the repo at all, or moved to external storage (Google Drive, Notion)?
