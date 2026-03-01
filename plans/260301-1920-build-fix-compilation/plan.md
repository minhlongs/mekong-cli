---
title: "Build Fix — mekong-cli Compilation"
description: "Run npm run build, fix all TS errors, verify exit 0"
status: pending
priority: P1
effort: 1h
branch: master
tags: [build, typescript, turbo, compilation]
created: 2026-03-01
---

# Build Fix — mekong-cli Compilation

## Phases

| # | Phase | Status | File |
|---|-------|--------|------|
| 1 | Run build and capture errors | pending | [phase-01](phase-01-run-build-capture-errors.md) |
| 2 | Fix TS compilation errors | pending | [phase-02](phase-02-fix-ts-compilation-errors.md) |
| 3 | Verify clean build | pending | [phase-03](phase-03-verify-clean-build.md) |

## Architecture
- Monorepo: pnpm workspaces + Turbo (26 apps)
- Build command: `pnpm run build` → `npx turbo run build`
- Each app builds independently, turbo manages dependency graph
- Root tsconfig: packages only. Apps have own tsconfigs extending `tsconfig.base.json`

## Key Risks
- 26 apps = many failure points, focus on recently modified (algo-trader, sophia-proposal)
- New untracked algo-trader modules may have missing imports/types
- Some apps may lack build script (turbo skips gracefully)
