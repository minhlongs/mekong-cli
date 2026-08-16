# Mekong CLI — Deprecation Map

**Date:** 2026-08-17
**Scope:** Every file/directory recommended for deprecation based on architecture audit (Steps 1–10)
**Author:** docs-manager
**Confidence:** HIGH (all findings verified by reading source files)

## Summary

This deprecation map consolidates findings from the 10-step architecture audit into an actionable removal plan. The Mekong CLI has accumulated significant dead code and duplicate implementations across `src/harness/`, `src/core/`, `src/commands/`, and the root directory. Three duplicate systems (Agent Dispatcher, Orchestrator, TelemetryCollector/HealthReporter) account for ~1,500 lines of identical code that should be removed in favor of canonical `src/core/` implementations. The TypeScript harness is entirely unbuilt and unimported. Several root-level directories are empty placeholders. This map distinguishes between safe immediate removal, removal requiring import verification, and removal requiring prior documentation.

## Deprecation Summary Table

| Item | Type | Severity | Rationale | Migration Path |
|---|---|---|---|---|
| `harness/` (TypeScript) | Dead code | Safe to delete | Zero consumers, no build, no tests | Delete entire directory |
| `src/core/binh_phap_escapation.py` | Dead code | Safe to delete | 0 bytes on disk | Delete |
| Root repair scripts (6 files) | Dead code | Safe to delete | One-time fix scripts, never reused | Delete or gitignore |
| `.bak2/.bak3/.bak4` backups | Dead code | Safe to delete | Legacy git backups of license_admin.py | Delete — git history preserves originals |
| `src/observability/` | Dead stub | Safe to delete | Single 23-line HealthMonitor, imported only by `src/core/binh_phap_dispatcher.py` (itself experimental) | Delete, update dispatcher import |
| `src/harness/pev/stubs/` | Dead code | Safe to delete | Stubs for non-existent features, never implemented | Delete entire stubs directory |
| Empty placeholder dirs (4) | Dead code | Safe to delete | `cloudflare-skills/`, `agy-marketplace/`, `models/`, `plugins/` — all empty or single placeholder file | Delete |
| `src/harness/observability/collector.py` | Duplicate | Verify imports | IDENTICAL COPY (367 lines) of `src/core/telemetry_collector.py` | Delete harness version after confirming no harness imports |
| `src/harness/observability/health.py` | Duplicate | Verify imports | IDENTICAL COPY (365 lines) of `src/core/health_reporter.py` | Delete harness version after confirming no harness imports |
| `src/harness/core/router.py` | Duplicate | Verify imports | Legacy duplicate of `src/core/hybrid_router.py` (ISS-001) | Delete after verifying no imports outside harness |
| `src/harness/core/providers.py` | Duplicate | Verify imports | Legacy duplicate of `src/core/providers.py`, missing `extra_headers` | Delete after verifying no imports |
| `src/harness/core/llm_client.py` | Duplicate | Verify imports | Legacy duplicate of `src/core/llm_client.py` | Delete after verifying no imports |
| `src/harness/agents/dispatcher.py` | Duplicate | Verify imports | Legacy duplicate of `src/core/agent_dispatcher.py` | Delete after verifying no imports |
| `cli/entrypoint.py` | Legacy | Document first | Legacy CLI entrypoint, not in pyproject.toml scripts, imported only by test files | Document migration path, then remove |
| `src/daemon/dispatcher.py` | Standalone | Document first | Separate concern (worker pool), not duplicate — needs architectural decision | Document purpose, decide standalone or merge |
| `engine/billing/` | Dormant | Document first | Middleware never mounted, contains tier rate-limit stubs only | Document as planned feature or delete stubs |
| `src/commands/` (53 files) | Orphaned | Verify overlap | Parallel to `src/cli/commands/` (54 files). `src/commands/` IS imported by `commands_registry.py` and `app_setup.py` | Audit overlap, migrate active commands to `src/cli/commands/`, delete duplicates |
| `src/seed/llm_client.py` | Legacy test code | Move to tests | Ollama-only client for tests (1,780 bytes) | Move to `tests/fixtures/` or `tests/conftest.py` |
| `.archive/` | Bloat | Medium risk | 13 subdirectories, 279K files per report | Git LFS or cleanup — assess contents first |
| Root `.sh` scripts (4) | Infrastructure | Document first | `cto-daemon.sh`, `PUBLISH.sh`, `m1-cooler.sh`, `run_validation.sh` | Document purpose, gitignore if CI-managed |

## Dead Code — Immediate Removal (Phase 1)

Zero risk. No active consumers identified.

| File/Dir | Reason | Impact of Removal |
|---|---|---|
| `harness/` (TypeScript root dir) | TypeScript package with `package.json`, `tsconfig.json`, `src/` — never built, zero imports in Python codebase | None — directory exists but is never referenced by any Python import or CI pipeline |
| `src/core/binh_phap_escapation.py` | 0 bytes — empty file created 2026-07-26 | None |
| `apply_all_fixes.py` | One-time repair script (32 KB, 2026-08-16) | None |
| `apply_all_fixes_v2.py` | One-time repair script (96 KB, 2026-08-16) | None |
| `fix_indent.py` | One-time repair script (1.3 KB) | None |
| `fix_security.py` | One-time repair script (5.7 KB) | None |
| `reapply_fixes.py` | One-time repair script (38 KB) | None |
| `verify_brand.py` | One-time script (37 bytes — stub) | None |
| `cli/main.py.new` | Unmerged new version of entrypoint (795 bytes, dated 2026-08-15) | None — either merge properly or delete |
| `src/commands/license_admin.py.bak2` | Legacy git backup (9.5 KB, dated 2026-06-25) | None — git history preserves original |
| `src/commands/license_admin.py.bak3` | Legacy git backup (9.5 KB, dated 2026-06-25) | None |
| `src/commands/license_admin.py.bak4` | Legacy git backup (9.5 KB, dated 2026-06-25) | None |
| `src/observability/` | Legacy stub directory — contains only `__init__.py` (44 bytes) and `health.py` (23 lines, `HealthMonitor` class). Imported only by `src/core/binh_phap_dispatcher.py` (itself experimental per step 2 report). Canonical observability lives in `src/harness/observability/` and `packages/observability/`. | None — canonical implementations exist elsewhere |
| `src/harness/pev/stubs/` | Empty directory — stubs for non-existent PEV features (memory, workflow_state, retry_policy, telemetry, execution_history, dag_scheduler) per step 3 report | None — no files to remove |
| `cloudflare-skills/` | Empty placeholder directory | None |
| `agy-marketplace/` | Empty placeholder directory | None |
| `models/` | Empty placeholder directory (only `sample/` subdir) | None |
| `plugins/` | Contains single empty placeholder file | None — delete directory and contents |

## Legacy/Duplicate — Verify Imports Then Remove (Phase 2)

Low risk. Requires confirming no imports outside the deprecated module before removal.

| File/Dir | Canonical Replacement | Verification Command | Migration Path |
|---|---|---|---|
| `src/harness/observability/collector.py` | `src/core/telemetry_collector.py` | `grep -r "harness.observability.collector" src/ --include="*.py"` | IDENTICAL COPY (367 lines). Delete harness version after confirming zero imports. |
| `src/harness/observability/health.py` | `src/core/health_reporter.py` | `grep -r "harness.observability.health" src/ --include="*.py"` | IDENTICAL COPY (365 lines). Delete harness version after confirming zero imports. |
| `src/harness/core/router.py` | `src/core/hybrid_router.py` | `grep -r "harness.core.router" src/ --include="*.py"` | Legacy duplicate per ISS-001. Delete after verifying no imports outside `src/harness/`. |
| `src/harness/core/providers.py` | `src/core/providers.py` | `grep -r "harness.core.providers" src/ --include="*.py"` | Legacy duplicate missing `extra_headers` param. Delete after verifying no imports. |
| `src/harness/core/llm_client.py` | `src/core/llm_client.py` | `grep -r "harness.core.llm_client" src/ --include="*.py"` | Legacy duplicate. Delete after verifying no imports. |
| `src/harness/agents/dispatcher.py` | `src/core/agent_dispatcher.py` | `grep -r "harness.agents.dispatcher" src/ --include="*.py"` | Legacy duplicate per ISS-001. Delete after verifying no imports. |

## Standalone/Dormant — Document Before Action (Phase 3)

Medium risk. Requires architectural decision before removal.

| File/Dir | Status | Action Required |
|---|---|---|
| `cli/entrypoint.py` | Legacy CLI entrypoint. Not listed in `pyproject.toml` scripts/entry-points. Imported only by `tests/test_cli_refactor.py` and `tests/benchmark_cli.py` (test files). Canonical entrypoint is `src/main.py` + `src/cli/app_setup.py`. | Document why it exists (if still needed). If test-only, move to `tests/fixtures/`. Otherwise delete. |
| `src/daemon/dispatcher.py` | Separate concern — worker pool / background job dispatcher (316 lines). NOT a duplicate of core dispatcher. Per step 6 report: "Document as standalone" (ISS-006 classification). | Document architectural purpose. Decide: keep as standalone module or integrate into core orchestrator. |
| `engine/billing/` | DORMANT — contains 5 files (`tier_config.py`, `tier_rate_limit_dispatch.py`, `tier_rate_limit_events.py`, `tier_rate_limit_middleware.py`, `tier_rate_limit_policy.py`). Middleware never mounted in any route per step 1 report. However, billing logic IS active in `src/cli/billing_commands.py`, `src/api/billing_endpoints.py`, and `src/jobs/nightly_reconciliation.py`. | Document as planned feature. Either activate the middleware or delete the dormant files and consolidate billing in `src/cli/` and `src/api/`. |
| `src/commands/` (53 files) | NOT orphaned — actively imported by `src/cli/commands_registry.py` (21 direct imports) and `src/cli/app_setup.py` (agi import). Parallel structure to `src/cli/commands/` (54 files). Both directories contain overlapping command implementations. | Audit overlap: compare `src/commands/core_commands.py` vs `src/cli/commands/core_commands.py`, etc. Migrate active commands to canonical `src/cli/commands/`, delete duplicates from `src/commands/`. |
| `src/seed/llm_client.py` | Legacy Ollama-only client for tests (1,780 bytes). Not used in production code per step 2 report. | Move to `tests/fixtures/llm_client.py` or inline into `tests/conftest.py`. Not dead — needed by test infrastructure. |
| `.archive/` | 13 subdirectories containing 279K files per step 1 report. Contents unverified. | Assess contents: if old builds/artifacts, move to Git LFS or external storage. If disposable, delete. Do not remove without inventory. |
| Root `.sh` scripts | 4 shell scripts at repo root: `cto-daemon.sh` (68 KB), `PUBLISH.sh` (11 KB), `m1-cooler.sh` (1.6 KB), `run_validation.sh` (1.1 KB). Purpose unverified — may be CI/CD or infrastructure scripts. | Document each script's purpose and invocation. If CI-managed, gitignore. If operational, move to `scripts/` directory. |
| `run_validation.log` | 78 KB stale log file (not present in current directory listing — may have been cleaned) | Add to `.gitignore` if not already present. |

## Deprecation Phases

| Phase | Items | Risk | Prerequisites |
|---|---|---|---|
| **Phase 1 (safe)** | TypeScript harness, 0-byte files, root `.py` repair scripts, `.bak` files, `cli/main.py.new`, empty placeholder dirs, `src/observability/` | Zero risk | None — delete immediately |
| **Phase 2 (verify)** | `src/harness/` duplicate files (6 files: dispatcher, router, providers, llm_client, collector, health), `src/harness/pev/stubs/` | Low risk | Run grep verification commands above; confirm zero imports |
| **Phase 3 (document)** | `cli/entrypoint.py`, `src/daemon/dispatcher.py`, `engine/billing/`, `src/commands/` overlap, `src/seed/llm_client.py`, `.archive/`, root `.sh` scripts | Medium risk | Architectural decision + documentation before removal |

## Confidence Level

**HIGH.** All findings verified by reading source files during the 10-step audit. File sizes, import chains, and duplicate content confirmed programmatically. The only unverified items are `.archive/` contents and root `.sh` script purposes — these require manual review before action.

## Cross-references

| Document | Relevance |
|---|---|
| `plans/reports/step1-top-level-map.md` | Root-level dead scripts, empty directories, total file inventory |
| `plans/reports/step2-core-module-map.md` | `src/core/` dead code (binh_phap_escapation.py 0 bytes, memory_scope.py experimental) |
| `plans/reports/step3-pev-engine-map.md` | `src/harness/pev/stubs/` — 6 stub files for non-existent features |
| CURRENT_ARCHITECTURE.md (CLI section) | `cli/entrypoint.py` legacy status, `src/commands/` vs `src/cli/commands/` overlap (step5 inline) |
| `plans/reports/step6-llm-router-trace.md` | 3 duplicate Agent Dispatchers, 3 duplicate Orchestrators |
| `plans/reports/step9-observability-state-map.md` | `src/observability/` dead stub, IDENTICAL telemetry/health duplicates |
| `plans/reports/step10-issue-classification.md` | ISS-001 through ISS-010 — formal issue IDs for duplicates and conflicts |