# v6.11.0 — Test Suite Green Reset & CI Hardening

> Stabilization push: tighten pytest reliability, scope file_stats, repair stale imports.

## Status

| Phase | Name | Status |
|-------|------|--------|
| 1 | pytest-timeout integration | ✅ Complete |
| 2 | file_stats scoping + traversal guard | ✅ Complete |
| 3 | pytest config consolidation | ✅ Complete |
| 4 | Stale .orchestrate gitignore | ✅ Complete |
| 5 | Docs sync (roadmap + changelog) | ✅ Complete |
| 6 | Release (commit + PR + merge) | 🔄 In Progress |
| 7 | Verification gate | ⏳ Pending |

## Goal

Ship a pure CI/test-infra stabilization release — no app behavior change. All existing
tests remain green, file_stats scans only `src/`, pytest config has a single canonical
source, and CI enforces a 60s per-test timeout.

## Scope

- Add pytest-timeout to CI and local deps.
- Scope `file_stats` to `src/` with path traversal guard.
- Consolidate pytest config into `pytest.ini` (remove pyproject.toml duplicate).
- Repair stale `cli/` imports in tracked files.
- Add `.orchestrate/` to `.gitignore`.
- Update roadmap + changelog.

## Non-Goals

- No new features.
- No app logic change (file_stats output shape preserved).
- No DNA/gate changes (no src/cli files touched beyond file_agent.py).

## Verification

1. `ruff check src/ tests/` — 0 errors.
2. `build_app().registered_groups == 39`.
3. Full pytest suite passes.
4. `tests/unit/test_file_agent_stats.py` — 7/7 pass.
5. No `[tool.pytest.ini_options]` warning in pytest output.
