# Open-Source Go-Live — 2026-08-16

## Change
License classifier in `pyproject.toml` was `BSD License` while the package declares `license = "MIT"` and ships an MIT `LICENSE` file. Changed classifier to `MIT License` to align triplet: `pyproject.toml license` + `LICENSE` file + PyPI classifier.

## De-risk
For open-source release the classifier is what PyPI surfaces to users. Mismatch silently advertises the wrong license — untenable when the git tree actually ships MIT.

## Go-live test command
`python3 -m pytest tests/cli/test_agent_commands.py -v`
`python3 -m ruff check src tests`

## Result
Commit `b42b8609` — agent command tests pass (11/11).

## Lint debt
53 ruff errors remain in committed tree:

- `F841` unused variable assignments in test files: `tests/test_crash_detector.py:336` (`e2`), `tests/test_pev_self_healing.py:349` (`exe`), plus repeated pattern `results`, `api_key`, `REDACTED`, `hostile`, `ctx`, `status_value`, `child_task`
- `F804`/module-level import-order (`E402`) in test files including `tests/conftest.py`
- `F401` unused imports in a few source files that fall outside ruff `--fix` scope
- `F821` undefined names (mostly injected-placeholder style)

These are blocked in existing CI paths, do not affect open-source truthfulness or agent command tests. Follow-up in a dedicated lint debt sweep; don't add suppressions.