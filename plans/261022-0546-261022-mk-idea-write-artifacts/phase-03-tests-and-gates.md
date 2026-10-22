---
title: "Phase 3: Tests and gates"
status: todo
---

# Phase 3: Tests and gates

## Overview

The CLI layer currently has no test coverage at all: `tests/test_idea_deep_opencore_brainstorm.py` exercises only `OpenCoreDeepBrainstormEngine`. Add tests for the behaviours this plan changes, then run the repo gates.

## Requirements

- [ ] A test asserts `mk idea run` writes more than one file and that one is `company.json`
- [ ] A test asserts `--json` output reports `written` paths that exist on disk
- [ ] A test asserts `--deep --dry-run` reaches IdeaLoop and emits `.mekong/idea/<run>/audit.jsonl`
- [ ] A test asserts `--dry-run` writes nothing while still printing the plan
- [ ] Existing suites stay green

## Implementation Steps

1. Extend `tests/test_idea_deep_opencore_brainstorm.py` with the four cases above, using `tmp_path` for output dirs and `CliRunner` (already the pattern in that file).
2. For the IdeaLoop case, monkeypatch the LLM client so no network call is made and assert on `audit.jsonl`.
3. Run `python3 -m pytest tests/test_idea_deep_opencore_brainstorm.py tests/test_opencore_saas_25_step_suite.py -q` — baseline is 12 passed and must not regress.
4. Run the LOC invariant test for the touched modules if one exists.
5. Report the exact pass counts.

## Files

- `tests/test_idea_deep_opencore_brainstorm.py`
- `src/cli/idea_commands.py` (fixes only)

## Todo

- [ ] four new tests added
- [ ] targeted suites pass
- [ ] LOC guard respected (src/ non-test ceiling 185)

## Success Criteria

`pytest tests/test_idea_deep_opencore_brainstorm.py tests/test_opencore_saas_25_step_suite.py -q` reports 12 passed plus the new cases; every new test fails if its corresponding behaviour is reverted.
