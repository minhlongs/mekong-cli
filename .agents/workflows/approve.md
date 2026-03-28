---
description: "Approve pending content, decisions, or deployments."
---

# /approve — Approve Pending Items

Review and approve items queued during development.

## Usage

Tell Antigravity one of:
- `approve` — List all pending items
- `approve all` — Approve everything
- `approve tweet` — Approve pending social posts
- `approve deploy` — Approve deployments
- `approve pr` — Approve pull requests

## Workflow

1. Scan for pending items:
   - Unmerged branches with completed work
   - Draft content files awaiting publish
   - Deployment queues
   - Open PRs

// turbo
```bash
echo "📋 PENDING ITEMS"
echo "════════════════"
echo ""
echo "🌿 Branches (unmerged):"
git branch --no-merged main 2>/dev/null || git branch --no-merged master 2>/dev/null
echo ""
echo "📝 Draft content:"
find . -name "DRAFT-*" -o -name "draft-*" 2>/dev/null | head -10
echo ""
echo "🔄 Recent stashes:"
git stash list 2>/dev/null | head -5
```

2. Present each item with preview
3. User decides: approve / reject / edit

## Safety

- **Content**: Preview shown before posting
- **Deploys**: Diff shown before push
- **PRs**: Code review summary shown
