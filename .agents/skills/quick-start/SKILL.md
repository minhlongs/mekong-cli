---
name: quick-start
description: >-
  Start any new project from idea to production in 5 steps. Quick project kickoff.
---

# 🚀 Quick Start: New Project in 5 Steps

> **"Dễ như ăn kẹo!"** — Any project, 5 steps, done.

## The 5 Steps

```
1. Brainstorm    → Market positioning + SWOT + GO/NO-GO
2. Plan          → Implementation plan & Mermaid architecture PRD
3. Build         → Template scaffolding (CLI, Web, Agent, Fullstack)
4. Ship          → Git initialization + commit + test validation
5. Revenue       → Monetization roadmap + launch channels
```

## Detailed Flow

### Step 1: Brainstorm
- Generate 5-10 related ideas from the core concept
- Strategic analysis (SWOT, market fit)
- Target persona and confidence score

### Step 2: Plan & Architecture
- Generate structured PRD: `plans/plan.md`
- System architecture diagram (`mermaid`)
- 5-step milestone checklist

### Step 3: Build & Scaffold
- Automated archetype generation:
  - `agent`: Solo CEO Agentic Harness with SOPs and registry
  - `cli`: Python Typer/Rich CLI engine with tests and pyproject
  - `web`: Standard HTTP microservice and health probe
  - `fullstack`: Integrated web UI + backend + agent runner
- Pre-configured `tests/` and `.gitignore`

### Step 4: Verify & Ship
- Initialize git repository (`main` branch)
- Synthesize conventional initial commit
- Run initial verification test battery

### Step 5: Revenue & Monetization
- Pricing tiers (Free, Pro Solo, Enterprise)
- Go-to-market distribution channels
- 90-day MRR roadmap: `plans/revenue.md`

---

## CLI Invocation

```bash
# Kick off an autonomous agentic harness project
mekong quick-start my-agent --type agent

# Kick off a CLI tool with custom directory
mekong quick-start my-cli --type cli --dir ./tools/my-cli

# Simulate kickoff without disk writes
mekong quick-start prototype --dry-run

# Headless machine-readable JSON output for MCP/agent swarms
mekong quick-start saas-api --type web --json
```

## Native MCP Tools

- `mekong_quick_start_plan(project_name, project_type)`: Simulates and retrieves the 5-step kickoff blueprint without writing files.
- `mekong_quick_start_create(project_name, project_type, target_dir, dry_run)`: Executes full 5-step kickoff and returns the complete creation receipt.
