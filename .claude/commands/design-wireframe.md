---
description: "Wireframe generation — user flows, screen layouts, interaction specs. 3 steps, ~20 min."
argument-hint: [feature or screen name]
allowed-tools: Read, Write, Bash, Task
---

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
