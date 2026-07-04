# 01. Agentic OS Design for Mekong CLI

> Blueprint: Mekong CLI as an Agentic Operating System running 39 autonomous agents.

---

## 1. Architecture Overview

Mekong CLI is not a script runner. It is an Agentic OS that orchestrates 39 specialized AI agents across 8 layers. Each agent is a Claude Code instance + local LLM (MLX on Apple Silicon). The COO agent acts as the kernel: dispatching workflows, monitoring completion, and enforcing Binh Phap Quan Luat (military discipline protocol).

### Layer Stack

| Layer | Agents | Role |
|-------|--------|------|
| C-Level (7) | CEO, CTO, COO, CMO, CSO, CFO, CHRO | Strategy, governance, cross-functional orchestration |
| Engineering (8) | Eng Lead, 7x eng agents | Code, test, deploy, review |
| Marketing (5) | CMO staff | Content, SEO, campaigns, analytics |
| Sales (4) | SDR, pipeline, deal desk, closing | Prospecting through close |
| Operations (6) | SRE, incidents, infra, finops, compliance, vendor | Run the business |
| Data/ML (4) | Data eng, ML eng, analytics, governance | Pipelines, models, reporting |
| People/HR (3) | Recruit, onboard, performance | Talent lifecycle |
| Finance (2) | Budget, treasury | Financial controls |

**Total: 39 agents.**

---

## 2. Agent Communication Model

- **COO dispatches all workflows** via `mekong run <workflow>` or skill invocation.
- **Agents communicate through filesystem** (task queues in `plans/`, reports in `plans/reports/`).
- **No agent talks to another agent directly.** All coordination is mediated by the COO.
- **Workflow DAG** is defined in the plan; agents execute leaves, COO merges results.

```
 CEO ──┐
        ├── COO ──┬── CTO ─── eng agents
        │          ├── CMO ─── mktg agents
        │          ├── CSO ─── sales agents
        │          ├── CFO ─── finance agents
        │          ├── CHRO ── HR agents
        │          └── ops agents
        │
        ├── Binh Phap Enforcer (audit layer)
        └── Metrics Collector (KPI layer)
```

---

## 3. Automation Percentages

| Function | Automation | Notes |
|----------|-----------|-------|
| Engineering | 90% | Agents code, test, deploy, review. Human only for final merge sign-off. |
| Marketing | 60% | Agents draft content, SEO analysis, campaign logic. Human publishes. |
| Sales | 40% | Agents research leads, enrich CRM. Human closes deals. |
| Operations | 85% | Agents monitor dashboards, auto-fix common failures, escalate edge cases. |
| Finance | 70% | Agents reconcile, forecast, flag anomalies. Human approves payments. |
| HR | 50% | Agents screen resumes, schedule interviews, track performance cycles. |
| Data/ML | 75% | Agents build pipelines, retrain models, generate reports. |

**Overall automation rate: ~70%**, with humans in the loop for approvals, closes, and escalations.

---

## 4. Agent KPIs

| Agent | Key Metric | Target | Frequency |
|-------|-----------|--------|-----------|
| CEO | Strategic decisions executed / quarter | 10 | Quarterly |
| CTO | Builds shipped / week | 5 | Weekly |
| COO | Workflow completion rate | >90% | Daily |
| CMO | Leads generated / week | 50 | Weekly |
| CSO | Demos booked / week | 10 | Weekly |
| CFO | Forecast accuracy | +/-5% | Monthly |
| CHRO | Time-to-fill (days) | <30 | Monthly |
| Eng Lead | PRs merged / week | 15 | Weekly |
| SDR | Qualified leads / week | 20 | Weekly |
| Content | Posts published / week | 3 | Weekly |
| SRE | Uptime | 99.9% | Daily |
| FinOps | Cost / customer (MoM) | -5% | Monthly |

---

## 5. Binh Phap Quan Luat Enforcement

The Binh Phap module (just built) enforces:

- **5 Factors** (Dao, Thien, Dia, Tuong, Phap) checked before every major decision.
- **6 Layers** of organizational depth are respected; no layer-skipping.
- **39 Agents** each have defined authority boundaries.
- **Inverted Triangle** — strategy starts at the top but execution flows bottom-up feedback.
- **Discipline triggers** — if an agent misses 2 consecutive KPIs, COO escalates to CEO.

---

## 6. Workflow Dispatch Model

1. User invokes `mekong run <workflow>` or a slash command skill.
2. COO parses intent and selects a workflow DAG from `plans/`.
3. COO fans out to relevant agents (C-Level first if strategic, department heads if tactical).
4. Each agent executes its node, writes results to `plans/reports/`.
5. COO collects outputs, checks Binh Phap rules, merges, presents to user.
6. Metrics collector logs completion, cycle time, and any escalations.

---

## 7. Gaps / Missing (Current State)

- **No Revenue Agent.** Revenue operations (attribution, pipeline forecasting, subscription analytics) is handled ad-hoc by CFO. A dedicated RevOps agent is needed.
- **No Sales Agent with CRM Access.** The CSO and SDR agents lack direct CRM integration. Lead data is entered manually. This is the single biggest automation bottleneck.
- **No Customer Success Agent.** Post-sale retention, onboarding, and NPS tracking are manual.
- **No Board Agent.** Board reporting is manually compiled from agent reports each month.
- **No Legal Agent.** Contract review, compliance monitoring, and IP management are manual.

### Priority Roadmap (Next 30 Days)

1. **Build Revenue Agent** — connect to Stripe/NOWPayments API, generate daily MRR/ARR/Churn reports.
2. **Build CRM-Connected Sales Agent** — read/write HubSpot or similar via MCP tool.
3. **Build Customer Success Agent** — trigger onboarding workflows, track usage, flag at-risk accounts.
4. **Build Board Agent** — auto-compile monthly board deck from agent KPIs.

---

## 8. Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| COO as sole dispatcher | Prevents agent conflicts, single audit trail |
| Filesystem as message bus | No infrastructure dependency, human-readable, git-tracked |
| Local LLM for all agents | Zero API cost, privacy, low latency |
| Binh Phap as audit layer | Catches agent drift before it affects output |
| KPIs on agents, not workflows | Measures system health, not just throughput |

---

## 9. Metrics & Observability

- **Cycle time** per workflow type (tracked in `plans/reports/`).
- **Agent KPI dashboard** compiled daily by COO into `plans/reports/daily-kpi.md`.
- **Binh Phap violation log** at `plans/reports/binh-phap-violations.md`.
- **System health check** runs every morning via `sre-morning-check` skill.

---

*Status: DONE*
*File: /Users/macbook/mekong-cli/plans/company-blueprint/01-agency-os.md*
