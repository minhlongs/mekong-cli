# Phase 7 — Verification Gate

**Goal:** Prove all acceptance criteria before finalize.

## Checks

1. `ruff check src/ tests/` — 0 errors
2. `build_app().registered_groups == 39`
3. `python3 -m pytest tests/ -q` — all pass
4. `python3 -m pytest tests/unit/test_file_agent_stats.py -v` — 7/7 pass
5. No `[tool.pytest.ini_options]` warning in pytest output
6. `.orchestrate/` untracked

## Acceptance

- All checks pass
- No regressions
