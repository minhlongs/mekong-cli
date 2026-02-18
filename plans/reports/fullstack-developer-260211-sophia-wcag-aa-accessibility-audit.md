# Sophia AI Factory - WCAG 2.1 AA Accessibility Audit

**Date:** 2026-02-11
**Agent:** fullstack-developer
**Scope:** All 130 TSX/JSX components in `apps/sophia-ai-factory/apps/sophia-ai-factory/src/`

---

## Summary

| Category | Found | Fixed | Manual Review |
|----------|-------|-------|---------------|
| Clickable divs (non-semantic) | 3 | 3 | 0 |
| Missing form labels (htmlFor/id) | 9 | 9 | 0 |
| Icon-only buttons missing aria-label | 4 | 4 | 0 |
| Toggle switches missing role="switch" | 1 | 1 | 0 |
| Missing ARIA reference IDs | 1 | 1 | 0 |
| Media missing aria-label | 1 | 1 | 0 |
| Overlay div missing presentation role | 1 | 1 | 0 |
| **Total** | **20** | **20** | **0** |

## Build Status

- Compilation: PASS (all 11 fixed files compile clean)
- TypeScript: FAIL (pre-existing type error in `generate-campaign.ts` -- unrelated to a11y fixes; prior session removed `@ts-expect-error` directive)
- A11y fixes: zero regressions introduced

## Files Modified (11)

### 1. `src/components/settings/sections/appearance-section.tsx`
- Converted 3 clickable `<div>` theme selectors to `<button>` elements
- Added `role="radio"`, `aria-checked`, `type="button"` to each
- Added `role="radiogroup" aria-label="Theme preference"` to container
- Added `aria-hidden="true"` to decorative color circles

### 2. `src/app/[locale]/(admin)/admin/settings/page.tsx`
- Replaced clickable `<Card onClick>` with semantic `<a href>` wrapper
- Added `htmlFor="admin-username"` / `id="admin-username"` to label/input pair
- Added `htmlFor="mock-tier"` / `id="mock-tier"` to label/select pair

### 3. `src/app/components/affiliate/program-grid.tsx`
- Added `aria-label="Search affiliate programs"` to search input
- Added `aria-label="Sort programs"` to sort select
- Added `aria-hidden="true"` to decorative Search and SlidersHorizontal icons

### 4. `src/app/[locale]/(admin)/admin/affiliates/page.tsx`
- Added `aria-label="Search affiliate programs"` to search input
- Added `aria-hidden="true"` to decorative Search icon
- Added dynamic `aria-label` to icon-only ExternalLink buttons

### 5. `src/app/[locale]/(admin)/admin/settings/integrations/page.tsx`
- Added sr-only `<label>` with `htmlFor`/`id` for ClickBank API Key input
- Added sr-only `<label>` with `htmlFor`/`id` for ShareASale API Token input
- Added sr-only `<label>` with `htmlFor`/`id` for ShareASale API Secret input

### 6. `src/components/settings/sections/api-keys-section.tsx`
- Added dynamic `aria-label` to OpenAI key visibility toggle button
- Added dynamic `aria-label` to Anthropic key visibility toggle button
- Added dynamic `aria-label` to ElevenLabs key visibility toggle button

### 7. `src/app/components/sections/faq.tsx`
- Added `id={`faq-question-${index}`}` to complete aria-controls/aria-labelledby chain

### 8. `src/app/[locale]/(admin)/admin/users/admin-users-client.tsx`
- Added `htmlFor="invite-email"` / `id="invite-email"` to email label/input
- Added `htmlFor="invite-tier"` / `id="invite-tier"` to tier label/select

### 9. `src/app/[locale]/(admin)/admin/features/page.tsx`
- Added `role="switch"`, `aria-checked={isEnabled}`, `aria-label` to toggle buttons

### 10. `src/app/[locale]/guide/layout.tsx`
- Added `role="presentation"` and `aria-hidden="true"` to mobile overlay backdrop

### 11. `src/components/video-preview.tsx`
- Added `aria-label="AI-generated video preview"` to `<video>` element

## Already Compliant (no fixes needed)

Strong existing a11y foundation across 20+ files:
- `layout.tsx` -- `lang={locale}`, skip-to-content link
- `navbar.tsx` -- `aria-label` on nav, mobile toggle
- `login/page.tsx` -- proper form labels, `role="alert"`
- `filter-panel.tsx` -- aria-label on search, label/id on all inputs
- `product-card.tsx` -- Image has `alt={product.title}`
- `roi-calculator.tsx` -- proper labels, `aria-live`, progressbar attrs
- `hero.tsx` -- proper h1, semantic structure
- `affiliate-discovery.tsx` -- `aria-pressed` on tier/filter buttons
- `filter-sidebar.tsx` -- all buttons are semantic `<button>`
- `dashboard/layout.tsx` -- nav aria-label, proper sidebar
- `campaign-export-control.tsx` -- labels, `role="dialog"`
- `create-project-form.tsx` -- labels, `role="alert"`
- `campaign-form.tsx` -- proper labels
- `template-selector.tsx` -- uses semantic `<button>`
- `social-proof.tsx` -- stars with `role="img"`, `aria-label`
- `workflow.tsx` -- semantic structure
- `youtube-embed.tsx` -- has `title` attribute
- `floating-help-button.tsx` -- `aria-label`, `role="menu"`
- `dashboard-stats.tsx` -- decorative icons only
- `video-preview.tsx` -- progressbar with full ARIA attrs (pre-existing)

## Designer-Input Needed

None. All issues were code-level ARIA/semantic HTML fixes requiring no visual changes.

## Recommendations (future)

1. Add `aria-live="polite"` to admin feedback messages (users page, integrations page)
2. Consider focus management when FAQ accordion opens (optional enhancement)
3. Add keyboard trap prevention to mobile sidebar overlay (close on Escape key)
