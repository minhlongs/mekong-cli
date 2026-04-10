---
description: "Test generation — unit tests, integration tests, edge cases, coverage report. 3 steps, ~15 min."
argument-hint: [module or function to test]
allowed-tools: Read, Write, Bash, Task
---

# /engineering:test — Test Generator

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── test-plan               → test-plan.md
  ├── test-generation         → tests/
  └── coverage-report         → coverage.md
```

## Output directory: reports/engineering/test/
