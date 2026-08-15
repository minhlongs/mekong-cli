# Mekong CLI Testing Summary

**Last Updated:** 2026-06-21  
**Overall Coverage:** 94%+

---

## Test Suite Overview

Mekong CLI maintains a comprehensive test suite covering unit, integration, E2E, stress, and load testing.

### Test Statistics

| Test Type | Count | Pass Rate | Coverage |
|-----------|-------|-----------|----------|
| Unit Tests | 450+ | 98% | Core modules |
| Integration Tests | 120+ | 96% | Cross-component |
| E2E Tests | 80+ | 94% | Full workflows |
| Stress Tests | 21 | 100% | Isolation & recovery |
| Load Tests | 5 scenarios | - | Performance baselines |
| **Total** | **670+** | **~97%** | **94%+** |

---

## Test Breakdown

### Unit Tests (`tests/unit/`)

- **Core Engine:** planner, executor, verifier, orchestrator
- **Plugin System:** registry, loader, manager, health monitor, sandbox
- **Agents:** GitAgent, FileAgent, ShellAgent, LeadHunter, ContentWriter
- **LLM Router:** model selector, provider adapters, fallback chains
- **Billing:** MCU tracking, credit accounts, usage meter
- **Security:** permission registry, secret manager, sandbox enforcer

**Run:** `pytest tests/unit/ -v`

### Integration Tests (`tests/integration/`)

- Plugin registration and lifecycle
- Command discovery and execution
- Database transactions and rollbacks
- API endpoints (gateway, vn_pilot, vn_pricing)
- Webhook handlers (Zalo, Polar)
- Cache invalidation flows

**Run:** `pytest tests/integration/ -v`

### E2E Tests (`tests/e2e/`)

- User onboarding complete flow
- Plugin marketplace purchase and installation
- Plugin developer upload and publish
- Payment processing with Polar
- Zalo OA message handling
- CI/CD pipeline validation

**Run:** `pytest tests/e2e/ -v`

### Stress Tests (`tests/stress/`)

- Memory leak detection under plugin cycling
- Crash recovery from sudden plugin termination
- System stability with many failing plugins
- Resource exhaustion with 200+ plugins
- Concurrent registry modification
- Long-running stability (24h+)

**Run:** `pytest tests/stress/ -v`

**Status:** ✅ All 21 stress tests passing

### Load Tests (`load-tests/`)

- Concurrent agent execution (100 VUs, 60s)
- Plugin command throughput
- API gateway saturation
- Database connection pool limits
- Circuit breaker behavior under load

**Run:** `./scripts/run-load-tests.sh plugins` or `k6 run load-tests/k6/agent-concurrent.js`

---

## Performance Benchmarks

### Plugin System

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Plugin discovery (100 plugins) | <2s | 1.2s | ✅ |
| Plugin load time | <100ms | 45ms | ✅ |
| Command execution overhead | <10ms | 6ms | ✅ |
| Memory per plugin | <10MB | 3.2MB | ✅ |
| Throughput (single plugin) | >1000/s | 2500/s | ✅ |

### API Gateway

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| P50 latency | <50ms | 28ms | ✅ |
| P95 latency | <150ms | 85ms | ✅ |
| P99 latency | <300ms | 180ms | ✅ |

---

## Running Tests

### Full Suite

```bash
# All tests (unit + integration + e2e)
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# With coverage threshold
pytest --cov=src --cov-fail-under=90
```

### Specific Suites

```bash
# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# E2E tests (requires running services)
pytest tests/e2e/ -v

# Stress tests
pytest tests/stress/ -v -m stress

# Performance benchmarks (requires pytest-benchmark)
pytest tests/benchmarks/plugin/test_performance.py --benchmark-only
```

### Parallel Execution

```bash
# Run tests in parallel (faster)
pytest -n auto tests/
```

---

## CI/CD Integration

Tests run automatically on:

- **Push to main/develop:** Full test suite with coverage
- **Pull requests:** Unit + integration tests (fast feedback)
- **Nightly:** Full suite including E2E and stress tests

**Quality Gates:**

- All tests must pass (0 failures)
- Coverage ≥ 90% on changed files
- No new critical security vulnerabilities
- Performance benchmarks within 10% of baseline

See `.github/workflows/` for CI configurations.

---

## Test Coverage Reports

HTML coverage reports are generated in `htmlcov/`:

```bash
pytest --cov=src --cov-report=html
open htmlcov/index.html
```

Reports include:

- Line coverage per module
- Branch coverage
- Missing lines highlighted
- Per-file breakdown

---

## Writing Tests

### Guidelines

1. **One test file per module:** `test_<module_name>.py`
2. **Use fixtures** for common setup/teardown
3. **Mock external dependencies** (LLM APIs, file I/O, network)
4. **Test error paths** not just happy paths
5. **Keep tests deterministic** (no random, no time.sleep without mocking)
6. **Clean up resources** (temp files, database records)

### Example

```python
def test_plugin_loader_with_invalid_plugin(tmp_path):
    """PluginLoader should skip invalid plugins gracefully."""
    plugin_file = tmp_path / "bad_plugin.py"
    plugin_file.write_text("not valid python syntax")

    loader = PluginLoader()
    loader.discover_local(plugin_dir=tmp_path)

    assert loader.plugin_count == 0  # Skipped, no crash
```

---

## Performance Testing Philosophy

We maintain:

1. **Regression benchmarks** - Track performance over time, alert on degradation >10%
2. **Load capacity tests** - Verify system handles 2x expected load
3. **Stress tests** - Push to breaking point to find failure modes
4. **Isolation tests** - Ensure plugin failures don't cascade

---

## Troubleshooting

### Tests fail with import errors

```bash
# Ensure dependencies installed
poetry install --with dev
# or
pip install -r requirements.txt
```

### E2E tests timeout

E2E tests require services running (API gateway, database). See `GO_LIVE_PLAYBOOK.md` for setup.

### Coverage not reporting

Make sure tests actually import the code. Pytest-cov only tracks imported modules.

---

## References

- [Performance Tuning Guide](./performance-tuning.md)
- [Plugin System Architecture](./architecture/plugin-architecture.md)
- [Testing Foundation Plan](../plans/testing-foundation-status-report.md)
