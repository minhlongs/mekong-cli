---
description: "Git commands — commit, create PR, fix issues, rebase, worktrees, husky hooks."
---

# /git — Git Workflow Command Suite

**AUTO-EXECUTE MODE.** Detect sub-command from user prompt and execute.

## Commit Commands

### `/git commit` — Conventional Commit
1. Run `git diff --staged` to see changes
2. Determine commit type (feat/fix/docs/refactor/test/chore)
3. Write concise message (50 chars max)
4. Add emoji prefix:
   - ✨ feat | 🐛 fix | 📝 docs | 💄 style | ♻️ refactor | ✅ test | 🔧 chore
5. Execute: `git commit -m "{emoji} {type}: {message}"`

### `/git commit-fast` — Quick Commit
// turbo
```bash
git add -A
MSG=$(git diff --cached --stat | tail -1)
git commit -m "🔧 chore: $MSG"
echo "✅ Fast committed: $(git log --oneline -1)"
```

## PR Commands

### `/git create-pr` — Create Pull Request
1. Push current branch
2. Generate PR title from branch name
3. Write description from commit log
4. Create PR via `gh pr create`

### `/git fix-pr` — Fix PR Issues
1. Read PR review comments
2. Apply requested changes
3. Push fixes
4. Reply to reviews

### `/git fix-issue` — Fix GitHub Issue
1. Read issue details
2. Create fix branch
3. Implement fix
4. Create PR referencing issue

### `/git analyze-issue` — Analyze GitHub Issue
1. Read issue description
2. Trace relevant code
3. Propose solution approach

## Branch Management

### `/git rebase` — Interactive Rebase
1. Identify rebase target
2. Execute rebase
3. Resolve conflicts if any
4. Force push

### `/git update-branch` — Update Branch
// turbo
```bash
BRANCH=$(git branch --show-current)
git fetch origin
git rebase origin/main 2>/dev/null || git rebase origin/master 2>/dev/null
echo "✅ Branch $BRANCH updated"
```

### `/git create-worktrees` — Create Git Worktrees
Setup parallel worktrees for multi-feature development

### `/git husky` — Setup Husky Hooks
Configure pre-commit and pre-push hooks
