# GEMINI.md — Mekong CLI Antigravity Rules
# Read by: Google Antigravity, Gemini CLI, Claude Code

## Project Overview
**Mekong CLI: CEO Solo Agentic Harness Engineering Platform.**
One CEO delegates to 4 layer agents (Business, Product, Engineering, Ops).
Embeds the Binh Pháp (Art of War) strategic execution framework for building, testing, and shipping.

## Antigravity Slash Commands (Skills)
All Mekong CLI workflows are mapped to native Antigravity skills in `.agents/skills/<name>/SKILL.md`:

| Command | Layer | Purpose |
|---------|-------|---------|
| `/cook` | Engineering | Feature development & plan execution (PEV engine) |
| `/idea` | Strategy | BizPlan OS Zero→IPO company generation |
| `/binh-phap` | Strategy | Strategic counsel via Sun Tzu agent |
| `/plan` | Product | Implementation planning (hard, fast, standard) |
| `/quick-start` | Product | 5-step project kickoff |
| `/ship` | Engineering | Lint → Test → Commit → Push → Deploy |
| `/daily` | Operations | Daily status report and git activity |
| `/cto` | Engineering | CTO architecture audit and review suite |
| `/ke-toan` | Business | VAS Vietnamese Accounting Standard & TT78 |
| `/thue` | Business | TNCN, TNDN, and GTGT tax calculation |
| `/zalo-oa` | Business | Zalo Official Account messaging & broadcast |
| `/sales` | Business | Lead outreach, deal prep, close reports |
| `/marketing`| Business | Content engine & growth campaigns |
| `/dev` | Engineering | Fullstack engineering commands |
| `/ops` | Operations | Incident response & system monitoring |

## Execution Protocols
- **CLI Invocations**: Execute via `mekong <group> <command> <args>`.
- **Safe Commands**: Commands annotated with `// turbo` can run without interactive confirmation.
- **High-Risk Gates**: Live deployments, financial changes >20%, and force-pushes require explicit user approval.
- **Context Budget**: Observe budget caps per role (CEO ≤ 30k, ENG ≤ 24k, PM ≤ 20k, OPS ≤ 16k).

## Subagent Dispatching
Mekong agent definitions live in `.agents/subagents/registry.json`. Use `define_subagent` and `invoke_subagent` to delegate to specialized roles (e.g., Sun Tzu, PM, QA, CTO).
