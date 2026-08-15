# SOP: CEO Weekly Review
**Layer:** CEO | **Version:** 1.0.0 | **Owner:** CEO Solo

## Intent
Systematic weekly review of all business layers to catch issues early and set priorities.

## Workflow

### §1 — Metrics Review (30 min)
- Revenue: actual vs target (Business layer)
- Product: shipped vs planned (Product layer)
- Engineering: bugs, incidents, deployment health (Engineering layer)
- Ops: vendor status, cost, incidents (Ops layer)

### §2 — Agent Status Check (15 min)
- Review agent reports from each layer
- Identify blockers or stalled tasks
- Decide: unblock, reassign, or deprioritize

### §3 — Priority Setting (15 min)
- Top 3 priorities for next week
- Assign each to specific layer agent
- Communicate via `/ae-deal-prep`, `/analyst-report`, etc.

### §4 — Risk Register Update (10 min)
- New risks identified this week
- Risk status changes
- Mitigation actions assigned

### §5 — Decision Log
- Decisions made this week → `decisions/weekly-YYYY-MM-DD.md`

## Acceptance Criteria
- [ ] All 4 layer reports reviewed
- [ ] Top 3 priorities set and assigned
- [ ] Risk register updated
- [ ] Decision log created

## Escalation
If >3 agents are blocked simultaneously: schedule emergency sync.
