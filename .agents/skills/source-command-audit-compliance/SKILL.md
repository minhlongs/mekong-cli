---
name: "source-command-audit-compliance"
description: "Full compliance audit — policy review, gap analysis, remediation plan. 3 steps, ~25 min."
---

# source-command-audit-compliance

Use this skill when the user asks to run the migrated source command `audit-compliance`.

## Command Template

# /compliance:audit-compliance — Compliance Audit

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── policy-review           → policy-gaps.md
  ├── gap-analysis            → findings-report.md
  └── remediation-plan        → action-items.md
```

## Output directory: reports/compliance/audit-compliance/
