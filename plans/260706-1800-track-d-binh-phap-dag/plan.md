# Track D — Binh Phap Automation Chain (DAG)

**Created:** 2026-07-10
**Status:** D1-D5 complete, D6 testing pending
**Branch:** fix/layer2-ruff-tech-debt

## Phases

| Phase | Name | Status | Deliverable |
|-------|------|--------|-------------|
| D1 | Chain Definition | ✅ complete | DNA JSON with `dag` key |
| D2 | State Schema | ✅ complete | `schema_version`, `run_id`, atomic write |
| D3 | Auto-Executor | ✅ complete | `Executor.run()` with chapter routing |
| D4 | Recovery/Retry | ✅ complete | `_handle_failure()` wired to recovery registry |
| D5 | CLI Integration | ✅ complete | `/chain next`, `/chain reset` Typer subcommands |
| D6 | Tests | ⏳ pending | DAG integration tests |

## Acceptance Criteria

- [x] DAG definition stored in DNA JSON with dependency edges + human-only nodes
- [x] State persistence uses atomic write (tmp → os.replace)
- [x] State schema includes schema_version + run_id + retry_policy
- [x] Legacy state files auto-upgrade on load
- [x] Failure recovery uses 4-action registry (retry/fallback/escalate/abort)
- [x] CLI: `/chain next` shows next runnable chapter
- [x] CLI: `/chain reset` clears state file
- [ ] Tests: schema versioning, atomic write, legacy upgrade (D6)
- [ ] Tests: full DAG execution end-to-end (D6)
