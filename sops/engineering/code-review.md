# SOP: Engineering Code Review
**Layer:** Engineering | **Version:** 1.0.0 | **Owner:** ENG (Engineer)

## Intent
Ensure code quality, security, and consistency across all changes.

## Workflow

### §1 — Pre-Review Checklist (Author)
- [ ] Tests pass: `pytest tests/`
- [ ] Lint passes: `pnpm lint`
- [ ] Type check passes (if applicable)
- [ ] Self-review completed
- [ ] Plan/reference linked in PR description

### §2 — Review Criteria (Reviewer)
- Correctness: does it solve the stated problem?
- Security: any injection, auth, data exposure risks?
- Performance: any unnecessary complexity or N+1?
- Tests: edge cases covered?
- Docs: relevant docs updated?

### §3 — Review Decision
- APPROVED: merge
- CHANGES_REQUESTED: specific list, re-review after fix
- BLOCKED: architectural concern, escalate to PM

### §4 — Post-Merge
- Monitor deployment health (observability dashboards)
- If incident: activate `/audit-execute` for post-mortem

## Hard Gates
- No merge without at least 1 approving review (CEO may override)
- No merge if CI checks fail
- No force-push to main

## Escalation
PR touches >3 directories or >500 lines: PM review required before ENG review.
