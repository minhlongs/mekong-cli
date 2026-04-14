# Test Coverage Audit — Mekong CLI

**Date:** 2026-04-04
**Reviewer:** code-reviewer agent
**Scope:** Full test suite (`tests/` vs `src/`, `factory/`, `ide-core/engine-farm/`)

---

## Test Run Summary

| Metric | Value |
|--------|-------|
| Passed | 4,785 |
| Failed | 46 |
| Skipped | 34 |
| Runtime | 6m12s |
| Source files (non-init) | 498 |
| Test files | 238 |
| File coverage ratio | 47.7% |
| Factory contracts | 558 JSON |

---

## Pre-existing Failures (46)

### test_memory.py — 14 failures
- **Root cause:** `TypeError: __init__` signature mismatch. MemoryStore constructor changed but tests not updated.
- All 14 test methods in `TestMemoryStore` fail identically.

### test_planner.py — 6 failures
- **Root cause:** `validate_plan` return value changed (AssertionError). Tests expect old contract.
- Affects: `test_valid_plan_no_issues`, `test_circular_dependency_on_self`, `test_orphan_dependency`, `test_multi_step_valid_dag`, `test_complex_valid_plan`, `test_duplicate_dependencies`

### test_orchestrator_integration.py — 2 failures
- `test_run_from_recipe_success`, `test_step_result_structure` — likely cascading from planner changes.

### test_memory_qdrant.py — 1 failure
- `test_record_still_works` — backward compat broken by same MemoryStore init change.

### test_executor_phase2.py — 1 failure
- `test_retry_policy_non_retryable_exit_code_stops_immediately` — retry policy behavior changed.

### test_self_healing.py — 1 failure
- `test_suggest_correction_called_on_failure` — self-heal mock expectations stale.

### Remaining 21 failures
- Distributed across other test files; all appear related to interface/contract drift between `src/core/` and tests.

---

## Severity-Rated Findings

### [CRITICAL] Entire billing subsystem has ZERO test coverage

**Evidence:** 11 billing/money files untested:
- `src/billing/engine.py`, `event_emitter.py`, `idempotency.py`, `proration.py`, `reconciliation.py`
- `src/raas/billing_engine.py` (457 lines), `billing_reconciliation.py` (538 lines), `billing_proration.py` (421 lines)
- `src/raas/credit_account_repository.py` (363 lines), `credits.py` (254 lines)
- `src/jobs/nightly_reconciliation.py` (718 lines)

**Impact:** Financial calculations with no verification. Proration, reconciliation, credit accounting bugs go undetected. This is the system that handles MCU billing ($49-$499/mo tiers).

**Recommendation:** Priority 1 — write unit tests for `billing_engine.py`, `billing_reconciliation.py`, `billing_proration.py`, and `nightly_reconciliation.py`. Focus on boundary conditions: zero balance, tier boundaries, partial month proration, idempotency key collisions.

---

### [CRITICAL] Security-critical modules untested (2,555 lines)

**Evidence:** No test files for:
- `src/security/command_sanitizer.py` (188 lines) — shell injection defense
- `src/core/command_sanitizer.py` (278 lines) — duplicate sanitizer, also untested
- `src/core/input_validation.py` (140 lines) — input validation layer
- `src/auth/secure_storage.py` (392 lines) — credential storage
- `src/auth/middleware.py` (355 lines) — auth middleware
- `src/core/auth_jwt.py` (134 lines) — JWT handling
- `src/core/machine_fingerprint.py` (477 lines) — device identity
- `src/core/certificate_store.py` (613 lines) — certificate management
- `src/security/attestation_generator.py` (308 lines)

**Impact:** Shell injection, auth bypass, JWT forgery, and certificate validation bugs would not be caught by CI. These are the exact modules an attacker would target.

**Recommendation:** Priority 1 — test `command_sanitizer.py` (both copies) with adversarial inputs (`;`, `|`, `$(...)`, backticks). Test `auth_jwt.py` with expired/malformed/forged tokens. Test `secure_storage.py` encryption roundtrip.

---

### [CRITICAL] Core PEV engine tests are broken (planner + memory + orchestrator)

**Evidence:** 23 failures across `test_memory.py` (14), `test_planner.py` (6), `test_orchestrator_integration.py` (2), `test_memory_qdrant.py` (1). The Plan-Execute-Verify loop is the architectural core.

**Impact:** The primary execution pipeline has no working test coverage. Any regression in planner or memory would ship undetected.

**Recommendation:** Fix immediately. The `MemoryStore.__init__` signature change and `validate_plan` return contract change need test updates to match current interfaces.

---

### [IMPORTANT] Daemon subsystem: 24 source files, 5,236 lines, ZERO tests

**Evidence:** `src/daemon/` contains 24 Python files including `agent_loop.py`, `dispatcher.py`, `executor.py`, `worker_pool.py`, `circuit_breaker.py`, `dlq.py`, `mission_control.py`, `pipeline_executor.py`. No test file references any daemon module.

**Impact:** The autonomous daemon (Tôm Hùm) runs unsupervised. Bugs in `worker_pool.py`, `circuit_breaker.py`, or `dlq.py` could cause silent task loss or infinite retry loops in production.

**Recommendation:** Start with `dispatcher.py`, `circuit_breaker.py`, `dlq.py` — these have clear input/output contracts suitable for unit testing.

---

### [IMPORTANT] API layer: 12 endpoint files with zero test coverage

**Evidence:** Untested API modules:
- `src/api/billing_endpoints.py`, `raas_router.py`, `raas_auth_middleware.py`
- `src/api/raas_billing_middleware.py`, `raas_billing_service.py`
- `src/api/polar_webhook.py`, `tier_config_routes.py`
- `src/api/license_server.py`, `license_ui.py`, `admin_license_service.py`
- `src/api/quota_status_endpoints.py`, `webhooks/router.py`

**Impact:** HTTP endpoints handling auth, billing, and webhooks have no request/response validation tests. OWASP-relevant surface area.

**Recommendation:** Add FastAPI TestClient tests for billing and auth endpoints. Webhook endpoints need signature verification tests.

---

### [IMPORTANT] E2E test_critical_flows.py is a stub (1 test, 13 lines)

**Evidence:** File contains single `test_health_check` that only verifies `/health` returns 200. Named "critical flows" but tests nothing critical.

**Impact:** False confidence. No e2e coverage for purchase flow completion, auth flow, or mission lifecycle.

**Recommendation:** Either populate with actual critical flow tests (auth -> create mission -> bill -> complete) or rename to `test_health_endpoint.py` to avoid misleading.

---

### [IMPORTANT] Engine farm scripts: 6 bash scripts, 22KB, zero tests

**Evidence:** `ide-core/engine-farm/` contains `start-farm.sh`, `stop-farm.sh`, `ab-test.sh` (10KB), `cutover.sh`, `migrate-models.sh`, `health-check.sh`. No test references found anywhere.

**Impact:** Model migration (`migrate-models.sh`) and A/B cutover (`cutover.sh`) are production-affecting operations with no validation.

**Recommendation:** Add `tests/test_engine_farm.sh` with dry-run validation for `health-check.sh` and syntax checking (`bash -n`) for all scripts. `ab-test.sh` at 10KB deserves its own test harness.

---

### [IMPORTANT] Factory contracts: 3 invalid JSON files, 23 missing coverage mappings

**Evidence:** `validate_contracts.py` reports:
- `ml-monitor.json`, `pm-analytics.json`, `revops-health.json` — invalid JSON (parse error at line 16)
- 23 commands have no contract coverage (e.g., `studio/studio-bootstrap`, `studio/studio-launch-full`)
- Health score: 71/100

**Impact:** Broken contracts could cause command dispatch failures. Missing coverage means 23 commands have no machine-readable spec.

**Recommendation:** Fix the 3 JSON parse errors (likely trailing commas or unquoted values). Generate contracts for the 23 uncovered commands.

---

### [MODERATE] 42% of test files use mocks (101/238) — acceptable but watch ratio

**Evidence:** 101 test files import mock/patch/MagicMock. 140 test files use no mocking. Ratio is reasonable.

**Impact:** Low — mocking is appropriate for LLM calls and external APIs. However, some mock-heavy files may mask integration issues.

**Recommendation:** No action needed, but ensure integration tests (`tests/integration/`) exercise real code paths for billing and auth.

---

### [MODERATE] Trivial assertion antipatterns found

**Evidence:**
- `test_rate_limit_observability.py` lines 753/759/765: `assert True` with comment "PII handling is in middleware"
- `test_health_crash.py` line 121: `assert True`
- `test_engagement_store.py` lines 55/63: `assert result is not None` (no value check)

**Impact:** These tests always pass. They inflate pass counts without verifying behavior.

**Recommendation:** Replace `assert True` with actual assertions or remove tests. `assert result is not None` should check result contents.

---

### [MODERATE] 260 source files have no corresponding test file (52.3% untested)

**Evidence:** Full list in audit data. Major untested areas by module:
- `src/cli/` — 34 untested command files
- `src/commands/` — 28 untested command files
- `src/core/` — 72 untested core files
- `src/daemon/` — 24 untested (entire module)
- `src/raas/` — 30 untested
- `src/api/` — 12 untested

**Impact:** Over half the codebase has no unit test coverage by file. New bugs in untested modules propagate silently.

**Recommendation:** Prioritize tests for modules that handle money (billing), security (auth/sanitizer), and data integrity (daemon/reconciliation). CLI command files are lower priority as they're mostly Typer wrappers.

---

### [MODERATE] Database layer completely untested

**Evidence:** `src/db/` has 6 files (database.py, migrate.py, queries/, repository.py, schema.py, tier_config_repository.py) with zero test coverage.

**Impact:** Schema migrations, query correctness, and repository CRUD operations are unverified.

**Recommendation:** Add repository unit tests with in-memory SQLite. Test migration idempotency.

---

## Positive Observations

1. **4,785 passing tests** — large test base exists and mostly works
2. **Polymarket module well-tested** — 18 test files covering trading pipeline, risk management, billing
3. **Founder/VC module well-tested** — 14 test files for IPO, cap table, term sheet, roadshow
4. **Integration test structure exists** — `tests/integration/`, `tests/e2e/`, `tests/regression/` directories
5. **Factory self-test system** — contract validation infrastructure exists and catches issues
6. **140 test files use zero mocking** — testing real behavior, not mock behavior
7. **Conftest provides clean fixtures** — centralized test setup

---

## Recommended Priority Actions

1. **[P0] Fix 23 broken PEV tests** — update `MemoryStore` and `validate_plan` test contracts to match current interfaces
2. **[P0] Add billing engine tests** — `billing_reconciliation.py` (538 lines) and `nightly_reconciliation.py` (718 lines) handle money
3. **[P0] Add security module tests** — both `command_sanitizer.py` copies, `auth_jwt.py`, `input_validation.py`
4. **[P1] Fix 3 broken factory JSON contracts** — `ml-monitor.json`, `pm-analytics.json`, `revops-health.json`
5. **[P1] Add daemon subsystem tests** — at minimum `circuit_breaker.py`, `dlq.py`, `dispatcher.py`
6. **[P1] Add API endpoint tests** — billing endpoints, auth middleware, webhook handlers
7. **[P2] Remove `assert True` placeholders** — 4 instances in rate_limit_observability and health_crash
8. **[P2] Populate e2e critical_flows** — currently a 1-test stub
9. **[P2] Add engine farm script tests** — at least `bash -n` syntax validation + dry-run checks

---

## Metrics Summary

| Metric | Value | Target | Status |
|--------|-------|--------|--------|
| Test pass rate | 98.9% (4785/4865) | 100% | FAIL |
| File coverage | 47.7% (238/498) | 80% | FAIL |
| Security test coverage | 0/10 critical files | 10/10 | FAIL |
| Billing test coverage | 0/11 money files | 11/11 | FAIL |
| Daemon test coverage | 0/24 files | 12/24 | FAIL |
| Factory contract health | 71/100 | 90/100 | FAIL |
| Mock ratio | 42% (101/238) | <50% | PASS |
| E2E test count | 3 files | 10+ | FAIL |
| Trivial tests | 4+ `assert True` | 0 | FAIL |

---

*Report: `/Users/macbookprom1/mekong-cli/plans/reports/reviewer-3-test-coverage-audit-260404.md`*
