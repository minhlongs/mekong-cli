---
phase: 1
title: "Run build and capture errors"
status: pending
priority: P1
---

# Phase 01: Run Build and Capture Errors

## Context
- [Plan](plan.md)
- Build: `pnpm run build` → turbo orchestrates 26 apps

## Overview
Run full monorepo build, capture all errors, categorize by app and type.

## Implementation Steps
1. Run `pnpm run build` — capture full output
2. Parse errors: group by app (algo-trader, sophia-proposal, etc.)
3. Categorize: TS type errors, missing imports, missing modules, config issues
4. If build script missing in any app → add minimal build script
5. Document all errors for Phase 02

## Todo
- [ ] Run pnpm run build
- [ ] Capture error output
- [ ] Categorize errors by app and type
- [ ] Check if any app missing build script

## Success Criteria
- Complete error inventory documented
- Each error categorized with file:line reference
