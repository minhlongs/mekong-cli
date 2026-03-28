---
description: "List all available mekong-cli commands organized by layer (Founder/Business/Product/Engineering/Ops). Replacement for /commands-status on Antigravity."
---

# /command — Mekong CLI Command Directory

Lists all available commands from the mekong-cli command system, organized by 5-layer hierarchy.

## How to Use

When a user asks `/command` or wants to see available commands:

1. Read the command files from `.claude/commands/` directory
2. Present them organized by the 5-layer structure below
3. For any specific command, read its `.md` file and follow the instructions

## 5-Layer Command Map

### 🏛️ Layer 1: Founder / Studio

| Command | Description |
|---------|-------------|
| `/idea` | Generate full company architecture from business idea (25-step BizPlan OS) |
| `/studio-strategy` | Studio-level strategy planning |
| `/studio-portfolio` | Portfolio management |
| `/studio-bootstrap` | Bootstrap new venture |
| `/studio-invest` | Investment analysis |
| `/studio-divest` | Divestment planning |
| `/studio-audit` | Studio audit |
| `/studio-report` | Studio reporting |
| `/studio-roi` | ROI analysis |
| `/studio-allocate` | Resource allocation |
| `/studio-launch-full` | Full launch sequence |
| `/studio-operate-daily` | Daily operations |
| `/studio-sprint-weekly` | Weekly sprint |
| `/studio-diligence-deep` | Deep due diligence |
| `/founder-raise` | Fundraising workflow |
| `/founder-negotiate` | Negotiation playbook |
| `/founder-validate` | Idea validation |
| `/founder-ipo` | IPO preparation |
| `/venture-*` | Venture analysis (five-factors, terrain, thesis, momentum, void-substance) |

### 💼 Layer 2: Business / Revenue

| Command | Description |
|---------|-------------|
| `/sales-pipeline-build` | Build sales pipeline |
| `/sales-deal-close` | Close deals |
| `/sales-weekly-review` | Weekly sales review |
| `/sdr-prospect` | SDR prospecting |
| `/sdr-outreach-blast` | Outreach campaigns |
| `/sdr-lead-qualify` | Lead qualification |
| `/marketing-campaign-run` | Run marketing campaigns |
| `/marketing-content-engine` | Content marketing engine |
| `/marketing-performance-report` | Marketing analytics |
| `/ck-marketing-*` | ClaudeKit marketing (ads, copy, cro, growth, local, seo) |
| `/business-*` | Business ops (campaign-launch, client-onboard, financial-close, hiring-sprint, quarterly-review, revenue-engine) |
| `/growth-*` | Growth (channel-optimize, experiment) |
| `/accounting-*` | Accounting (daily, invoice-batch) |
| `/ae-*` | Account executive (close-report, deal-prep, follow-up) |
| `/finance-*` | Finance (budget-plan, collections, monthly-close) |

### 📦 Layer 3: Product

| Command | Description |
|---------|-------------|
| `/product-sprint-plan` | Sprint planning |
| `/product-discovery` | Product discovery |
| `/product-launch-feature` | Feature launch |
| `/product-competitive-intel` | Competitive intelligence |
| `/product-retrospective` | Sprint retrospective |
| `/pm-*` | PM tools (backlog, delegate, milestone, okr, plan, retro, scope, sprint, standup) |
| `/design-sprint` | Design sprint |
| `/design-user-research` | User research |
| `/ui-*` | UI design (component, review) |
| `/ux-*` | UX research (interview, usability) |

### ⚙️ Layer 4: Engineering

| Command | Description |
|---------|-------------|
| `/plan` | Create implementation plan |
| `/dev-feature` | Build new feature |
| `/dev-bug-sprint` | Bug fix sprint |
| `/dev-pr-review` | PR code review |
| `/dev-refactor` | Code refactoring |
| `/dev-scaffold` | Scaffold new module |
| `/dev-audit` | Code audit |
| `/dev-debug` | Debug issues |
| `/dev-deploy` | Deploy code |
| `/cto-*` | CTO tools (architect, dashboard, deploy, health, incident, observability, onboard, review, roadmap, scorecard, selftest, team, workforce) |
| `/tech-*` | Tech (api-design, architecture-review, migration) |
| `/ship` | Ship release |
| `/release-*` | Release mgmt (ship, hotfix) |
| `/releng-*` | Release engineering (pre-release, post-release) |
| `/backend-*` | Backend (api-build, db-task) |
| `/frontend-*` | Frontend (ui-build, responsive-fix) |
| `/devops-*` | DevOps (deploy-pipeline, rollback) |
| `/worker-*` | Worker tasks (build, code, commit, exec, health, log, push, rollback, scan, test, trace, backup) |

### 🔧 Layer 5: Ops / Support

| Command | Description |
|---------|-------------|
| `/ops-health-sweep` | System health check |
| `/ops-sync-all` | Sync all systems |
| `/ops-security-audit` | Security audit |
| `/ops-disaster-recovery` | DR planning |
| `/sre-morning-check` | SRE morning check |
| `/sre-incident` | Incident response |
| `/hr-*` | HR (onboard, recruit, performance-cycle) |
| `/people-*` | People ops (onboard, offboard) |
| `/legal-*` | Legal (compliance-check, contract-review) |
| `/analyst-*` | Analytics (report, forecast-update) |
| `/writer-*` | Content (blog, newsletter, social-batch) |
| `/daily` | Daily standup |
| `/cloudflare` | Cloudflare management |

### 🔗 Cross-Layer / Meta

| Command | Description |
|---------|-------------|
| `/bridge` | Unified bridge for all CLI tools |
| `/antibridge` | Antigravity AI agent control |
| `/gemini` | Gemini CLI integration |
| `/commands-status` | Command health dashboard (Claude-only) |
| `/quick-start` | Quick start guide |
| `/production-status` | Production status check |
| `/project-matrix` | Project matrix overview |
| `/model-matrix` | AI model matrix |
| `/factory-intelligence` | Factory intelligence report |
| `/ck-binh-phap` | Binh Phap strategy |

## Usage on Antigravity

To use any command on Antigravity:

1. **Find the command** in the table above
2. **Tell Antigravity**: "Read `.claude/commands/<command-name>.md` and execute it"
3. **Provide context**: Give the business/technical context as your prompt

### Example

```
Read .claude/commands/dev-feature.md and execute it for: 
"Add user authentication with JWT to the API"
```

## Notes

- Commands marked with `*` have multiple sub-commands (e.g., `/cto-*` = cto-architect, cto-dashboard, etc.)
- Some commands reference Claude-specific features (OpenClaw, Factory Loop) — these parts are skipped on Antigravity
- The core instructions in each command `.md` file work as AI-agnostic prompts
