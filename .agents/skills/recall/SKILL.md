---
name: recall
description: >-
  🧠 Semantic Associative Recall — search cross-mission execution logs, decisions, symbols, and patterns.
---

# /recall — Semantic Associative Recall

Searches across the federated multi-domain memory mesh (episodic logs, architectural
decisions, codebase knowledge graph entities, and self-repair patterns) using
pure standard-library hybrid BM25 and vector cosine similarity.

## Usage

```bash
# Search all federated memory domains for relevant patterns
mekong recall "checkpoint rollback on corrupt file"

# Search specific domain (episodic, decisions, entities, patterns)
mekong recall "monolith vs microservices" --domain decisions
mekong recall "AST syntax error auto repair" --domain patterns
mekong recall "ConsensusBridge" --domain entities

# Output machine-readable JSON results
mekong recall "rate limit quotas" --json
```

## Features

1. **Multi-Domain Federation**:
   - `episodic`: Historic mission goals, execution durations, and outcomes.
   - `decisions`: ADRs, debate resolutions, and cryptographic consensus ballots.
   - `entities`: Codebase AST symbols, class/function definitions, and file paths.
   - `patterns`: Recurring failure modes, bug fixes, and self-repair recipes.
2. **Hybrid BM25 + Cosine Search**:
   - Tokenizes and computes BM25 term weighting alongside dense vector cosine similarity.
   - 100% provider-neutral and standard-library only.
3. **Gateway Event Streaming**:
   - Emits real-time `memory_associative_hit` events over the Phase 12 Gateway broker.

## Options

- `-d, --domain`: Target domain (`episodic`, `decisions`, `entities`, `patterns`, `all`).
- `-l, --limit`: Maximum number of results to return (default: `5`).
- `--json`: Output machine-readable JSON search results.
