# Phase B: Agentic Core — Architecture Decisions / QUYẾT ĐỊNH KIẾN TRÚC

> **Date:** 2026-07-07 | **Scope:** Steps 6–25 of 25-step IDE roadmap

---

## Why Each Component Was Built This Way / TẠI SAO XÂY DỰNG NHƯ VẬY

### B2: Usage Tracker Merge

- **Decision:** Keep `src/usage/`, delete `src/metering/`.
- **Why:** Two trackers meant double writes, divergent metrics, 2x maintenance. DRY principle.
- **Trade-off:** Import paths changed (`src.metering` → `src.usage`). Acceptable — only 6 callers needed updating.

### B3: NLU Unification

- **Decision:** Single `classify_intent()` in `src/core/nlu.py`; `harness/pev/nlu.py` delegates upstream.
- **Why:** Two intent classifiers produced conflicting classifications (PEV version: 5 intents; core version: ~50). Delegation eliminates duplication.
- **Trade-off:** PEV path now depends on core NLU. Low risk — core NLU is production-stable.

### B4: Memory Bridge

- **Decision:** Protocol class (`MemoryBridge`) with 4 adapters instead of direct refactor of each module.
- **Why:** 7 memory modules had incompatible APIs. A protocol lets each adapter handle its own storage backend without forcing a uniform schema.
- **Trade-off:** Added abstraction layer. Worth it: new backends (qdrant, mem0ai) drop in without touching existing modules.

### B5: PEV Parser Real

- **Decision:** Markdown recipe format with YAML frontmatter + `## Steps` sections.
- **Why:** Markdown is human-readable (CEO can author recipes); YAML frontmatter carries metadata without parsing the body.
- **Trade-off:** Parsing complexity vs. authoring simplicity. Markdown selected for product doctrine (no-code/CEO-authored).

### B6: Agent Factory

- **Decision:** YAML config + factory function instead of code-based instantiation.
- **Why:** Eliminates `CEOAgent(llm=llm)` boilerplate. New agent types become config additions, not code changes. Supports the no-tech doctrine.
- **Trade-off:** YAML indirection means runtime errors (typos in config names) instead of import errors. Mitigated by factory validation at load time.

### B7: Integration + Validation

- **Decision:** End-to-end integration test as the final gate, not individual unit tests.
- **Why:** Phase B's value is the pipeline working as a whole: goal → plan → execute → verify → memory. Unit tests prove parts; E2E proves the loop.
- **Trade-off:** E2E tests are slower and more brittle. Restricted to the primary happy path; edge cases covered by unit tests in earlier waves.

---

## Trade-offs Accepted / CHỐT CHUYỂN ĐỒNG Ý

| Trade-off | Accepted Risk | Mitigation |
|-----------|--------------|------------|
| Import path changes (B2) | Brief breakage during migration | 6 callers updated atomically |
| Protocol indirection (B4) | Added layer complexity | Lazy imports; backward-compatible adapter |
| YAML config for agents (B6) | Runtime config errors | Factory validates at `load_config()` |
| Markdown recipe format (B5) | Parsing fragility | Well-defined section headers; fallback to stub |
| E2E as final gate (B7) | Slower feedback | Restricted to happy path; unit tests cover edges |

---

## Layer Boundary Enforcement / GIỚI HẠN LỚP

Phase B respects the 4-layer architecture:

| Layer | Import rule | Phase B violation? |
|-------|-------------|-------------------|
| seed | Importable by all | B2's `src/usage/` lives in `seed/` — compliant |
| tree | Imports seed only | B3 NLU delegates via function call — compliant |
| forest | Imports seed, tree | B4 adapters, B5 PEV pipeline — compliant |
| land | Imports seed, tree, forest | No B7 land changes — compliant |

**Forbidden imports avoided:** No `land → forest` circulars; no `seed → tree` up-imports. B6 factory lives in `harness/` (forest) and accepts `memory` (seed) as dependency — compliant.

---

## Protected Flows Verification

No Phase B component touches: Setup Wizard, Telegram Bot, or Payment Flow. These remain isolated in `land/` with no import dependency on agentic core modules.

---

*Tài liệu này ghi lại các quyết định kiến trúc để tham khảo khi maintain Phase C+.*
