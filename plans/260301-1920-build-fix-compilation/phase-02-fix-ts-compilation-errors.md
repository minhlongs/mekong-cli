---
phase: 2
title: "Fix TS compilation errors"
status: pending
priority: P1
---

# Phase 02: Fix TS Compilation Errors

## Context
- [Plan](plan.md)
- [Phase 01](phase-01-run-build-capture-errors.md) — error inventory
- Recently modified: algo-trader (BacktestEngine, BotEngine, CLI commands, plugins), sophia-proposal (layout)

## Overview
Fix all TypeScript compilation errors found in Phase 01. Priority: algo-trader (most changes).

## Likely Error Categories
1. **Missing imports** — new modules not importing dependencies
2. **Type mismatches** — refactored interfaces not updated across files
3. **Missing type definitions** — new files need proper type exports
4. **Config issues** — tsconfig include/exclude paths

## Implementation Steps
1. Fix errors in order: most depended-on files first
2. For each error: read file → understand context → fix type/import
3. After fixing each app, run app-specific build to verify
4. Add missing build script if any app lacks one

## Todo
- [ ] Fix algo-trader TS errors (highest priority — most changes)
- [ ] Fix sophia-proposal errors if any
- [ ] Fix other app errors if any
- [ ] Add build scripts where missing

## Success Criteria
- 0 TS compilation errors across all apps
- No `any` types introduced as shortcuts
