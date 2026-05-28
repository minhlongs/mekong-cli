# Project: System Audit and Refactoring Blueprint

## Architecture & Scope
The mission is to analyze mekong-cli's architecture, verify local model execution on Apple Silicon via Ollama, and design a production-grade architecture blueprint for a persistent autonomous organization.

## Milestones
| # | Name | Scope | Dependencies | Status | Conversation ID |
|---|------|-------|-------------|--------|-----------------|
| 1 | Deep System Audit | Audit all 11 layers of mekong-cli (reasoning, routing, coding swarm, orchestration, workflow graph, memory, tool, execution runtime, observability, persistence, agent communication). Identify bottlenecks, concurrency constraints, Apple Silicon memory pressure, and token waste. | None | DONE | 54e577f7-0958-459d-b625-34dbe4d98550 |
| 2 | Live Verification | Inspect CheetahClaws codebase, check Ollama server status/throughput, and run `tests/bench_coding.py` under local model execution (demo integrity mode). Document outputs, error tracebacks, and success rates. | None | IN_PROGRESS | 577f0841-efc6-4d27-8a13-d17b020cd4af |
| 3 | Production Redesign | Design system design specification (model roles, routing policies, local stack Ollama vs. llama.cpp vs. MLX, LangGraph supervisor topology, SQLite/Redis memory layout). | 1, 2 | PLANNED | TBD |
| 4 | Synthesis & Handoff | Synthesize findings into handoff.md under /Users/macbook/mekong-cli/.agents/orchestrator_system_audit/handoff.md. | 3 | PLANNED | TBD |

## Interface Contracts & Guidelines
- All observations and analysis must be evidence-backed (direct file paths, run outputs, error tracebacks).
- Local model execution uses Ollama at `http://localhost:11434`.
- CheetahClaws codebase is located at `/Users/macbook/.local/share/uv/tools/cheetahclaws/lib/python3.14/site-packages`.
