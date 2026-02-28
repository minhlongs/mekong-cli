# Implementation Plan: L9 Deep Knowledge & Vector Persistence

## Context Links
- [Architecture Gaps Report](../260225-1104-tom-hum-agi-100-self-healing/research/researcher-02-architecture-gaps.md)
- [Vector Store Research](../260225-1104-tom-hum-agi-100-self-healing/reports/research-vector-store.md)

## Overview
- **Priority:** High (L9 AGI Milestone)
- **Status:** Planning
- **Description:** Implement a RAG-based knowledge retrieval system using LanceDB to address scaling issues with JSON persistence and enable deep knowledge injection from the `knowledge/` folder.

## Key Insights
- **LanceDB** is the selected vector store due to its embedded nature, M1 compatibility, and SQL-filtering capabilities.
- Current JSON-based persistence is a bottleneck for long-term AGI evolution.
- Semantic search will allow Tôm Hùm to inject relevant domain context into every mission prompt automatically.

## Requirements
- Node.js environment with `@lancedb/lancedb` and an embedding provider (e.g., Gemini or OpenAI via Antigravity Proxy).
- Seamless migration from `mission-history.json` to LanceDB.
- Zero-downtime integration with `mission-dispatcher.js`.

## Architecture
- `lib/vector-service.js`: Core service for LanceDB operations (CRUD, search).
- `lib/knowledge-indexer.js`: Background worker to keep the `knowledge/` folder synced with the vector store.
- `lib/mission-journal.js` (Updated): Writes outcomes to both JSON (for backward compatibility/backup) and LanceDB.
- `lib/mission-dispatcher.js` (Updated): Queries `knowledge` and `history` tables before mission generation.

## Related Code Files
- `lib/vector-service.js` (New)
- `lib/knowledge-indexer.js` (New)
- `lib/mission-journal.js` (Modify)
- `lib/mission-dispatcher.js` (Modify)
- `scripts/migrate-to-vector.js` (New)

## Implementation Phases
1. [Phase 01: Setup & Vector Service](./phase-01-setup-vector-service.md)
2. [Phase 02: Knowledge Indexing](./phase-02-knowledge-indexing.md)
3. [Phase 03: Journal & History Migration](./phase-03-journal-migration.md)
4. [Phase 04: Dispatcher Integration (RAG)](./phase-04-dispatcher-rag.md)

## Success Criteria
- [ ] LanceDB successfully stores and retrieves embeddings on M1.
- [ ] 100% of `knowledge/` docs are indexed.
- [ ] Mission history migrated without data loss.
- [ ] Mission prompts include relevant "KNOWLEDGE INTEL" sections.

## Risk Assessment
- Native binary issues with LanceDB on ARM64 (Mitigation: Fallback to Orama if needed).
- Token usage increase due to RAG context (Mitigation: Limit context chunks).

## Next Steps
- Implement Phase 01.

## Unresolved Questions
- Which embedding model to use? (Default: `text-embedding-004` via Gemini).
- Retention policy for vector store? (Default: Indefinite for now).
