# Journal — 2026-07-13: Warp Task Complete

## Plan 260712-1849-mekong-warptask — FULLY COMPLETED

### Phase 1: Improve AI Search (NL Routing) ✅
- Expanded `cli/tui/router.py` ROUTE_TABLE from ~20 to **48 bilingual commands** (VI+EN)
- Added 6 new domain families: DevOps, Database, API, Testing, Monitoring, Security
- **Shadow fix** in `src/cli/ask_keyword_router.py`: `route_ask()` now picks longest-match (most specific) instead of first-match, preventing broad commands from shadowing specific ones
  - `"run e2e test"` → `"e2e-test"` (not `"test"`)
  - `"migrate database"` → `"db-migrate"` (not `"backend-db-task"`)
  - `"metrics dashboard"` → `"metrics-dashboard"` (not `"metrics"`)
- 70/70 tests pass in `tests/test_nl_routing.py`
- Backward compat: `route_ask(input_text: str) -> Optional[str]` signature unchanged
- New helper: `best_match()` for specificity-aware selection

### Phase 2: Port Workflow Concept ✅
- Already implemented pre-existing: `cli/commands/workflow.py` (209 lines, 3 subcommands: list/show/domains)
- `docs/workflows-overview.md` expanded with FABRIC DAG + skill catalog + composing recipes
- 16/17 tests pass in `tests/test_workflow_list_show_commands.py` (1 pre-existing gap: `docs` domain missing from infer_domain.layer_map)

### Execution
- Ultracode parallel workflow: Track 1 (NL routing) + Track 2 (workflows) ran concurrently
- Code review: 3 parallel reviewers (T1 code, T2 code, integration test)
- Pre-existing integration test failures (ModuleNotFoundError for `src.main`) — unrelated to routing changes

### Key Decisions
- Shadow fix applied at `ask_keyword_router.py` layer (not table reordering) — 3 lines vs. moving 6 RouteEntry blocks
- `best_match()` kept as new public function alongside `match_routes()` for specificity-aware use cases

---

*Journal entry written: 2026-07-13*
*Plan: plans/260712-1849-mekong-warptask/plan.md*
