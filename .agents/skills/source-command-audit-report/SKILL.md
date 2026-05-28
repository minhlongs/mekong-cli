---
name: "source-command-audit-report"
description: "Generate audit report from findings — executive summary, detailed findings, risk ratings. 2 steps, ~12 min."
---

# source-command-audit-report

Use this skill when the user asks to run the migrated source command `audit-report`.

## Command Template

# /compliance:audit-report — Audit Report Generator

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── findings-analysis       → risk-matrix.md
  └── report-generation       → audit-report.md
```

## Output directory: reports/compliance/audit-report/
