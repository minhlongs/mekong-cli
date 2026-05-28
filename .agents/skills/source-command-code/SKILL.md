---
name: "source-command-code"
description: "Code generation from spec — architecture, implementation, tests. 3 steps, ~20 min."
---

# source-command-code

Use this skill when the user asks to run the migrated source command `code`.

## Command Template

# /engineering:code — Code Generator

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── architecture-plan       → design.md
  ├── implementation          → src/
  └── test-generation         → tests/
```

## Output directory: reports/engineering/code/
