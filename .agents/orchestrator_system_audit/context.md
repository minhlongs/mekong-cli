# Mission Context: System Audit and Refactoring Blueprint

## Objectives
1. Perform deep system audit of all 11 layers of mekong-cli AI stack.
2. Verify local inference on Ollama (port 11434) and benchmark tests/bench_coding.py in demo integrity mode.
3. Redesign production architecture (Ollama vs llama.cpp vs MLX, LangGraph supervisor, SQLite/Redis memory layout).

## Constraints
- Run audit and benchmarks using specialized subagents.
- Write handoff.md under /Users/macbook/mekong-cli/.agents/orchestrator_system_audit/handoff.md.
- Ensure strict zero code modifications to production source code during the audit.
