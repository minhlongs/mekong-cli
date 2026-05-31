# SOP: CEO Decision Making
**Layer:** CEO | **Version:** 1.0.0 | **Owner:** CEO Solo

## Intent
Ensure every CEO decision is documented, reversible, and aligned with company goals.

## Workflow

### §1 — Receive Decision Request
- Input: business event, agent escalation, or CEO initiative
- Record: date, context, urgency, affected layers
- If urgency == "critical": skip to §4

### §2 — Gather Context
- Pull relevant data: financials, agent reports, market signals
- Maximum context gathering time: 30 minutes
- If insufficient data after 30 min: make decision with documented assumption

### §3 — Evaluate Options
- List ≥2 options (including "do nothing")
- Score each: impact × confidence (1-5 scale)
- Select highest-scoring option

### §4 — Execute Decision
- Document: decision, rationale, expected outcome
- Dispatch to relevant layer agent with clear task brief
- Set review date (typically 2 weeks)

### §5 — Review Outcome
- At review date: check actual vs expected outcome
- Update SOP if process gap identified
- Archive decision record to `decisions/`

## Acceptance Criteria
- [ ] Decision is documented before execution
- [ ] Rationale recorded with at least 2 options evaluated
- [ ] Relevant layer agent dispatched with task brief
- [ ] Review date set

## Escalation
If decision involves >$50k impact or legal exposure: pause, get external counsel.
