# UI Audit Report — Responsive, Accessibility & Visual Consistency

**Date:** 2026-03-19
**Auditor:** UI/UX Designer Agent
**Scope:** raas-landing, raas-dashboard, vibe-ui, ui packages

---

## Executive Summary

| Area | Score | Status |
|------|-------|--------|
| Responsive Design | 7/10 | **Good** — Mobile breakpoints present, needs refinement |
| Accessibility | 6/10 | **Moderate** — Basic ARIA present, keyboard nav incomplete |
| Visual Consistency | 5/10 | **Needs Work** — Multiple design systems, token mismatch |

---

## 1. Responsive Design Audit

### 1.1 raas-landing (Landing Page)

**Good Patterns:**

- `global.css` defines comprehensive responsive breakpoints:
  - `@media (max-width: 1024px)` — Tablet landscape
  - `@media (max-width: 968px)` — Tablet portrait
  - `@media (max-width: 768px)` — Mobile landscape
  - `@media (max-width: 640px)` — Mobile portrait
  - `@media (max-width: 480px)` — Small mobile
- Hero section uses `clamp()` for fluid typography
- Grid layouts adapt: `.grid-4` → `.grid-2` → `.grid-1`
- Testimonial carousel adjusts visible cards (3 → 2 → 1)

**Issues Found:**

| Priority | File | Line | Issue |
|----------|------|------|-------|
| **High** | `global.css` | 479-488 | Hero grid breakpoint at 968px leaves gap before 768px — recommend consolidate to 1024px |
| **Medium** | `global.css` | 1733-1737 | CTA buttons set `width: 100%` at 768px but parent `.hero-cta` doesn't have `flex-direction: column` |
| **Medium** | `index.astro` | 377-395 | Social proof counter uses fixed flex layout without proper mobile stacking at small screens |
| **Low** | `global.css` | 1759-1771 | `.fomo-text` hide at 480px uses `::after` for content — screen readers may announce incorrectly |

**Recommendations:**

```css
/* Consolidate hero breakpoints */
@media (max-width: 1024px) {
  .hero-container {
    grid-template-columns: 1fr;
    text-align: center;
  }
  .hero-content { max-width: 760px; margin: 0 auto; }
}

/* Fix CTA stacking on mobile */
@media (max-width: 768px) {
  .hero-cta {
    flex-direction: column;
    align-items: stretch;
  }
}

/* Make counter responsive */
@media (max-width: 640px) {
  .social-proof-counter {
    flex-direction: column;
    gap: 20px;
  }
  .counter-divider { display: none; }
}
```

---

### 1.2 raas-dashboard

**Good Patterns:**

- Basic mobile responsive rule at 768px
- Sidebar hides on mobile with `transform: translateX(-100%)`

**Critical Issues:**

| Priority | File | Line | Issue |
|----------|------|------|-------|
| **CRITICAL** | `dashboard.css` | 82-85 | **No hamburger menu implementation** — sidebar disappears completely on mobile, no way to access navigation |
| **High** | `dashboard.css` | 23-28 | Sidebar `position: fixed` with no z-index — may overlap with content |
| **High** | `dashboard.css` | 48 | `.card-grid` uses `auto-fit` without minmax consideration for very small screens (<320px) |
| **Medium** | `dashboard.css` | 26 | Sidebar fixed width `220px` — no responsive scaling for tablet |

**Recommendations:**

```css
/* Add mobile navigation toggle */
@media (max-width: 768px) {
  .sidebar {
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    z-index: 100;
  }
  .sidebar.open {
    transform: translateX(0);
  }
  .menu-toggle {
    display: block; /* Add hamburger button */
    position: fixed;
    top: 16px;
    left: 16px;
    z-index: 101;
  }
}
```

---

### 1.3 vibe-ui Components

**Good Patterns:**

- `GlassCard` uses responsive Tailwind classes
- `ThemeToggle` has fixed size but appropriate for its purpose

**Issues:**

| Priority | Component | Issue |
|----------|-----------|-------|
| **Medium** | `Skeleton` | No responsive props — width/height should accept responsive object |
| **Low** | `Modal` | `maxWidth` prop uses fixed breakpoints without responsive consideration |

---

## 2. Accessibility Audit

### 2.1 raas-landing

**Strengths:**

- Skip link implemented (`base-layout.astro` line 217-220)
- ARIA labels on navigation (`role="navigation"`, `aria-label`)
- Focus states defined in CSS (`.skip-link:focus`)
- `prefers-reduced-motion` support (lines 1162-1182, 1798-1829)
- `prefers-contrast: high` support (lines 1832-1847)
- Form inputs use proper `<label>` associations
- `aria-invalid`, `aria-describedby` on inputs
- JSON-LD structured data for SEO/accessibility

**Issues Found:**

| Priority | File | Line | Issue | Impact |
|----------|------|------|-------|--------|
| **CRITICAL** | `index.astro` | 600-611 | Carousel buttons missing `type="button"` — may submit forms unexpectedly | Form submission |
| **High** | `index.astro` | 352 | Demo button uses `href="#features"` without `id` matching — skip link broken | Keyboard users |
| **High** | `global.css` | 1122 | Focus outline only on `.carousel-btn:focus-visible` — should be `:focus-visible` with fallback | Keyboard nav |
| **Medium** | `index.astro` | 321-326 | FOMO badge uses `role="status"` without live region updates — screen readers won't announce changes | Screen readers |
| **Medium** | `base-layout.astro` | 252-256 | Language switcher lacks `aria-expanded` and keyboard navigation | Keyboard users |
| **Medium** | `global.css` | 218-242 | Skip link uses absolute positioning hack instead of modern `:not(:focus)` pattern | Maintainability |
| **Low** | `index.astro` | 402-404 | Logo items use emoji as icons without `aria-hidden="true"` | Screen readers |

**Recommendations:**

```tsx
// Fix carousel buttons
<button
  className="carousel-btn prev"
  id="carouselPrev"
  type="button"  // Add this
  aria-label="Previous testimonial"
>

// Fix FOMO badge with live region
<div
  className="fomo-badge-wrapper"
  role="status"
  aria-live="polite"  // Add this
  aria-atomic="true"  // Add this
>

// Fix language switcher
<div
  role="group"
  aria-label={isEn ? 'Language switcher' : 'Chuyển ngôn ngữ'}
>
  <button
    aria-current={!isEn ? 'true' : 'false'}
    aria-pressed={!isEn}  // Add this
  >
```

---

### 2.2 raas-dashboard

**Critical Accessibility Gaps:**

| Priority | File | Issue |
|----------|------|-------|
| **CRITICAL** | `dashboard.astro` | No skip link for main content |
| **CRITICAL** | `signup.astro` | Form inputs have `<label>` but `for` attribute may not match dynamic IDs |
| **High** | `dashboard.css` | No focus states defined for interactive elements (`:focus`, `:focus-visible`) |
| **High** | `dashboard.css` | Color contrast: `--text2: #94a3b8` on `--bg: #0f1117` = 7.2:1 (passes AA large, fails AA normal) |
| **Medium** | `dashboard.css` | No `prefers-reduced-motion` support for `.pulse` animation |
| **Low** | `dashboard.astro` | Status messages use `id="stat-messages"` without `aria-live` for dynamic updates |

**Color Contrast Analysis:**

| Element | Foreground | Background | Ratio | WCAG AA | WCAG AAA |
|---------|------------|------------|-------|---------|----------|
| Body text | `#e2e8f0` | `#0f1117` | 14.5:1 | **PASS** | **PASS** |
| Muted text | `#94a3b8` | `#0f1117` | 7.2:1 | **FAIL** (needs 4.5:1) | **FAIL** |
| Primary btn | `#ffffff` | `#6366f1` | 5.8:1 | **PASS** | **FAIL** |
| Sidebar nav | `#94a3b8` | `#1a1d27` | 6.1:1 | **PASS** | **FAIL** |

**Recommendations:**

```css
/* Add focus states */
.btn:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}

.nav-item:focus-visible {
  outline: 2px solid var(--accent2);
  outline-offset: -2px;
}

/* Fix contrast for muted text */
:root {
  --text2: #a3b0c2; /* Lighten from #94a3b8 */
}

/* Add reduced motion support */
@media (prefers-reduced-motion: reduce) {
  .status-dot { animation: none; opacity: 1; }
}

/* Add skip link */
<body>
  <a href="#main-content" class="skip-link">Chuyển đến nội dung chính</a>
  <!-- ... -->
</body>
```

---

### 2.3 vibe-ui Components

**Accessibility Assessment:**

| Component | Status | Notes |
|-----------|--------|-------|
| `Button` | **Good** | Uses native `<button>`, supports `aria-*` props |
| `Input` | **Good** | Proper `aria-invalid`, `aria-describedby`, label association |
| `Select` | **Good** | Similar to Input, proper ARIA attributes |
| `Modal` | **Good** | Focus trap implemented, keyboard escape, `aria-modal`, `role="dialog"` |
| `Skeleton` | **Good** | Uses `aria-hidden="true"` appropriately |
| `ThemeToggle` | **Good** | `role="switch"`, `aria-checked`, `aria-label` present |

**Minor Issues:**

| Priority | Component | Issue |
|----------|-----------|-------|
| **Low** | `Modal` | Close button text "Close modal" is hardcoded — should be i18n-aware |
| **Low** | `Button` | Loading text "Loading..." hardcoded |

---

### 2.4 ui Components (MD3 System)

**Assessment:**

| Component | Status | Notes |
|-----------|--------|-------|
| `Button` | **Good** | `focus-visible:outline-none focus-visible:ring-2` present |
| `Card` | **Good** | Semantic HTML structure |

---

## 3. Visual Consistency Audit

### 3.1 Design Token Analysis

**CRITICAL FINDING: Three separate design systems with conflicting tokens**

| System | Files | Primary Color | Surface | Border |
|--------|-------|---------------|---------|--------|
| **raas-landing MD** | `global.css` | `#00BCD4` (Cyan) | `#0a0f1a` | `rgba(255,255,255,0.08)` |
| **raas-dashboard** | `dashboard.css` | `#6366f1` (Indigo) | `#0f1117` | `#2e3248` |
| **vibe-ui Aura** | `design-tokens.ts` | `#0ea5e9` (Sky) | `#0f172a` | `#334155` |
| **ui MD3** | `button.tsx/card.tsx` | `primary` (undefined) | `surface` (undefined) | `border-outline` (undefined) |

**Inconsistencies:**

1. **raas-landing** uses Material Design color naming (`--md-primary`)
2. **raas-dashboard** uses generic naming (`--accent`, `--bg`)
3. **vibe-ui** uses Tailwind color names (`emerald`, `violet`, `pink`)
4. **ui** package uses MD3 semantic tokens that reference undefined CSS variables

### 3.2 Typography Inconsistencies

| Package | Font Stack | Weight Scale |
|---------|------------|--------------|
| raas-landing | `'Be Vietnam Pro', 'Inter'` | 300-800 |
| raas-dashboard | `'Be Vietnam Pro'` only | 300-700 |
| vibe-ui | System default (no font defined) | 400-700 |
| ui | System default | 400-600 |

**Issue:** `vibe-ui` and `ui` components will render with different fonts when used in apps.

### 3.3 Border Radius Inconsistency

| Package | Value |
|---------|-------|
| raas-landing | `16px` (large), `8px` (small) |
| raas-dashboard | `8px` uniform |
| vibe-ui | `24px` (3xl), `16px` (2xl) |
| ui | `12px` (xl), varies by component |

### 3.4 Component Variant Mismatch

**Button Variants:**

| raas-landing | raas-dashboard | vibe-ui | ui (MD3) |
|--------------|----------------|---------|----------|
| `.btn-primary` | `.btn-primary` | `primary` | `filled` |
| `.btn-outline` | `.btn-secondary` | `outline` | `outlined` |
| N/A | N/A | `ghost` | `text` |
| N/A | N/A | `danger` | N/A |
| N/A | N/A | N/A | `tonal` |
| N/A | N/A | N/A | `elevated` |

**Recommendation:** Standardize to MD3 naming across all packages.

---

## 4. Tailwind Configuration Status

**CRITICAL:** None of the audited packages have `tailwind.config.*` files!

| Package | Tailwind Installed? | Config Found? |
|---------|---------------------|---------------|
| raas-landing | No | N/A |
| raas-dashboard | No | N/A |
| vibe-ui | No (uses raw CSS strings) | N/A |
| ui | No (uses class-variance-authority) | N/A |

**Impact:**

- Cannot use Tailwind's responsive utilities consistently
- Theme customization not centralized
- Design tokens not accessible via `theme()` function
- PurgeCSS/optimal builds not configured

---

## 5. Priority Issue Summary

### Critical (Fix Immediately)

1. **raas-dashboard mobile navigation completely broken** — No way to access menu on mobile
2. **Three conflicting design systems** — Brand inconsistency
3. **No Tailwind configuration** — Cannot leverage utility classes
4. **Carousel buttons missing `type="button"`** — Form submission risk

### High (Fix This Sprint)

1. **raas-dashboard focus states missing** — Keyboard users cannot navigate
2. **Color contrast fails WCAG AA** in raas-dashboard muted text
3. **Hero breakpoint gaps** — Layout issues at tablet sizes
4. **MD3 semantic tokens undefined** — ui package components may not render correctly

### Medium (Fix Next Sprint)

1. **Skip link implementation inconsistent** — Some pages missing
2. **Live regions not implemented** for dynamic content
3. **Typography not standardized** — Font rendering differs across packages
4. **Border radius inconsistency** — Visual polish issues

### Low (Polish)

1. **Hardcoded strings** in components (i18n issue)
2. **Emoji icons without `aria-hidden`** — Minor screen reader noise
3. **fomo-badge `::after` content** — May cause duplicate announcements

---

## 6. Recommendations Roadmap

### Phase 1: Critical Fixes (Week 1)

1. **Fix mobile navigation in raas-dashboard**
   - Add hamburger menu button
   - Implement slide-out drawer
   - Add focus trap when open

2. **Unify design tokens**
   - Create `@mekong/design-tokens` package
   - Define CSS custom properties for colors, spacing, typography
   - Export as both CSS and TypeScript types

3. **Add Tailwind config to all packages**
   - Create shared `tailwind-preset.js`
   - Configure responsive breakpoints
   - Set up design token theme

4. **Fix accessibility blockers**
   - Add `type="button"` to all buttons
   - Add focus states to all interactive elements
   - Fix color contrast ratios

### Phase 2: Consistency (Week 2-3)

1. **Standardize component APIs**
   - Align button variants to MD3
   - Unify naming conventions
   - Create component migration guide

2. **Typography system**
   - Define font stack in design tokens
   - Create type scale (h1-h6, body, caption)
   - Apply consistently across packages

3. **Responsive patterns**
   - Document breakpoint system
   - Create responsive utility classes
   - Audit all layouts against new standards

### Phase 3: Polish (Week 4)

1. **Animation system**
   - Define motion tokens (duration, easing)
   - Add `prefers-reduced-motion` everywhere
   - Document animation guidelines

2. **i18n support**
   - Extract hardcoded strings
   - Integrate with `@mekong/i18n` package
   - Add Vietnamese/English translations

---

## 7. Files Requiring Updates

### raas-landing
- `/Users/macbook/mekong-cli/packages/raas-landing/src/styles/global.css`
- `/Users/macbook/mekong-cli/packages/raas-landing/src/layouts/base-layout.astro`
- `/Users/macbook/mekong-cli/packages/raas-landing/src/pages/index.astro`

### raas-dashboard
- `/Users/macbook/mekong-cli/packages/raas-dashboard/src/styles/dashboard.css`
- `/Users/macbook/mekong-cli/packages/raas-dashboard/src/layouts/dashboard-layout.astro`
- `/Users/macbook/mekong-cli/packages/raas-dashboard/src/pages/signup.astro`

### vibe-ui
- `/Users/macbook/mekong-cli/packages/vibe-ui/src/design-tokens.ts` (needs color system expansion)

### ui
- `/Users/macbook/mekong-cli/packages/ui/src/components/button.tsx` (MD3 token references)
- `/Users/macbook/mekong-cli/packages/ui/src/components/card.tsx`

---

## Unresolved Questions

1. **Design system decision:** Should we standardize on Material Design 3 (raas-landing/ui) or create a new unified system?
2. **Tailwind strategy:** Should all packages use Tailwind, or keep raas-landing as pure CSS?
3. **i18n scope:** Should vibe-ui components support i18n natively, or rely on app-level translation?
4. **Browser support:** What is the minimum browser support target? (affects CSS feature choices)
5. **Dark mode:** Should raas-dashboard support theme switching like vibe-ui components?

---

**Audit completed:** 2026-03-19
**Next review:** After Phase 1 fixes (Week 2)
