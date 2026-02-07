# METAMORPHOSIS PROTOCOL — AgencyOS Landing 100/100

## Phase 1: CENSUS
- Scan `src/` directory.
- Count occurrences of `console.log`, `TODO`, and `: any`.
- List all routes and components.
- Output findings to `plans/reports/AUDIT.md`.

## Phase 2: UX (Deep Space Design)
- Implement Deep Space color palette:
  - Background: `#030014`
  - Primary: `#00F5FF`
  - Accent: `#8B5CF6`
- Add `framer-motion` animations:
  - Staggered hero entry.
  - Scroll-reveal sections.
  - Hover scale on cards.
- Add Google Fonts: `Inter` and `Outfit`.
- Implement Glassmorphism for cards:
  - `backdrop-blur-xl`
  - `border-white/10`

## Phase 3: POLISH
- Implement Dark mode toggle with smooth transition.
- Add Animated stats counters.
- Add Typewriter effect on hero headline.

## Phase 4: i18n
- Verify 100% Vietnamese/English translations.
- Ensure zero fallbacks.
- Fix any missing keys.

## Phase 5: PERF
- Code-split all routes with dynamic imports.
- Optimize images to WebP via `next/image`.
- Target <150KB main bundle size.

## Phase 6: SECURITY
- Add Zod validation on all forms.
- Configure CSP headers in `next.config`.
- Implement XSS sanitization.

## Phase 7: MOBILE
- Ensure responsive mobile-first design.
- Implement Bottom nav for mobile.
- Ensure 44px touch targets.
- Verify breakpoints: 320px, 375px, 428px.

## Phase 8: TYPES
- Eliminate `: any` types.
- Run `tsc --noEmit` and ensure 0 errors.

## Phase 9: LCCO (Conversion)
- Add Sticky CTA bar for mobile.
- Add Trust badges.
- Implement Animated pricing section.
- Add Exit-intent lead capture.

## Phase 11: THEME
- Implement full Dark/Light mode support.
- Remove hardcoded grays.
- Use Semantic color tokens.

## FINAL
- Delete any duplicate route files.
- Verify `pnpm build` passes.
- Commit and push: `git add -A && git commit -m "feat: 100/100 WOW Metamorphosis" && git push`.
