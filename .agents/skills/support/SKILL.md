---
name: support
description: >-
  Customer success — onboarding, feedback, support channels
---

# /support — Customer Success & Support Suite

Autonomous customer success, guided project onboarding milestones, Net Promoter Score (NPS) feedback, bug reporting, and smart issue triage.

---

## Onboarding Milestones
1. **API Keys & Providers**: Set environment variables in `HARNESS.md` / `.env`
2. **Layer Agents**: Configure and verify C-Level agents in `agents/registry.yaml`
3. **First Workflow**: Run first autonomous PEV goal workflow via `mekong cook`
4. **Results & Observability**: Review traces and scorecards via `mekong daily`
5. **Production Deployment**: Deploy and subscribe to RaaS Agency OS production tier

---

## Typer CLI Commands

```bash
# Customer success control plane overview
mekong support [--json]

# Onboarding: check progress or complete milestone step
mekong support onboard [--step <1-5>] [--reset] [--notes <text>] [--json]

# Feedback: submit NPS rating (0-10) or view aggregate report
mekong support feedback [--nps <0-10>] [--text <str>] [--category <product|pricing|perf|support>] [--report] [--json]

# Bug Reporting: submit structured bug report
mekong support bug "SQLite lock timeout under load" --severity high --desc "Worker failed with database locked" [--steps <str>] [--json]

# Smart Issue Triage: automated error diagnosis & escalation
mekong support triage "Error: 401 Unauthorized token expired during dispatch" [--json]

# Support Channels: display contact channels
mekong support contact [--json]
```

---

## Native MCP Tools

| MCP Tool | Description | Arguments |
|---|---|---|
| `mekong_support_onboard_status` | Query current onboarding milestones and progress | None |
| `mekong_support_feedback_submit` | Record customer satisfaction or NPS score | `nps_score: int, feedback_text: str = "", category: str = "general"` |
| `mekong_support_triage` | Analyze issue description and suggest resolution | `issue_text: str` |
