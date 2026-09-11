# Development Roadmap

## Phases

| Phase | Name            | Status        | Completion % |
|-------|-----------------|---------------|-------------|
| 1     | Spec-kit SDD    | Complete      | 100%        |
| 2     | Command System  | Complete      | 100%        |
| 3     | Billing + Auth  | Complete      | 100%        |
| 4     | Vietnam Hub     | Complete      | 100%        |
| 5     | AI Video (Sophia) | In progress | ~40%        |
| 6     | Cloud Deploy    | In progress   | ~50%        |
| 7     | Design Intelligence | Complete | 100%        |

## Architecture Gaps

| # | Gap                                    | Status   |
|---|----------------------------------------|----------|
| 1 | Duplicated AgentBase / AgentRegistry   | **CLOSED** (2026-09-10) |
| 2 | Billing / Payment Provider Routing     | **CLOSED** (2026-09-10) |
| 3 | Memory store three-way split           | **CLOSED** (2026-09-10) |
| 4 | Harness verifier merge + DAG scheduler swap | **CLOSED** (SC8, 2026-09-08) |
| 5 | External MCP client-side consumption of third-party servers | **CLOSED** (2026-09-09) |
| 6 | CLI command surfaces unification       | **CLOSED** (2026-09-10) |
| 7 | RecipeVerifier autonomous loop merge   | **CLOSED** (2026-09-10) |
| 8 | Orphan command modules clean & shim    | **CLOSED** (2026-09-10) |
| 9 | Tier configuration & rate limiting     | **CLOSED** (2026-09-10) |
| 10 | Funnel restoration (Zalo OA + Tax + Accounting → CLI) | **CLOSED** (2026-09-09) |

## Focus Areas
- PriorityStack + spec-kit SDD pipeline wired
- 39 groups / 128 commands mapped in COMMAND_REGISTRY.md
- MCU billing + license gate active
- MIT license + Python-only contributor flow live
- Core runtime shares `RecipeVerifier`; multi-step plans execute in topological order
- Full convergence of DUPLICATION_MAP items 1-9 across core, harness, and seed layers
- Programmatic JWT session rotation via `POST /auth/refresh` with dynamic tier upgrade resolution and rate limiting
- Vietnam Hub complete (100%): 3 business funnels (Zalo OA, Tax, Accounting) wired into CLI/API, VietQR webhook HMAC verification, multi-tenant org isolation, bilingual soft paywall gate