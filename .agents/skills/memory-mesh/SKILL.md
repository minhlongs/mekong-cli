---
name: memory-mesh
description: >-
  🕸️ Federated Memory Mesh — index codebase symbols, view memory telemetry, and query knowledge graph.
---

# /memory-mesh — Federated Memory Mesh & Knowledge Graph

Manages the federated memory subsystem, scans codebase AST symbols, builds
relational knowledge graphs, and inspects memory health statistics.

## Usage

```bash
# Index codebase entities, historical ballots, and execution patterns
mekong memory-mesh index
mekong memory-mesh index --json

# View health, item counts, and domain distribution
mekong memory-mesh stats
mekong memory-mesh stats --json

# Traverse knowledge graph relationships around a class, function, or file
mekong memory-mesh graph ConsensusBridge --depth 2
mekong memory-mesh graph "src/core/consensus_bridge.py" --json
```

## Features

1. **Automated AST Indexing**:
   - Walks Python files and registers file, class, and function nodes with directional relationships (`defines`, `imports`, `calls`).
2. **Relational Knowledge Graph**:
   - Breadth-first graph traversal returning interconnected entity nodes and edges up to depth 4.
3. **Persistent SQLite Store**:
   - Stored in WAL-mode SQLite database at `.mekong/memory_federation.db`.
