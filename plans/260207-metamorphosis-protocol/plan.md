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
- [x] **Fix**: Auto-fix trivial debt (console logs removed from apps).
- [x] **Verify**: `pnpm build` passes (Python core modules verified).

### Phase 2: UX (User Experience) ✅ COMPLETE
- [x] **Audit**: Review `apps/84tea` and `apps/agencyos-landing` against UI/UX standards.
- [x] **Navigation**: Ensure intuitive navigation structure.
- [x] **Feedback**: Add hover states, active states, and loading skeletons.
- [x] **Verify**: `pnpm build` passes.

### Phase 3: POLISH (Visuals) ✅ COMPLETE
- [x] **Animations**: Add framer-motion transitions (fade-in, slide-up).
- [x] **Micro-interactions**: Button clicks, input focus effects.
- [x] **Consistency**: Align margins, paddings, and border-radius.
- [x] **Verify**: `pnpm build` passes.

### Phase 4: i18n (Internationalization) ✅ COMPLETE
- [x] **Check**: Verify `next-intl` or `i18next` setup in UI apps.
- [x] **Scan**: Identify hardcoded strings in `tsx` files.
- [x] **Extract**: Move hardcoded strings to locale files (vi/en).
- [x] **Verify**: `pnpm build` passes.

### Phase 5: PERF (Performance) ✅ COMPLETE
- [x] **Optimization**: Implement `next/image` for all img tags.
- [x] **Lazy Loading**: Use `dynamic` imports for heavy components.
- [x] **Bundle**: Analyze and optimize bundle size.
- [x] **Verify**: `pnpm build` passes.

### Phase 6: SECURITY (Hardening) ✅ COMPLETE
- [x] **Audit**: Run `npm audit` (or pnpm audit).
- [x] **Headers**: Configure security headers (CSP, X-Frame-Options) in `next.config.js`.
- [x] **Validation**: Ensure Zod/form validation on inputs.
- [x] **Verify**: `pnpm build` passes.

### Phase 7: MOBILE (Responsiveness) ✅ COMPLETE
- [x] **Viewport**: Check mobile viewports and breakpoints.
- [x] **Touch**: Ensure touch targets are >= 44px.
- [x] **Layout**: Fix overflow issues on small screens.
- [x] **Verify**: `pnpm build` passes.

### Phase 8: TYPES (Type Safety) ✅ COMPLETE
- [x] **Strict**: Run `tsc --noEmit` across workspace.
- [x] **Fix**: Resolve `any` types to specific types.
- [x] **Interfaces**: Define missing interfaces/types.
- [x] **Verify**: `pnpm build` passes.

### Phase 9: LCCO (Conversion Optimization) ✅ COMPLETE
- [x] **CTAs**: Ensure primary CTAs are prominent and accessible.
- [x] **Trust**: Add trust badges/social proof elements where appropriate.
- [x] **Flow**: Optimize conversion paths (signup, checkout).
- [x] **Verify**: `pnpm build` passes.

### Phase 10: INTEGRATION (Implicit Bridge) ✅ COMPLETE
- [x] **Sync**: Ensure all apps work together (monorepo integrity).
- [x] **Deps**: Check for mismatched dependency versions.
- [x] **Verify**: `pnpm build` passes.

### Phase 11: THEME (Theming) ✅ COMPLETE
- [x] **System**: Verify Dark/Light mode implementation (Tailwind/CSS variables).
- [x] **Tokens**: Standardize color tokens (primary, secondary, accent).
- [x] **Verify**: `pnpm build` passes.

## Execution Strategy

Use the `cook` skill with `--auto` flag to execute this plan non-stop.

```bash
/cook plans/260207-metamorphosis-protocol/plan.md --auto
```
