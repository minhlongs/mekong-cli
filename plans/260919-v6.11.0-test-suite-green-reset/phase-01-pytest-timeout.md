# Phase 1 — pytest-timeout Integration

**Goal:** Add pytest-timeout to CI and local deps, wire `--timeout=60` into pytest invocation.

## Changes

- `requirements.txt`: added `pytest-timeout>=2.2.0`
- `pyproject.toml`: added `pytest-timeout = "^2.2.0"` under dev deps
- `.github/workflows/test.yml`: added to pip install line + `--timeout=60` flag
- `tests/CLAUDE.md`: updated timeout docs

## Acceptance

- `pip install pytest-timeout` succeeds
- CI pytest runs with `--timeout=60`
- Hung tests fail fast instead of consuming runner
