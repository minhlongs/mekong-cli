# Phase B4: Memory Bridge (Steps 11-14)

## Goal
Unified memory interface across all 7 memory modules.

## Current Landscape
- `seed/memory.py` — SQLite-backed, agent-scoped, works
- `core/memory*.py` (3 files) — legacy, undefined API
- `mekongcli/core/memory/backends.py` — MemoryBackend protocol exists
- `harness/pev/memory.py` — MemoryStore stub
- `vector_memory_store.py` — optional qdrant/mem0ai

## Implementation
1. **Create `src/core/memory_bridge.py`** with clean interface:
   ```python
   class MemoryBridge:
       def remember(self, agent_id: str, content: str, metadata: dict) -> str
       def recall(self, query: str, k: int = 5) -> list[dict]
       def clear(self, agent_id: str = None)
       def search(self, query: str, limit: int = 10) -> list[dict]
   ```
2. **Refactor `seed/memory.py`** → implement `MemoryBridge` (already SQLite-backed)
3. **Wire `harness/pev/memory.py`** → delegate to bridge
4. **Wire `vector_memory_store.py`** → as optional backend (qdrant if available, fallback SQLite)
5. **Delete/consolidate** `core/memory*.py` if unused

## Verification
- All memory operations go through `MemoryBridge` interface
- `seed` agents continue to work (backward compat)
- PEV pipeline can `remember()` and `recall()` execution history
- SQLite fallback works without qdrant installed

## Risk: HIGH (7 modules affected, careful backward compat)
