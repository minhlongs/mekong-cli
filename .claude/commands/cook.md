---
description: "Recipe executor — run a multi-step DAG recipe from recipes/ directory. 1 step, variable time."
argument-hint: [recipe name from recipes/]
allowed-tools: Read, Write, Bash, Task
---

# /core:cook — Recipe Runner

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── recipe-load             → parsed recipe
  └── step-execution          → recipe output
```

## Output directory: reports/core/cook/
