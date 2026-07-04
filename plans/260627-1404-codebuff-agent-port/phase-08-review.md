---
phase: 8
title: "Review"
status: pending
priority: P2
dependencies: [7]
---

# Phase 8: Review

## Overview
Final review, documentation, and cleanup before merge.

## Requirements
- Code review for all new/modified files
- Documentation updates (CLAUDE.md, README if needed)
- Ensure no breaking changes
- Verify public repo boundary (no private content leaked)

## Implementation Steps
1. Run code-reviewer on all new files
2. Update `CLAUDE.md` if new public paths added
3. Update `docs/system-architecture.md` with new pipeline stages
4. Verify git diff contains only intended changes (no apps/, no secrets)
5. Final test run

## Success Criteria
- [ ] Code review passes (no critical issues)
- [ ] Documentation updated
- [ ] Git diff clean (no private content)
- [ ] All tests pass
- [ ] Plan ready for merge to main
