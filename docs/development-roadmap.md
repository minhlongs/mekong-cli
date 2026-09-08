# Development Roadmap

## Phases

| Phase | Name            | Status        | Completion % |
|-------|-----------------|---------------|-------------|
| 1     | Spec-kit SDD    | Complete      | 100%        |
| 2     | Command System  | In progress   | ~95%        |
| 3     | Billing + Auth  | In progress   | ~70%        |
| 4     | Vietnam Hub     | In progress   | ~75%        |
| 5     | AI Video (Sophia) | In progress | ~40%        |
| 6     | Cloud Deploy    | In progress   | ~50%        |
| 7     | Design Intelligence | Complete | 100%        |

## Architecture Gaps

| # | Gap                                    | Status   |
|---|----------------------------------------|----------|
| 4 | Harness verifier merge + DAG scheduler swap | **CLOSED** (SC8, 2026-09-08) |
| 5 | External MCP client-side consumption of third-party servers | **CLOSED** (2026-09-09) |
| 10 | Funnel restoration (Zalo OA + Tax + Accounting → CLI) | **CLOSED** (2026-09-09) |

## Focus Areas
- PriorityStack + spec-kit SDD pipeline wired
- 39 groups / 128 commands mapped in COMMAND_REGISTRY.md
- MCU billing + license gate active
- MIT license + Python-only contributor flow live
- Core runtime shares `RecipeVerifier`; multi-step plans execute in topological order