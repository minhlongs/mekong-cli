---
description: Ship code to production - test, commit, push, deploy
---

# 🚀 Ship Command

One command to test, commit, push, and deploy.

## Usage

```bash
/ship "commit message"
```

## Steps

### Step 0: Pre-Flight Tech Debt Check

// turbo

```bash
cd /Users/macbookprom1/mekong-cli
echo "🔍 Pre-flight CI/CD check..."
gh run list --limit 1 --json conclusion --jq '.[0].conclusion' | grep -q "success" && echo "✅ GitHub CI: GREEN" || echo "⚠️ GitHub CI: Check /debugger"
python3 -m ruff check . --quiet 2>/dev/null && echo "✅ Ruff: 0 errors" || echo "⚠️ Run: ruff check . --fix"
```

### Step 1: Run Validation

// turbo

```bash
cd /Users/macbookprom1/mekong-cli
python3 -m ruff check . --fix
pnpm --filter mekong-docs build
python3 -m pytest backend/tests -q --tb=no
```

### Step 2: Stage & Commit

```bash
git add -A
git commit -m "$ARGUMENTS"
```

### Step 3: Push (triggers Husky pre-push)

```bash
git push origin main
```

### Step 4: Verify Live

// turbo

```bash
curl -s https://www.agencyos.network | head -20
echo "✅ SHIPPED!"
```

## Quick Verify

```bash
gh run list --limit 1
```
