---
description: "Bug sprint — debug, fix, test. Batch bug fixes cycle."
---

# /dev-bug-sprint — Bug Sprint

**AUTO-EXECUTE MODE.** Debug, fix, and test bugs in batch.

## Pipeline

```
SEQUENTIAL: Debug → Fix → Test     (~15 min)
    |
OUTPUT: Bugs fixed and verified
```

## Execution Steps

### Step 1: Identify & Debug

1. Read bug description / error logs from user
2. Locate relevant source files
3. Reproduce the issue (run failing test or trace code path)
4. Identify root cause

### Step 2: Fix

1. Apply minimal, targeted fix
2. Follow existing code patterns
3. Add comments explaining why the fix works (if non-obvious)

### Step 3: Test

// turbo
```bash
# Run project tests
if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
  python3 -m pytest -q --tb=short 2>/dev/null
fi
if [ -f "package.json" ]; then
  npm test 2>/dev/null
fi
```

### Step 4: Verify

- Confirm the original bug is fixed
- Confirm no regressions introduced
- Report: what was broken, why, and what was fixed
