---
name: "source-command-venture-portfolio"
description: "Portfolio review — company updates, performance tracking, follow-on decisions. 3 steps, ~20 min."
---

# source-command-venture-portfolio

Use this skill when the user asks to run the migrated source command `venture-portfolio`.

## Command Template

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
