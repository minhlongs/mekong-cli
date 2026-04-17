# CX Support Department as a Service

> Replace a support team with AI agents that resolve tickets, answer FAQs, and escalate complex issues — 24/7 coverage at $0.75/ticket.

## Value Proposition

| What you replace | Annual cost | What you pay |
|-----------------|-------------|--------------|
| 2 Support Reps ($55k each) | $110,000/yr | $49/mo floor |
| Intercom / Zendesk | $12,000/yr | $0.75/ticket |
| **Total replaced** | **$122,000/yr** | **~$3,600/yr** |

## What This Department Does

1. **Ticket Resolution** — L1/L2 support automation: FAQs, billing, access issues, how-tos
2. **Knowledge Base** — Auto-generate and update KB articles from resolved tickets
3. **Escalation Handling** — Smart routing to engineering/CS/billing based on issue type
4. **CSAT Reporting** — Weekly customer satisfaction analysis with trend detection
5. **24/7 Coverage** — Instant first response at any hour, no on-call burnout

## Outcome-Based Pricing

| Deliverable | Price |
|------------|-------|
| Support ticket resolved (L1) | $0.75 |
| Support ticket resolved (L2) | $1.50 |
| KB article generated | $5 |
| CSAT report | $8 |
| Escalation handled | $5 |

**Monthly floor:** $49 (65 tickets).

## Included Commands

```bash
mekong business-client-onboard    # New customer onboarding support
mekong business-revenue-engine    # Identify expansion from support signals
```

## Install

```bash
mekong install dept-cx-support
```

## Configuration

```bash
# .mekong/.env.dept-cx-support
DEPT_CX_PLATFORM=intercom  # intercom|zendesk|freshdesk
DEPT_CX_API_KEY=your_key
DEPT_CX_ESCALATION_CHANNEL=slack
DEPT_CX_ESCALATION_SLACK_CHANNEL=#escalations
DEPT_CX_AUTO_RESOLVE_L1=true   # Auto-resolve L1 without human review
DEPT_CX_AUTO_RESOLVE_L2=false  # L2 requires human approval
DEPT_CX_CSAT_FREQUENCY=7  # days between CSAT reports
```

## SLA Targets

| Tier | First Response | Resolution |
|------|---------------|------------|
| L1 (FAQ) | < 2 minutes | < 5 minutes |
| L2 (Technical) | < 5 minutes | < 2 hours |
| L3 (Engineering) | < 10 minutes | Escalated |
