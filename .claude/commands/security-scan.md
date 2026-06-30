---
description: "Security scan — vulnerability assessment, dependency audit, configuration review. 3 steps, ~15 min."
argument-hint: [codebase or system]
allowed-tools: Read, Write, Bash, Task
---

# /security:security-scan — Security Scan

**Super command** — chains steps via DAG pipeline.

## Pipeline

```
SEQUENTIAL:
  ├── vulnerability-scan      → vulnerabilities.md
  ├── dependency-audit        → dependencies.md
  └── config-review           → security-report.md
```

## Output directory: reports/security/security-scan/
