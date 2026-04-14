# Code Review: Solo Company Operations (Phase 1+2)

**Date:** 2026-03-25
**Reviewer:** code-reviewer agent
**Verdict:** COMMENT (no blocking issues, several improvements recommended)

---

## Scope

| File | LOC | Focus |
|------|-----|-------|
| `src/daemon/llm_config.py` | 166 | Tri-model registry + capability map |
| `src/daemon/heartbeat_scheduler.py` | 347 | Loop discovery, cron parse, scheduler |
| `.mekong/heartbeat-config.json` | 32 | Production config |
| `.mekong/loops/*.json` (5 files) | ~115 | Loop definitions |
| `scripts/start-solo-ops.sh` | 87 | tmux launcher |
| **Total** | **~747** | |

**Dependents scouted:** `executor.py` imports `ModelConfig`, `llm_router.py` imports `FALLBACK_MODEL` + `get_model_for_capability`, `telegram_bot.py` imports `HeartbeatScheduler`. All imports still valid.

---

## Overall Assessment

Solid implementation. Tri-model config is clean, backward compat preserved, loop discovery has proper JSON error handling. Two notable issues: shell injection surface in Tier 2 and heartbeat_scheduler exceeds 200-line limit.

---

## Critical Issues

### C1: Shell Injection in Tier 2 Command Construction

**File:** `heartbeat_scheduler.py:271`

```python
cmd = f"mekong {task.description.lower().replace(' ', '-')}"
result = subprocess.run(cmd, shell=True, ...)
```

`task.description` is built from JSON files: `f"[{data.get('name', ...)}] {data.get('description', '')}"`. If a malicious JSON file is placed in `.mekong/loops/`, the description flows unsanitized into `shell=True`. Example payload: `"; rm -rf /; echo "`.

**Risk:** Low probability (attacker needs write access to `.mekong/loops/`), but high impact.

**Fix:**
```python
import shlex
safe_desc = shlex.quote(task.description.lower().replace(' ', '-'))
cmd = f"mekong {safe_desc}"
# Or better: use shell=False with list args
subprocess.run(["mekong", task.description.lower().replace(' ', '-')], ...)
```

### C2: Tier 1 Commands Also Use shell=True (Line 254)

Same pattern — `task.command` from JSON runs via `shell=True`. This is somewhat expected (commands like `curl -sf ... | jq` need shell piping), but should be documented as a trust boundary.

**Recommendation:** Add comment at line 252 documenting that `.mekong/loops/` is a trusted config directory. Consider validating command against an allowlist of prefixes (`curl`, `python3`, `mekong`).

---

## High Priority

### H1: heartbeat_scheduler.py Exceeds 200-Line Limit (347 lines)

Project rules require <200 lines per file. Suggested split:
- `heartbeat_scheduler.py` — `HeartbeatScheduler` class + `main()` (core loop)
- `heartbeat_loop_loader.py` — `discover_loops()`, `_parse_cron()` (~50 lines)
- `heartbeat_parser.py` — `parse_heartbeat()` (~60 lines)

### H2: `_loop_config` Monkey-Patched onto Dataclass (Line 122)

```python
task._loop_config = data  # type: ignore[attr-defined]
```

This stores tier 2 prompt/verify metadata but nothing reads it. Dead code now, but if future tier 2 escalation needs it, a proper field should exist on `ScheduledTask`.

**Fix:** Either add `loop_config: Optional[dict] = None` to the dataclass, or remove the assignment until needed (YAGNI).

### H3: Telegram Bot Only Shows HEARTBEAT.md Tasks, Not Loops

`telegram_bot.py:638-649` calls `discover_heartbeats()` + `parse_heartbeat()` but never calls `discover_loops()`. Users running `/heartbeat` in Telegram see zero loop tasks.

**Fix:** Add `discover_loops()` call after heartbeat discovery in `heartbeat_handler()`.

---

## Medium Priority

### M1: `dry_run` Flag in JSON Not Enforced by Scheduler

Loop configs have `"dry_run": true` but `discover_loops()` only logs it — `execute_task()` runs the command regardless. The `--dry-run` CLI flag works (it skips `run_forever()`), but per-loop dry_run is cosmetic.

**Fix:** Check `task._loop_config.get("dry_run", False)` before execution, or remove the field from JSON to avoid false confidence.

### M2: `tier2_only_on_failure` in monitor.json Not Implemented

`monitor.json` has `"tier2_only_on_failure": true` but no code reads this field. Tier 2 will always run when tier 1 succeeds with a non-zero exit code.

### M3: Loop Config Fields (`expected`, `expected_contains`, `min_value`) Unused

Tier 1 checks in JSON define `expected`, `expected_contains`, `min_value` but the scheduler only checks `returncode == 0`. The semantic validation (comparing output to expected value) is not implemented.

### M4: Cron Timezone Field Ignored

All loop JSON files specify `"timezone": "UTC"` but `_parse_cron()` and `is_due()` use `datetime.now()` (local time). This silently misschedules tasks if the host is not in UTC.

**Fix:** Use `datetime.now(timezone.utc)` when `schedule.timezone == "UTC"`, or document that all times are local.

### M5: `heartbeat-config.json` Has IP Address Hardcoded

Config file has `"url": "http://192.168.11.111:11436/v1"` — fine for `.mekong/` (gitignored), but the same IP is also in `llm_config.py:47-49` as `M1_MAX_HOST` default. If the M1 Max IP changes, both files need updating.

**Suggestion:** `heartbeat-config.json` should use `M1_MAX_HOST` env var reference, or be generated from `llm_config.py` constants.

### M6: Config `models` Section Not Used by Scheduler

`heartbeat-config.json` has a `models` block with health URLs, but `_load_config()` only reads `enabled`, `check_interval`, `max_concurrent`, `workspaces`. The model health URLs are dead config.

---

## Low Priority

### L1: Duplicate `import json` in heartbeat_scheduler.py

Line 18: `import json` at module level. Line 66: `import json` again inside `_load_config()`. The inner import is redundant.

### L2: DashScope API Key Empty String Default

`llm_config.py:56`: `DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")`. If env var is unset, CODING_MODEL gets `api_key=""` which will cause auth failures. Consider raising early or logging a warning.

### L3: `alerts` Section in Config Uses Template Syntax

```json
"telegram_bot_token": "${TELEGRAM_BOT_TOKEN}"
```

This is string literal `${TELEGRAM_BOT_TOKEN}`, not env var expansion. Python's `json.loads()` returns it as-is. If alert integration is planned, these need `os.getenv()` resolution.

---

## Positive Observations

- **Backward compat preserved:** `PLANNING_MODEL = CODING_MODEL` and `WORKER_MODEL = DEEP_MODEL` aliases maintained. `llm_router.py` imports still valid.
- **Clean capability routing:** 17 capabilities mapped across 3 tiers, `get_model_for_capability()` fallback to DEEP_MODEL sensible.
- **JSON parse errors caught:** `discover_loops()` wraps in `try/except (json.JSONDecodeError, KeyError)`.
- **Circuit breaker unaffected:** `llm_router.py` imports unchanged, circuit breaker logic untouched.
- **Shell script well-structured:** `start-solo-ops.sh` has proper `set -euo pipefail`, python fallback, idempotent start check.
- **All loops start with `dry_run: true`** (except monitor) — safe bootstrapping.
- **`__all__` exports updated** in llm_config.py.

---

## Recommended Actions (Priority Order)

1. **Sanitize Tier 2 shell command** (C1) — switch to `shell=False` with list args
2. **Split heartbeat_scheduler.py** (H1) — extract parser + loop loader modules
3. **Add `loop_config` field to dataclass** or remove monkey-patch (H2)
4. **Fix Telegram `/heartbeat` to show loops** (H3)
5. **Implement per-loop `dry_run` enforcement** (M1)
6. **Use UTC-aware datetime** (M4)
7. **Implement tier1 output validation** (`expected`, `min_value`) (M3)

---

## Metrics

| Metric | Value |
|--------|-------|
| Type Coverage | Good — type hints on all functions, `dict[str, ModelConfig]` typed |
| Test Coverage | Not assessed (no test files found for new code) |
| Linting Issues | 1 (duplicate import), 1 (`type: ignore` monkey-patch) |
| Security Issues | 1 critical (shell injection surface), 1 medium (IP hardcoded) |
| Files Over 200 Lines | 1 (`heartbeat_scheduler.py` at 347) |

---

## Unresolved Questions

1. Is `tier2_only_on_failure` planned for Phase 3? If so, `_loop_config` storage makes sense; otherwise remove dead fields.
2. Will loop configs ever come from untrusted sources (API, user upload)? If yes, C1 becomes urgent.
3. Should the Telegram bot's `/heartbeat` handler also show loop tasks? Currently it only shows HEARTBEAT.md-sourced tasks.
4. Are tests planned for `_parse_cron()`? Edge cases like `*/0`, `60 25 * * *`, or 6-field cron strings would crash or silently misbehave.
