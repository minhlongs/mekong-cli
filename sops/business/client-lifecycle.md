# SOP: Business Client Lifecycle
**Layer:** Business | **Version:** 1.0.0 | **Owner:** AE (Account Executive)

## Intent
Standardize client journey from lead → contract → delivery → retention.

## Stages

### §1 — Lead Qualification
- Trigger: new inbound lead or outbound prospect
- Tools: `/ae-outreach`, CRM lookup
- Criteria: budget confirmed, authority confirmed, timeline within 90 days
- Output: qualified lead → `leads/qualified/` or discard

### §2 — Proposal & Contract
- Trigger: qualified lead
- Use `/ae-deal-prep` to generate proposal
- Contract review → CEO approval gate if >$10k
- Output: signed contract → `contracts/active/`

### §3 — Delivery Handoff
- Trigger: contract signed
- Handoff brief: scope, timeline, contacts, SLA
- Assign PM agent for delivery management
- Output: active project → `projects/active/`

### §4 — Delivery & Check-in
- Weekly check-ins via `/ae-follow-up`
- Monthly health score calculation
- If score < 60/100: CEO escalation

### §5 — Renewal / Upsell
- 60 days before contract end: renewal outreach
- Evaluate upsell opportunities
- CEO approval for >20% contract value change

## Acceptance Criteria
- [ ] All stages have clear entry/exit criteria
- [ ] Client data consistent across CRM and files
- [ ] CEO notified at: qualification, contract, renewal, churn risk

## Escalation
Client health score < 40 → CEO emergency review.
