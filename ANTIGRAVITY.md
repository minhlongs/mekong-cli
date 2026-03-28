# 🌌 Mekong CLI for Antigravity

> **Use the full power of Mekong CLI's 240+ commands on Antigravity AI — zero config required.**

Antigravity is a powerful AI coding assistant by Google DeepMind. This guide helps Antigravity users leverage Mekong CLI's 5-layer business platform directly from their IDE.

## Quick Start

```
# In Antigravity, just say:
"Read .agents/workflows/quick-start.md and execute for: my SaaS idea"
```

Or reference any workflow directly:

```
"/idea AI-powered restaurant management platform for Vietnam"
"/plan hard: add OAuth2 authentication"
"/cook build the landing page"
"/ship deploy to production"
"/daily"
```

## 📁 Workflow Files

All Antigravity-compatible workflows live in `.agents/workflows/`. These are adapted from the original `.claude/commands/` with Claude-specific features removed.

### 🏛 Layer 1: Founder / Strategy

| Workflow | Description |
|----------|-------------|
| [`idea.md`](.agents/workflows/idea.md) | BizPlan OS — Generate full company architecture (25-step, Zero→IPO) |
| [`studio.md`](.agents/workflows/studio.md) | VC Studio, Founder, and Venture analysis commands (23 sub-commands) |
| [`binh-phap.md`](.agents/workflows/binh-phap.md) | ⚔️ Strategic execution framework: plan → implement → verify → ship |

### 💼 Layer 2: Business / Revenue

| Workflow | Description |
|----------|-------------|
| [`sales.md`](.agents/workflows/sales.md) | Sales, SDR, Account Executive, and Dealflow (18 sub-commands) |
| [`marketing.md`](.agents/workflows/marketing.md) | Marketing, Growth, and Content Writer (20 sub-commands) |
| [`business.md`](.agents/workflows/business.md) | Business Ops, RaaS, Expert Network, Utilities (16 sub-commands) |

### 📦 Layer 3: Product

| Workflow | Description |
|----------|-------------|
| [`plan.md`](.agents/workflows/plan.md) | Implementation planning with 3 modes: hard, fast, standard |
| [`quick-start.md`](.agents/workflows/quick-start.md) | 5-step project kickoff: Brainstorm → Plan → Build → Ship → Revenue |
| [`context.md`](.agents/workflows/context.md) | Context prime, PRD generator, documentation, utilities (14 sub-commands) |

### ⚙️ Layer 4: Engineering

| Workflow | Description |
|----------|-------------|
| [`cook.md`](.agents/workflows/cook.md) | Smart feature implementation with modes: auto, fast, parallel |
| [`dev.md`](.agents/workflows/dev.md) | Dev, Engineering, Backend, Frontend, DevOps, Release (35 sub-commands) |
| [`dev-feature.md`](.agents/workflows/dev-feature.md) | Full feature development cycle |
| [`dev-bug-sprint.md`](.agents/workflows/dev-bug-sprint.md) | Bug fix sprint |
| [`code.md`](.agents/workflows/code.md) | TDD, CI runner, Code analysis (15 sub-commands) |
| [`git.md`](.agents/workflows/git.md) | Git operations: commit, PR, rebase, worktrees (10 sub-commands) |
| [`cto.md`](.agents/workflows/cto.md) | CTO command suite (13 sub-commands) |
| [`ship.md`](.agents/workflows/ship.md) | Ship to production: lint → test → commit → push → deploy |

### 🔧 Layer 5: Operations

| Workflow | Description |
|----------|-------------|
| [`ops.md`](.agents/workflows/ops.md) | Ops, PM, HR, Finance, Legal, Product, Design, UX (60+ sub-commands) |
| [`daily.md`](.agents/workflows/daily.md) | Daily status report with git activity |
| [`approve.md`](.agents/workflows/approve.md) | Approve pending items |
| [`command.md`](.agents/workflows/command.md) | Full directory of all 240+ commands |

## 🔄 How It Works

Mekong CLI commands are written as markdown instruction files. On Claude Code, they run from `.claude/commands/` with features like `$ARGUMENTS` and `allowed-tools`. On Antigravity, the same instructions are adapted in `.agents/workflows/` with:

| Claude Feature | Antigravity Equivalent |
|----------------|----------------------|
| `$ARGUMENTS` | User provides input in prompt |
| `allowed-tools` header | Antigravity auto-selects tools |
| `// turbo` annotation | ✅ Supported (auto-run safe commands) |
| Subagent spawning | Single-agent execution |
| DAG pipeline / recipes | Sequential workflow steps |
| OpenClaw daemon | Manual sequential execution |

Both systems run **side-by-side** — the original `.claude/commands/` (246 files) remain untouched.

## 🏯 Binh Pháp Framework

Mekong CLI embeds the Binh Pháp (Art of War) strategic framework throughout its command system:

```
/binh-phap plan       → 第一篇 始計 (Strategic Planning)
/binh-phap implement  → 第七篇 軍爭 (Parallel Execution)  
/binh-phap verify     → 第十一篇 九地 (Verification)
/binh-phap ship       → 第十二篇 火攻 (Deploy)
```

## 📊 Stats

- **21 workflow files** adapted for Antigravity
- **2,189 lines** of workflow instructions
- **240+ sub-commands** covered across 5 layers
- **0 files modified** in original codebase

## 🤝 Contributing

Want to add more Antigravity workflows? 

1. Fork this repo
2. Create a new `.md` file in `.agents/workflows/`
3. Use the YAML frontmatter format: `description: "your description"`
4. Submit a PR

### Workflow File Format

```markdown
---
description: "Short description of what this workflow does"
---

# /command-name — Human Readable Title

**AUTO-EXECUTE MODE.** Instructions for the AI.

## Steps

### Step 1: First Step
Instructions...

### Step 2: Second Step  
// turbo
\```bash
# Commands marked with // turbo run automatically
echo "safe command"
\```
```

## 📚 More Info

- [Mekong CLI Documentation](https://github.com/longtho638-jpg/mekong-cli)
- [Antigravity AI](https://antigravity.dev)
- **Built by:** Antigravity × Mekong CLI community

---

> 🏯 _"Thiên lý chi hành, thủy ư túc hạ"_  
> _A journey of a thousand miles begins with a single step_
