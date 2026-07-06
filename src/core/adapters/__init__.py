"""Memory bridge adapters package.

Provides bridge implementations for each backend:
- SeedBridge   → src.seed.memory (SQLite)
- MemoryStoreBridge → src.core.memory (YAML + vector)
- ScopedBridge → src.core.memory_scope (in-memory, scoped)
- PevBridge    → src.harness.pev.memory (in-memory dict)
"""
