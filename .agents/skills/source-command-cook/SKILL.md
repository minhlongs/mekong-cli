---
name: "source-command-cook"
description: "Recipe executor — run a multi-step DAG recipe from recipes/ directory. 1 step, variable time."
---

# source-command-cook

Use this skill when the user asks to run the migrated source command `cook`.

## Command Template

# /core:cook — Recipe Runner

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── recipe-load             → parsed recipe
  └── step-execution          → recipe output
```

## Output directory: reports/core/cook/
