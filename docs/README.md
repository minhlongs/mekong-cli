# 📚 Mekong CLI Documentation Hub

Welcome to the official documentation for **Mekong CLI**, **Mekong IDE**, and **AgencyOS** products.

---

## 🏠 Project Overview

Mekong CLI is an autonomous multi-agent operational platform designed to **empower solo founders with a 10-layer AI agent workforce for $49/mo**. The core platform automates planning, software development, quality assurance, system operations, copy generation, and business workflows through structured agency protocols.

### Core Execution Loop: Plan-Execute-Verify (PEV)
Mekong CLI operates on a rigid **Plan-Execute-Verify (PEV)** cycle:
1. **Plan**: Natural language requests are parsed, mapping goals to Directed Acyclic Graphs (DAG) of discrete tasks.
2. **Execute**: The `DAGScheduler` runs steps concurrently or sequentially, routing execution to local system shells, local/cloud LLMs, or automated browser agents.
3. **Verify**: The validation engine evaluates execution outputs against quality gates and assertions, triggering self-healing recovery loops if a step fails.

---

## 👥 The 10-Layer Workforce

Our system organizes autonomous agents into 10 specialized operational layers:

1. **Founder**: Sets long-term vision, manages capital allocation, rebalances budgets, and governs core risk levels.
2. **Business**: Conducts market research, develops pricing structures, handles monetization strategies, and tracks customer acquisition costs.
3. **Product**: Creates Product Requirement Documents (PRDs), handles feature planning, and designs user feedback loops.
4. **Engineering**: Translates PRDs into concrete software designs, manages database schemas, and outlines system integrations.
5. **Ops (Operations)**: Monitors application health, coordinates alert handlers, and manages deployment infrastructure.
6. **Studio (Creative/Design)**: Designs UI layouts, styles user interfaces, and generates marketing and visual assets.
7. **CTO**: Manages technical debt, enforces coding standards, reviews system performance, and regulates backend architecture.
8. **PM (Project Manager)**: Tracks issue backlogs, maps task dependencies, and manages the team's Kanban board.
9. **Dev (Developer)**: Writes clean, minimal code, implements new features, and fixes bugs on target environments.
10. **Worker**: Performs atomic tasks, runs tests, triggers builds, and executes low-level shell actions.

---

## 🚀 Getting Started

### 1. Set Up Your System
Configure your environment using the [Developer Setup Guide](./setup-guide.md) to install Python 3.11, Node.js, and tmux.

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and fill in necessary LLM, database, and webhook credentials as documented in the [Environment Variables Guide](./env-vars.md).

### 3. Start Local Environment
```bash
# Start backend API server
make server

# Start dashboard UI
pnpm dev
```

---

## 💳 Pricing & Subscriptions

| Plan | Pricing | Core Target | Features |
| :--- | :--- | :--- | :--- |
| **Starter** | $49 / month | Solo Founders | 10-layer AI workforce, basic PEV loop execution, local LLM integrations. |
| **Growth** | $149 / month | Growing Startups | Parallel command runs, shared vector memory caches, cloud LLM fallback. |
| **Pro** | $499 / month | Scaleups & Agencies | Unlimited credits, custom agent templates, dedicated macOS node tunnels. |

---

## 🛟 Support & Community

For support and community discussions:

- **Email Support**: support@mekongmind.com (or visit [mekongmind.com/support](https://mekongmind.com/support))
- **Discord Server**: [Join our Discord community](https://discord.gg/mekongmind)
- **Twitter / X**: [@mekongmind](https://twitter.com/mekongmind)

---

## 📄 License & Terms

Mekong CLI is licensed under the Mekong Commercial License.
- ✅ Use in personal and commercial projects.
- ✅ Modify and customize codebase for internal business operations.
- ❌ Redistribute, resell, or white-label the core orchestrator without prior agreement.
- ❌ Share active license keys across unauthorized tenants.
