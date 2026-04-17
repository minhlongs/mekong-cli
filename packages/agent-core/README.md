# agent-core

Seed-phase agent kernel for the Mekong solo-platform.

Provides a minimal, dogfoodable BaseAgent with persistent memory (SQLite +
optional ChromaDB vector store), an LLM client that speaks Anthropic-compat
Messages API against `mekongd` (see `../mekongd/`), and a small tool registry
(browser, file_system, execute).

Maps to Phase 1 ("Hạt giống") of the DeepSeek solo-platform design. Forest /
multi-tenant primitives (gateway, worker pool, per-user isolation) land in a
separate package later.

## Install

```bash
cd packages/agent-core
poetry install                  # core only (SQLite memory)
poetry install --with vector    # adds ChromaDB for semantic recall
```

## Quickstart

```bash
# 1. mekongd must be running (see packages/mekongd/README.md)
export MEKONGD_URL=http://127.0.0.1:8765

# 2. Ask the CEO agent to plan + Developer to execute
poetry run agent-core run "Tạo một landing page giới thiệu dịch vụ AI consulting"
```

Outputs land in `./outputs/`. Memory lives in `~/.agent-core/`.

## Layout

```
src/agent_core/
├── memory.py        # SQLite + (optional) ChromaDB
├── llm_client.py    # Anthropic-compat client for mekongd
├── base_agent.py    # think → act → observe loop
├── cli.py           # typer entry point
├── agents/
│   ├── ceo.py
│   ├── developer.py
│   └── tool_agent.py
└── tools/
    ├── browser.py
    ├── file_system.py
    └── execute.py
```

All files are <200 LOC per project modularization rule.
