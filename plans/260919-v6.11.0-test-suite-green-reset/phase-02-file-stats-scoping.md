# Phase 2 — file_stats Scoping + Traversal Guard

**Goal:** Scope `file_stats` to `src/` subtree; add path traversal guard.

## Changes

- `src/agents/file_agent.py`:
  - Default `path` input = `"src"`
  - Resolve + guard with `Path.is_relative_to()`
  - Fallback to `src/` on traversal / `None` / non-existent
- `tests/unit/test_file_agent_stats.py`: 7 unit tests

## Acceptance

- Stats scan only `src/` by default
- Traversal attempt (`../../../etc`) falls back to `src/`
- `path=None` falls back without TypeError
- Non-existent path falls back to `src/`
