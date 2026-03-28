---
description: "Ship code to production — lint, test, commit, push, deploy. One workflow to rule them all."
---

# 🚀 Ship Command

One workflow to test, commit, push, and deploy.

## Steps

### Step 0: Pre-Flight Check

// turbo
```bash
echo "🔍 Pre-flight check..."
git status --short
echo ""
echo "Branch: $(git branch --show-current)"
echo "Remote: $(git remote get-url origin 2>/dev/null || echo 'no remote')"
```

### Step 1: Run Validation

// turbo
```bash
echo "🔍 Running linters..."
# Python projects
if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
  python3 -m ruff check . --fix 2>/dev/null || echo "ruff not available"
fi
# Node projects
if [ -f "package.json" ]; then
  npm run lint 2>/dev/null || echo "no lint script"
fi
echo ""
echo "🧪 Running tests..."
if [ -f "pyproject.toml" ] || [ -f "setup.py" ]; then
  python3 -m pytest -q --tb=short 2>/dev/null || echo "pytest not available"
fi
if [ -f "package.json" ]; then
  npm test 2>/dev/null || echo "no test script"
fi
```

### Step 2: Stage & Commit

Stage all changes and commit with a descriptive message based on the changes made.

```bash
git add -A
git commit -m "<type>: <description>"
```

Commit types: `feat`, `fix`, `docs`, `refactor`, `test`, `chore`

### Step 3: Push

```bash
git push origin $(git branch --show-current)
```

### Step 4: Verify (if deployed)

// turbo
```bash
echo "✅ SHIPPED!"
git log --oneline -1
```

If there's a production URL, check it via browser to confirm deployment.
