# Implementation Plan: Harness Engineering Test Runner Framework

## 🎯 Goal
Implement a custom Python test harness runner (`tests/e2e/harness.py`) to wrap `pytest` execution, support programmatically selecting Mock/Production tracks, filter by features or test tiers, and auto-generate markdown test run reports.

---

## 📅 Roadmap & Phases

### Phase 1: Preparation & Setup [DONE - 2026-05-29]
- **Step 2.1**: Initialize `tests/e2e/harness.py` with standard library imports (`argparse`, `os`, `sys`, `subprocess`, `time`, `pathlib`). [DONE]
- **Step 2.2**: Implement CLI argument parsing supporting: [DONE]
  - `--mock`: Run E2E tests against Python mock CLI shim (default).
  - `--prod` or `--production`: Run E2E tests against compiled Rust binary.
  - `--feature` or `-f`: Filter by Feature ID (F1–F5).
  - `--tier` or `-t`: Filter by Tier complexity (1–4).
  - `--parallel` or `-p`: Run tests in parallel using isolated workspace databases.
  - `--report`: Custom path for report generation (defaults to `docs/reports/harness-run-report.md`).
- **Step 2.3**: Implement environment variable injection logic: [DONE]
  - Mock mode: Auto-inject `ANTIGRAVITY_BIN="python3 tests/e2e/mock_antigravity.py"` and `ANTHROPIC_API_KEY="mock_key"` (if unset).
  - Production mode: Verify compiled Rust binary exists at `/Users/macbook/mekong-cli/antigravity/hybrid_runtime/target/debug/antigravity`.
- **Step 2.4**: Implement test execution logic that dynamically builds the `pytest` command line (forwarding filters and additional parameters) and captures standard output/error. [DONE]
- **Step 2.5**: Implement report generation logic to write a formatted markdown summary to `docs/reports/harness-run-report.md`. [DONE]

---

### Phase 2: Testing & Verification [DONE - 2026-05-29]
- **Step 3.1**: Run `python3 tests/e2e/harness.py --mock` and verify all 60 tests run successfully and generate the report. [DONE]
- **Step 3.2**: Verify that filtering works (e.g. `python3 tests/e2e/harness.py --mock --feature F1` runs only F1 tests). [DONE]
- **Step 3.3**: Verify that incorrect parameters (e.g., prod mode when Rust binary is not compiled/missing) fail gracefully with a clean user-facing error message. [DONE]

---

### Phase 3: Code Review & Quality Gates [DONE - 2026-05-29]
- **Step 4.1**: Audit code quality using Ruff linting. [DONE]
- **Step 4.2**: Verify adherence to KISS, DRY, and YAGNI. [DONE]
