---
name: "source-command-hr-review"
description: "Performance review — self-assessment, peer feedback, manager evaluation, development plan. 4 steps, ~25 min."
---

# source-command-hr-review

Use this skill when the user asks to run the migrated source command `hr-review`.

## Command Template

# /hr:hr-review — Performance Review

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── self-assessment         → self-review.md
  ├── peer-feedback           → peer-input.md
  ├── manager-evaluation      → evaluation.md
  └── development-plan        → growth-plan.md
```

## Output directory: reports/hr/hr-review/
