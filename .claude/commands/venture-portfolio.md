---
description: "Portfolio review — company updates, performance tracking, follow-on decisions. 3 steps, ~20 min."
argument-hint: [portfolio or fund name]
allowed-tools: Read, Write, Bash, Task
---

# /venture:venture-portfolio — Venture Portfolio Review

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── company-updates         → updates.md
  ├── performance-tracking    → performance.md
  └── follow-on-analysis      → portfolio-review.md
```

## Output directory: reports/venture/venture-portfolio/
