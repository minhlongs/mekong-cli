---
phase: 01
title: "Absorb Quintessence from Sophia AI Factory"
priority: P1
status: pending
effort: 3h
---

# Phase 01: Absorb Quintessence

## Context Links

- Source: `apps/sophia-ai-factory/packages/`
- Target: `packages/core/`
- Hub Architecture: `/Users/macbookprom1/mekong-cli/CLAUDE.md`

## Overview

**Priority:** P1 (Foundation for all subsequent phases)
**Status:** Pending
**Effort:** 3h

Move vibe-* packages from Sophia AI Factory into mekong-cli Hub SDK core layer, establishing the foundation packages that all other layers depend on.

## Key Insights

- vibe, vibe-agents, shared form the **foundation trilogy**
- All other packages (integrations, business, ui, tooling) depend on core
- Must maintain import paths and type safety during migration
- Sophia AI Factory will reference these packages post-migration

## Requirements

### Functional Requirements
- Move `vibe`, `vibe-agents`, `shared` to `packages/core/`
- Preserve all type definitions and exports
- Update import paths in source packages
- Maintain backward compatibility for Sophia AI Factory

### Non-Functional Requirements
- Zero downtime for existing mekong-cli commands
- No breaking changes to public APIs
- Type checking passes after migration
- Git history preserved for packages

## Architecture

### Package Movement Map

```
SOURCE: apps/sophia-ai-factory/packages/
├── vibe/        → packages/core/vibe/
├── vibe-agents/ → packages/core/vibe-agents/
└── shared/      → packages/core/shared/

DEPENDENCIES (remain in sophia-ai-factory):
├── bridge/      → packages/integrations/ (Phase 02)
├── newsletter/  → packages/business/ (Phase 02)
└── vibe-ui/     → packages/ui/ (Phase 02)
```

### Import Path Updates

**Before:**
```typescript
import { Agent } from '@sophia/vibe-agents'
import { config } from '@sophia/shared'
```

**After:**
```typescript
import { Agent } from '@mekong/vibe-agents'
import { config } from '@mekong/shared'
```

## Related Code Files

### Files to Move
- `apps/sophia-ai-factory/packages/vibe/*`
- `apps/sophia-ai-factory/packages/vibe-agents/*`
- `apps/sophia-ai-factory/packages/shared/*`

### Files to Create
- `packages/core/vibe/package.json`
- `packages/core/vibe-agents/package.json`
- `packages/core/shared/package.json`
- `packages/core/README.md`

### Files to Modify
- `packages/core/vibe/tsconfig.json` (update paths)
- `packages/core/vibe-agents/tsconfig.json`
- `packages/core/shared/tsconfig.json`

## Implementation Steps

### Step 1: Pre-Migration Audit
```bash
# Document current state
ls -la apps/sophia-ai-factory/packages/vibe/
ls -la apps/sophia-ai-factory/packages/vibe-agents/
ls -la apps/sophia-ai-factory/packages/shared/

# Check for external dependencies
grep -r "import.*vibe" apps/sophia-ai-factory/
```

### Step 2: Create Core Layer Structure
```bash
mkdir -p packages/core/{vibe,vibe-agents,shared}
```

### Step 3: Move Packages with Git History
```bash
# Option A: Git mv (preserves history in same repo)
git mv apps/sophia-ai-factory/packages/vibe packages/core/vibe
git mv apps/sophia-ai-factory/packages/vibe-agents packages/core/vibe-agents
git mv apps/sophia-ai-factory/packages/shared packages/core/shared

# Option B: Copy (if need to keep both temporarily)
cp -r apps/sophia-ai-factory/packages/vibe packages/core/
cp -r apps/sophia-ai-factory/packages/vibe-agents packages/core/
cp -r apps/sophia-ai-factory/packages/shared packages/core/
```

### Step 4: Update Package Names
```bash
# Update package.json in each moved package
# vibe: @sophia/vibe → @mekong/vibe
# vibe-agents: @sophia/vibe-agents → @mekong/vibe-agents
# shared: @sophia/shared → @mekong/shared
```

### Step 5: Update Import Paths
```bash
# Find all imports in packages/core/
grep -r "@sophia/vibe" packages/core/
grep -r "@sophia/shared" packages/core/

# Replace with @mekong/* equivalents
# Use sed or manual updates
```

### Step 6: Update TypeScript Configs
```bash
# Update tsconfig.json path mappings
# packages/core/vibe/tsconfig.json
# packages/core/vibe-agents/tsconfig.json
# packages/core/shared/tsconfig.json
```

### Step 7: Create Core Layer README
```bash
cat > packages/core/README.md << 'EOF'
# Core Layer - Foundation SDK

Foundation packages that all other Hub layers depend on.

## Packages

- **vibe**: Core agent framework
- **vibe-agents**: Pre-built agent templates
- **shared**: Shared utilities and types

## Dependency Flow

```
ui/ ──┐
      ├──> integrations/ ──> core/ (foundation)
business/ ┘                    └── vibe, vibe-agents, shared
```
EOF
```

### Step 8: Verify Build
```bash
cd packages/core/vibe && npm install && npm run build
cd packages/core/vibe-agents && npm install && npm run build
cd packages/core/shared && npm install && npm run build
```

### Step 9: Update Workspace Root
```bash
# Update root package.json workspaces if using npm/yarn workspaces
# Add packages/core/* to workspace list
```

### Step 10: Commit Checkpoint
```bash
git add packages/core/
git commit -m "refactor: absorb quintessence - move vibe-* to packages/core/"
```

## Todo List

- [ ] Pre-migration audit complete
- [ ] Core layer directory structure created
- [ ] vibe package moved
- [ ] vibe-agents package moved
- [ ] shared package moved
- [ ] Package names updated (@mekong/*)
- [ ] Import paths updated in moved packages
- [ ] TypeScript configs updated
- [ ] Core layer README created
- [ ] All packages build successfully
- [ ] Workspace configuration updated
- [ ] Git checkpoint committed

## Success Criteria

### Definition of Done
- ✅ All three packages in `packages/core/`
- ✅ `npm run build` passes in each package
- ✅ `tsc --noEmit` passes (zero type errors)
- ✅ Import paths use `@mekong/*` namespace
- ✅ Git history preserved
- ✅ No references to old `@sophia/*` paths in core layer

### Validation Methods
```bash
# Type checking
cd packages/core/vibe && npx tsc --noEmit
cd packages/core/vibe-agents && npx tsc --noEmit
cd packages/core/shared && npx tsc --noEmit

# Build verification
npm run build --workspace=packages/core/vibe
npm run build --workspace=packages/core/vibe-agents
npm run build --workspace=packages/core/shared

# Import path check
grep -r "@sophia" packages/core/ || echo "✅ No old imports"

# Package name check
grep "\"name\":" packages/core/*/package.json | grep "@mekong"
```

## Risk Assessment

### Potential Issues
1. **Breaking Sophia AI Factory** - Moving packages may break existing imports
   - Mitigation: Keep symlinks temporarily, or update imports in parallel
2. **Type conflicts** - Duplicate type definitions during transition
   - Mitigation: Use strict module resolution, clear dist/ folders
3. **Build failures** - Missing dependencies after move
   - Mitigation: Run `npm install` after each package move

### Mitigation Strategies
- Test builds incrementally (per package)
- Maintain rollback checkpoint before starting
- Document all import path changes for future reference

## Security Considerations

- No auth/authorization changes in this phase
- Verify no secrets in package.json or config files
- Ensure .gitignore excludes node_modules, dist/

## Next Steps

**Dependencies:** None (foundation phase)

**Blocks:** Phase 02, 03, 04, 05 (all depend on core layer)

**Follow-up:** After completion, proceed to Phase 02 (Standardize Packages) to move remaining packages into proper Hub layers.
