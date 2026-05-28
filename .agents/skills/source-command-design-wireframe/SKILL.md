---
name: "source-command-design-wireframe"
description: "Wireframe generation — user flows, screen layouts, interaction specs. 3 steps, ~20 min."
---

# source-command-design-wireframe

Use this skill when the user asks to run the migrated source command `design-wireframe`.

## Command Template

# /design:design-wireframe — Wireframe Generator

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── user-flow               → user-flow.md
  ├── screen-layout           → wireframes.md
  └── interaction-spec        → interactions.md
```

## Output directory: reports/design/design-wireframe/
