# Phase 01: Standardize on pnpm

## Context

- Current: Mixed npm/pnpm state (package-lock.json exists)
- Target: Pure pnpm monorepo with workspace configuration

## Overview

**Priority**: P1
**Status**: Pending
**Effort**: 20min

Remove npm artifacts, configure pnpm workspace, fresh install.

## Requirements

### Functional
- Remove package-lock.json
- Ensure pnpm-workspace.yaml exists
- Install all dependencies via pnpm
- Generate pnpm-lock.yaml

### Non-Functional
- No breaking changes to dependency versions
- Preserve existing workspace structure

## Related Code Files

### To Modify
- `package.json` (verify workspace config)
- `pnpm-workspace.yaml` (create if missing)

### To Delete
- `package-lock.json`
- `node_modules/` (clean install)

## Implementation Steps

1. **Remove npm lockfile**
   ```bash
   rm -f package-lock.json
   ```

2. **Verify pnpm-workspace.yaml**
   ```bash
   cat pnpm-workspace.yaml
   # Should contain:
   # packages:
   #   - 'packages/*'
   #   - 'apps/*'
   #   - etc.
   ```

3. **Clean node_modules (optional but recommended)**
   ```bash
   rm -rf node_modules
   find packages -name node_modules -type d -exec rm -rf {} +
   find apps -name node_modules -type d -exec rm -rf {} +
   ```

4. **Install with pnpm**
   ```bash
   pnpm install
   ```

5. **Verify lockfile created**
   ```bash
   ls -lh pnpm-lock.yaml
   ```

## Todo List

- [ ] Remove package-lock.json
- [ ] Verify pnpm-workspace.yaml exists
- [ ] Clean node_modules (optional)
- [ ] Run pnpm install
- [ ] Confirm pnpm-lock.yaml generated

## Success Criteria

- No package-lock.json in root
- pnpm-lock.yaml present
- All dependencies installed without errors
- No warnings about package manager conflicts

## Next Steps

Proceed to Phase 02: Verify & Fix
