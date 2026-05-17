---
description: Run tests and validate code quality. 1 command, ~10-20 min.
argument-hint: [test scope or file]
allowed-tools: Read, Bash, Task
---

# /test — Test Runner

**Engineering** — single command.

## Estimated: 3 credits, 10-20 minutes

## Workflow

```
[Load Tests] → [Run Suite] → [Analyze Coverage] → [Report Failures]
```

## Execution

1. Run test suite (vitest/jest/pytest)
2. Check coverage (target: >80%)
3. Analyze failures
4. Fix failing tests (if auto mode)
5. Report results

## Goal context

<goal>$ARGUMENTS</goal>
