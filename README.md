# 🌊 Mekong CLI - RaaS Agency Operating System

<div align="center">

![MAX WOW](https://img.shields.io/badge/MAX-WOW-8b5cf6?style=for-the-badge&logo=sparkles&logoColor=white)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)
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
poetry install
cd frontend && npm install

# Start development servers
npm run dev  # Runs API + Frontend concurrently

# Execute a recipe
mekong run "implement user authentication"
mekong cook recipes/deploy-api.md
```

---

## 📦 Architecture

```
mekong-cli/
├── src/core/              # Plan-Execute-Verify engine
│   ├── planner.py         # 謀 Task decomposition
│   ├── executor.py        # 執 Multi-mode runner
│   ├── verifier.py        # 證 Result validation
│   └── orchestrator.py    # 統 Workflow coordination
├── _bmad/                 # 169 workflows + 9 agents
├── packages/              # Monorepo hub structure
│   ├── core/              # Foundation (vibe, agents, shared)
│   ├── integrations/      # Connectors (bridge, CRM)
│   ├── tooling/           # Dev tools (analytics, dev)
│   ├── business/          # Revenue (money, ops, marketing)
│   └── ui/                # Components (vibe-ui, i18n)
├── apps/                  # Product applications
│   ├── agencyos-landing/  # Main landing page
│   ├── sophia-ai-factory/ # AI product showcase
│   ├── api/               # FastAPI revenue backend
│   └── ...                # Additional apps
└── automation/            # Revenue automation scripts
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
