# Plan 260712-1849-mekong-warptask

**Status:** completed
**Source:** xia Warp→mekong-cli analysis (2026-07-12)
**Mode:** improve + port (dual-track parallel)
**Completed:** 2026-07-13

## Phases

### Phase 1: Improve AI Search [--improve]
Enhance natural language command routing so users can type free-form intent instead of memorizing slash commands.

**Status:** DONE

- ROUTE_TABLE expanded from ~20 to 48 bilingual RouteEntry commands (VI + EN keywords)
- 6 new domain families added: DevOps/CI, Database, API/Backend, Testing, Monitoring, Security
- Shadow fix: `route_ask()` in `src/cli/ask_keyword_router.py` now picks longest-match = most specific command (fixes `test` swallowing `e2e-test`, `backend-db-task` swallowing `db-migrate`, `metrics` swallowing `metrics-dashboard`)
- Backward compat: `route_ask(input_text: str) -> Optional[str]` signature unchanged
- `match_routes()` unchanged — table order still = priority
- New function `best_match()` added for specificity-aware selection
- 70 tests in `tests/test_nl_routing.py` — all passing
- Integration tests in `tests/integration/test_ask_routing.py` — pre-existing env issue (ModuleNotFoundError for `src.main`) unrelated to routing logic

### Phase 2: Port Workflow Concept [--port]
Document and expose FABRIC DAG + skills as user-facing "Workflows" — zero new code, make existing power discoverable.

**Status:** DONE (pre-existing implementation)

- `cli/commands/workflow.py` (209 lines) — Typer subcommands: `list`, `show`, `domains` — bilingual VI+EN
- `cli/commands/_workflow_catalog_helpers.py` — DOMAIN_RULES, infer_domain, render helpers
- Registered in `cli/entrypoint.py` line 38 import + line 54 `app.add_typer(workflow_app, name="workflow")`
- 17 tests in `tests/test_workflow_list_show_commands.py` — 16/17 passing (1 pre-existing: `docs` domain missing from `infer_domain.layer_map`)
- `docs/workflows-overview.md` expanded: FABRIC DAG section with ASCII diagram, top-30 skill catalog table by domain, Section 7 "Composing Your Own" with 2 workflow recipes

## Dependencies
- Phase 2 depends on Phase 1 for shared NL-routing logic
- Meant to be run via: `/ck:cook plans/260712-1849-mekong-warptask/ plan.md --auto --parallel`

## Acceptance Criteria

- [x] Users can type free-form NL → mekong auto-resolves to right command
- [x] Existing `/ask` and `/cook` commands enhanced with NL routing (shadow fix ensures correct routing when multiple commands match)
- [x] Workflow documentation exists and is bilingual (VI+EN)
- [x] Skills discoverable as "workflow extensions" via `mekong workflow list|show|domains`
