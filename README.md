# 🌊 Mekong CLI - RaaS Agency Operating System

<div align="center">

![v0.2.0](https://img.shields.io/badge/v0.2.0-release-22c55e?style=for-the-badge)
![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)
![TypeScript](https://img.shields.io/badge/TypeScript-5.0+-3178C6?style=for-the-badge&logo=typescript&logoColor=white)
![Binh Pháp](https://img.shields.io/badge/Binh_Pháp-兵法-ec4899?style=for-the-badge&logo=military-tech&logoColor=white)

**Revenue-First Architecture Powered by ClaudeKit DNA + Binh Pháp Framework**

[🚀 Quick Start](#-quick-start) • [📦 Architecture](#-architecture) • [🎯 Features](#-features) • [📚 Documentation](#-documentation)

</div>

---

## ✨ Features

### 🧠 **Plan-Execute-Verify Engine**
- LLM-powered task decomposition with `RecipePlanner`
- Multi-mode execution (shell/LLM/API) via `RecipeExecutor`
- Automated verification with rollback capabilities
- Exponential backoff retry logic
- Unified LLM client (OpenAI-compatible, Antigravity Proxy)

### 🍳 **CLI Commands**
```bash
mekong cook "deploy auth system"   # Plan → Execute → Verify (full pipeline)
mekong plan "add payment flow"     # Generate plan only (no execution)
mekong run recipes/deploy-api.md   # Execute existing recipe file
mekong agent git status            # Run agent directly
mekong agent file stats            # Project file statistics
```

### 🤖 **Built-in Agents**
| Agent | Purpose |
|-------|---------|
| `GitAgent` | Git operations (status, diff, commit, branch) |
| `FileAgent` | File search, read, tree, stats, grep |
| `LeadHunter` | CEO lead discovery |
| `ContentWriter` | Content generation |
| `RecipeCrawler` | Recipe discovery |

### 🏗️ **Hub Architecture**
Monorepo with logical layer separation:
- **Core** - Foundation SDKs (vibe, agents, shared)
- **Integrations** - External connectors (bridge, CRM)
- **Tooling** - Developer utilities (dev, analytics)
- **Business** - Revenue logic (money, ops, marketing)
- **UI** - Interface components (vibe-ui, i18n)

### 🤖 **169 BMAD Workflows**
Pre-built agent workflows from BMAD Method:
- `/product-brief` - Scope definition
- `/create-prd` - Requirements engineering
- `/create-architecture` - System design
- `/dev-story` - Implementation with QA

### ⚡ **Agent Teams Integration**
Parallel execution with Claude Code CLI:
- Automatic spawning (FE + BE + Debug + Review)
- Shared task list coordination
- Plan-driven delegation

---

## 🚀 Quick Start

```bash
# Install dependencies
pip install typer rich pydantic

# Plan a task (generates steps, no execution)
mekong plan "implement user authentication"

# Cook: full Plan → Execute → Verify pipeline
mekong cook "deploy API with rate limiting"

# Execute a recipe file
mekong run recipes/deploy-api.md

# Use agents directly
mekong agent git status
mekong agent file stats
```

---

## 📦 Architecture

```
mekong-cli/
├── src/core/              # Plan-Execute-Verify engine
│   ├── planner.py         # 謀 Task decomposition
│   ├── executor.py        # 執 Multi-mode runner
│   ├── verifier.py        # 證 Result validation
│   ├── orchestrator.py    # 統 Workflow coordination
│   ├── llm_client.py      # 🤖 Unified LLM client
│   └── agent_base.py      # Base class (Plan-Execute-Verify)
├── src/agents/            # Built-in agents
│   ├── git_agent.py       # Git operations
│   ├── file_agent.py      # File system operations
│   ├── lead_hunter.py     # Lead discovery
│   └── content_writer.py  # Content generation
├── _bmad/                 # 169 workflows + 9 agents
├── apps/                  # Product applications
│   ├── raas-gateway/      # Cloudflare Worker gateway
│   ├── agencyos-landing/  # Main landing page
│   └── openclaw-worker/   # OpenClaw bridge
└── tests/                 # Test suite
```

---

## 🎯 Tech Stack

### Backend
- **Python 3.11+** with Poetry
- **FastAPI** for API layer
- **Typer** for CLI commands
- **Rich** for terminal UI
- **Pydantic** for type safety

### Frontend
- **Next.js 16** with App Router
- **TypeScript 5.0+**
- **Tailwind CSS 4.0**
- **Framer Motion** for animations
- **Glassmorphism** design system

### AI & Orchestration
- **Claude 3.5 Sonnet** via Anthropic API
- **Gemini Pro** integration
- **Agent Teams** coordination
- **BMAD Method** workflows

---

## 🏯 Binh Pháp Quality Gates

Every recipe execution enforces quality standards:

| Gate | Criterion | Verification |
|------|-----------|--------------|
| 始計 (Tech Debt) | 0 TODOs/FIXMEs | `grep -r "TODO\|FIXME" src` |
| 作戰 (Type Safety) | 0 `any` types | `grep -r ": any" src` |
| 謀攻 (Performance) | Build < 10s | `time npm run build` |
| 軍形 (Security) | 0 high vulns | `npm audit --audit-level=high` |
| 兵勢 (UX) | Loading states | Manual review |
| 虛實 (Documentation) | Updated docs | Git diff check |

---

## 📚 Documentation

- **[CLAUDE.md](./CLAUDE.md)** - Binh Pháp rules for AI agents
- **[docs/](./docs/)** - Project documentation
- **[packages/](./packages/)** - Package-specific READMEs
- **[_bmad/](._bmad/)** - BMAD workflow catalog

---

## 🎨 Visual Design System

### Glassmorphism Classes
```css
.glass-card {
  @apply bg-white/10 backdrop-blur-xl border border-white/20 shadow-2xl;
}
```

### Dark Mode Palette
- Background: `#0a0a0f`
- Surface: `#13131a`
- Accent: `#8b5cf6` (Purple), `#ec4899` (Pink)

### Typography
- **Headings**: Inter Display
- **Body**: Inter
- **Code**: JetBrains Mono

---

## 🤝 Contributing

This is an open-core project. See our [contribution guidelines](./CONTRIBUTING.md).

---

## 📄 License

MIT License - See [LICENSE](./LICENSE)

---

<div align="center">

**Built with 🏯 Binh Pháp Principles**

*"Bất chiến nhi khuất nhân chi binh" - Win without fighting*

[AgencyOS](https://agencyos.dev) • [Documentation](./docs/) • [BMAD Method](./_bmad/)

</div>
