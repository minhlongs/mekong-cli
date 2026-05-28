---
name: "source-command-git-fix-pr"
description: "Address unresolved PR review comments"
---

# source-command-git-fix-pr

Use this skill when the user asks to run the migrated source command `git-fix-pr`.

## Command Template

// turbo

# /fix-pr - PR Comment Fixer

Fetch and fix all unresolved PR review comments.

## Usage

```
/fix-pr [pr-number]
```

## Codex Prompt Template

```
Fix PR comments workflow:

1. Fetch PR review comments:
   gh pr view {number} --json reviews,comments
2. List unresolved comments
3. For each comment:
   - Understand the feedback
   - Make targeted code changes
   - Mark as resolved if possible
4. Commit fixes: git commit -m "♻️ refactor: address PR review #{number}"
5. Push updates

Report:
- Comments addressed
- Changes made
- Remaining items
```

## Example Output

```
📋 PR #55: Add authentication

💬 Comments to address: 3
   1. ✅ "Add error handling" → Added try/catch
   2. ✅ "Use const instead of let" → Fixed
   3. ✅ "Add JSDoc" → Added documentation

✅ All comments addressed
✅ Pushed to feature/auth
```
