---
description: Code review with scout-based edge case detection. 1 command, ~10-20 min.
argument-hint: [file/path to review]
allowed-tools: Read, Grep, Task
---

# /review — Code Review

**Engineering** — single command.

## Estimated: 1 credit, 10-20 minutes

## Workflow

```
[Read Code] → [Scout Edge Cases] → [Security Audit] → [Performance Check] → [Report]
```

## Review Checklist

- [ ] Code follows established patterns
- [ ] No security vulnerabilities (OWASP Top 10)
- [ ] Error handling complete
- [ ] Type safety (no any types)
- [ ] No console.log pollution
- [ ] Tests cover edge cases
- [ ] Performance optimized

## Output

Review report at `./plans/reports/review-{date}-{slug}.md`

## Goal context

<goal>$ARGUMENTS</goal>
