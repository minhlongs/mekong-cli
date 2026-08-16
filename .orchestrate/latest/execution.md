# Execution Log — Architecture Update (Phases 1-3)

**Pipeline Status:** EXECUTE — Architecture Update Phases 1-3
**Agent:** fullstack-developer (auto, parallel)

## Phase 1: Safe Deletion (Zero-Risk Dead Code)
Status: COMPLETE (commit bc400af5e)
- Deleted: TypeScript `harness/` (never built, zero Python imports)
- Deleted: `src/observability/` (dead stub, zero imports)
- Deleted: `.bak2/.bak3/.bak4` backup files (git history preserves originals)
- Deleted: `src/core/binh_phap_escapation.py` (0 bytes)
- Deleted: empty placeholder dirs (agy-marketplace, cloudflare-skills, models, plugins)

## Phase 2: Duplicate Removal (Verified Zero External Imports)
Status: COMPLETE (commit 217328ad0)
- Removed: `src/harness/observability/collector.py` (370 lines) → `src/core/telemetry_collector.py`
- Removed: `src/harness/observability/health.py` (368 lines) → `src/core/health_reporter.py`
- Removed: `src/harness/core/router.py` (331 lines) → canonical `src/core/hybrid_router.py`
- Removed: `src/harness/core/providers.py` (456 lines) → `src/core/providers.py`
- Removed: `src/harness/core/llm_client.py` (615 lines) → `src/core/llm_client.py`
- Removed: `src/harness/agents/dispatcher.py` (187 lines) → `src/core/agent_dispatcher.py`
- Re-wired: `src/harness/observability/__init__.py` → imports from `src/core/telemetry_collector` + `src/core/health_reporter`
- Re-wired: `src/harness/agents/__init__.py` → imports from `src/core/agent_dispatcher`

## Phase 3: Document Legacy/Dormant Components (NO DELETION)
Status: DOCUMENTED — awaiting architectural decision

| Component | Status | Risk | Action Required |
|---|---|---|---|
| `cli/entrypoint.py` | Legacy CLI entrypoint (263 lines). NOT in pyproject.toml scripts. Imported only by test files. Canonical entrypoint is `src/main.py` + `src/cli/app_setup.py`. | Low | Document why it exists. If test-only, move to `tests/fixtures/`. Otherwise delete. |
| `src/daemon/dispatcher.py` | Worker pool / background job dispatcher (316 lines). NOT a duplicate of `src/core/agent_dispatcher.py`. Separate concern (ISS-006). | Medium | Document architectural purpose. Decide: keep standalone or integrate into core orchestrator. |
| `engine/billing/` | Dormant billing middleware (5 files). Never mounted in any route. Billing IS active in `src/cli/billing_commands.py` and `src/api/billing_endpoints.py`. | Medium | Document as planned feature. Either activate middleware or delete dormant files and consolidate billing in `src/cli/` + `src/api/`. |
| `src/commands/` (53 files) | Parallel to `src/cli/commands/` (54 files). Both contain overlapping command implementations. Imported by `src/cli/commands_registry.py` (21 direct imports) and `src/cli/app_setup.py`. | Medium | Audit overlap: compare `src/commands/core_commands.py` vs `src/cli/commands/core_commands.py`. Migrate active commands to canonical `src/cli/commands/`, delete duplicates. |
| `src/seed/llm_client.py` | Legacy Ollama-only client for tests (1,780 bytes). Not used in production. | Low | Move to `tests/fixtures/llm_client.py` or inline into `tests/conftest.py`. Not dead — needed by test infrastructure. |

**Rationale for stopping here:** Per DEPRECATION_MAP.md, these are Phase 3 (document-first) items. They have active consumers or architectural implications. Further action requires explicit user decision per audit findings.

## Verification
- Phase 1: ruff clean, 218 tests passed
- Phase 2: ruff clean, 218 tests passed (1 pre-existing failure in test_agent_commands.py)
- Commits: bc400af5e, 217328ad0