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

### Tools (24)
Memory: mem_store, mem_search, mem_recent, mem_stats. Tasks: task_create, task_list, task_status, task_update. Agents: agent_spawn, agent_list, agent_kill. Skills: skill_load, skill_list, skill_search. MCP: mcp_list, mcp_call, mcp_health. Plugins: plugin_install, plugin_list, plugin_remove. Brainstorm, Lab (sandbox), Trading (paper), Monitor (metrics), Plan (decompose), SSJ (supervisor).

### Adapters (`mekong/adapters/`)
`ai-os.sh` (AI OS entry point), `intent-router` (NL→command mapping), `mcp-bridge` (tool proxy), `health-check` (liveness probe), `provider-config` (LLM env setup), `registry.sh` (AI CLI registry).

### Provider Config
```bash
export LLM_BASE_URL=<url>   # Any OpenAI-compatible API
export LLM_API_KEY=<key>
export LLM_MODEL=<model>    # e.g. gpt-4, claude-3, deepseek
```
