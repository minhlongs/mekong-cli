---
title: "Fix Well Build Error - UserRank Import Issue"
description: "Plan to resolve TypeScript error TS1361 with UserRank enum import in Well project"
status: pending
priority: P1
effort: 1h
branch: master
tags: [typescript, build-error, well-project]
created: 2026-02-28
---

# Plan Fix Well Build Error: UserRank Import Issue

## Error Summary
**Build Error:** TypeScript compilation failing with error TS1361
```
'UserRank' cannot be used as a value because it was imported using 'import type'.
```

**Location:** `apps/well/src/agents/custom/TheBeeAgent.ts` at lines 104, 141, 145, 149

## Root Cause Analysis

### ✅ Current Code State:
1. **TheBeeAgent.ts**: Uses `UserRank` as enum values (line 104, 141, 145, 149)
2. **Import Statement**: `import { UserRank } from '@/types';` (correct enum import)
3. **Type Definition**: `UserRank` is defined as `export enum UserRank` in `apps/well/src/types.ts`

### ❌ Problem:
- Import statement is correct, but TypeScript complains about using enum as value
- The issue suggests there might be conflicting import declarations

## Verification Commands

1. **Verify UserRank definition:**
```bash
grep -n "UserRank" /Users/macbookprom1/mekong-cli/apps/well/src/types.ts
```

2. **Check for any other import patterns:**
```bash
grep -r "UserRank" /Users/macbookprom1/mekong-cli/apps/well/src/
```

3. **Verify path resolution:**
```bash
ls -la /Users/macbookprom1/mekong-cli/apps/well/src/types/
```

## Potential Issues Identified

### 🎯 Primary Suspect: Path Resolution
- `@/types` may resolve differently than expected
- Need to check if `@/types` resolves to `src/types.ts` correctly

### 🎯 Secondary Suspect: Duplicate Import Issues
- Possibly multiple import declarations for same symbol
- Need to check for type-only imports elsewhere

## Implementation Plan

### Phase 1: Research & Diagnosis
1. **Analyze TypeScript path resolution** - Check `tsconfig.json` paths
2. **Review all imports** - Search for any `import type` declarations
3. **Check for conflicts** - Look for multiple UserRank definitions

### Phase 2: Solution Options
Based on findings, choose one approach:

#### Option A: Direct Import (Recommended)
```typescript
import { UserRank } from '../types';  // Relative path
```

#### Option B: Import from types.ts directly
```typescript
import { UserRank } from '@/types'; // If path mapping is correct
```

#### Option C: Import from index barrel file
```typescript
import { UserRank } from '@/types/index'; // Explicit barrel
```

### Phase 3: Verification
1. **Build test** - Run `npm run build` in apps/well directory
2. **Type check** - Ensure no remaining TypeScript errors
3. **Functionality test** - Verify UserRank enum usage works correctly

## Risk Assessment
- **Low Risk**: Simple import fix, no breaking changes
- **Quick Fix**: Estimated 15-30 minutes implementation
- **Easy Rollback**: If issues, revert import changes

## Success Criteria
- ✅ Build completes without TypeScript errors
- ✅ UserRank enum values accessible and usable
- ✅ No breaking changes to existing functionality
- ✅ Code compiles with `tsc && vite build`

## Files to Modify
- `/Users/macbookprom1/mekong-cli/apps/well/src/agents/custom/TheBeeAgent.ts` (line 3)

## Next Steps
1. **Developer**: Execute Phase 1 research to confirm path resolution
2. **Developer**: Apply chosen solution approach
3. **Tester**: Run build and verify success
4. **Code Reviewer**: Review changes for code quality

## Unresolved Questions
- Is `@/types` path mapping correctly configured?
- Are there any other files importing UserRank incorrectly?
- Does the `src/types/` directory contain conflicting definitions?