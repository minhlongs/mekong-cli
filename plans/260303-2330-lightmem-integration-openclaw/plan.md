# LightMem Integration Plan — OpenClaw Worker

**Date:** 2026-03-03
**Status:** Planning
**Work Context:** `/Users/macbookprom1/mekong-cli/apps/openclaw-worker`

---

## 📚 LightMem Paper Summary (arxiv.org/abs/2510.18866)

### Core Concepts

**LightMem** = Lightweight Memory for LLM Agents

| Component | Description |
|-----------|-------------|
| **Working Memory** | Short-term context for current task |
| **Long-term Memory** | Consolidated knowledge from past experiences |
| **Memory Retrieval** | Similarity-based search for relevant memories |
| **Forgetting Mechanism** | Decay old/irrelevant memories to save space |

### Key Architecture

```
┌──────────────────────────────────────────────────────────┐
│                   LLM Agent Core                          │
└────────────────────┬─────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
┌───────────────┬───────────────┬───────────────┐
│ Working       │ Long-term     │ Retrieval     │
│ Memory        │ Memory        │ Engine        │
│ (Active ctx)  │ (Consolidated)│ (Similarity)  │
└───────────────┴───────────────┴───────────────┘
        │            │
        ▼            ▼
┌───────────────────────────────────────────────┐
│          Memory Consolidation                 │
│   (Session end → Working → Long-term)         │
└───────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────┐
│          Forgetting Mechanism                 │
│   (Decay old memories, keep high-value)       │
└───────────────────────────────────────────────┘
```

---

## 🔍 OpenClaw Worker Current State

### Existing Memory Files

| File | Purpose | LightMem Mapping |
|------|---------|------------------|
| `mission-history.json` | Mission outcomes | Long-term Memory |
| `mission-outcomes.json` | Recent mission results | Working Memory |
| `cross-session-memory.json` | Session tracking | Session Memory |
| `cto-lessons.json` | Learned patterns | Consolidated Knowledge |
| `dispatched-tasks.json` | Active tasks | Working Memory |
| `strategic-state.json` | Strategic context | Context Memory |

### Gaps Identified

1. **No unified memory interface** — scattered across files
2. **No retrieval mechanism** — can't search past missions by similarity
3. **No forgetting/decay** — old data accumulates without pruning
4. **No consolidation process** — working → long-term not automated
5. **No memory scoring** — all memories treated equally

---

## 🎯 Implementation Phases

### Phase 1: Core Memory Module (`lib/lightmem-memory.js`)
- [ ] WorkingMemory class (in-memory, fast access)
- [ ] LongTermMemory class (file-based, persistent)
- [ ] MemoryItem schema (id, content, timestamp, importance, decay)
- [ ] CRUD operations (add, get, update, delete)

### Phase 2: Retrieval Engine (`lib/lightmem-retrieval.js`)
- [ ] Similarity scoring (keyword overlap + recency + importance)
- [ ] Top-K retrieval (find N most relevant memories)
- [ ] Query interface (search by project, task type, outcome)
- [ ] Context injection (format memories for LLM prompt)

### Phase 3: Consolidation Pipeline (`lib/lightmem-consolidation.js`)
- [ ] Session-end trigger (working → long-term)
- [ ] Importance scoring (success/failure, tokens, files changed)
- [ ] Pattern extraction (extract lessons from outcomes)
- [ ] Merge duplicates (dedup similar memories)

### Phase 4: Forgetting Mechanism (`lib/lightmem-forgetting.js`)
- [ ] Decay function (exponential decay over time)
- [ ] Pruning threshold (remove low-importance old memories)
- [ ] Archive system (move pruned to archive, not delete)
- [ ] Retention policy (configurable TTL per memory type)

### Phase 5: Integration (`lib/brain-mission-runner.js`)
- [ ] Inject retrieved memories into mission prompt
- [ ] Record mission outcome to working memory
- [ ] Trigger consolidation on mission complete
- [ ] Apply forgetting on schedule (every 24h)

### Phase 6: Testing (`test/lightmem-*.test.js`)
- [ ] Unit tests for Memory classes
- [ ] Integration tests for retrieval
- [ ] E2E tests for consolidation pipeline
- [ ] Performance tests (memory size vs latency)

---

## 📊 Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| Memory retrieval latency | < 50ms | Time to find top-5 memories |
| Working memory capacity | 100 items | Max items in RAM |
| Long-term memory capacity | 10,000 items | Max items on disk |
| Consolidation success rate | > 95% | % of missions consolidated |
| Forgetting accuracy | > 90% | Low-value memories pruned |
| Mission success improvement | +20% | Before/after comparison |

---

## 🔒 Security & Quality Gates

- [ ] No sensitive data in memories (API keys, tokens)
- [ ] File I/O error handling (corrupted JSON recovery)
- [ ] Memory size limits (prevent disk exhaustion)
- [ ] Atomic writes (temp file + rename pattern)
- [ ] Graceful degradation (memory system failure ≠ mission failure)

---

## 📅 Timeline

| Phase | Estimated Time | Dependencies |
|-------|----------------|--------------|
| Phase 1: Core Module | 2 hours | None |
| Phase 2: Retrieval | 2 hours | Phase 1 |
| Phase 3: Consolidation | 2 hours | Phase 1, 2 |
| Phase 4: Forgetting | 1 hour | Phase 1 |
| Phase 5: Integration | 2 hours | Phase 1-4 |
| Phase 6: Testing | 2 hours | Phase 5 |
| **Total** | **11 hours** | Sequential |

---

## 🚀 Next Steps

1. ✅ Approve this plan
2. Spawn `fullstack-developer` agent for Phase 1-6 implementation
3. Spawn `tester` agent for test writing
4. Spawn `code-reviewer` for security audit
5. Verify build + browser check
6. Commit changes

---

**Files to Create:** 6
- `lib/lightmem-memory.js`
- `lib/lightmem-retrieval.js`
- `lib/lightmem-consolidation.js`
- `lib/lightmem-forgetting.js`
- `test/lightmem-memory.test.js`
- `test/lightmem-retrieval.test.js`

**Files to Modify:** 2
- `lib/brain-mission-runner.js` (integrate memory injection)
- `config.js` (add memory config constants)
