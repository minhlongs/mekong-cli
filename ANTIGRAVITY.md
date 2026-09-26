# 🌌 Mekong CLI for Google Antigravity

> **Use the full power of Mekong CLI's 240+ commands and multi-agent harness on Google Antigravity — zero config required.**

Antigravity is Google DeepMind's advanced AI coding assistant and agentic development platform. This integration exposes Mekong CLI's complete 5-layer business platform and harness multi-agent system directly into Antigravity via **native Skills (`.agents/skills/`)**, **Subagents (`.agents/subagents/`)**, and **Rules (`GEMINI.md`)**.

---

## ⚡ Quick Start: Native Slash Commands

In Antigravity's chat, simply type any slash command:

```text
/cook "implement user profile modal with avatar upload"
/binh-phap "phân tích chiến lược mở rộng thị trường SME"
/idea "nền tảng đặt bàn và quản lý nhà hàng thông minh"
/ke-toan "lập hóa đơn điện tử TT78 và bút toán VAS"
/thue "tính thuế TNCN lũy tiến cho lương net 50 triệu"
/zalo-oa "gửi thông báo cập nhật đơn hàng qua Zalo"
/ship "production deploy"
/daily
```

Antigravity automatically discovers all skills in `.agents/skills/` via **progressive disclosure**:
- Skill names and descriptions are injected into the agent context for instant routing.
- The full procedure, guidelines, and safe bash execution blocks (`// turbo`) are loaded on demand.

---

## 📁 Native Skills Layer (`.agents/skills/`)

All workflows are standardized into `.agents/skills/<name>/SKILL.md`:

### 🏛 Layer 1: Founder / Strategy

| Skill | Slash Command | Description |
|-------|---------------|-------------|
| [`binh-phap`](.agents/skills/binh-phap/SKILL.md) | `/binh-phap` | ⚔️ Strategic execution framework: plan → implement → verify → ship |
| [`idea`](.agents/skills/idea/SKILL.md) | `/idea` | BizPlan OS — Generate full company architecture (25-step, Zero→IPO) |
| [`studio`](.agents/skills/studio/SKILL.md) | `/studio` | VC Studio, Founder, and Venture analysis commands |

### 💼 Layer 2: Business / Revenue & Vietnam Funnels

| Skill | Slash Command | Description |
|-------|---------------|-------------|
| [`ke-toan`](.agents/skills/ke-toan/SKILL.md) | `/ke-toan` | VAS Vietnamese Accounting Standard & TT78/2021 electronic invoices |
| [`thue`](.agents/skills/thue/SKILL.md) | `/thue` | Thuế TNCN lũy tiến, TNDN chuẩn 20%, và thuế GTGT |
| [`zalo-oa`](.agents/skills/zalo-oa/SKILL.md) | `/zalo-oa` | Zalo Official Account messaging, broadcast, followers, and captioning |
| [`sales`](.agents/skills/sales/SKILL.md) | `/sales` | Sales, SDR, Account Executive, and Dealflow workflows |
| [`marketing`](.agents/skills/marketing/SKILL.md) | `/marketing` | Marketing campaigns, growth strategies, and content engine |
| [`business`](.agents/skills/business/SKILL.md) | `/business` | Business Ops, RaaS, and Expert Network operations |

### 📦 Layer 3: Product

| Skill | Slash Command | Description |
|-------|---------------|-------------|
| [`plan`](.agents/skills/plan/SKILL.md) | `/plan` | Implementation planning with modes: hard, fast, standard |
| [`quick-start`](.agents/skills/quick-start/SKILL.md) | `/quick-start` | 5-step project kickoff: Brainstorm → Plan → Build → Ship → Revenue |
| [`context`](.agents/skills/context/SKILL.md) | `/context` | Context primer, PRD generator, and spec management |

### ⚙️ Layer 4: Engineering

| Skill | Slash Command | Description |
|-------|---------------|-------------|
| [`cook`](.agents/skills/cook/SKILL.md) | `/cook` | Smart feature implementation with modes: auto, fast, parallel |
| [`dev`](.agents/skills/dev/SKILL.md) | `/dev` | Fullstack engineering commands (backend, frontend, devops) |
| [`dev-feature`](.agents/skills/dev-feature/SKILL.md) | `/dev-feature` | Complete feature development cycle |
| [`dev-bug-sprint`](.agents/skills/dev-bug-sprint/SKILL.md) | `/dev-bug-sprint` | Fast bug hunt and regression resolution |
| [`code`](.agents/skills/code/SKILL.md) | `/code` | TDD, CI test runner, and code analysis |
| [`git`](.agents/skills/git/SKILL.md) | `/git` | Git operations: atomic commits, rebase, worktree management |
| [`cto`](.agents/skills/cto/SKILL.md) | `/cto` | CTO architecture audit and quality governance suite |
| [`ship`](.agents/skills/ship/SKILL.md) | `/ship` | Ship to production: lint → test → commit → push → deploy |

### 🔧 Layer 5: Operations & Complete Catalog

| Skill | Slash Command | Description |
|-------|---------------|-------------|
| [`ops`](.agents/skills/ops/SKILL.md) | `/ops` | Ops, PM, HR, Finance, Legal, and System Monitoring |
| [`daily`](.agents/skills/daily/SKILL.md) | `/daily` | Daily standup summary and git activity report |
| [`approve`](.agents/skills/approve/SKILL.md) | `/approve` | High-risk gate review and approval management |
| [`command`](.agents/skills/command/SKILL.md) | `/command` | Full directory of 190+ Mekong CLI commands |

---

## 🤖 Antigravity Subagent System (`.agents/subagents/`)

Mekong CLI's CEO Solo Harness defines 13 specialized roles and 12+ auxiliary agents, now exported to Antigravity:

| Agent ID | Role | Model Tier | Override | Context Cap |
|----------|------|------------|----------|-------------|
| `ceo` | Chief Executive Officer | `pro` | **YES** | 30,000 tok |
| `sun-tzu` | Strategic Counsel | `pro` | NO | 30,000 tok |
| `ae` | Account Executive (BD) | `inherit` | NO | 16,000 tok |
| `pm` | Product Manager | `inherit` | NO | 20,000 tok |
| `eng` | Engineer | `inherit` | NO | 24,000 tok |
| `ops` | Operations & Observability | `inherit` | NO | 16,000 tok |
| `tester` | Quality Assurance (QA) | `inherit` | NO | 16,000 tok |
| `cto` | Chief Technology Officer | `pro` | NO | 24,000 tok |
| `cmo` | Chief Marketing Officer | `inherit` | NO | 20,000 tok |
| `coo` | Chief Operating Officer | `inherit` | NO | 16,000 tok |
| `cfo` | Chief Financial Officer | `inherit` | NO | 16,000 tok |
| `cso` | Chief Strategy Officer | `inherit` | NO | 16,000 tok |
| `planner` | Tech Lead Planner | `pro` | NO | 20,000 tok |

### Inspecting & Bootstrapping Subagents

Use the subagent helper:

```bash
# List all 25 registered subagents
python3 scripts/antigravity_agent_loader.py --list

# Get define_subagent payload for an agent (e.g. ceo)
python3 scripts/antigravity_agent_loader.py --get ceo
```

---

## 🔄 Synchronization & Maintenance

Keep Antigravity skills, subagents, and rules in sync with one command:

```bash
# Full sync & validation
python3 scripts/sync_antigravity.py --all

# Audit & verify conformance
python3 scripts/sync_antigravity.py --verify
```

---

## 🏯 Binh Pháp Framework in Antigravity

Mekong CLI's Binh Pháp framework operates seamlessly inside Antigravity:

```text
/binh-phap plan       → 第一篇 始計 (Strategic Planning)
/binh-phap implement  → 第七篇 軍爭 (Parallel Execution)  
/binh-phap verify     → 第十一篇 九地 (Objective Verification)
/binh-phap ship       → 第十二篇 火攻 (Production Deploy)
```

> 🏯 _"Thiên lý chi hành, thủy ư túc hạ"_  
> _A journey of a thousand miles begins with a single step_
