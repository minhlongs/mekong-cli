# Phase 01 — Commit Uncommitted Work

> Clear the battlefield before handover. No loose files.

## Context Links

- [Plan Overview](plan.md)
- [Researcher 02 — Git State](research/researcher-02-deploy-git-state.md)
- Sophia root: `apps/sophia-ai-factory/`

## Overview

- **Priority**: P1 (Blocker for all subsequent phases)
- **Status**: Pending
- **Description**: Commit 629 insertions across 24 modified + 9 untracked files. Includes loading skeletons, error boundaries, landing page refinements, FadeInView animation, pricing updates.

## Key Insights

- Uncommitted work spans UI polish, not core logic — low risk of breakage
- Build and tests were passing before these changes — must re-verify
- Some files may be submodule-level changes (sophia-ai-factory is a submodule)
- Submodule commits must happen INSIDE the submodule directory first

## Requirements

### Functional
- All modified files committed with clean conventional commit messages
- Build passes with 0 TypeScript errors
- All 145+ tests pass

### Non-functional
- No secrets or .env files committed
- No `console.log` in committed code
- No `:any` types introduced

## Architecture

No architectural changes. This is a commit-only phase.

## Related Code Files

**Modified (24 files)** — loading skeletons, error boundaries, FadeInView, pricing:
- `apps/sophia-ai-factory/` — all changes within submodule

**Untracked (9 files)** — new components/utilities added but not staged

## Implementation Steps

1. `cd apps/sophia-ai-factory`
2. Run `git status` to inventory all changes
3. Run `npm run build` — verify 0 errors
4. Run `npm test` — verify all tests pass
5. Run quality gates:
   ```bash
   grep -r ": any" src --include="*.ts" --include="*.tsx" | wc -l  # must = 0
   grep -r "console\.log" src --include="*.ts" --include="*.tsx" | wc -l  # must = 0
   ```
6. Stage all files: `git add -A`
7. Commit: `git commit -m "feat(sophia): add loading skeletons, error boundaries, and pricing refinements"`
8. `cd ../..` (back to mekong-cli root)
9. Stage submodule pointer: `git add apps/sophia-ai-factory`
10. Commit root: `git commit -m "chore: update sophia-ai-factory submodule"`
11. Push: `git push origin master`
12. Poll CI/CD until GREEN

## Todo List

- [ ] Inventory uncommitted changes via `git status`
- [ ] Verify build passes (`npm run build`)
- [ ] Verify tests pass (`npm test`)
- [ ] Run quality gates (zero any, zero console.log)
- [ ] Commit in submodule with conventional message
- [ ] Update submodule pointer in root repo
- [ ] Push and verify CI/CD GREEN
- [ ] Verify HTTP 200 on production URL

## Success Criteria

- Zero uncommitted changes in `apps/sophia-ai-factory/`
- CI/CD pipeline GREEN after push
- Production site responds HTTP 200

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Build fails after staging | Low | Medium | Fix TS errors before commit |
| Test regression | Low | High | Run full test suite, fix before commit |
| Submodule pointer mismatch | Medium | Low | Commit inside submodule FIRST, then root |

## Security Considerations

- Verify no `.env`, API keys, or credentials in staged files
- Check `.gitignore` covers sensitive paths

## Next Steps

- Phase 02: Production Health Verification (depends on this phase completing)
