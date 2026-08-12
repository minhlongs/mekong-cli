# Code Review Report — RaaS Landing Final Polish

**Date:** 2026-03-19
**Reviewer:** code-reviewer agent
**Scope:** Homepage (VI/EN), Pricing (VI/EN), Base Layout, Astro Config
**Build Status:** ✅ PASS (658ms, 4 pages)

---

## Executive Summary

| Category | Score | Status |
|----------|-------|--------|
| Code Quality | 8.5/10 | ✅ Good |
| SEO Optimization | 9/10 | ✅ Excellent |
| Accessibility | 7.5/10 | ⚠️ Needs Work |
| Performance | 8/10 | ✅ Good |
| Content Polish | 8/10 | ✅ Good |

**Overall:** Production-ready with minor improvements recommended.

---

## ✅ Critical Issues — NONE

No blocking issues found. Build passes, SEO is strong, accessibility is functional.

---

## 🔴 High Priority Issues

### 1. Accessibility — Skip Link Target Missing

**Location:** `base-layout.astro` line 262

```astro
<main id="main-content" role="main"><slot /></main>
```

**Problem:** The `id="main-content"` exists, but the skip link at line 217-220 only becomes visible on focus. However, there's no focus trap or proper focus management for screen reader users navigating the carousel controls.

**Impact:** Keyboard users can't efficiently skip to main content on mobile.

**Fix:**
```astro
<!-- Add tabindex="-1" to main element for programmatic focus -->
<main id="main-content" role="main" tabindex="-1"><slot /></main>
```

### 2. Accessibility — Carousel Controls Missing Aria Labels

**Location:** `index.astro` (VI) lines 601-611

```astro
<button type="button" class="carousel-btn prev" id="carouselPrev" aria-label="Previous testimonial">
<button type="button" class="carousel-btn next" id="carouselNext" aria-label="Next testimonial">
```

**Problem:** English version (`en/index.astro`) does NOT have `aria-label` attributes on carousel buttons.

**Fix:** Add `aria-label` to EN version matching VI version.

### 3. SEO — Missing OG Image File

**Location:** All pages reference `/og-default.jpg`

**Problem:** File does not exist in `/public/` folder. Only `robots.txt` and `sitemap.xml` present.

**Impact:** Social shares will fall back to generic preview.

**Fix:** Generate and add `og-default.jpg` (1200x630px) to `/public/`.

---

## 🟡 Medium Priority Issues

### 4. Code Quality — Inconsistent Plan Data Structure

**Location:** `index.astro` (VI) vs `en/index.astro`

**VI version:**
```js
const plans = [
  { name: 'Free', price: '$0', period: '/mo', tag: '', features: [...] },
];
```

**EN version:**
```js
const plans = [
  { name: 'Free', price: '$0', period: '/mo', tag: '', features: [...] },
];
```

**Problem:** Structure is identical, but VI pricing page uses `price: '$8/mo'` while EN uses `price: '$8/mo'` — consistent. However, homepage plans arrays have slight copy differences that could drift.

**Recommendation:** Extract plans data to a shared `src/data/plans.ts` module with i18n keys.

### 5. Performance — Large Inline Styles

**Location:** All pages use extensive inline `style=""` attributes.

**Problem:** Inline styles increase HTML size and prevent CSS caching.

**Example (index.astro line 106):**
```astro
<section style="background:linear-gradient(135deg,#0a0f1a 0%,#1a1040 50%,#0a2030 100%);min-height:90vh;display:flex;align-items:center;position:relative;overflow:hidden;" aria-label="OpenClaw Introduction">
```

**Fix:** Move critical styles to `global.css` with class names:
```css
.hero-section {
  background: linear-gradient(135deg, #0a0f1a 0%, #1a1040 50%, #0a2030 100%);
  min-height: 90vh;
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}
```

**Impact:** Reduces HTML by ~15-20KB, improves cacheability.

### 6. Accessibility — Form Elements Missing Labels

**Location:** FAQ section (`index.astro` lines 303-309)

```astro
<details class="card animate-on-scroll" style={`animation-delay:${i*0.08}s;padding:0;`} open={i===0}>
  <summary style="padding:20px 24px;cursor:pointer;font-weight:600;font-size:0.975rem;list-style:none;display:flex;justify-content:space-between;align-items:center;gap:12px;">
    {f.q}
```

**Problem:** `<summary>` elements rely on visual text only. Screen readers handle `<details>` natively, but adding `aria-expanded` state improves clarity.

**Fix:**
```astro
<summary
  role="button"
  aria-expanded={i===0 ? 'true' : 'false'}
  style="..."
>
```

### 7. SEO — Sitemap References Non-Existent Pages

**Location:** `public/sitemap.xml`

**Problem:** Sitemap lists 13 URLs, but only 4 pages exist:
- `/signup` — ❌ Missing
- `/en/signup` — ❌ Missing
- `/demo` — ❌ Missing
- `/privacy` — ❌ Missing
- `/terms` — ❌ Missing

**Impact:** Google may flag 404s in Search Console.

**Fix Options:**
1. Create missing pages (recommended for SEO)
2. Remove from sitemap until created
3. Add 301 redirects to appropriate destinations

---

## 🟢 Low Priority / Suggestions

### 8. Content — Inconsistent Testimonial Data

**Location:** `index.astro` (VI) has 5 testimonials; `en/index.astro` has only 3.

**VI version includes:**
- Minh Tuấn, Hà Linh, Đức Anh, Thu Hằng, Thanh Nam

**EN version includes:**
- Minh Tuan, Ha Linh, Duc Anh (no diacritics)

**Recommendation:** Sync testimonial count and add localized names for EN version.

### 9. Performance — Counter Animation Not Used

**Location:** `base-layout.astro` lines 313-342

**Problem:** Counter animation code exists but no elements with class `.counter-value` and `data-target` attribute exist in VI homepage. VI homepage uses hardcoded "500+" instead of animated counters.

**Fix:** Either:
1. Add `<span class="counter-value" data-target="500">0</span>` to homepage
2. Or remove unused animation code

### 10. Accessibility — Missing Lang Attribute on EN Homepage

**Location:** `en/index.astro` line 95

```astro
BaseLayout
  lang="en"
```

**Status:** ✅ CORRECT — Already set. However, double-check that all nested components inherit this properly.

### 11. SEO — Twitter Card Handle Unverified

**Location:** `base-layout.astro` line 175

```astro
<meta name="twitter:site" content="@agencyos" />
```

**Problem:** @agencyos Twitter account may not exist or be verified.

**Fix:** Verify account exists or remove Twitter-specific meta tags.

### 12. Content — FOMO Badge Not Localized

**Location:** `index.astro` (VI) line 324

```astro
<span class="fomo-text">47 doanh nghiệp đăng ký hôm nay</span>
```

**Problem:** EN homepage (`en/index.astro`) does NOT have the FOMO badge at all.

**Recommendation:** Add localized FOMO badge to EN version:
```astro
<span class="fomo-text">47 businesses signed up today</span>
```

### 13. Performance — Missing Image Optimization

**Location:** Customer logos section (`index.astro` lines 400-406)

```astro
<div class="logo-item" title={logo.name} aria-label={logo.name}>
  <span class="logo-icon" aria-hidden="true">{logo.icon}</span>
</div>
```

**Current approach:** Emoji icons (🍜, 💄, ☕, etc.)

**Problem:** Emojis render differently across OS/browsers.

**Recommendation:** Replace with SVG icons or optimized WebP images for consistency.

### 14. Code Quality — Magic Numbers in Animation Delays

**Location:** Multiple pages

```astro
style={`animation-delay:${i*0.1}s`}
style={`animation-delay:${i*0.12}s`}
style={`animation-delay:${i*0.08}s`}
```

**Recommendation:** Extract to constant:
```js
const ANIM_DELAY_STEP = 0.1; // seconds
```

---

## ✅ Positive Observations

### What's Done Well

1. **SEO Meta Tags:** Comprehensive Open Graph, Twitter Cards, hreflang tags ✅
2. **JSON-LD Structured Data:** SoftwareApplication, FAQPage, Product, Organization schemas ✅
3. **Sitemap:** Auto-generated with video schema support ✅
4. **Robots.txt:** Well-configured with crawl delays and path restrictions ✅
5. **i18n Routing:** Proper prefix-based routing with `prefixDefaultLocale: false` ✅
6. **Semantic HTML:** Proper use of `<main>`, `<nav>`, `<section>`, `<article>` ✅
7. **Responsive Design:** Mobile-first CSS with clamp() typography ✅
8. **Reduced Motion Support:** `@media (prefers-reduced-motion: reduce)` queries ✅
9. **High Contrast Support:** `@media (prefers-contrast: high)` queries ✅
10. **Print Styles:** `@media print` optimization ✅

---

## Unresolved Questions

1. **OG Image:** Should we generate `/public/og-default.jpg` now or use external image URL?
2. **Missing Pages:** Priority order for creating `/signup`, `/privacy`, `/terms`, `/demo`?
3. **Testimonials:** Should EN version have same 5 testimonials as VI (with romanized names)?
4. **Analytics:** Any plan to add Google Analytics / Vercel Analytics tracking?
5. **A/B Testing:** Any infrastructure for testing CTA variations?

---

## Recommended Actions (Prioritized)

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| P0 | Add `tabindex="-1"` to `<main>` element | 1 min | High (a11y) |
| P0 | Add aria-labels to EN carousel buttons | 2 min | High (a11y) |
| P1 | Generate/add `og-default.jpg` (1200x630) | 15 min | High (SEO) |
| P1 | Create `/privacy` and `/terms` pages | 1 hr | Medium (SEO/Legal) |
| P2 | Move critical inline styles to CSS classes | 2 hrs | Medium (Performance) |
| P2 | Sync EN testimonials with VI version | 30 min | Low (Content) |
| P3 | Add FOMO badge to EN homepage | 10 min | Low (Marketing) |
| P3 | Remove unused counter animation code | 10 min | Low (Cleanup) |

---

## Metrics

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Build Time | 658ms | < 1000ms | ✅ |
| Pages Built | 4 | - | ✅ |
| TypeScript Errors | 0 | 0 | ✅ |
| Lighthouse SEO | ~95 (est.) | 90+ | ✅ |
| Lighthouse A11y | ~85 (est.) | 90+ | ⚠️ |
| Lighthouse Performance | ~90 (est.) | 90+ | ✅ |
| Sitemap URLs | 13 | Actual: 4 | ⚠️ |
| JSON-LD Schemas | 8 | - | ✅ |

---

## Files Reviewed

| File | LOC | Status |
|------|-----|--------|
| `src/pages/index.astro` (VI) | 706 | ✅ |
| `src/pages/en/index.astro` (EN) | 337 | ✅ |
| `src/pages/pricing.astro` (VI) | 148 | ✅ |
| `src/pages/en/pricing.astro` (EN) | 147 | ✅ |
| `src/layouts/base-layout.astro` | 1850 | ✅ |
| `astro.config.mjs` | 14 | ✅ |
| `src/styles/global.css` | 1872 | ✅ |
| `public/robots.txt` | 34 | ✅ |
| `public/sitemap.xml` | 129 | ✅ |

**Total LOC Reviewed:** ~5,137 lines

---

## Conclusion

The RaaS Landing codebase is **production-ready** with strong SEO foundations and good performance. Primary gaps are:

1. **Accessibility refinements** (skip link focus, carousel labels)
2. **Missing OG image asset**
3. **Sitemap/page mismatch** (13 URLs listed, 4 exist)

All issues are fixable within 2-3 hours. No architectural changes needed.

**Recommendation:** Fix P0 items immediately, schedule P1-P3 for next sprint.

---

_Generated by code-reviewer agent — 2026-03-19_
