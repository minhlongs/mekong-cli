# Task — Wave 2 Implementation: Fix Defect 4 (Masked Broken Imports)

User authorization: "go" (2026-08-25) following Wave 1 merge (PR #4, squash 9b61cf3d7).

## Verbatim intent

Implement the next item in the audit's implementation order (docs/architecture/ARCHITECTURE_ASSESSMENT.md): Wave 1 explicitly deferred "defect 4 (masked broken imports)" as out of scope; it is now to be FIXED for real.

## Re-verified evidence at HEAD 9b61cf3d7 (2026-08-25)

The audit snapshot's paths drifted; current truth:

1. **`src/command_fabric/router.py:25`** — `from cli.tui.router import (...)` raises `ModuleNotFoundError: No module named 'cli.tui.router'` (target exists at `src/cli/tui/router.py`; missing `src.` prefix). Module is un-importable today. No internal importers found — verify consumers/tests before and after fix.
2. **`src/cli/commands/implement/__init__.py:188`** — `from src.mekongcli.core.verification import SQLiteGoalStore` raises ImportError: class actually lives at `src/mekongcli/core/goal_engine/store.py` (exported via `src.mekongcli.core.goal_engine`, canonical import used by `src/cli/cook_command.py:23`). The bad import masks the goal-engine path in the implement command.
3. **`src/agents/agi_bridge.py`** (`AGIBridge.start`, :30-45) — spawns `apps/openclaw-worker/task-watcher.js` which does NOT exist on disk → `start()` silently returns False; `src/commands/agi.py:12` is the only consumer. Fix must make this honest: fail-loud/report clearly when worker binary is absent, consistent with repo error-handling patterns. Do NOT invent a new Node daemon.

## Hard constraints

- DO NOT break protected flows: NOWPayments IPN webhook → tier activation; license gate chain (engine/license ↔ src/middleware/license_gate ↔ src/gateway.py)
- No new parallel architecture; no new daemons invented; reuse existing primitives
- Test parity: pytest fail-set must not grow beyond the frozen baseline (223 failed IDs archived at .orchestrate/archive/audit-refresh-7459010db/failed_tests_head_0878f966f.txt). Current state post-Wave-1: 223 failed / 7569 passed / 75 skipped. Fixing masked imports may legitimately turn some baseline-red tests green — count and note in PR. If an un-masked test reveals a NEW distinct failure not explainable by its own previously-masked import, treat as AMEND-worthy.
- ruff clean on src/ + tests/
- Real implementations only — no mocks/cheats
- Known pre-existing CI red on main (pnpm-lock.yaml config debt) remains out of scope

## Deliverable

Working code + real tests + PR merged to main + smoke evidence. Out of scope: dead-code deletion waves, plan()/delegate() upgrades, pnpm-lock CI debt.
