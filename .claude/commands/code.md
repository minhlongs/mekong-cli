---
description: "Code generation from spec — architecture, implementation, tests. 3 steps, ~20 min."
argument-hint: [feature spec or task description]
allowed-tools: Read, Write, Bash, Task
---

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
