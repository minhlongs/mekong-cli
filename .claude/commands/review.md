---
description: "Code review — architecture check, security scan, performance analysis, improvement suggestions. 3 steps, ~15 min."
argument-hint: [PR number or file path]
allowed-tools: Read, Write, Bash, Task
---

# /engineering:review — Code Review

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── architecture-review     → architecture.md
  ├── security-check          → security.md
  └── improvements            → review-feedback.md
```

## Output directory: reports/engineering/review/
