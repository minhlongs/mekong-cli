# Tests — Quality Verification Layer

> **第十篇 地形 (Di Xing)** — Know the terrain: quality gates enforce victory conditions
>
> This file governs CC CLI behavior ONLY when working inside `tests/`.
> Inherits from root `CLAUDE.md` (Constitution) and `~/.claude/CLAUDE.md` (Global).

## Identity

**Role:** Test suite for the Mekong CLI Python engine
**Framework:** pytest (Python 3.9.6 system Python)

## Test Suite

| Test File | Module | Tests |
|-----------|--------|-------|
| `test_content_writer.py` | ContentWriter agent | Content generation |
| `test_lead_hunter.py` | LeadHunter agent | Lead discovery |
| `test_recipe_crawler.py` | RecipeCrawler agent | Recipe file discovery |
| `test_git_agent.py` | GitAgent | Git operations |
| `test_file_agent.py` | FileAgent | File operations |
| `test_shell_agent.py` | ShellAgent | Shell commands |
| `test_orchestrator_integration.py` | Orchestrator | Full Plan→Execute→Verify |
| `test_self_healing.py` | Self-healing | AI command correction |
| `test_telemetry.py` | Telemetry | Execution tracing |
| `test_memory.py` | MemoryStore | Goal→recipe matching |
| `test_nlu.py` | IntentClassifier | NLU classification |
| `test_smart_router.py` | SmartRouter | Intent→recipe routing |
| `test_gateway.py` | Gateway | FastAPI server |
| `test_cook_command.py` | Cook CLI command | End-to-end cook flow |
| `test_governance.py` | Governance | Policy enforcement |
| `test_autonomous.py` | Autonomous mode | Auto-execution |

**Total:** 62 tests | **Runtime:** ~2.5 minutes

## Development Rules (Domain-Specific)

### Running Tests
```bash
python3 -m pytest                    # Full suite
python3 -m pytest tests/test_nlu.py  # Single file
python3 -m pytest -x                 # Stop on first failure
python3 -m pytest -v                 # Verbose output
```

### Critical Warnings
- Use `python3` NOT `python` (not available on this Mac)
- pytest-timeout IS installed — use `--timeout=60` in CI to catch hung tests
- Suite takes ~4min; `file_stats` now scans only `src/` subtree (was full repo)
- Test files MUST use snake_case `test_*.py` (overrides kebab-case rule)

### Writing Tests
- One test file per module: `test_{module_name}.py`
- Use `unittest.mock.patch` for external dependencies (LLM calls, file I/O)
- DO NOT use fake data or mocks that bypass real logic
- Test error scenarios, not just happy paths
- Every new module in `src/core/` or `src/agents/` needs a test file

### Test Quality
- No `@pytest.mark.skip` without documented reason
- No `assert True` placeholder tests
- All tests must be deterministic (no random, no network calls)
- Clean up any files created during tests (use `tmp_path` fixture)

## Quality Gates

- `python3 -m pytest` — 100% pass rate required before commit
- New code must include tests
- Failed tests must be fixed, never ignored
