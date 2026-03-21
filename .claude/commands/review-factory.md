---
description: "Full code review of factory-loop.sh — lint, logic, integration, security"
argument-hint: [--strict | --quick]
allowed-tools: Read, Bash, Grep
---

# /review:factory — Factory Loop Code Review

Comprehensive code review of `factory-loop.sh` and supporting modules.

## Checklist

1. **Syntax**: `bash -n factory-loop.sh`
2. **Unit tests**: `bash tests/test_detect_project_state.sh`
3. **Integration**: Verify all functions called in main loop exist and have correct signatures
4. **Security**: No secrets in code, safe tmux key injection, proper quoting
5. **Error handling**: All external calls have `|| true` or `2>/dev/null`
6. **Node.js calls**: All wrapped in `timeout` to prevent hang
7. **File operations**: Atomic writes (tmp + rename) where needed
8. **State files**: Proper cleanup in trap handler
9. **Metrics**: All events logged consistently with correct format
10. **Brain learning**: Outcomes recorded on both success and timeout paths

## Review Steps

Read and review these files in order:
1. `factory-loop.sh` — main loop, all functions
2. `factory-watchdog.sh` — auto-restart logic
3. `apps/openclaw-worker/lib/factory-roi-calculator.js` — ROI + brain state
4. `apps/openclaw-worker/lib/output-intelligence.js` — output classifier
5. `tests/test_detect_project_state.sh` — unit tests
6. `docs/factory-system-architecture.md` — architecture doc accuracy

For each file, check:
- Logic correctness
- Edge cases (empty output, missing files, node not available)
- Performance (no unnecessary loops, reasonable timeouts)
- Consistency (same patterns used across functions)

Report format:
```
## Factory Code Review Report

### Critical Issues (must fix)
- [file:line] description

### Warnings (should fix)
- [file:line] description

### Notes (nice to have)
- observation

### Score: X/10
```

## Goal context

<goal>$ARGUMENTS</goal>
