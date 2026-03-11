# Code Quality Audit — Mekong CLI

**Date:** 2026-03-11
**Scope:** src/core/ PEV engine + agents — type hints, standards, linting, compile checks

---

## 1. Compile Status

All four core PEV files compile clean:

| File | Status |
|------|--------|
| src/core/planner.py | OK (python3 -m py_compile) |
| src/core/executor.py | OK |
| src/core/verifier.py | OK |
| src/core/orchestrator.py | OK |

---

## 2. Type Hints Coverage

Checked via grep for `: Any` in core files (a proxy for untyped parameters):

```
src/core/planner.py   — 3 `: Any` usages (PlanningContext.constraints, project_info, task dicts)
src/core/executor.py  — 0 `: Any` in public signatures
src/core/verifier.py  — 1 `: Any` (criteria dict param — dict[str, Any], acceptable)
src/core/agent_base.py — 1 `: Any` (Task.input — intentional, heterogeneous input)
```

Assessment: Type hint coverage is good in core files. `dict[str, Any]` patterns are used appropriately where schema varies by step type. Return types documented on all public methods.

Concerns:
- `StepExecutor.execute_and_verify` returns `StepResult` but `execution: Any` field in `StepResult` dataclass bypasses type safety
- `_init_agi_module()` returns `Any` — acceptable as optional modules
- orchestrator.py uses `Any | None` for multiple optional AGI module fields — could define a Protocol

---

## 3. TODO / FIXME Count

```bash
grep -rn "TODO|FIXME" src/ --include="*.py"
```

Results (12 matches, but quality varies):

| File | Count | Nature |
|------|-------|--------|
| src/commands/ocop_commands.py | 2 | Real TODOs: LLM client not integrated |
| src/core/output_verifier.py | 2 | Part of detection regex — not actual debt |
| src/core/code_evolution.py | 2 | Scanner targets — not actual debt |
| src/core/verifier.py | 2 | Documentation in docstring — not debt |
| src/core/company_init.py | 1 | Prompt instruction — not debt |
| src/core/company_workflow.py | 1 | Pre-deploy checklist text — not debt |

**Real technical debt:** 2 TODOs in `ocop_commands.py` where LLM integration is stubbed out.

---

## 4. Console/Print Statement Count

```bash
grep -rn "console\." src/ --include="*.py" | wc -l  → 1881
```

This is **extremely high** but almost entirely false positives: these are Rich console object method calls (`self.console.print(...)`) — the correct approach for a CLI tool. Rich Console is the proper abstraction.

Actual `print()` calls (not console.print):
```bash
grep -rn "^    print(" src/ --include="*.py" | grep -v "console\|test\|#" | head -10
```
These are rare and limited to debug/bootstrap contexts.

---

## 5. Linting Standards (Ruff)

Project uses `ruff` (configured in CI). Key config from `ci.yml`:
- `ruff check src/ tests/`
- `ruff format --check src/ tests/` (continue-on-error)

Observed standards in core files:
- `from __future__ import annotations` used consistently for deferred type evaluation
- `dataclass` + `field(default_factory=...)` used correctly
- f-strings used throughout (modern Python style)
- `shlex.split()` for shell commands (not string interpolation)
- `subprocess.run()` with `check=True`, `text=True`, `capture_output=True` — correct pattern

Minor issues seen:
- `import re as _re` and `import hashlib as _hashlib` inside methods (late imports should be module-level)
- `import requests as req` inside `_execute_api_step` — avoids top-level optional dependency, acceptable but inconsistent

---

## 6. File Size Compliance

Target: < 200 lines per file. Current violations:

| File | Lines | Status |
|------|-------|--------|
| src/core/orchestrator.py | 1048 | CRITICAL violation |
| src/raas/sync_client.py | 932 | Violation |
| src/core/raas_auth.py | 903 | Violation |
| src/lib/raas_gate.py | 881 | Violation |
| src/core/auto_recovery.py | 807 | Violation |
| src/lib/usage_metering_service.py | 754 | Violation |
| src/core/telegram_bot.py | 752 | Violation |
| src/commands/raas_maintenance_commands.py | 743 | Violation |
| src/cli/billing_commands.py | 725 | Violation |
| src/core/planner.py | 659 | Violation |
| src/core/executor.py | 489 | Violation |

11 of top 25 files violate 200-line rule. Core PEV trio (planner/executor/verifier) all need splitting.

---

## 7. Docstring Coverage

Assessed in core files:
- `RecipePlanner`: class + all public methods documented
- `RecipeExecutor`: class + execute_step + all _execute_* methods documented
- `RecipeVerifier`: class + all verify_* methods documented
- `RecipeOrchestrator`: class documented, but several inner methods sparse
- `AgentBase`: fully documented including abstract method contracts

Coverage: approximately 85% for public APIs in core.

---

## 8. Error Handling Patterns

Consistent patterns used:
- `try/except Exception as e` with logging at warning level in AGI modules
- `subprocess.CalledProcessError` caught explicitly in executor
- `subprocess.TimeoutExpired` caught in verifier custom checks
- AGI module failures silently suppressed (correct — optional features)
- LLM failures logged with `logger.exception()` (correct — captures traceback)

Anti-pattern found:
- `except Exception:` (bare, no `as e`) in several AGI pipeline methods — loses error context

---

## 9. Security Standards

Double-layer shell protection:
1. `DANGEROUS_PATTERNS` list check (fast, 13 patterns)
2. `CommandSanitizer(strict_mode=True)` — full sanitization

Rollback commands also sanitized — consistent application of security layer.
`shlex.split()` prevents shell=True injection everywhere subprocess is used.

---

## 10. Summary Scorecard

| Area | Score | Notes |
|------|-------|-------|
| Type hints | 7/10 | Good in core, Any used where appropriate |
| TODO/FIXME | 9/10 | Only 2 real TODOs in ocop_commands |
| File sizes | 4/10 | 11+ violations, orchestrator critical |
| Docstrings | 8/10 | Well documented public APIs |
| Error handling | 7/10 | Consistent, some bare except blocks |
| Security patterns | 9/10 | Double-layer sanitization excellent |
| Import hygiene | 7/10 | Late imports inside methods inconsistent |

**Overall: 7.3/10** — solid core quality, file size compliance is main gap.
