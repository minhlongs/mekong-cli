# Fix Remaining Test Failures

## Overview
Fix 14 integration test failures after full suite sweep.

## Context
- Source insight: `tests/integration/test_ask_routing.py`
- Root cause insight: `ask_cmd` routes via `subprocess.run([sys.executable, "-m", "src.main", ...])` with `PYTHONPATH=src/`, but `-m src.main` needs the **repo root** on PYTHONPATH so `src/` resolves as a package root. Currently it gets `src/` which makes Python look for `src/src/main.py` and exit 1.
- Verified test insight: `test_provision_missing_customer` expects 200 status + `credits_provisioned == 0` when Stripe customer lookup returns `None`; current code falls through to `CreditStore().add_credits(...)` regardless.

## Key Insight
- The `pytest.ini` `pythonpath` change didn't apply; pytest reports "ignoring pytest config in pyproject.toml!" and still uses `/Users/macbook/mekong-cli/pytest.ini`. The parallel fix via `src.cli.__init__.py` also didn't fire because pytest's assertion-rewrite hook intercepts module imports before `__init__.py` runs.
- Real cause: `ask_cmd` uses `PYTHONPATH=src` for `python -m src.main`. For `-m src.main` to work from any cwd, PYTHONPATH needs to be the **repo root** (where `src/` is a directory), not `src/` itself.

## Phases

### Phase 1 — Fix ask routing (7 failures)
- **Files to modify**: `src/commands/core_commands.py`
  - Add `from pathlib import Path` (already imported `os`, `subprocess`, `sys`)
  - Add `REPO_ROOT = str(Path(__file__).resolve().parent.parent.parent)`
  - Change `subprocess.run(...)` env to use `PYTHONPATH=REPO_ROOT` instead of `PYTHONPATH=os.path.dirname(os.path.dirname(__file__))` (= `src/`)
  - Change `cwd=os.path.dirname(os.path.dirname(__file__))` to `cwd=REPO_ROOT`
- **Success criteria**: `pytest tests/integration/test_ask_routing.py` → 0 failures

### Phase 2 — Fix Stripe missing-customer (1 failure)
- **Files to modify**: `src/api/billing_endpoints.py`
  - Move credit provisioning block (`evaluate_trial`, `CreditStore().add_credits`, `credits_provisioned = credits`, `logger.info(...)`) **inside** the `if customer:` block (currently it runs regardless)
- **Success criteria**: `pytest tests/integration/test_stripe_checkout_webhook.py` → 0 failures

### Phase 3 — Verify
- Run `pytest tests/integration/test_ask_routing.py tests/integration/test_stripe_checkout_webhook.py -v`
- Expect 0 failures

## Anti-rationalization
- Do NOT change test assertions to match broken behavior — fix the code
- Do NOT add mocks — fix the real subprocess path
- Do NOT revert the `pytest.ini`/`pyproject.toml` changes yet — keep and verify
