---
description: "Feature build — plan, code, test, review. Full feature cycle."
---

# /dev-feature — Feature Build

**AUTO-EXECUTE MODE.** Full feature development cycle.

## Pipeline

```
SEQUENTIAL: Plan → Code → Test → Review     (~15-30 min)
    |
OUTPUT: Feature implemented, tested, and ready for ship
```

## Execution Steps

### Step 1: Understand & Plan

1. Read relevant source files to understand current architecture
2. Create a brief implementation plan (can be inline, no separate file needed for small features)
3. Identify files to create/modify

### Step 2: Implement

1. Write the core implementation
2. Follow existing code patterns and conventions
3. Create new files as needed

### Step 3: Test

// turbo
```bash
# Auto-detect and run tests
if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
  python3 -m pytest -q --tb=short 2>/dev/null
fi
if [ -f "package.json" ]; then
  npm test 2>/dev/null
fi
```

Write new tests if the feature warrants them.

### Step 4: Quality Check

// turbo
```bash
# Lint check
if [ -f "pyproject.toml" ]; then
  python3 -m ruff check . 2>/dev/null
fi
if [ -f "package.json" ]; then
  npm run lint 2>/dev/null
fi
```

Review your own code for:
- Security issues
- Performance concerns
- Edge cases
- Error handling

## Output

Report what was built, what was tested, and any remaining concerns.
