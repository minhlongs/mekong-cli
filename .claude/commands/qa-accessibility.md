---
description: "WCAG AA accessibility audit"
argument-hint: [goal]
allowed-tools: Read, Write, Bash, Task
---

# /qa:accessibility — Accessibility Audit

**IC super command** — WCAG AA accessibility audit

## Pipeline

```
PARALLEL: axe-scan + lighthouse-audit
    |
SEQUENTIAL: remediation-report
    |
OUTPUT: reports/qa/accessibility/
```

## Trigger

Runs recipe `recipes/qa/accessibility.json` through DAGScheduler.

## Execution

1. Load recipe DAG definition
2. Execute DAG groups in dependency order
3. Compile results into summary report

## Usage

```
/qa:accessibility [goal]
```

## Estimated: 2 credits, 8 minutes

## Goal context
<goal>$ARGUMENTS</goal>

Pass this goal to every sub-command as context for their analysis.
