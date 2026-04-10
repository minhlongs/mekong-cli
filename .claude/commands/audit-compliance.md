---
description: "Full compliance audit — policy review, gap analysis, remediation plan. 3 steps, ~25 min."
argument-hint: [framework: SOC2 / ISO27001 / GDPR / HIPAA]
allowed-tools: Read, Write, Bash, Task
---

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
