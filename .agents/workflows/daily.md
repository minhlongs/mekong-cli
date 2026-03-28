---
description: "Daily status report — revenue, pending approvals, system health, today's focus."
---

# /daily — Daily Status Report

Quick daily summary of project activity and pending decisions.

**AUTO-EXECUTE MODE.** Gather all data automatically and present report.

## Data Collection

// turbo
```bash
echo "🏯 DAILY REPORT — $(date '+%b %d, %Y')"
echo "═══════════════════════════════════"
echo ""

# Git activity
echo "📊 Git Activity (last 24h):"
COMMITS=$(git log --oneline --since="24 hours ago" 2>/dev/null | wc -l | xargs)
echo "  Commits: $COMMITS"
git log --oneline --since="24 hours ago" 2>/dev/null | head -5
echo ""

# Files changed
echo "📁 Files Changed (last 24h):"
git diff --stat HEAD~${COMMITS:-1}..HEAD 2>/dev/null | tail -3
echo ""

# TODOs and FIXMEs
echo "⚠️ Open TODOs/FIXMEs:"
grep -r "TODO\|FIXME\|HACK\|XXX" --include="*.py" --include="*.ts" --include="*.js" --include="*.md" -l . 2>/dev/null | head -5
echo ""

# Branch status
echo "🌿 Branch Status:"
git branch -v 2>/dev/null | head -5
```

## Report Format

Present the collected data as:

1. **Activity Summary** — Commits, lines changed, key files
2. **Pending Items** — Open TODOs, FIXMEs, unmerged branches
3. **System Health** — Build status, test results
4. **Today's Focus** — Recommended priorities based on activity

## Example Output

```
🏯 DAILY REPORT — Mar 28, 2026

📊 Activity: 5 commits, 3 files changed
⚠️ Pending: 2 TODOs, 1 unmerged branch
⚙️ Health: Tests passing, no errors
🎯 Focus: Complete feature X, review PR #42
```
