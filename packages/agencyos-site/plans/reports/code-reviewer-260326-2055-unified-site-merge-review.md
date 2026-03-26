# Code Review: Unified Astro Site Merge

**Reviewer:** code-reviewer | **Date:** 2026-03-26
**Scope:** packages/agencyos-site/ (raas-landing + mekong-docs + raas-dashboard merged)
**Files:** ~80 source files | **Build:** PASSES (62 pages, 0 errors)

---

## Overall Assessment

Build passes and layout routing is correct. However, there are **2 critical** and **3 high-priority** issues that will cause runtime failures or broken functionality in production.

---

## CRITICAL Issues

### C1. dashboard.css is a broken 404 in production

**Impact:** All dashboard pages render WITHOUT styles (broken UX).

`dashboard-layout.astro`, `signup.astro`, `onboard.astro`, `onboarding.astro` all use:
```html
<link rel="stylesheet" href="/styles/dashboard.css" />
```
This is a raw HTML `<link>` tag pointing to `/styles/dashboard.css`. But `dashboard.css` lives in `src/styles/`, NOT `public/styles/`. Astro does NOT copy `src/styles/` to `dist/styles/`. The build output confirms `dist/styles/` does not exist -- this link will **404 at runtime**.

**Fix options:**
1. Move `src/styles/dashboard.css` to `public/styles/dashboard.css` (quick fix, loses Astro processing)
2. Replace `<link>` with Astro import: `import '../../styles/dashboard.css';` in frontmatter (recommended, enables bundling)

**Affected files:**
- `src/layouts/dashboard-layout.astro:39`
- `src/pages/dashboard/signup.astro:9`
- `src/pages/dashboard/onboard.astro:9`
- `src/pages/dashboard/onboarding.astro:11`

### C2. docs-layout.astro hardcodes old subdomain URL

**Impact:** All `/docs/*` pages have wrong canonical URLs, breaking SEO and OG tags.

```typescript
// src/layouts/docs-layout.astro:17
const siteUrl = 'https://mekong-docs.pages.dev';  // OLD subdomain
```

Canonical URLs, OG URLs, and Twitter card URLs for all 30+ docs pages point to the old Cloudflare Pages domain instead of `https://agencyos.network`.

**Fix:** Change to `const siteUrl = 'https://agencyos.network';`

---

## HIGH Priority

### H1. Missing pages: /privacy, /terms, /forgot-password

Links in `base-layout.astro` footer (lines 398-399) link to `/privacy` and `/terms`. Login page links to `/forgot-password`. None of these pages exist. Users clicking these links get 404.

**Affected links:**
- `base-layout.astro:398` -> `/privacy`
- `base-layout.astro:399` -> `/terms`
- `dashboard/login.astro:45` -> `/forgot-password`

### H2. Pricing inconsistency between docs/pricing and main pricing

`docs/pricing.astro` shows different prices than `pricing.astro` and `en/pricing.astro`:

| Tier | docs/pricing | pricing.astro |
|------|-------------|---------------|
| Starter | $29 | $49 |
| Pro | $99 | $149 |
| Agency/Growth | $199 | $299 |

`docs/pricing.astro` also links to `/#pricing` (old anchor-based checkout) instead of NOWPayments links. This creates customer confusion about actual pricing.

### H3. Inconsistent API base URLs across dashboard pages

Two different API endpoints used inconsistently:
- `https://api.agencyos.network` -- used by most dashboard pages (upgrade, missions, contacts, content, signup, dashboard, reports, settings, integrations, messages)
- `https://mekong-engine.agencyos.network` -- used by login, billing, usage

This could cause auth/CORS issues if they resolve to different backends. Should be unified or made configurable via env var.

---

## MEDIUM Priority

### M1. base-layout.astro preloads source CSS path

```html
<!-- Line 220 -->
<link rel="preload" as="style" href="/src/styles/global.css" />
```

`/src/styles/global.css` does not exist in the build output. This preload does nothing (silent 404). The actual CSS is bundled by Astro into `/_astro/*.css`. Remove this line.

### M2. docs-layout footer links to old root pricing anchor

```html
<!-- src/layouts/docs-layout.astro:78 -->
<a href="/#pricing">Buy</a>
```
Also in `docs/pricing.astro:157`. The root landing page (`/`) may not have a `#pricing` anchor anymore since pricing is now at `/pricing`. Should link to `/pricing` instead.

### M3. NOWPayments links use CSS class `link-polar`

`billing.astro` uses class `link-polar` for NOWPayments checkout links. Misleading class name since Polar.sh is listed as primary payment provider in rules. No functional impact but creates confusion about which payment provider is actually used.

### M4. Duplicate onboarding pages

Both `dashboard/onboard.astro` and `dashboard/onboarding.astro` exist with similar purpose. Should consolidate to one.

### M5. auth-layout.astro has no CSS import for dashboard variables

`auth-layout.astro` defines its own CSS variables inline (lines 13-26) that duplicate `dashboard.css` variables. If dashboard.css changes, auth pages will be out of sync.

---

## LOW Priority

### L1. base-layout.astro is 622 lines

Exceeds 200-line file size rule. Nav, footer, carousel logic, and JSON-LD schemas should be extracted into components.

### L2. Crisp chat placeholder ID

Both `base-layout.astro:618` and `dashboard-layout.astro:157` use `CRISP_WEBSITE_ID="openclaw-placeholder"`. Live chat won't work until real ID is set.

### L3. Command mega-menu links are dead (`href="#"`)

Most 5-Layer command items in `base-layout.astro` and `dashboard-layout.astro` sidebar link to `#`. Non-functional navigation.

---

## Positive Observations

1. **Layout routing is correct** -- all pages use appropriate layout (base/docs/dashboard/auth)
2. **Import paths are correct** -- all relative imports match directory depth
3. **NOWPayments checkout IDs are consistent** -- same IDs across pricing.astro, en/pricing.astro, upgrade.astro, billing.astro (Starter: 6245075877, Pro: 5438578229, Growth: 5821366482)
4. **i18n configuration is correct** -- vi default, en prefix, proper hreflang tags
5. **No old subdomain URLs** in page content (except docs-layout siteUrl)
6. **astro.config.mjs is clean** -- correct site URL, i18n, sitemap integration
7. **package.json dependencies look correct** -- astro, supabase, material web, chart.js
8. **JSON-LD structured data** is well-implemented for SEO

---

## Recommended Actions (Priority Order)

1. **[CRITICAL]** Fix dashboard.css loading -- convert `<link>` to Astro import or move file to `public/`
2. **[CRITICAL]** Fix `docs-layout.astro` siteUrl from `mekong-docs.pages.dev` to `agencyos.network`
3. **[HIGH]** Create stub pages for `/privacy`, `/terms`, `/forgot-password`
4. **[HIGH]** Align `docs/pricing.astro` prices with main pricing or remove/redirect
5. **[HIGH]** Unify API base URL to single env var
6. **[MEDIUM]** Remove broken CSS preload in base-layout line 220
7. **[MEDIUM]** Fix `/#pricing` links to `/pricing`

---

## Unresolved Questions

1. Are `api.agencyos.network` and `mekong-engine.agencyos.network` the same backend or different services?
2. Is `docs/pricing.astro` (CLI pricing) intentionally different from root `pricing.astro` (RaaS pricing)?
3. Should Crisp chat use a real website ID or is it intentionally disabled?
