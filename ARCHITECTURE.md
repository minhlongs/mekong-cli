# 🏯 Unified Agent Architecture

> **Version**: v6.0.0 | **Date**: 2026-05-03
> **ClaudeKit-Engineer** + **Antigravity IDE** Unified Framework
> **Status**: PRODUCTION READY | Layered (global canon + project domain)

## Layering Decision (Option B, 2026-05-03)

ClaudeKit `~/.claude/` is the **canonical source** for stock primitives
(skills, agents, commands shipped by Anthropic). Mekong-CLI's `.claude/`
directory is **the domain layer** — RaaS, Sophia, marketing-bundles,
antigravity, claude-flow, products/, etc.

| Layer | Owns | Source of truth |
|-------|------|-----------------|
| 1. Stock primitives | 14 stock subagents (brainstormer, code-reviewer, code-simplifier, debugger, docs-manager, fullstack-developer, git-manager, journal-writer, mcp-manager, planner, project-manager, researcher, tester, ui-ux-designer); 1 stock skill bundle (`document-skills`) | `~/.claude/` |
| 2. Domain (Mekong) | ~493 unique skills, ~399 unique commands, antigravity, claude-flow, products/, factory/contracts/, clipmart/ | `~/mekong-cli/.claude/` |

Stock items previously duplicated in `~/mekong-cli/.claude/` were removed
on 2026-05-03. Same-name skills retained in mekong are **deliberate
overrides** — each must include a "Why-override" header in its
`SKILL.md`. See architecture-mapping report at:
`~/projects/sophia-ai-factory/plans/260503-0443-claudekit-mekong-architecture-mapping/architecture-mapping.md`

---

## 📁 Directory Structure

```
mekong-cli/
├── .claude/                    # ClaudeKit-Engineer (for Claude Code)
│   ├── agents/                 # 22 persona-based agents
│   ├── commands/               # 24 slash commands
│   ├── hooks/                  # Session & privacy hooks
│   ├── skills/                 # 39+ deep skill modules
│   └── settings.json           # Claude-specific config
│
├── .agent/                     # Antigravity IDE (for Gemini)
│   ├── subagents/              # 106 task-based subagents
│   │   ├── core/               # WIN3, orchestration (5)
│   │   ├── hubs/               # Department hubs (18)
│   │   ├── ops/                # Operations agents (34)
│   │   └── mekongAgent/        # Community imports (42)
│   ├── workflows/              # 40 agentic workflows
│   ├── skills/                 # Quick skills (6 categories)
│   └── crews/                  # Multi-agent crews
│
├── products/                   # 📦 Product Catalog
│   ├── vscode-starter-pack/    # $0 (Lead Magnet)
│   ├── ai-skills-pack/         # $27
│   ├── vietnamese-agency-kit/  # $67
│   ├── agencyos-pro/           # $197
│   └── agencyos-enterprise/    # $497
│
└── GEMINI.md                   # Shared memory (both read)
```

---

## 📦 Product Catalog

| Tier       | Product             | Price |
| ---------- | ------------------- | ----- |
| FREE       | VSCode Pack         | $0    |
| Basic      | AI Skills, Auth     | $27   |
| Pro        | AgencyOS Pro        | $197  |
| Enterprise | AgencyOS Enterprise | $497  |

**Total Catalog Value:** $916+

---

## 🔗 Synced Components

| Component       | Claude                                   | Gemini                                   | Status    |
| --------------- | ---------------------------------------- | ---------------------------------------- | --------- |
| **Binh Pháp**   | `.claude/agents/binh-phap-strategist.md` | `.agent/subagents/hubs/binh-phap-hub.md` | ✅ SYNCED |
| **WIN-WIN-WIN** | `GEMINI.md`                              | `GEMINI.md`                              | ✅ SHARED |
| **Data Diet**   | `GEMINI.md`                              | `GEMINI.md`                              | ✅ SHARED |

---

## 📊 Statistics

| Metric    | Claude | Gemini       | Total |
| --------- | ------ | ------------ | ----- |
| Agents    | 22     | 106          | 128   |
| Skills    | 39     | 6 categories | 45+   |
| Workflows | 24     | 40           | 64    |
| Products  | —      | —            | 15    |

---

## 🏯 Core Wisdom

> **"Bất chiến nhi khuất nhân chi binh"**
> Win without fighting - the highest form of victory.

---

_Unified Architecture by AgencyOS | v3.2.0 | January 19, 2026_
