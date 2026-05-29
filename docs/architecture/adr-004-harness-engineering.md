# ADR-004: Anti-Gravity E2E Test Harness Framework

## Status
Accepted

## Context
The Anti-Gravity 2.0 runtime requires a structured mechanism to execute 60 E2E tests across two distinct tracks:
1. **Mock Track**: Uses the Python CLI mock shim (`tests/e2e/mock_antigravity.py`).
2. **Production Track**: Uses the compiled Rust binary (`/Users/macbook/mekong-cli/antigravity/hybrid_runtime/target/debug/antigravity`).

Running these tests manually via `pytest` requires complex environment variables (`ANTIGRAVITY_BIN`, `ANTHROPIC_API_KEY`, etc.) and doesn't produce visual, high-fidelity summaries or automatic markdown reports. This makes tracking test results difficult for developers and AI agents alike, violating the verification rules requiring visual verification of test suite health.

## Decision
We will build a custom CLI Test Harness runner (`tests/e2e/harness.py`). It will:
- Wrap `pytest` execution programmatically.
- Provide simple flags to switch between Mock (`--mock`) and Production (`--prod`) tracks.
- Automate configuration of essential environment variables (injecting `ANTHROPIC_API_KEY=mock_key` in mock mode if unset).
- Enable filtering by Feature (F1–F5) and Tier (1–4) via command-line arguments.
- Execute tests using `pytest-xdist` or multiprocess workers if parallel flag is set.
- Automatically generate a markdown report under `docs/reports/harness-run-report.md` displaying execution details, pass/fail status, errors, and target track.

## Rationale
- **Simplicity**: Users can run a single command (`python3 tests/e2e/harness.py --mock`) instead of writing long, error-prone shell command lines.
- **Auto-verification**: Storing test reports directly in the workspace enables visual confirmation of test state by downstream agents.
- **Robustness**: Automated fallback and validation checks (e.g. check binary existence before running in production mode) prevent invalid execution states.

## Trade-offs
- A custom wrapper script adds a small amount of extra code to maintain. However, keeping the script light and leveraging standard library modules (like `argparse`, `subprocess`, `sys`) mitigates this complexity.

## Consequences
- **Positive**: Simple one-line test execution, automated test reports, and programmatic track configuration.
- **Negative**: Custom runner configuration might need updates if pytest arguments change significantly.
- **Mitigation**: Keep the arg parsing generic and forward unrecognized arguments to pytest.
