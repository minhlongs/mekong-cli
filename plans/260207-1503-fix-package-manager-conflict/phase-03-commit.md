# Phase 03: Commit

## Context

Commit the pnpm migration and any fixes to git.

## Overview

**Priority**: P1
**Status**: Pending
**Effort**: 10min

Stage changes, create clean commit.

## Requirements

### Functional
- All changes staged
- Clean commit message following conventional commits
- No unintended files committed

### Non-Functional
- Commit message explains the migration
- Follows project commit standards

## Implementation Steps

1. **Check git status**
   ```bash
   git status
   ```

2. **Stage pnpm files**
   ```bash
   git add pnpm-lock.yaml
   git add pnpm-workspace.yaml  # if modified
   ```

3. **Stage any fixes**
   ```bash
   git add <files-with-ts-fixes>
   ```

4. **Verify no package-lock.json**
   ```bash
   git status | grep package-lock.json  # Should be empty
   ```

5. **Commit**
   ```bash
   git commit -m "$(cat <<'EOF'
   chore: migrate from npm to pnpm package manager

   - Remove package-lock.json
   - Add pnpm-lock.yaml
   - Fix TypeScript build errors
   - Standardize on pnpm workspace

   Build verified: pnpm run build passes
   EOF
   )"
   ```

## Todo List

- [ ] Review git status
- [ ] Stage pnpm-lock.yaml
- [ ] Stage any code fixes
- [ ] Verify package-lock.json not staged
- [ ] Commit with conventional message

## Success Criteria

- Clean commit created
- Commit message follows convention
- Only intended files committed
- No package-lock.json in commit

## Security Considerations

- Verify no secrets in staged files
- Ensure .gitignore excludes sensitive data

## Next Steps

Plan complete. Ready for implementation via `/cook`.
