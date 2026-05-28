---
name: "source-command-compliance-monitor"
description: "Continuous compliance monitoring — drift detection, policy violations, alert rules. 2 steps, ~10 min."
---

# source-command-compliance-monitor

Use this skill when the user asks to run the migrated source command `compliance-monitor`.

## Command Template

# /compliance:compliance-monitor — Compliance Monitor

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── drift-detection         → drift-report.md
  └── alert-configuration     → monitor-rules.md
```

## Output directory: reports/compliance/compliance-monitor/
