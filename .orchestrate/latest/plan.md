# Incident Response Execution Plan — Ops Layer SOP v1.0.0

## Reframed Problem

An active operations incident requires disciplined, time-bound execution of the incident-response SOP to minimize user impact, restore service within severity-defined SLAs, and produce actionable post-mortems for P1/P2 events. The core challenge is not technical complexity but procedural adherence under pressure: detecting automatically, acknowledging within SLAs, containing spread, resolving root cause, and institutionalizing learnings. Success is measured by time-to-acknowledge, time-to-resolve per severity tier, and post-mortem completion within 5 business days for major incidents.

---

## Work Checklist

| Step | Action | Acceptance Criteria | Owner |
|------|--------|---------------------|-------|
| **§1 Detect** | Automated alert fires from Prometheus/Grafana; on-call receives page; run `/audit-trail` check for error spikes | Alert acknowledged in monitoring tool; error spike confirmed or ruled out via audit trail within 5 min of detection | Monitoring Agent / On-call |
| **§2 Acknowledge** | Respond to alert within severity SLA (P1=15m, P2=1h, P3=4h, P4=24h); assign Incident Commander (ENG lead); create dedicated incident channel (#incident-YYYY-MM-DD-<title>) | SLA timer stops; IC named; channel exists with stakeholders invited; initial severity confirmed | Incident Commander |
| **§3 Assess & Contain** | Identify blast radius (users, regions, services); update incident doc `incidents/YYYY-MM-DD-<title>.md` with timeline; if P1/P2, execute immediate rollback if available and safe | Scope documented; rollback executed if applicable and service shows recovery; timeline starts at detection time | Incident Commander + Eng Lead |
| **§4 Resolve** | Implement root-cause fix; verify via monitoring dashboards and synthetic probes; communicate status to stakeholders every 30 min until resolved | Monitoring green for ≥15 min; stakeholders notified; incident channel moves to "monitoring" phase | Engineering Team |
| **§5 Post-Mortem** | *(P1/P2 only)* Draft post-mortem in same incident doc: timeline, root cause, impact metrics, action items with owners/deadlines; schedule review within 5 business days | Document published; review meeting scheduled; all action items assigned with due dates | Incident Commander |
| **Escalation** | If P1 unresolved after 1 hour, trigger CEO emergency notification | CEO/executive team paged; executive bridge call initiated if requested | Incident Commander |

---

## Risks & Gates

| Risk | Likelihood | Impact | Mitigation | Gate |
|------|-----------|--------|------------|------|
| Alert fatigue / missed page | Medium | High (SLA breach) | Ensure on-call rotation coverage; test alerting weekly | Gate 1: Alert delivery confirmed before declaring incident |
| Incorrect severity classification | Medium | Medium | Require second opinion from ENG lead for P1/P2 | Gate 2: Severity validated by IC within 10 min |
| Rollback causes worse outage | Low | High | Verify rollback candidate in staging; have runbook with abort criteria | Gate 3: Rollback readiness check before execution (even for P1/P2) |
| Root cause misidentification | Medium | High | Require data-backed hypothesis before fix; avoid band-aids | Gate 4: Fix verified by monitoring for 15 min before closure |
| Post-mortem never completed | High | Medium | Auto-create doc template at incident start; calendar hold for review | Gate 5: Doc exists and review scheduled within 24h of resolution (P1/P2) |
| CEO escalation delay | Low | Critical | Pre-approved escalation list; auto-escalation bot if SLA timer expires | Gate 6: Escalation path tested quarterly |

---

## Agent Suggestion per Step

| Step | Primary Agent | Supporting Agents | Rationale |
|------|---------------|-------------------|-----------|
| **§1 Detect** | **Monitoring Agent** (automated) + **On-call Engineer** | NOC / SRE | Automation provides first signal; human confirms and initiatesresponse |
| **§2 Acknowledge** | **Incident Commander** (ENG Lead) | On-call, PM, Support Lead | Single commander prevents chaos; cross-functional stakeholders brought in early |
| **§3 Assess & Contain** | **Incident Commander** + **Domain Expert** (e.g., infra, app, DB) | Support (for customer impact data) | Technical depth needed to scope; support provides real-time user reports |
| **§4 Resolve** | **Engineering Team** (assigned by IC) | QA (for verification), Support (for comms) | Fix requires hands-on engineering; QA validates; support keeps customers informed |
| **§5 Post-Mortem** | **Incident Commander** (facilitator) | All participants, PM (for action tracking) | IC owns timeline; team contributes; PM tracks remediation items |

---

## Ship Plan

Since this is an operational procedure (not software code), the "ship" metaphor maps to **incident lifecycle completion**:

| Phase | Action | Success Criteria |
|-------|--------|------------------|
| **Commit** | Create incident document `incidents/YYYY-MM-DD-<title>.md` with initial timeline, severity, and assignees | Doc exists; linked from incident channel; stakeholders notified |
| **PR** | Post-mortem review meeting for P1/P2; action items peer-reviewed and prioritized | Review completed within 5 business days; action items approved by attendees |
| **Deploy** | Implement approved action items (fixes, runbook updates, monitoring improvements) | Each item has PR/issue; merged/deployed; linked back to incident doc |
| **Smoke** | Verify monitoring green; run incident-response tabletop exercise or drill within 30 days; confirm no recurrence | 48h monitoring stability; next drill scheduled; retrospective metrics improved |

---

## Assumptions

1. On-call rotation and escalation paths are already configured in PagerDuty/Opsgenie.
2. `/audit-trail` command is available and returns structured error-spike data.
3. Incident documentation directory `incidents/` exists in version control.
4. Prometheus/Grafana alerts are already tuned with appropriate severity thresholds.
5. CEO emergency contact list is maintained and accessible to Incident Commanders.

---

## Feasibility Assessment

**Feasible:** Yes. This plan is a procedural wrapper around existing tooling (monitoring, chat, docs). The main risks are human (fatigue, misclassification, incomplete post-mortems), not technical. Feasibility depends on:
- Team training on SOP (quarterly drills recommended)
- Automation of alert routing and doc creation
- Executive buy-in on post-mortem timelines

**Not Feasible If:** On-call coverage is spotty, monitoring is unreliable, or the organization treats post-mortems as blame assignments rather than learning exercises.

---

*Plan generated for SOP: Ops Incident Response v1.0.0. Ready for persistence to `.orchestrate/latest/plan.md`.*