---
name: "source-command-design-system"
description: "Design system scaffold — tokens, components, patterns, documentation. 4 steps, ~30 min."
---

# source-command-design-system

Use this skill when the user asks to run the migrated source command `design-system`.

## Command Template

# /design:design-system — Design System

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── design-tokens           → tokens.json
  ├── component-inventory     → components.md
  ├── pattern-library         → patterns.md
  └── documentation           → design-system.md
```

## Output directory: reports/design/design-system/
