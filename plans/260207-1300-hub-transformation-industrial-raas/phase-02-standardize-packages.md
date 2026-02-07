---
phase: 02
title: "Standardize Hub SDK Package Structure"
priority: P1
status: pending
effort: 2h
---

# Phase 02: Standardize Hub SDK Package Structure

## Context Links

- Source: `apps/sophia-ai-factory/packages/`, `packages/newsletter/`
- Hub Architecture: `/Users/macbookprom1/mekong-cli/CLAUDE.md`
- Dependencies: Phase 01 (core layer must exist)

## Overview

**Priority:** P1
**Status:** Pending
**Effort:** 2h

Reorganize remaining packages into proper Hub SDK layers (integrations, business, ui, tooling), ensuring strict layer dependency flow and removing architectural debt.

## Key Insights

- `newsletter` package incorrectly placed at root `packages/` - should be in `business/`
- Remaining sophia packages need layer classification
- Hub enforces dependency flow: `ui → integrations → core`
- Each layer has distinct purpose and dependency constraints

## Requirements

### Functional Requirements
- Move `packages/newsletter/` to `packages/business/newsletter/`
- Move `apps/sophia-ai-factory/packages/bridge/` to `packages/integrations/bridge/`
- Move `apps/sophia-ai-factory/packages/vibe-ui/` to `packages/ui/vibe-ui/`
- Create i18n package in `packages/ui/i18n/`
- Establish layer READMEs documenting purpose and dependencies

### Non-Functional Requirements
- Maintain import path consistency
- Zero breaking changes to existing code
- Layer dependency rules enforced in tsconfig
- Documentation reflects new structure

## Architecture

### Hub SDK Layer Structure

```
packages/
├── core/                    # Foundation (Phase 01)
│   ├── vibe/
│   ├── vibe-agents/
│   └── shared/
├── integrations/            # External connectors (THIS PHASE)
│   ├── bridge/              ← from sophia-ai-factory
│   └── crm/                 (future)
├── business/                # Revenue logic (THIS PHASE)
│   ├── newsletter/          ← from packages/newsletter
│   ├── money/               (future: Polar integration)
│   ├── ops/                 (future: provisioning)
│   └── marketing/           (future: campaigns)
├── ui/                      # Interface components (THIS PHASE)
│   ├── vibe-ui/             ← from sophia-ai-factory
│   └── i18n/                ← new package
└── tooling/                 # Developer utilities (future)
    ├── dev/
    └── analytics/
```

### Dependency Flow

```
┌─────────┐
│   UI    │ (vibe-ui, i18n)
└────┬────┘
     │
┌────▼────────┐
│ Integrations│ (bridge, CRM)
└────┬────────┘
     │
┌────▼────┐
│  Core   │ (vibe, vibe-agents, shared)
└─────────┘

Business layer can import from core + integrations
```

## Related Code Files

### Files to Move
- `packages/newsletter/*` → `packages/business/newsletter/`
- `apps/sophia-ai-factory/packages/bridge/*` → `packages/integrations/bridge/`
- `apps/sophia-ai-factory/packages/vibe-ui/*` → `packages/ui/vibe-ui/`

### Files to Create
- `packages/integrations/README.md`
- `packages/business/README.md`
- `packages/ui/README.md`
- `packages/ui/i18n/package.json` (scaffolding for future i18n)
- `packages/tooling/README.md` (placeholder)

### Files to Modify
- Root `package.json` (workspace paths)
- Moved packages' `package.json` (update names if needed)
- Moved packages' `tsconfig.json` (path mappings)

## Implementation Steps

### Step 1: Create Layer Directories
```bash
mkdir -p packages/{integrations,business,ui,tooling}
```

### Step 2: Move Newsletter to Business Layer
```bash
# Move with git history
git mv packages/newsletter packages/business/newsletter

# Update package.json name
# @mekong/newsletter → @mekong/business-newsletter (optional, or keep short)
```

### Step 3: Move Bridge to Integrations Layer
```bash
git mv apps/sophia-ai-factory/packages/bridge packages/integrations/bridge

# Update package.json
# @sophia/bridge → @mekong/bridge
```

### Step 4: Move Vibe-UI to UI Layer
```bash
git mv apps/sophia-ai-factory/packages/vibe-ui packages/ui/vibe-ui

# Update package.json
# @sophia/vibe-ui → @mekong/vibe-ui
```

### Step 5: Create i18n Package Scaffold
```bash
mkdir -p packages/ui/i18n

cat > packages/ui/i18n/package.json << 'EOF'
{
  "name": "@mekong/i18n",
  "version": "0.1.0",
  "description": "Internationalization utilities for mekong-cli",
  "main": "dist/index.js",
  "types": "dist/index.d.ts",
  "scripts": {
    "build": "tsc",
    "dev": "tsc --watch"
  },
  "dependencies": {
    "@mekong/shared": "workspace:*"
  }
}
EOF
```

### Step 6: Create Layer READMEs
```bash
# Integrations Layer
cat > packages/integrations/README.md << 'EOF'
# Integrations Layer - External Connectors

Packages that connect mekong-cli to external services.

## Packages
- **bridge**: AntiBridge SDK connector
- **crm**: (future) CRM system integrations

## Dependencies
- Can import from: **core** layer only
EOF

# Business Layer
cat > packages/business/README.md << 'EOF'
# Business Layer - Revenue Logic

Packages handling revenue operations, marketing, and business workflows.

## Packages
- **newsletter**: Newsletter management
- **money**: (future) Polar.sh payment integration
- **ops**: (future) Provisioning and operations
- **marketing**: (future) Campaign management

## Dependencies
- Can import from: **core**, **integrations**
EOF

# UI Layer
cat > packages/ui/README.md << 'EOF'
# UI Layer - Interface Components

Packages providing user interface components and utilities.

## Packages
- **vibe-ui**: Component library
- **i18n**: Internationalization utilities

## Dependencies
- Can import from: **core**, **integrations**, **business**
EOF

# Tooling Layer
cat > packages/tooling/README.md << 'EOF'
# Tooling Layer - Developer Utilities

Packages for development, debugging, and analytics.

## Packages
- **dev**: (future) Development utilities
- **analytics**: (future) Usage analytics

## Dependencies
- Can import from: any layer (tooling is top-level)
EOF
```

### Step 7: Update Import Paths in Moved Packages
```bash
# Check for old @sophia imports
grep -r "@sophia" packages/integrations/bridge/
grep -r "@sophia" packages/ui/vibe-ui/

# Update to @mekong equivalents
# Manual or scripted replacement
```

### Step 8: Update Workspace Configuration
```bash
# Root package.json workspaces
# Add:
# "packages/integrations/*"
# "packages/business/*"
# "packages/ui/*"
# "packages/tooling/*"
```

### Step 9: Verify Builds
```bash
# Business layer
cd packages/business/newsletter && npm install && npm run build

# Integrations layer
cd packages/integrations/bridge && npm install && npm run build

# UI layer
cd packages/ui/vibe-ui && npm install && npm run build
```

### Step 10: Update Documentation
```bash
# Update root README.md with new Hub structure
# Update CLAUDE.md with correct package paths
```

### Step 11: Commit Checkpoint
```bash
git add packages/
git commit -m "refactor: standardize Hub SDK layers - organize packages by layer"
```

## Todo List

- [ ] Layer directories created
- [ ] newsletter moved to business/
- [ ] bridge moved to integrations/
- [ ] vibe-ui moved to ui/
- [ ] i18n package scaffolded
- [ ] All layer READMEs created
- [ ] Import paths updated
- [ ] Workspace configuration updated
- [ ] All moved packages build successfully
- [ ] Root documentation updated
- [ ] Git checkpoint committed

## Success Criteria

### Definition of Done
- ✅ All packages in correct layer directories
- ✅ Layer READMEs document purpose and dependencies
- ✅ `npm run build` passes in all moved packages
- ✅ No cross-layer dependency violations
- ✅ Workspace recognizes all package locations
- ✅ Import paths use `@mekong/*` namespace

### Validation Methods
```bash
# Verify structure
tree -L 3 packages/

# Build all layers
npm run build --workspaces

# Type checking
npx tsc --noEmit --project packages/business/newsletter/tsconfig.json
npx tsc --noEmit --project packages/integrations/bridge/tsconfig.json
npx tsc --noEmit --project packages/ui/vibe-ui/tsconfig.json

# Check for old imports
grep -r "@sophia" packages/{business,integrations,ui}/ || echo "✅ No old imports"

# Verify layer isolation (no ui importing from business, etc.)
grep -r "@mekong/business" packages/ui/ && echo "❌ Layer violation" || echo "✅ Clean"
grep -r "@mekong/ui" packages/integrations/ && echo "❌ Layer violation" || echo "✅ Clean"
```

## Risk Assessment

### Potential Issues
1. **Sophia AI Factory breakage** - Moving packages breaks sophia's imports
   - Mitigation: Update sophia imports in parallel, or symlink temporarily
2. **Circular dependencies** - Packages inadvertently import from higher layers
   - Mitigation: Use TypeScript project references to enforce layer boundaries
3. **Build order issues** - Workspace builds in wrong order
   - Mitigation: Explicit build scripts respecting layer dependencies

### Mitigation Strategies
- Test each layer's build independently
- Document layer dependency rules in CLAUDE.md
- Use linting rules to prevent cross-layer violations

## Security Considerations

- Verify no API keys or secrets in moved package configs
- Ensure .gitignore covers node_modules, dist/, .env files
- Review newsletter package for any credential handling

## Next Steps

**Dependencies:** Phase 01 (core layer)

**Blocks:** Phase 03 (engine needs organized packages)

**Follow-up:** After completion, proceed to Phase 03 (Wire Engine) to implement LLM-powered planner and multi-mode executor.
