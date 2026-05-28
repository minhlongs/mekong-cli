---
name: "source-command-git-update-branch"
description: "Update branch name with proper prefix and format"
---

# source-command-git-update-branch

Use this skill when the user asks to run the migrated source command `git-update-branch`.

## Command Template

// turbo

# /update-branch - Branch Renamer

Rename current branch with proper naming conventions.

## Usage

```
/update-branch [new-name]
```

## Prefixes

- `feature/` - New features
- `fix/` - Bug fixes
- `hotfix/` - Urgent fixes
- `refactor/` - Code refactoring
- `docs/` - Documentation
- `test/` - Test additions

## Codex Prompt Template

```
Branch rename workflow:

1. Get current branch: git branch --show-current
2. If new-name doesn't have prefix, add appropriate one
3. Slugify the name (lowercase, hyphens)
4. Rename local: git branch -m {old} {new}
5. If remote exists:
   - Delete old remote: git push origin --delete {old}
   - Push new: git push -u origin {new}

Report old and new branch names.
```

## Example Output

```
🌿 Branch Renamed

Old: my-feature
New: feature/my-feature

✅ Local renamed
✅ Remote updated
```
