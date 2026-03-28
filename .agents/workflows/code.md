---
description: "Code quality commands — TDD, code analysis, optimization, CI, debugging, checking."
---

# /code — Code Quality & CI Command Suite

**AUTO-EXECUTE MODE.** Detect sub-command from user prompt and execute.

## TDD (Test-Driven Development)

### `/tdd` — TDD Workflow
Enforce Red-Green-Refactor discipline:

🔴 **RED Phase:**
1. Understand the feature requirement
2. Write a failing test that defines expected behavior
3. Run test to confirm it fails
4. Commit: `🔴 test: add failing test for {feature}`

🟢 **GREEN Phase:**
1. Write MINIMAL code to pass the test
2. No extra features, just pass the test
3. Run test to confirm it passes
4. Commit: `🟢 feat: implement {feature} to pass test`

♻️ **REFACTOR Phase:**
1. Review code for improvements
2. Apply SOLID principles
3. Extract methods, reduce duplication
4. Run tests to ensure still passing
5. Commit: `♻️ refactor: clean up {feature}`

### `/tdd implement` — TDD Implementation
Full TDD cycle for a specific feature — write test first, then implement.

## Code Analysis

### `/code check` — Quality Check
// turbo
```bash
echo "🔍 Code Quality Check"
echo "====================="
if [ -f "pyproject.toml" ]; then
  echo "Python lint:" && python3 -m ruff check . 2>/dev/null
  echo "Python type:" && python3 -m mypy . 2>/dev/null || true
fi
if [ -f "package.json" ]; then
  echo "JS/TS lint:" && npx eslint . 2>/dev/null || true
  echo "TS type:" && npx tsc --noEmit 2>/dev/null || true
fi
```

### `/code analysis` — Deep Code Analysis
1. Complexity metrics
2. Dependency analysis
3. Security scan
4. Code duplication detection
5. Report with recommendations

### `/code optimize` — Performance Optimization
1. Identify performance bottlenecks
2. Suggest optimizations
3. Apply changes
4. Benchmark before/after

### `/code repro-issue` — Reproduce Issue
1. Read issue/error description
2. Create minimal reproduction
3. Verify reproduction
4. Identify fix path

## CI Commands

### `/ci run` — Run CI Locally
Local CI pipeline to catch issues before push:

// turbo
```bash
echo "🔄 Running Local CI..."
echo ""
echo "Step 1: Lint"
if [ -f "pyproject.toml" ]; then python3 -m ruff check . 2>/dev/null && echo "✅ Ruff OK" || echo "❌ Ruff errors"; fi
if [ -f "package.json" ]; then npm run lint 2>/dev/null && echo "✅ ESLint OK" || echo "❌ ESLint errors"; fi
echo ""
echo "Step 2: Tests"
if [ -f "pyproject.toml" ]; then python3 -m pytest -q --tb=short 2>/dev/null && echo "✅ pytest OK" || echo "❌ pytest errors"; fi
if [ -f "package.json" ]; then npm test 2>/dev/null && echo "✅ npm test OK" || echo "❌ npm test errors"; fi
echo ""
echo "Step 3: Build"
if [ -f "package.json" ]; then npm run build 2>/dev/null && echo "✅ Build OK" || echo "❌ Build errors"; fi
```

### `/ci status` — CI Status
// turbo
```bash
echo "📊 CI Status"
gh run list --limit 5 2>/dev/null || echo "GitHub CLI not available"
```

### `/ci debugger` — CI Debugger  
1. Read CI failure logs
2. Identify root cause
3. Suggest fix
4. Test fix locally

### `/ci deploy` — CI Deploy
1. Trigger deployment pipeline
2. Monitor status
3. Verify deployment

### `/ci supabase-sync` — Supabase Sync
Sync database schema and migrations with Supabase
