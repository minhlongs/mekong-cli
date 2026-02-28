# Planner Report: AGI Hoa RaaS — Open Source Integration

**Date:** 2026-02-28 | **Agent:** planner | **Status:** Plan delivered

---

## Summary

Plan tao thanh cong tai `plans/260228-0819-agi-raas-open-source-integration/`. 6 phases, 5 song song + 1 sequential. Tong effort uoc tinh 28h.

## Deliverables

| File | Purpose |
|------|---------|
| `plan.md` | Overview, dependency graph, file ownership matrix |
| `phase-01-memory-vector-layer.md` | Mem0 + Qdrant thay Chroma/YAML |
| `phase-02-agent-orchestration-langgraph.md` | LangGraph wrap Plan-Execute-Verify |
| `phase-03-observability-langfuse.md` | Langfuse self-hosted telemetry |
| `phase-04-self-healing-engine.md` | Aider CLI bridge vao auto-cto-pilot |
| `phase-05-agent-marketplace-registry.md` | AgencyOS dashboard marketplace UI |
| `phase-06-integration-tests-docs.md` | Cross-cutting tests + docs |

## Parallel Execution Strategy

```
GROUP A (SONG SONG, tat ca doc lap):
  Phase 01: packages/memory/ + src/core/memory*.py
  Phase 02: src/core/orchestrator.py + graph_engine.py
  Phase 03: packages/observability/ + src/core/telemetry.py
  Phase 04: apps/openclaw-worker/lib/aider-bridge.js + auto-cto-pilot.js
  Phase 05: apps/agencyos-web/app/dashboard/marketplace/

GROUP B (SEQUENTIAL, sau Group A):
  Phase 06: tests/ + docs/
```

## File Ownership (Zero Overlap Verified)

- Phase 01: `packages/memory/`, `src/core/memory.py`, `src/core/memory_client.py`
- Phase 02: `src/core/orchestrator.py`, `src/core/planner.py`, `src/core/verifier.py`, `src/core/graph_engine.py`
- Phase 03: `packages/observability/`, `src/core/telemetry.py`
- Phase 04: `apps/openclaw-worker/lib/aider-bridge.js`, `apps/openclaw-worker/lib/auto-cto-pilot.js`
- Phase 05: `apps/agencyos-web/app/dashboard/marketplace/`, `apps/agencyos-web/components/marketplace/`
- Phase 06: `tests/test_memory_qdrant.py`, `tests/test_langgraph.py`, `tests/test_langfuse.py`, `tests/test_aider_bridge.py`, `docs/agi-integration.md`

**Conflict risk: ZERO** — moi phase co exclusive file ownership.

## Key Design Decisions

1. **LangGraph WRAP, khong REWRITE** — existing RecipePlanner/Executor/Verifier giu nguyen, LangGraph la orchestration layer ben ngoai
2. **Graceful degradation** — moi integration co fallback (Qdrant→YAML, LangGraph→linear, Langfuse→JSON, Aider→mission dispatch)
3. **Docker infrastructure** — Qdrant + Langfuse self-hosted, aggregate compose file
4. **Marketplace V1 READ-ONLY** — khong co install/publish, chi browse
5. **Aider route qua Proxy 9191** — `--openai-api-base http://localhost:9191`

## New Dependencies

| Package | Version | Phase | Language |
|---------|---------|-------|----------|
| `mem0ai` | >=0.1.0 | 01 | Python |
| `qdrant-client` | >=1.7.0 | 01 | Python |
| `langgraph` | >=0.2.0 | 02 | Python |
| `langchain-core` | >=0.3.0 | 02 | Python |
| `langfuse` | >=2.0.0 | 03 | Python |
| `aider-chat` | latest | 04 | Python (pipx) |

## Unresolved Questions

1. **Mem0 OSS rate limits** — self-hosted Mem0 co rate limit nao khong? Can benchmark voi multi-tenant load
2. **Aider + Antigravity Proxy compat** — `--openai-api-base` co tuong thich voi Anthropic-style API cua proxy 9191 khong? Can test thu
3. **LangGraph overhead** — can benchmark Plan-Execute-Verify cycle: graph vs linear, neu >100ms overhead thi disable graph
4. **Langfuse PostgreSQL tren M1 16GB** — can tune `max_connections`, `shared_buffers` de khong anh huong CC CLI performance
5. **Marketplace data seeding** — registry co the trong khi chua co agents registered; can seed defaults tu AGENT_REGISTRY
