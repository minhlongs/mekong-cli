# Mekong Dev Shop

> Engineering-focused AI agency template — 8 specialized agents.

A software development agency template for teams that ship code professionally —
with dedicated agents for SRE, security, QA, DevOps, and project management.

---

## The 8 Agents

| Agent | Role | Team | Reports To | Budget |
|-------|------|------|-----------|--------|
| **cto** | Chief Technology Officer | engineering | board | 400 MCU/mo |
| **vp-engineering** | VP Engineering | engineering | cto | 400 MCU/mo |
| **sre-lead** | SRE Lead | engineering | cto | 200 MCU/mo |
| **security-lead** | Security Lead | engineering | cto | 200 MCU/mo |
| **qa-lead** | QA Lead | engineering | vp-engineering | 200 MCU/mo |
| **devops-lead** | DevOps Lead | engineering | cto | 200 MCU/mo |
| **tech-lead** | Tech Lead | engineering | vp-engineering | 300 MCU/mo |
| **project-manager** | Project Manager | engineering | vp-engineering | 200 MCU/mo |

Total monthly budget: **2,100 MCU/mo**

---

## Org Chart

```
board
  └── cto (九變 — Nine Variations)
        ├── vp-engineering (軍爭 — Military Contention)
        │     ├── qa-lead (謀攻 — Attack by Stratagem)
        │     ├── tech-lead (兵勢 — Momentum)
        │     └── project-manager (始計 — Laying Plans)
        ├── sre-lead (行軍 — Army on March)
        ├── security-lead (九變 — Nine Variations)
        └── devops-lead (軍形 — Disposition)
```

---

## Quick Start

```bash
# Install via Paperclip CLI
paperclip company install mekong-dev-shop

# Or clone manually
git clone https://github.com/longtho638-jpg/mekong-cli
cd mekong-cli/clipmart/mekong-dev-shop
paperclip company init .

# Launch your dev shop
mekong company/start
```

---

## Agent Roles

### CTO — Chief Technology Officer
Owns architecture decisions, technology strategy, team structure, and system health.
Governs all engineering agents. Reports to board.

### VP Engineering
Runs day-to-day engineering: sprints, deployments, tech debt, and developer onboarding.
Manages qa-lead, tech-lead, and project-manager.

### SRE Lead
Owns observability: metrics, alerts, logs, traces, dashboards.
Ensures production reliability and incident response.

### Security Lead
Runs security audits, vulnerability scans, penetration tests, compliance reports, access reviews.
Partners with DevOps on hardening.

### QA Lead
Owns automated testing, regression suites, performance benchmarks, and QA reports.
Gates every release.

### DevOps Lead
Owns CI/CD pipelines, infrastructure provisioning, monitoring, and auto-scaling.
Partners with SRE on production operations.

### Tech Lead
Drives technical implementation: cooking features, code review, refactoring, architecture alignment.

### Project Manager
Owns roadmap, backlog grooming, sprint planning, daily standups, and retrospectives.

---

## Skills Included

```
cook                — AI-assisted full feature implementation
code                — Code implementation
test                — Automated testing
deploy              — CI/CD deployment
review              — Code review
refactor            — Code refactoring
sprint              — Sprint planning and execution
daily               — Daily standup
obs-metrics         — Observability metrics
obs-alerts          — Alert configuration and triage
sec-audit           — Security audit
sec-scan            — Vulnerability scanning
ci-status           — CI/CD pipeline status
architecture-review — Architecture review and ADRs
```

---

## Binh Pháp Governance

| Agent | Chapter | Principle |
|-------|---------|-----------|
| cto | 九變 — Nine Variations | Adapt strategy to every situation |
| vp-engineering | 軍爭 — Military Contention | Contend for velocity advantage |
| sre-lead | 行軍 — Army on March | Know the terrain (production) |
| security-lead | 九變 — Nine Variations | Anticipate every variation of attack |
| qa-lead | 謀攻 — Attack by Stratagem | Winning without defects |
| devops-lead | 軍形 — Disposition | Position infrastructure for victory |
| tech-lead | 兵勢 — Momentum | Build unstoppable engineering momentum |
| project-manager | 始計 — Laying Plans | Plan meticulously before executing |

---

## Upgrade Path

For a full company (sales, marketing, finance, legal + engineering):
- **[mekong-saas-startup](../mekong-saas-startup)** — Full 22-department company

For a leaner solo setup:
- **[mekong-solo-founder](../mekong-solo-founder)** — 5 essential agents

---

## License

MIT — see [LICENSE](LICENSE)

Built by [Binh Phap Venture Studio](https://agencyos.network)
