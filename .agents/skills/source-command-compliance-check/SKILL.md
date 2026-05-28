---
name: "source-command-compliance-check"
description: "Compliance check against framework — gap identification, risk scoring, action items. 2 steps, ~15 min."
---

# source-command-compliance-check

Use this skill when the user asks to run the migrated source command `compliance-check`.

## Command Template

# /compliance:compliance-check — Compliance Check

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── framework-scan          → gaps.md
  └── action-plan             → compliance-actions.md
```

## Output directory: reports/compliance/compliance-check/
