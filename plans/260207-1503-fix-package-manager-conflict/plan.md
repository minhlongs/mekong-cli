---
title: "Fix Package Manager Conflict (npm → pnpm)"
description: "Standardize on pnpm, verify build, fix TypeScript errors"
status: pending
priority: P1
effort: 1h
branch: master
tags: [tooling, build, pnpm]
created: 2026-02-07
---

# Fix Package Manager Conflict

## Overview

Remove npm lockfile, standardize on pnpm across monorepo, verify build integrity.

## Phases

1. **Phase 01: Standardize pnpm** - Remove package-lock.json, configure workspace, install deps
2. **Phase 02: Verify & Fix** - Run build, fix TypeScript errors
3. **Phase 03: Commit** - Git operations

## Success Criteria

- ✅ No package-lock.json in repo
- ✅ pnpm-lock.yaml present
- ✅ All packages build without errors
- ✅ Changes committed to git

## Dependencies

- pnpm installed globally
- Node.js 18+

## Risks

- Build may reveal hidden dependency issues
- TypeScript errors may require code fixes
