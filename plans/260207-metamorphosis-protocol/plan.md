# Metamorphosis Protocol - Mekong CLI Monorepo

> **Status**: Planning
> **Mode**: Non-stop Auto (`--auto`)
> **Goal**: 100/100 Lột Xác (Transformation)

## Protocol Overview

This plan executes the 11-phase Metamorphosis Protocol across the `mekong-cli` monorepo, focusing on key applications (`apps/84tea`, `apps/agencyos-landing`) and shared packages.

**Constraint**: `pnpm build` MUST pass after each phase.
**Constraint**: Commit & Push after each phase.
**Constraint**: NON-STOP AUTO MODE.

## Phases

### Phase 1: CENSUS (Audit) ✅ COMPLETE
- [x] **Scan**: Run codebase census (lines of code, file counts).
- [x] **Debt Scan**: Count `TODO`, `FIXME`, `console.log`, `any` types.
- [x] **Report**: Generate/Update `AUDIT.md` in root and per-app.
- [ ] **Fix**: Auto-fix trivial debt (unused imports, console logs).
- [x] **Verify**: `pnpm build` passes (Python core modules verified).

### Phase 2: UX (User Experience)
- [ ] **Audit**: Review `apps/84tea` and `apps/agencyos-landing` against UI/UX standards.
- [ ] **Navigation**: Ensure intuitive navigation structure.
- [ ] **Feedback**: Add hover states, active states, and loading skeletons.
- [ ] **Verify**: `pnpm build` passes.

### Phase 3: POLISH (Visuals)
- [ ] **Animations**: Add framer-motion transitions (fade-in, slide-up).
- [ ] **Micro-interactions**: Button clicks, input focus effects.
- [ ] **Consistency**: Align margins, paddings, and border-radius.
- [ ] **Verify**: `pnpm build` passes.

### Phase 4: i18n (Internationalization)
- [ ] **Check**: Verify `next-intl` or `i18next` setup in UI apps.
- [ ] **Scan**: Identify hardcoded strings in `tsx` files.
- [ ] **Extract**: Move hardcoded strings to locale files (vi/en).
- [ ] **Verify**: `pnpm build` passes.

### Phase 5: PERF (Performance)
- [ ] **Optimization**: Implement `next/image` for all img tags.
- [ ] **Lazy Loading**: Use `dynamic` imports for heavy components.
- [ ] **Bundle**: Analyze and optimize bundle size.
- [ ] **Verify**: `pnpm build` passes.

### Phase 6: SECURITY (Hardening)
- [ ] **Audit**: Run `npm audit` (or pnpm audit).
- [ ] **Headers**: Configure security headers (CSP, X-Frame-Options) in `next.config.js`.
- [ ] **Validation**: Ensure Zod/form validation on inputs.
- [ ] **Verify**: `pnpm build` passes.

### Phase 7: MOBILE (Responsiveness)
- [ ] **Viewport**: Check mobile viewports and breakpoints.
- [ ] **Touch**: Ensure touch targets are >= 44px.
- [ ] **Layout**: Fix overflow issues on small screens.
- [ ] **Verify**: `pnpm build` passes.

### Phase 8: TYPES (Type Safety)
- [ ] **Strict**: Run `tsc --noEmit` across workspace.
- [ ] **Fix**: Resolve `any` types to specific types.
- [ ] **Interfaces**: Define missing interfaces/types.
- [ ] **Verify**: `pnpm build` passes.

### Phase 9: LCCO (Conversion Optimization)
- [ ] **CTAs**: Ensure primary CTAs are prominent and accessible.
- [ ] **Trust**: Add trust badges/social proof elements where appropriate.
- [ ] **Flow**: Optimize conversion paths (signup, checkout).
- [ ] **Verify**: `pnpm build` passes.

### Phase 10: INTEGRATION (Implicit Bridge)
- [ ] **Sync**: Ensure all apps work together (monorepo integrity).
- [ ] **Deps**: Check for mismatched dependency versions.
- [ ] **Verify**: `pnpm build` passes.

### Phase 11: THEME (Theming)
- [ ] **System**: Verify Dark/Light mode implementation (Tailwind/CSS variables).
- [ ] **Tokens**: Standardize color tokens (primary, secondary, accent).
- [ ] **Verify**: `pnpm build` passes.

## Execution Strategy

Use the `cook` skill with `--auto` flag to execute this plan non-stop.

```bash
/cook plans/260207-metamorphosis-protocol/plan.md --auto
```
