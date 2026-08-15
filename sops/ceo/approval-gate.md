# SOP: CEO Approval Gate
**Layer:** CEO | **Version:** 1.0.0 | **Owner:** CEO Solo

## Intent
Define when CEO approval is required before any agent action proceeds.

## Approval Required (High-Risk)
- Any financial commitment >$10k
- New client contract signing
- Hiring decision (full-time employee)
- Legal or regulatory action
- Public communication on behalf of company

## Approval Not Required (Low-Risk)
- Bug fixes in existing products
- Routine ops tasks (monitoring, reports)
- Internal documentation updates
- Non-binding vendor outreach

## Approval Process
1. Agent submits approval request via `/approve`
2. CEO reviews context + recommendation
3. CEO response: APPROVED / REJECTED / MODIFIED
4. Decision recorded to `decisions/approval-log.md`
5. Agent proceeds or escalates

## Fast-Track
For time-critical low-risk items, CEO may pre-authorize a category:
"All bug fixes under 4 hours: auto-approve"
Record in `decisions/fast-track-authorizations.md`
