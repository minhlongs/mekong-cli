# Phase 3 — Pytest Config Consolidation

**Goal:** Single canonical pytest config in `pytest.ini`.

## Changes

- Removed `[tool.pytest.ini_options]` from `pyproject.toml`
- Consolidated `pytest.ini` with `pythonpath = src`, comprehensive `norecursedirs`
- Dropped dead `tests/python` reference

## Acceptance

- No `[tool.pytest.ini_options]` warning in pytest output
- pytest.ini is the sole config source
