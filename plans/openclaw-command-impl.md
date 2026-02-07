# OpenClaw Command Suite Implementation Plan

> **Date:** 2026-02-07
> **Status:** Implementation Phase

## 1. `task-watcher.js` Upgrade

We need to upgrade the `executeTask` function to route commands based on prefixes.

### Routing Logic

| Prefix    | Executor   | Command Line              |
| :-------- | :--------- | :------------------------ |
| `!cmd`    | **Shell**  | `cmd` (Existing)          |
| `/any`    | **CC CLI** | `claude -p "/any [args]"` |
| (Default) | **CC CLI** | `claude -p "[text]"`      |

### Implementation Details

- Detect `!` prefix for Shell.
- Route EVERYTHING else to `claude`.
- This exploits the **Agent's Skills** (via `claudekit`) to handle `/plan`, `/cook`, etc.
- `ck` CLI is NOT used directly as it is a project manager, not an agent runner.
- **Verification:** `claude` agent receives the query and decides how to execute it (e.g. calling `planner` tool).

## 2. `raas-gateway` Upgrade (Optional for now)

- Currently, it forwards raw text. This is fine for now as `task-watcher.js` will handle parsing.
- Later: Add slash command registration with Telegram API.

## 3. Verification

- Create `/tmp/openclaw_task_test_ck.txt` with content `/plan Verify system status`.
- Check logs.
