# AGENTS.md — Mekong CLI
# Read by: Claude Code, Gemini CLI, OpenCode, Cursor, Codex, Amp

## Project
AI-operated business platform. 6 layers, 300+ commands. BSL 1.1.
Universal LLM: 3 env vars (LLM_BASE_URL, LLM_API_KEY, LLM_MODEL), any provider.

## Commands
Commands live in `.claude/commands/*.md`. Execute via: `mekong <name> <args>`
Engine: Python CLI (Typer) → PEV orchestrator → LLM Router → Agent Layer

## Build & Test
```bash
pip install -e .           # Python CLI
pnpm install               # TypeScript packages
python3 -m pytest tests/   # Tests
mekong doctor check        # Health
```

## Style
Python: snake_case, type hints, < 200 lines. TypeScript: strict, ESM.
Commits: conventional (feat/fix/refactor/docs/test). No AI refs in messages.

## Architecture
Studio → Founder → Business → Product → Engineering → Ops
Water Protocol 水: multi-agent context flow between layers.

## AI OS (CheetahClaws)

### MCP Server
```bash
mekong ai-os start        # Start MCP server (port 8199)
mekong ai-os stop         # Stop server
mekong ai-os status       # Check health
```
Server entry in `.claude/mcp.json` as `mekong-ai-os` (stdio, venv-based).

### Tools (25, all prefixed `cc_`)
Memory: `cc_memory_search`, `cc_memory_consolidate`.
Tasks: `cc_tasks_list`, `cc_tasks_create`, `cc_tasks_done`, `cc_tasks_start`, `cc_tasks_delete`.
Agents: `cc_agents_list`, `cc_agents_start`, `cc_agents_stop`.
Skills: `cc_skills_list`.
MCP: `cc_mcp_list`.
Plugins: `cc_plugins_list`, `cc_plugins_install`.
Brainstorm (`cc_brainstorm`), Lab (`cc_lab_start`, `cc_lab_status`), Trading (`cc_trading_analyze`, `cc_trading_price`), Monitor (`cc_monitor_run`, `cc_monitor_status`), Plan (`cc_plan_start`, `cc_plan_list`, `cc_plan_done`), SSJ (`cc_ssj`).

### Adapters (`mekong/adapters/`)
`ai-os.sh` (AI OS entry point), `intent-router` (NL→command mapping), `mcp-bridge` (tool proxy), `health-check` (liveness probe), `provider-config` (LLM env setup), `registry.sh` (AI CLI registry).

### Provider Config
```bash
export LLM_BASE_URL=<url>   # Any OpenAI-compatible API
export LLM_API_KEY=<key>
export LLM_MODEL=<model>    # e.g. gpt-4, claude-3, deepseek
```
