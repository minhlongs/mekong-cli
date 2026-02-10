# Packages — 第三篇 謀攻 (Mou Gong) — Shared Arsenal

> **Inherits**: `../CLAUDE.md` (Root Constitution)
> **Domain**: Shared SDK packages — the foundational weapons used by all apps
> **Binh Phap**: 謀攻 — Attack by stratagem: shared code multiplies force across all projects

## Package Registry

| Package | Path | Purpose |
|---------|------|---------|
| `ui` | `packages/ui/` | Shared UI component library |
| `build-optimizer` | `packages/build-optimizer/` | Build pipeline optimization |

## Hub Architecture (Planned)

```
packages/
├── core/               # Foundation SDKs
│   ├── vibe/           # Core framework
│   ├── vibe-agents/    # Agent framework
│   └── shared/         # Shared utilities
├── integrations/       # External connectors
│   ├── bridge/         # Integration bridge
│   └── crm/            # CRM connector
├── tooling/            # Developer utilities
│   ├── dev/            # Dev tools
│   └── analytics/      # Analytics SDK
├── business/           # Revenue logic
│   ├── money/          # Payment processing
│   ├── ops/            # Operations
│   └── marketing/      # Marketing tools
└── ui/                 # Interface components
    ├── vibe-ui/        # UI component library
    └── i18n/           # Internationalization
```

## Dependency Flow

```
ui/ ──────────────┐
                  ├──> integrations/ ──> core/ (foundation)
business/ ────────┘                      └── vibe, vibe-agents, shared
```

## Rules

- Packages MUST NOT have circular dependencies
- Each package MUST have its own `package.json`
- Shared types go in `packages/core/shared/`
- UI components must be framework-agnostic where possible
- All packages must build independently: `pnpm --filter <pkg> build`
- Follow semantic versioning for all packages
- TypeScript strict mode mandatory
