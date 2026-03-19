# AGENTS.md — Mekong CLI Universal Configuration
# Read by: Claude Code, Gemini CLI, OpenCode, Cursor, Codex, Amp
# Ref: https://agents.md

## Project Overview
Mekong CLI — AI-operated business platform. 6 layers, 300+ commands.
Open source (BSL 1.1). Universal LLM (3 vars, any provider).

## Commands
All mekong commands are in `.claude/commands/*.md` format.
To execute any command: `mekong <command-name> <arguments>`
Engine routes to Python CLI → PEV orchestrator → LLM.

## Code Style
- Python: snake_case, type hints required, < 200 lines per file
- TypeScript: camelCase, strict mode, ESM imports
- Commits: conventional format (feat/fix/refactor/docs/test)
- Tests: pytest (Python), vitest (TypeScript)

## Build & Test
```bash
pip install -e .          # Python CLI
pnpm install              # TypeScript packages
python3 -m pytest tests/  # Run tests
mekong doctor check       # Health check
```

## Architecture
```
CLI (mekong cook/fix/plan) → API Gateway → PEV Engine → Agent Layer → LLM Router
```
6 Layers: Studio → Founder → Business → Product → Engineering → Ops
