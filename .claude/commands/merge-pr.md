---
description: "Auto-merge PR — fetch, resolve conflicts, merge, restore protection"
argument-hint: "<pr-url> [--admin]"
---

# /merge-pr — Auto Pull Request Merger

Automates the full PR lifecycle:
1. Fetch PR details
2. Auto-resolve simple conflicts (accept ours/theirs)
3. Disable branch protection
4. Merge (squash)
5. Re-enable branch protection

## Usage
```
/merge-pr https://github.com/owner/repo/pull/123
/merge-pr 123 --repo owner/repo
/merge-pr 123 --repo owner/repo --admin
```

## Flow
1. `gh pr view <pr>` — check mergeability
2. If conflicts: `git merge base-branch` → resolve with strategy
3. `gh pr merge --squash --admin`
4. Restore branch protection
