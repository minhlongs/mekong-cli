# Crisis + Reputation OS

> Operational system for detecting, responding to, and recovering from critical
> events that threaten company reputation, operations, or continuity.

---

## 1. Crisis Scenarios

### 1.1 Security Breach (Source Code Leak)
- Unauthorized access to private repositories
- Customer data exposure via compromised dependency
- Insider threat — disgruntled employee exfiltrates IP
- Third-party vendor breach with shared credentials

### 1.2 AI Provider Outage (Claude API Down)
- Upstream LLM API returns 5xx or degraded responses
- Rate-limit exhaustion during critical customer campaign
- Model deprecation or breaking API change with < 24h notice
- Provider compliance / policy ban affecting allowed use cases

### 1.3 Founder Health Emergency
- Founder incapacitated with no proxy decision rights in place
- Critical business decisions frozen for > 48 hours
- Investor and team communication gap during recovery

### 1.4 Reputation Attack (SaaS Competitor FUD)
- Coordinated negative reviews on G2 / Capterra / Product Hunt
- Competitor-funded blog or press FUD campaign
- Social media pile-on from bot or troll networks
- False technical claims published in comparison articles

---

## 2. Crisis Playbook

### Step 1 — Detect
- Monitoring alerts via Sentry, Better Stack, or PagerDuty
- Social listening tools (Brandwatch, Google Alerts)
- Customer support ticket velocity spike detection
- GitHub secret-scanning and dependency alert hooks

### Step 2 — Assess
- **Low**: Minor complaint, isolated issue, no customer impact
- **Medium**: Affects subset of customers, requires response within 4h
- **Critical**: Active breach, total outage, legal liability, press coverage

### Step 3 — Respond
- Founder or on-call director decides within 60 minutes
- Assemble crisis response team (founder, CTO, comms lead)
- If critical: freeze deploys, isolate affected systems, invoke incident response
- If breach: engage legal counsel, notify affected parties per SLA
- Document every decision with timestamp and rationale

### Step 4 — Communicate
- Internal: team-wide Slack / Telegram update within 1 hour
- Customer: status page post within 2 hours; direct email within 4 hours
- Public: blog post or social statement within 4 hours (if critical)
- Always include: what happened, what is being done, when to expect update
- Bilingual (Vietnamese + English) for all customer-facing communication

### Step 5 — Resolve
- Implement root-cause fix with hotfix or patch
- Verify fix in staging before production rollout
- Add monitoring / alerting to prevent recurrence
- Restore normal service levels and confirm with affected customers

### Step 6 — Learn (Post-Mortem)
- Blameless post-mortem written within 1 week of resolution
- Timeline of events: detection time, response time, fix time
- Root cause analysis (5 Whys or fishbone diagram)
- Action items with owners and deadlines
- Update runbooks and playbooks with lessons learned

---

## 3. Communication Templates

### Internal Alert (Telegram / Slack)
```
[SEVERITY: LOW | MEDIUM | CRITICAL]
Incident: <brief title>
Detected at: <timestamp>
Impact: <what is affected>
Response lead: <name>
Next update: <time>
```

### Customer Status Page
```
We are investigating an issue affecting <feature>. We will provide
an update within <X> hours. <Link to status page>
```

### Public Statement (Critical Only)
```
A security incident was identified on <date>. We have contained the issue,
engaged independent security reviewers, and are notifying affected parties.
Full post-mortem will be published at <link> by <date>.
```

---

## 4. Runbook Inventory

| Runbook | Location | Owner |
|---------|----------|-------|
| Security breach response | `plans/incident-response/security-breach.md` | CTO |
| AI provider failover | `plans/incident-response/ai-provider-failover.md` | Engineering |
| Founder succession plan | `plans/company-blueprint/25-succession.md` | Founder |
| Reputation defense playbook | `plans/incident-response/reputation-defense.md` | Comms Lead |
| Customer data breach notification | `plans/legal/breach-notification.md` | Legal Counsel |

---

## 5. Metrics & Review

- **Mean Time To Detect (MTTD)**: target < 15 min
- **Mean Time To Respond (MTTR)**: target < 60 min (critical)
- **Mean Time To Resolve**: target < 4 hours (critical)
- **Post-mortem completeness**: 100% of critical incidents
- **Quarterly tabletop exercise**: simulate one scenario per quarter
