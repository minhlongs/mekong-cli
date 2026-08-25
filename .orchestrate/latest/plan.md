# Wave 2 Plan — Fix Defect 4: Masked Broken Imports (3 sites)

**Branch**: `feat/wave2-masked-imports` from HEAD `9b61cf3d7`
**Baseline parity**: 223 failed / 7569 passed / 75 skipped
**Parity source**: `.orchestrate/archive/audit-refresh-7459010db/failed_tests_head_0878f966f.txt`

---

## 1. Reframed Problem

Three import sites are broken but hidden behind silent fallbacks: a wrong module path (`cli.tui.router` → `src.cli.tui.router`), a wrong submodule (`verification` → `goal_engine` for `SQLiteGoalStore`), and a missing entry script swallowed into `return False`. The fix is surgical — correct each import path / error behavior with zero architectural changes. The goal is to make the code honest: modules that claim to export something should actually be importable; failures should surface, not hide.

---

## 2. Work Checklist

### Step A — Fix `src/command_fabric/router.py:25` import path

**File**: `src/command_fabric/router.py`

**Change A1** (line 25):
```python
# BEFORE
from cli.tui.router import (
    CommandMatch,
    RouteEntry,
    get_all_commands,
    get_route_table,
)

# AFTER
from src.cli.tui.router import (
    CommandMatch,
    RouteEntry,
    get_all_commands,
    get_route_table,
)
```

**Change A2** (line 33 — docstring comment, update to match):
```python
# BEFORE
#    from cli.tui.router directly

# AFTER
#    from src.cli.tui.router directly
```

**Rationale**: The real module is `src/cli/tui/router.py`. Verified exports present: `RouteEntry` (dataclass, line 12), `CommandMatch` (dataclass, line 21), `get_route_table` (def, line 58), `get_all_commands` (def, line 62). No other file in the repo imports `command_fabric.router` (confirmed via grep), but this is a public surface documented in `docs/architecture/ARCHITECTURE_ASSESSMENT.md:144` — fix is mandatory.

**Acceptance criteria**:
```bash
python3 -c "from src.command_fabric.router import route_command, RouteTable; print('A-OK')"
# Expected: prints "A-OK" with no ModuleNotFoundError
```

---

### Step B — Fix `src/cli/commands/implement/__init__.py:188` import target

**File**: `src/cli/commands/implement/__init__.py`

**Change B1** (line 188):
```python
# BEFORE (line 187-189, inside _create_goal try block)
from src.mekongcli.core.goal_engine import GoalEngine
from src.mekongcli.core.verification import SQLiteGoalStore

# AFTER
from src.mekongcli.core.goal_engine import GoalEngine, SQLiteGoalStore
```

**Rationale**: `SQLiteGoalStore` is defined at `src/mekongcli/core/goal_engine/store.py:31` and re-exported via `src/mekongcli/core/goal_engine/__init__.py:19`. The old import path `src.mekongcli.core.verification` is a *package* (`verification/__init__.py`) that only exports `VerificationGate` and `VerificationPipeline` — `SQLiteGoalStore` was never there. The import always raised `ImportError`, silently falling back to subprocess. Canonical pattern confirmed at `src/cli/cook_command.py:23` and `src/cli/goal_commands.py:17`.

**Trace the codepath** (lines 176–200): `_create_goal()` tries the direct import, falls back to `subprocess.run(["python", "-m", "src.main", "goal", "create", ...])`. After fix, the direct path succeeds and the subprocess fallback is no longer exercised (but remains for resilience). No behavioral change to the fallback — just a new happy path.

**Acceptance criteria**:
```bash
python3 -c "from src.mekongcli.core.goal_engine import SQLiteGoalStore; print('B-OK')"
# Expected: prints "B-OK"

python3 -c "from src.cli.commands.implement import implement_app; print('B-IMPORT-OK')"
# Expected: prints "B-IMPORT-OK" — module loads without triggering the verification ImportError
```

---

### Step C — Fix `src/agents/agi_bridge.py` start() to fail honestly

**File**: `src/agents/agi_bridge.py`

**Change C1** (lines 35–37, in `start()`):
```python
# BEFORE
entry = self.worker_dir / "task-watcher.js"
if not entry.exists():
    return False

# AFTER
entry = self.worker_dir / "task-watcher.js"
if not entry.exists():
    raise FileNotFoundError(
        f"AGI daemon entry script not found: {entry}\n"
        "apps/openclaw-worker/task-watcher.js does not exist. "
        "Install the openclaw-worker package or disable AGI daemon features."
    )
```

**Change C2** (lines 47–48, in `start()` except block):
```python
# BEFORE
except FileNotFoundError:
    return False

# AFTER
except FileNotFoundError:
    raise  # Re-raise caller-facing errors; only system-level missing 'node' is caught below
except OSError as exc:
    raise RuntimeError(f"Failed to spawn AGI daemon process: {exc}") from exc
```

Note: The bare `except FileNotFoundError` catch was for the `subprocess.Popen(["node", ...])` case (node binary missing). After the change, the first `FileNotFoundError` (entry script check) is raised *before* Popen, so the except clause now only catches the system-level `node` binary missing case. We re-raise to avoid masking it.

**Contract update in consumer** `src/commands/agi.py:26-31`: The consumer already handles `ok = bridge.start()` returning False, printing red error and exiting. After fix, `bridge.start()` will raise `FileNotFoundError` instead of returning False. Update the consumer to catch it:

**Change C3** (`src/commands/agi.py:25-31`):
```python
# BEFORE
console.print("[dim]Starting Tom Hum daemon...[/dim]")
ok = bridge.start()
if ok:
    console.print("[green]Daemon started successfully[/green]")
else:
    console.print("[red]Failed to start daemon (task-watcher.js not found or node error)[/red]")
    raise typer.Exit(code=1)

# AFTER
console.print("[dim]Starting Tom Hum daemon...[/dim]")
try:
    bridge.start()
except FileNotFoundError as exc:
    console.print(f"[red]{exc}[/red]")
    raise typer.Exit(code=1)
except RuntimeError as exc:
    console.print(f"[red]{exc}[/red]")
    raise typer.Exit(code=1)
console.print("[green]Daemon started successfully[/green]")
```

**Rationale**: The task explicitly forbids inventing a new daemon. The correct behavior for a missing entry script is to raise a clear error with the exact missing path and remediation hint — not silently return False. The consumer (`src/commands/agi.py`) is the only importer of `AGIBridge` (confirmed via grep). The repo error-handling pattern (seen in `src/commands/build.py`, `src/commands/run.py`, `src/commands/dashboard_commands.py`) uses `console.print("[red]...")` + `raise typer.Exit(code=1)` — we follow this exactly.

**Acceptance criteria**:
```bash
python3 -c "
from src.agents.agi_bridge import AGIBridge
import tempfile, os
# Test 1: missing entry script raises FileNotFoundError
b = AGIBridge(mekong_dir=tempfile.mkdtemp())
try:
    b.start()
    print('FAIL: should have raised')
except FileNotFoundError as e:
    assert 'task-watcher.js' in str(e), f'Wrong message: {e}'
    print('C-OK')
"
# Expected: prints "C-OK"
```

---

## 3. Risks & Gates

### Protected flows — zero-touch verification

| Flow | File(s) | Risk |
|------|---------|------|
| NOWPayments IPN → tier activation | `src/api/webhooks/router.py`, `src/raas/nowpayments_router.py`, `src/gateway.py`, `src/middleware/license_gate.py` | NONE — none of the 3 defect files are in this chain |
| License gate engine | `src/seed/license/`, `src/middleware/license_gate.py` | NONE — no import path touched |

### Parity gate

- **Baseline**: 223 failed test IDs archived at `.orchestrate/archive/audit-refresh-7459010db/failed_tests_head_0878f966f.txt`
- **Post-fix rule**: fail-set must NOT grow. Legitimate green-flips (tests that were red due to masked imports now passing) are VALID and documented in PR body.
- **Method**: Run full pytest, diff fail-set against baseline, note any new failures (must be explainable as unmasked existing tests, not regressions).

### Quality gates

| Gate | Command | Expected |
|------|---------|----------|
| ruff clean | `ruff check src/ tests/` | 0 new errors |
| pytest parity | `pytest tests/ -v --tb=short 2>&1 \| tail -5` | failed ≤ 223 (may decrease) |
| No mock-che | Manual review | No new mock/patch of import paths in tests |

---

## 4. Ship Plan

### Pre-deploy checklist
1. Branch `feat/wave2-masked-imports` from HEAD `9b61cf3d7`
2. Apply Changes A1/A2, B1, C1/C2/C3 (5 file edits across 3 files)
3. Run `ruff check src/ tests/` — must be clean
4. Run `pytest tests/ -v --tb=short` — capture summary, diff fail-set vs baseline
5. Smoke all 3 fixes (python one-liners from acceptance criteria above)
6. Commit with conventional format (no plan codes in message/body)

### Branch & commit strategy

**Branch**: `feat/wave2-masked-imports`

**Commit 1**:
```
fix(router): correct cli.tui.router import path in command_fabric/router.py

The import `from cli.tui.router` was missing the `src.` prefix, causing
ModuleNotFoundError on import. Corrected to `from src.cli.tui.router`
matching the canonical path used elsewhere in the codebase.
```

**Commit 2**:
```
fix(implement): import SQLiteGoalStore from goal_engine, not verification

SQLiteGoalStore lives in src.mekongcli.core.goal_engine.store, not in
src.mekongcli.core.verification. The wrong import always raised ImportError,
falling back silently to subprocess. This restores the direct-import happy
path used by cook_command.py and goal_commands.py.
```

**Commit 3**:
```
fix(agi_bridge): raise on missing daemon entry script instead of silent False

AGIBridge.start() now raises FileNotFoundError with remediation guidance
when apps/openclaw-worker/task-watcher.js is absent. The consumer
(src/commands/agi.py) is updated to catch the error and display it.
```

### PR

- Title: `fix: correct three masked broken import paths (Wave 2)`
- Body: include parity table (baseline vs post-fix), list each fix with before/after, note green-flips if any
- CI verify with escrow logic (per PR #3/#4 pattern): `pnpm-lock` config debt is pre-existing red, out of scope

### CI verification steps
```bash
ruff check src/ tests/
pytest tests/ -v --tb=short
python3 -c "from src.command_fabric.router import route_command; print('A-OK')"
python3 -c "from src.mekongcli.core.goal_engine import SQLiteGoalStore; print('B-OK')"
python3 -c "
from src.agents.agi_bridge import AGIBridge
import tempfile
b = AGIBridge(mekong_dir=tempfile.mkdtemp())
try:
    b.start()
    print('FAIL')
except FileNotFoundError:
    print('C-OK')
"
```

### Post-merge

- Squash merge to main
- Smoke: run the 3 python one-liners on main
- **DO NOT deploy. DO NOT stage `.orchestrate/`.**

---

## 5. Assumptions

| # | Assumption | Confidence |
|---|-----------|------------|
| 1 | `src/cli/tui/router.py` is the intended target for `command_fabric/router.py` (not a stale root-level `cli/` package) | HIGH — confirmed by ARCHITECTURE_ASSESSMENT docs and canonical import pattern in `ask_keyword_router.py:14` |
| 2 | `SQLiteGoalStore` was never exported by `src/mekongcli.core.verification` — the import always failed | HIGH — `verification/__init__.py` exports only `VerificationGate`, `VerificationPipeline`; no `SQLiteGoalStore` anywhere in verification package |
| 3 | Tests that were masked-red due to these imports may now flip green; this is valid | HIGH — no test was written to assert the fallback behavior; the fallback was unintentional |
| 4 | `src/commands/agi.py` is the only consumer of `AGIBridge.start()` return value | HIGH — grep confirms only `src/commands/agi.py:12` imports AGIBridge |
| 5 | The `_create_goal` fallback to subprocess in `implement/__init__.py` still works after fix (defense-in-depth) | HIGH — fallback code path unchanged, only the try-block import corrected |
