# SOP: Ops Incident Response
**Layer:** Ops | **Version:** 1.0.0 | **Owner:** OPS (Operations)

## Intent
Minimize impact and restore service quickly during incidents.

## Severity Levels

| Severity | Definition | Response Time | Example |
|----------|-------------|---------------|---------|
| P1 | Complete outage | 15 min | API down, all users affected |
| P2 | Degraded service | 1 hour | Slow responses, partial outage |
| P3 | Minor issue | 4 hours | Single feature broken |
| P4 | Cosmetic | 24 hours | UI glitch, typo |

## Response Steps

### §1 — Detect (automated)
- Alerts from observability stack (Prometheus + Grafana)
- `/audit-trail` check for error spikes

### §2 — Acknowledge
- Respond to alert within severity SLA
- Assign incident commander (usually ENG lead)
- Create incident channel

### §3 — Assess & Contain
- Identify affected scope
- If P1/P2: consider immediate rollback
- Document timeline in `incidents/YYYY-MM-DD-<title>.md`

### §4 — Resolve
- Fix root cause
- Verify resolution via monitoring
- Communicate status to stakeholders

### §5 — Post-Mortem (P1/P2 only)
- Timeline, root cause, impact
- Action items with owners and deadlines
- Post-mortem review within 5 business days

## Escalation
P1 not resolved in 1 hour → CEO emergency notification.
