# Testing Strategy

## Overview

This document defines the comprehensive testing strategy for the Mekong CLI platform. The test suite is organized into multiple layers, each serving a distinct purpose in ensuring quality, security, and performance.

## Test Pyramid

```
          /\
         /E2E\          10 critical user journeys + Playwright specs
        /------\
       /Security\      Advanced security E2E tests
      /----------\
     /Integration\    RaaS, Stripe, orchestrator, plugin integration
    /--------------\
   /Contract\       OpenAPI schema validation (schemathesis)
  /--------------\
 /Performance\     Benchmark suite (latency, throughput)
/----------------\
   Unit Tests     Extensive module-level tests (>80% coverage)
```

## Test Categories

### 1. Unit Tests (`tests/unit/`)

**Purpose:** Validate individual components in isolation.

**Scope:**
- Core modules (PEV engine, LLM router, memory store)
- Agents (GitAgent, FileAgent, ShellAgent)
- Utilities and helpers
- Command fabric (before plugin migration)

**Coverage Target:** >80% line coverage for `src/`

**Run:** On every commit via pre-commit hook and CI.

**Example:**
```bash
pytest tests/unit/test_nlu.py -v
```

### 2. Integration Tests (`tests/integration/`)

**Purpose:** Verify interactions between multiple components with real implementations.

**Scope:**
- PEV orchestrator full flow
- RaaS mission lifecycle (create → execute → bill)
- Stripe webhook processing
- License gate enforcement
- MCP server protocol
- Governance policy evaluation

**Key Characteristics:**
- Use isolated SQLite databases via `tmp_path`
- Mock external services (LLM, Stripe, email) by default
- Autouse fixtures truncate tables between tests
- Test real database transactions and middleware

**Run:** On every PR via `integration` job in CI.

**Example:**
```bash
pytest tests/integration/test_raas_integration.py -v
```

### 3. E2E Critical Journeys (`tests/e2e/critical_journeys/`)

**Purpose:** Simulate real user scenarios from API request to final state.

**The 10 Critical Journeys:**

1. **Finance Command Execution** (`test_journey_01_finance_command.py`)
   - User signs up → logs in → executes finance command → billing verification

2. **Stripe Purchase Flow** (`test_journey_02_stripe_purchase.py`)
   - Checkout → webhook → credit addition → balance update

3. **Plugin Install and Execution** (`test_journey_03_plugin_install_execute.py`)
   - Upload → install → command run → sandbox verification

4. **Admin User Management** (`test_journey_04_admin_user_management.py`)
   - Admin creates user → adjusts credits → views reports

5. **Credit Exhaustion and Recovery** (`test_journey_05_credit_exhaustion_recovery.py`)
   - Fund → exhaust → 402 → purchase → recover

6. **Rate Limit Retry** (`test_journey_06_rate_limit_retry.py`)
   - Trigger 429 → wait → retry succeeds

7. **Plugin Dependency Resolution** (`test_journey_07_plugin_dependencies.py`)
   - Plugin with deps → auto-install order → execution

8. **Token Refresh Flow** (`test_journey_08_token_refresh.py`)
   - Expired JWT → refresh → continue

9. **Concurrent Billing Accuracy** (`test_journey_09_concurrent_billing.py`)
   - Parallel requests → no negative balance → correct total

10. **Audit Trail Verification** (`test_journey_10_audit_trail.py`)
    - All actions logged → immutable → queryable

**Shared Fixtures:** `tests/e2e/critical_journeys/conftest.py` provides:
- Isolated database per test
- Tenant and user factories
- Mock external services (LLM, Stripe, email)
- App factories with dependency overrides
- Test data generators

**Run:** Daily at 2 AM UTC and on-demand via `e2e-tests.yml` workflow.

### 4. OpenAPI Contract Tests (`tests/contract/`)

**Purpose:** Ensure API implementation matches the OpenAPI specification 100%.

**Tool:** `schemathesis` - property-based testing against OpenAPI schema.

**Scope:**
- All API endpoints (`/missions`, `/billing/*`, `/auth/*`, `/admin/*`)
- Request/response validation
- Error response formats
- Status code compliance

**Example:**
```bash
pytest tests/contract/test_openapi.py -v
```

**Coverage Goal:** 100% of endpoints and operations.

### 5. Security Tests (`tests/security/`)

**Purpose:** Detect vulnerabilities and ensure security controls are effective.

#### Standard Security Tests (`tests/security/`)
- Basic auth checks
- JWT validation
- Input sanitization

#### Advanced E2E Security (`tests/security/advanced/`)
- **SQL Injection:** Attempt injection via mission goals, billing params
- **JWT Manipulation:** Tamper with exp, sub, admin claims
- **Rate Limit Bypass:** Spoof X-Forwarded-For, rotate user agents
- **Sandbox Escape:** Plugin code with path traversal, system calls
- **XSS:** Script tags in user input, admin reports
- **RBAC Bypass:** Privilege escalation attempts
- **API Key Brute Force:** Invalid key handling

**Run:** Nightly and on PRs with security changes.

### 6. Performance Benchmarks (`tests/benchmarks/`)

**Purpose:** Track latency and throughput regressions.

**Tool:** `pytest-benchmark` with stored baselines.

**Key Metrics:**
- Mission creation latency: p95 < 500ms
- Authentication flow: p95 < 200ms
- Credit deduction: p95 < 50ms
- Database queries: p95 < 10ms
- CLI startup time: <500ms

**Thresholds:** Defined in `pyproject.toml` or `.benchmarks.yml`.

**Run:** Nightly via `benchmarks` job; track trends over time.

**Example:**
```bash
pytest tests/benchmarks/test_performance.py --benchmark-only
```

### 7. CLI Unit Tests (`tests/cli/`)

**Purpose:** Verify CLI argument parsing, command dispatch, and output formatting.

**Scope:**
- Help text and version output
- Command routing and execution
- JSON/YAML output formatting
- Error messages and exit codes
- Config file handling

**Tool:** `click.testing.CliRunner` for command simulation.

**Example:**
```bash
pytest tests/cli/test_commands.py -v
```

## CI/CD Integration

### GitHub Actions Workflows

| Workflow | Trigger | Jobs | Duration |
|----------|---------|------|----------|
| `test.yml` | PR, push | unit, integration, contract, security-tests, benchmarks, cli-tests | ~25 min |
| `e2e-tests.yml` | Daily 2 AM, PR, manual | e2e-tests | ~30 min |
| `load-testing.yml` | Nightly | k6 load tests | ~1 hour |
| `ci.yml` | PR, push | backend (build check), typescript, security scan | ~15 min |

### Job Matrix

- **Unit tests:** Python 3.11, 3.12 (matrix)
- **Integration/E2E:** Python 3.12 with Postgres + Redis services
- **TypeScript:** Node.js 22 with pnpm

### Coverage Reporting

- Unit tests: `--cov=src` with 70% minimum
- Integration: `--cov=tests.integration` (separate reporting)
- E2E: `--cov=tests.e2e` (separate artifact)
- All coverage reports uploaded as artifacts and to Codecov (if configured)

### Test Selection

To run specific categories locally:

```bash
# Unit only
pytest tests/unit/ -k "not e2e and not integration"

# Integration only
pytest tests/integration/ -k "not e2e"

# E2E only
pytest tests/e2e/ -k "not unit and not integration"

# Security only
pytest tests/security/ -v

# Performance only
pytest tests/benchmarks/ --benchmark-only

# CLI only
pytest tests/cli/
```

## Test Data Management

### Isolation

- **Database:** Each test gets a fresh SQLite file via `tmp_path` fixture.
- **Redis:** Mocked in tests; use ` fakeredis` or skip in CI with real Redis service.
- **File system:** Use `tmp_path` for any file writes; auto-cleaned after test.

### Fixtures

- `conftest.py` at root and in each subdirectory.
- Shared fixtures in `tests/conftest.py`:
  - `db_path` - isolated SQLite path
  - `tenant_store` - TenantStore instance
  - `credit_store` - CreditStore instance
  - `app_with_auth` - FastAPI app with test auth override
- E2E-specific fixtures in `tests/e2e/critical_journeys/conftest.py`

### External Service Mocking

- **Stripe:** `patch('src.billing.stripe.StripeCustomer.retrieve')` → mock object
- **LLM:** `patch('src.llm.router.LLMRouter.chat_completion')` → mock response
- **Email:** `patch('src.email.service.EmailService.send')` → return True
- **Polar Webhooks:** Send test payloads with `Stripe-Signature: test-signature`

## Flaky Test Prevention

1. **No timing dependencies:** Use deterministic mocks, not `time.sleep()`
2. **Database cleanup:** Autouse fixtures truncate all tables after each test
3. **Idempotency:** Tests can run in any order; no shared state.
4. **Parallel safe:** Tests use unique tmp_path; no global caches.
5. **Explicit waits only:** For async operations, poll with timeout rather than fixed sleep.

If a test is flaky:
1. Mark with `@pytest.mark.flaky(reruns=3)` temporarily
2. Investigate root cause (race condition, DB leak, external call)
3. Fix or rewrite with better isolation

## Performance Testing

### pytest-benchmark

Baseline results stored in `tests/benchmarks/baselines.json`. CI compares current run against baseline and fails if regression >10%.

### Load Testing (k6)

Separate k6 scripts in `load-tests/`:
- `missions-api.js` - simulate 100 concurrent users
- `websocket-runner.js` - real-time agent execution
- `cli-load.js` - spawn multiple CLI processes

Run nightly via `load-testing.yml` with thresholds:
- p95 < 500ms
- Error rate < 0.1%
- Throughput > 100 RPS

## Security Testing

### Static Analysis

- **Bandit:** Python security scanner (run in gates.yml)
- **Semgrep:** Multi-language security rules
- **Trivy:** Dependency vulnerability scanning

### Dynamic Analysis

- E2E security tests (SQLi, XSS, JWT manipulation)
- OWASP ZAP baseline scan (weekly)
- Penetration testing (quarterly, external auditor)

### Secrets Detection

Pre-commit hook blocks commits with:
- Hardcoded API keys
- Passwords in strings
- JWT secrets in code

CI job in `ci.yml` greps for patterns and fails.

## Test Documentation

Every test file must include:
- Module docstring describing test scope
- Fixture docstrings explaining purpose and return type
- Test function docstrings with scenario description
- Inline comments for complex setup/assertion logic

## Running Tests Locally

### Prerequisites

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .
pip install pytest pytest-cov pytest-asyncio anyio "httpx<0.28" pytest-benchmark schemathesis pyyaml click
```

### Run All Tests

```bash
# Full suite (unit + integration + e2e) - may take 10+ minutes
pytest tests/

# By category
pytest tests/unit/ tests/integration/ tests/e2e/ -v

# With coverage
pytest tests/ --cov=src --cov-report=html
open htmlcov/index.html
```

### Run Specific Test File

```bash
pytest tests/e2e/critical_journeys/test_journey_05_credit_exhaustion_recovery.py -v
```

### Run with Debug Logging

```bash
pytest tests/ -v --log-cli-level=DEBUG
```

## Troubleshooting

### Import Errors

Ensure `PYTHONPATH` includes project root:
```bash
export PYTHONPATH=$PWD
```

### Database Locked

Tests use SQLite; parallel runs can conflict. Use `-n auto` with `pytest-xdist` carefully, or run single-threaded.

### Redis Connection Refused

Mock Redis in unit/integration tests. For E2E, ensure Redis service is running or skip tests.

### Stripe API Errors

All Stripe calls are mocked in tests. If un-mocked, set `STRIPE_SECRET_KEY=sk_test_xxx` and `STRIPE_WEBHOOK_SECRET=whsec_xxx` in env.

### Slow Tests

Use `pytest -m "not slow"` to skip tests marked `@pytest.mark.slow`. Currently none marked; consider marking E2E as slow.

## Future Improvements

- [ ] Add mutation testing with `cosmic-ray`
- [ ] Implement contract testing with Pact for service-to-service
- [ ] Add visual regression testing for Playwright specs
- [ ] Integrate with Sentry for error tracking in tests
- [ ] Automated baseline updates for benchmarks (on approved performance improvements)
- [ ] Fuzzing integration for API endpoints

## References

- [pytest documentation](https://docs.pytest.org/)
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/)
- [schemathesis](https://schemathesis.readthedocs.io/)
- [FastAPI testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [OWASP Testing Guide](https://owasp.org/www-project-web-security-testing-guide/)

---

**Last Updated:** 2026-06-20
**Owner:** CTO (OpenClaw)
**Review Cycle:** Quarterly
