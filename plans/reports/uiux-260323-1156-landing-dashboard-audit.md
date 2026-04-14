# UI/UX Audit Report: OpenClaw Landing + Dashboard

**Date:** 2026-03-23
**Auditor:** ui-ux-designer
**Sites:** agencyos.network (Landing) | app.agencyos.network (Dashboard)

---

## Scoring Summary

| Category | Landing | Dashboard | Notes |
|---|---|---|---|
| 1. CTA Prominence | 9/10 | 7/10 | Landing excellent; Dashboard upgrade CTA could be stronger |
| 2. Pricing Clarity | 8/10 | 6/10 | Landing clear 4-tier; Dashboard has 5 tiers (inconsistent w/ landing) |
| 3. Mobile Responsive | 5/10 | 7/10 | **Landing nav has NO hamburger menu** - critical gap |
| 4. Color Consistency | 7/10 | 7/10 | Landing uses cyan/purple; Dashboard uses indigo - mismatched brand |
| 5. Loading States | 3/10 | 5/10 | Landing has none; Dashboard has basic "Dang tai..." text |
| 6. Error States | 2/10 | 5/10 | Landing has no error handling; Dashboard has basic catch |
| 7. Navigation | 6/10 | 7/10 | Landing nav items overflow on mobile; Dashboard sidebar OK |
| 8. Trust Signals | 8/10 | 3/10 | Landing has 6 trust badges + testimonials; Dashboard has none |
| 9. Conversion Funnel | 6/10 | 5/10 | Signup page is separate (signup.astro) and doesn't use AuthLayout |
| 10. Accessibility | 7/10 | 4/10 | Landing has ARIA/skip-link; Dashboard lacks ARIA labels |
| **Overall** | **6.1/10** | **5.6/10** | |

---

## Detailed Findings

### 1. CTA Prominence

**Landing (9/10):**
- Primary CTA "Dung thu mien phi 14 ngay" above fold with pulse animation (`btn-pulse`, `btn-glow`)
- Secondary CTA "Xem demo 30s" with play icon
- Sticky nav has "Dung mien phi" / "Start Free" button always visible
- Bottom CTA banner "Start for free" reinforces action

**Dashboard (7/10):**
- Upgrade CTA exists in MCU banner but only shows when credits < 20%
- No persistent upgrade nudge for free-tier users
- Missing "Start first mission" CTA for new users (empty state)

### 2. Pricing Clarity

**Landing (8/10):**
- 4 tiers: Free / Starter ($49) / Pro ($149) / Enterprise ($499)
- Pro marked "Pho bien nhat" with gradient border animation
- Comparison table on /pricing page is thorough
- Monthly/Annual toggle exists but is **visual-only** (no actual toggle logic)

**Dashboard (6/10) - INCONSISTENCY:**
- Billing page has **5 tiers**: Free / Starter / Pro / **Growth** / Enterprise
- Growth and Pro both show 1,490,000d ($149) - **same price, confusing**
- Pro on billing shows 500 MCU vs 1,000 MCU on landing - **data mismatch**
- VND pricing (490,000d) added but conversion rate unclear

### 3. Mobile Responsive

**Landing (5/10) - CRITICAL:**
- Grid system properly collapses (grid-4 -> grid-2 -> grid-1)
- Hero section has mobile breakpoints for CTA buttons
- **NO hamburger menu** - nav items (Features, Commands, Pricing, FAQ, VI|EN, CTA) all display inline
- At 768px nav items will overflow horizontally
- Commands mega-dropdown (600px min-width) unusable on mobile
- Step connector dots don't hide properly on mobile

**Dashboard (7/10):**
- Hamburger toggle present with overlay
- Sidebar slides in from left
- Charts collapse to single column
- Stats grid goes single column
- Escape key closes sidebar (good)

### 4. Color Consistency

**Landing palette:**
- Primary: `#00BCD4` (cyan/teal)
- Secondary: `#7C4DFF` (deep purple)
- Surface: `#0a0f1a` (near-black blue)
- Gradients: cyan -> purple throughout

**Dashboard palette:**
- Primary accent: `#6366f1` (indigo) - **different from landing**
- Secondary: `#818cf8` (lighter indigo)
- Surface: `#0f1117` (different dark shade)
- Success/Warn/Danger colors match

**Issue:** Brand disconnect between landing and dashboard. User transitions from cyan/purple to indigo/purple. Logo color on login (`#6366f1`) differs from landing (`gradient cyan-purple`).

### 5. Loading States

**Landing (3/10):**
- No skeleton screens
- No loading indicators for any content
- Scroll animations use IntersectionObserver (good for perceived performance)
- Counter animation exists but no fallback if JS fails

**Dashboard (5/10):**
- Text-based "Dang tai hoat dong..." in activity feed
- Charts show empty canvas during load
- MCU balance shows "---" as placeholder
- No skeleton loaders or shimmer effects
- No loading state on chart period change

### 6. Error States

**Landing (2/10):**
- No error boundaries
- No fallback UI if API/CDN fails
- No offline indicator
- Fonts load via external CDN with no fallback strategy beyond system fonts

**Dashboard (5/10):**
- Dashboard catch block shows "Khong the tai du lieu" error message
- Login page shows error message styled with red border
- Billing page has silent catch (console.error only)
- No retry button on errors
- No global error boundary

### 7. Navigation

**Landing (6/10):**
- Sticky nav with glass effect (good)
- Language switcher VI|EN prominent
- 5-layer Commands mega-menu is creative but:
  - All links go to `#` (non-functional)
  - 600px min-width breaks mobile
  - No keyboard navigation within dropdown
- Footer links include Dashboard link (good cross-linking)
- Smooth scroll to anchor sections works

**Dashboard (7/10):**
- Sidebar with 5-layer hierarchy (Founder/Business/Product/Engineering/Ops)
- Accordion nav groups with expand/collapse
- Active page indicator (left border highlight)
- Most nav items link to `#` (not yet implemented)
- Logout redirects to /signup instead of /login
- No breadcrumbs within pages

### 8. Trust Signals

**Landing (8/10):**
- 6 trust badges (SSL, Cloudflare, No CC, 2-min setup, Top 1 AI VN 2025, 4.9/5 rating)
- 5 testimonials with names, roles, avatars, verified badges, result metrics
- Customer logos section (emoji-based, not real logos)
- FOMO badge "47 doanh nghiep dang ky hom nay" (hardcoded, not dynamic)
- Platform stats (319 commands, 540 skills, etc.)
- "500+ businesses" claim repeated multiple times
- JSON-LD structured data with aggregateRating

**Dashboard (3/10):**
- No trust signals post-login
- No "verified" or "secure" indicators
- No data security reassurance
- No success stories or tips for new users

### 9. Conversion Funnel

**Landing -> Signup -> Dashboard -> First Mission -> Upgrade:**

1. Landing -> Signup: **Good.** Multiple CTAs point to `app.agencyos.network/signup`
2. Signup page: **Issues.**
   - Uses raw HTML, NOT AuthLayout (inconsistent with login page styling)
   - Only requires email (no password!) - creates account with just email
   - API key login on same page is confusing for new users
   - No plan selection passed through (URL params exist but not used)
3. Signup -> Dashboard: Redirects through `/onboard` (good onboarding intent)
4. Dashboard: No guided first-use experience, no empty states with CTAs
5. Dashboard -> Upgrade: `/billing` and `/upgrade` both exist (redundant?)

**Critical funnel issue:** Two different signup flows exist:
- `signup.astro` (raw HTML, email-only, API-based)
- `login.astro` uses Supabase auth with email+password
- User confusion: which flow is canonical?

### 10. Accessibility

**Landing (7/10):**
- Skip-to-content link with focus styles
- `aria-label` on all major sections and interactive elements
- `aria-hidden="true"` on decorative elements (orbs, dots)
- `role="navigation"`, `role="menubar"`, `role="listitem"` used
- `lang` attribute set correctly per page (vi/en)
- Focus-visible styles on nav links and buttons
- **Missing:** Focus trap for mega-dropdown, screen reader announcements for carousel
- `prefers-reduced-motion` support not found in landing CSS (only in dashboard CSS)

**Dashboard (4/10):**
- Only 7 total ARIA attributes across entire dashboard
- No `aria-label` on stat cards, charts, or interactive elements
- Menu toggle has `aria-label` and `aria-expanded` (good)
- `prefers-reduced-motion` in dashboard.css (good)
- No skip-to-content link
- Charts (canvas) have no accessible alternatives
- Form inputs lack `aria-describedby` for error states
- Color-only status indicators (progress bar colors)

---

## Top 5 Critical Issues

1. **Landing: No mobile hamburger menu** - Nav items overflow on mobile, mega-dropdown breaks
2. **Pricing inconsistency** - Landing shows 4 tiers, billing shows 5 tiers with conflicting MCU counts
3. **Dual signup flows** - signup.astro (email-only) vs login.astro (Supabase auth) creates user confusion
4. **Brand color disconnect** - Landing (#00BCD4 cyan) vs Dashboard (#6366f1 indigo) different primary colors
5. **Dashboard accessibility** - Only 7 ARIA attributes total, charts inaccessible, no skip-link

## Top 5 Quick Wins (High Impact, Low Effort)

### 1. Add Mobile Hamburger Menu to Landing Nav
**Impact:** Fixes completely broken mobile navigation
**Effort:** ~30 min
**File:** `packages/raas-landing/src/layouts/base-layout.astro`

```html
<!-- Add before the nav links div -->
<button class="mobile-menu-toggle" id="mobileMenuToggle"
  aria-label="Toggle menu" aria-expanded="false">
  <svg width="24" height="24" viewBox="0 0 24 24" fill="none"
    stroke="currentColor" stroke-width="2">
    <line x1="3" y1="6" x2="21" y2="6"/>
    <line x1="3" y1="12" x2="21" y2="12"/>
    <line x1="3" y1="18" x2="21" y2="18"/>
  </svg>
</button>
```

```css
/* Add to global.css */
.mobile-menu-toggle { display: none; background: none; border: 1px solid var(--md-outline); color: var(--md-on-surface); padding: 8px; border-radius: 8px; cursor: pointer; }

@media (max-width: 768px) {
  .mobile-menu-toggle { display: flex; }
  .nav-links { display: none; position: fixed; top: 64px; left: 0; right: 0; background: var(--md-surface); border-bottom: 1px solid var(--md-outline); flex-direction: column; padding: 16px 24px; gap: 12px; }
  .nav-links.open { display: flex; }
  .dropdown-container .dropdown-menu { position: static; min-width: unset; grid-template-columns: repeat(2, 1fr); }
}
```

### 2. Unify Primary Color Across Landing + Dashboard
**Impact:** Brand consistency across entire product
**Effort:** ~15 min
**File:** `packages/raas-dashboard/src/styles/dashboard.css`

```css
/* Change dashboard accent to match landing */
:root {
  --accent: #00BCD4;   /* was #6366f1 */
  --accent2: #7C4DFF;  /* was #818cf8 */
}
```

Also update `auth-layout.astro` and `login.astro` hardcoded colors.

### 3. Add prefers-reduced-motion to Landing CSS
**Impact:** Accessibility compliance, respects user preferences
**Effort:** ~5 min
**File:** `packages/raas-landing/src/styles/global.css`

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
  html { scroll-behavior: auto; }
  .btn-pulse::after { animation: none; }
  body::before, body::after { animation: none; }
}
```

### 4. Fix Pricing Toggle (Currently Non-Functional)
**Impact:** Annual toggle shows "-20%" but does nothing - misleading
**Effort:** ~20 min
**File:** `packages/raas-landing/src/pages/en/index.astro` (and vi version)

Either: (a) Make toggle functional with JS to show annual prices, or (b) Remove toggle entirely to avoid misleading users. Option (b) is quickest:

```astro
<!-- Remove or comment out the toggle div in both index.astro files -->
<!-- <div style="display:flex;justify-content:center;margin-bottom:48px;">
  <div class="pricing-toggle">...</div>
</div> -->
```

### 5. Add ARIA Labels to Dashboard Stat Cards
**Impact:** Screen reader users can understand dashboard metrics
**Effort:** ~10 min
**File:** `packages/raas-dashboard/src/pages/dashboard.astro`

```html
<div class="stat-card" role="status" aria-label="Tin nhan hom nay">
  ...
</div>
<div class="stat-card" role="status" aria-label="Tong khach hang">
  ...
</div>
```

Also add `aria-label` to charts:
```html
<canvas id="usage-chart" role="img" aria-label="Bieu do su dung MCU 30 ngay"></canvas>
```

---

## Unresolved Questions

1. Is the "Growth" tier on billing page intentional or leftover? Landing only shows 4 tiers.
2. Is Supabase auth the canonical flow? signup.astro uses direct API while login.astro uses Supabase.
3. Are the testimonials real? Names look Vietnamese but avatars are emojis, customer logos are emojis.
4. "47 doanh nghiep dang ky hom nay" - is this hardcoded or should it be dynamic?
5. Should annual pricing toggle be functional? If so, what are annual prices?
6. The mega-dropdown command links all go to `#` - are these planned pages or should they be removed?
