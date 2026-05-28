---
name: "source-command-security-scan"
description: "Security scan — vulnerability assessment, dependency audit, configuration review. 3 steps, ~15 min."
---

# source-command-security-scan

Use this skill when the user asks to run the migrated source command `security-scan`.

## Command Template

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
