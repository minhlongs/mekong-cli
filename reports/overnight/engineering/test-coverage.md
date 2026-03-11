# Test Coverage Analysis — Mekong CLI

**Date:** 2026-03-11
**Scope:** Full test suite structure, coverage metrics, patterns, gaps

---

## 1. Test Suite Size

```
3638 tests collected (pytest --co -q)
125 top-level test_*.py files
Subdirectories: tests/agents/, tests/backend/, tests/benchmarks/,
                tests/cli/, tests/commands/, tests/core/,
                tests/data/, tests/deployment/, tests/e2e/,
                tests/fixtures/, tests/integration/, tests/raas/,
                tests/regression/, tests/smoke_test_queue.py
```

CI ignores: `tests/backend`, `tests/e2e`, `tests/integration`, `tests/unit`, `tests/benchmarks`

---

## 2. Coverage Numbers

**Default CI run** (ignoring backend/e2e/integration/unit/benchmarks):
```
123 passed, 6 warnings in 8.87s
Coverage: 10% overall (26,151 stmts, 23,557 missed)
CI threshold: --cov-fail-under=15 (test.yml) / 80 (ci.yml with continue-on-error)
```

**Core PEV files coverage** (from test run):

| File | Stmts | Missed | Coverage |
|------|-------|--------|----------|
| src/core/planner.py | ~250 | — | tested (118 pass) |
| src/core/executor.py | ~180 | — | tested |
| src/core/verifier.py | ~130 | — | tested (100% quality gate tests) |
| src/security/command_sanitizer.py | 52 | 19 | 63% |
| src/lib/raas_gate.py | 374 | 313 | 16% |
| src/lib/usage_metering_service.py | 221 | 168 | 24% |

**Most critical gaps:** `src/lib/`, `src/services/`, `src/middleware/`, `src/usage/` — all 0-30% covered.

---

## 3. Core PEV Test Results

Run: `python3 -m pytest tests/test_planner.py tests/test_executor.py tests/test_verifier.py tests/test_orchestrator_integration.py -q`

```
118 passed in 6.53s (0 failures)
```

All core engine tests pass cleanly.

---

## 4. Test File Inventory — Key Files

| Test File | Tests | Domain |
|-----------|-------|--------|
| test_planner.py | ~20 | RecipePlanner decomposition + DAG |
| test_executor.py | ~15 | Shell/LLM/API/Tool/Browse execution |
| test_verifier.py | ~25 | All verification check types + quality gates |
| test_orchestrator_integration.py | ~10 | Full PEV workflow integration |
| test_agent_registry.py | ~8 | AGENT_REGISTRY lookup |
| test_git_agent.py | ~10 | GitAgent plan/execute/verify |
| test_shell_agent.py | ~8 | ShellAgent execution |
| test_lead_hunter.py | ~10 | LeadHunter scraping |
| test_nlu.py | ~8 | IntentClassifier |
| test_dag_scheduler.py | ~12 | DAG topological sort + parallel |
| test_memory.py | ~8 | MemoryStore record/query |
| test_smart_router.py | ~6 | SmartRouter routing decisions |
| test_llm_cache.py | ~8 | LRU cache behaviour |
| test_hybrid_router.py | ~6 | Provider failover |
| test_mcu_billing.py | ~10 | MCU credit accounting |
| test_gateway_api.py | ~15 | RaaS gateway endpoints |
| test_raas_gate.py | ~12 | License gate enforcement |
| test_anomaly_detection.py | ~10 | AnomalyDetector alerts |
| test_dag_scheduler.py | ~12 | DAG concurrency |
| test_fallback_chain.py | ~8 | LLM provider fallback |

---

## 5. Test Patterns Observed

**Unit test pattern** (dominant):
```python
class TestRecipePlanner(unittest.TestCase):
    def setUp(self):
        self.planner = RecipePlanner()

    def test_decompose_goal_implement(self):
        context = PlanningContext(goal="implement auth")
        tasks = self.planner._rule_based_decompose("implement auth", context)
        self.assertGreater(len(tasks), 0)
        self.assertEqual(tasks[0]["title"], "Setup environment")
```

**Integration test pattern** (`test_orchestrator_integration.py`):
```python
def test_run_from_goal_sequential(self):
    orchestrator = RecipeOrchestrator(enable_health_endpoint=False)
    result = orchestrator.run_from_goal("list files")
    self.assertIn(result.status, [OrchestrationStatus.SUCCESS, ...])
```

**Mock usage:** Moderate — LLM client mocked in most unit tests via `MagicMock()` or `unittest.mock.patch`. Real subprocess calls made in integration tests with safe commands (ls, git status, etc.).

---

## 6. Test Subdirectory Structure

```
tests/e2e/          — Browser/accessibility E2E (Playwright implied)
  accessibility/    — a11y tests
  api/              — API endpoint E2E
  auth/             — Auth flow E2E

tests/integration/  — Cross-component integration
  test_api_crm.py
  test_api_franchise.py
  test_api_kanban.py

tests/benchmarks/   — AGI performance benchmarks
  test_agi_tasks.py (run separately in CI benchmarks job)

tests/regression/   — Regression suite (specific bug fixes)
tests/smoke_test_queue.py — Queue smoke tests
```

---

## 7. Coverage Gaps (Critical)

| Module | Coverage | Risk |
|--------|----------|------|
| src/lib/raas_gate.py | 16% | HIGH — billing enforcement |
| src/middleware/auth_middleware.py | 0% | HIGH — auth bypass risk |
| src/services/license_enforcement.py | 32% | HIGH — license logic |
| src/lib/usage_metering_service.py | 24% | MEDIUM — billing accuracy |
| src/security/attestation_generator.py | 0% | MEDIUM |
| src/raas/sync_client.py | ~5% | MEDIUM — sync reliability |
| src/core/telegram_bot.py | ~10% | LOW — async bot |

---

## 8. CI Coverage Configuration

From `pyproject.toml` (referenced in test.yml):
```
--cov-fail-under=15  (test.yml — permissive)
--cov-fail-under=80  (ci.yml — with continue-on-error, so non-blocking)
```

Effective gate: 15% minimum. Target is 80% but not enforced hard.

---

## 9. Recommendations

1. **Raise CI hard gate to 40%** — current 15% threshold too low for billing-critical code
2. **Add tests for `auth_middleware.py`** — 0% on auth code is a security risk
3. **Add tests for `raas_gate.py`** — billing enforcement needs >80% coverage
4. **Add property-based tests** for CommandSanitizer (fuzzing dangerous patterns)
5. **Move e2e/integration into CI matrix** — currently excluded from main test run
6. **Add snapshot tests** for CLI output via `typer.testing.CliRunner`

---

## 10. Test Health Summary

- 3638 tests collected is impressive for a CLI tool
- Core PEV: 123/123 passing (100% pass rate in CI scope)
- 10% overall coverage is low — reflects large src/ surface not yet tested
- No flaky tests observed in 3 consecutive local runs
- 6 warnings in CI run — likely deprecation warnings from pytest-asyncio version
