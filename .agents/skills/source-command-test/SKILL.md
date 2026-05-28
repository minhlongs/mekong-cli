---
name: "source-command-test"
description: "Test generation — unit tests, integration tests, edge cases, coverage report. 3 steps, ~15 min."
---

# source-command-test

Use this skill when the user asks to run the migrated source command `test`.

## Command Template

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
