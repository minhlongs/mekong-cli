# Research: Build Setup Analysis

## Monorepo Build Architecture
- **PM**: pnpm 9.15.0 with workspaces
- **Build**: `npx turbo run build` (turbo.json configured)
- **Turbo config**: build outputs `dist/**`, `.next/**`, depends on `^build`

## TypeScript Config
- Root `tsconfig.json`: packages only, `noEmit: true`, excludes apps
- `tsconfig.base.json`: shared compiler options, strict mode, ES2022 target
- Each app has own tsconfig extending base

## Apps with Build Scripts (26 apps total)
- algo-trader, sophia-proposal, openclaw-worker, 84tea, apex-os, anima119, etc.
- Each app defines own `build` script in package.json
- Turbo orchestrates build order via `^build` dependency graph

## Potential Issues
- 26 apps = many possible failure points
- Recently modified: algo-trader (major refactor), sophia-proposal (layout), openclaw-worker (runtime)
- New untracked TS files in algo-trader may have import/type issues
- Not all apps may have `build` script → turbo skips them gracefully
