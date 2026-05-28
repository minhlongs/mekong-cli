---
name: "source-command-ops-health"
description: "Operations health check — system status, capacity planning, bottleneck analysis. 3 steps, ~15 min."
---

# source-command-ops-health

Use this skill when the user asks to run the migrated source command `ops-health`.

## Command Template

# /ops:ops-health — Operations Health Check

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── status-check            → system-status.md
  ├── capacity-analysis       → capacity.md
  └── bottleneck-report       → health-report.md
```

## Output directory: reports/ops/ops-health/
