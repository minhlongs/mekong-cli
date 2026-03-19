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
