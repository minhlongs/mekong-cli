# 🦞 OpenClaw Worker — TÔM HÙM Autonomous Daemon

> **第九篇 行軍 (Xing Jun)** — On the march, seek high ground and reliable water sources
>
> This file governs CC CLI behavior ONLY when working inside `apps/openclaw-worker/`.
> Inherits from root `CLAUDE.md` (Constitution) and `~/.claude/CLAUDE.md` (Global).

## Identity

**Codename:** Tôm Hùm (Lobster)
**Role:** General / Đại Tướng — autonomous task dispatch daemon
**ĐIỀU 54:** Tôm Hùm Tự Trị (Autonomous Self-Governance)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Node.js |
| Language | JavaScript (CommonJS) |
| Brain Control | Expect (TCL) via `scripts/tom-hum-persistent-dispatch.exp` |
| IPC | Atomic file writes (`/tmp/tom_hum_next_mission.txt`) |
| Proxy | Antigravity Proxy (port 8080) |
| Model | claude-opus-4-6-thinking |

## Architecture (v22.0 Modular Brain)

```
apps/openclaw-worker/
├── task-watcher.js              # Thin orchestrator: boot + shutdown (entry point)
├── config.js                    # All constants, paths, env vars, project registry
└── lib/
    ├── brain-process-manager.js # Spawn/monitor/kill expect brain process
    ├── mission-dispatcher.js    # Atomic file IPC, prompt building, project routing
    ├── task-queue.js            # File watching (fs.watch + poll), FIFO queue
    ├── auto-cto-pilot.js        # Self-CTO: generates Binh Phap quality tasks
    └── m1-cooling-daemon.js     # M1 thermal/RAM protection
```

## Key Files & Contracts

### config.js — Single Source of Truth
- `MEKONG_DIR` — Root project directory
- `WATCH_DIR` — `tasks/` directory for mission files
- `PROCESSED_DIR` — `tasks/processed/` for completed missions
- `MISSION_FILE` — `/tmp/tom_hum_next_mission.txt` (IPC inbox)
- `DONE_FILE` — `/tmp/tom_hum_mission_done` (completion signal)
- `EXPECT_SCRIPT` — Path to `scripts/tom-hum-persistent-dispatch.exp`
- `TASK_PATTERN` — `/^mission_.*\.txt$/` (file naming convention)
- `MISSION_TIMEOUT_MS` — 45 minutes per mission
- `PROJECTS` — Array of sub-project names for routing

### IPC Protocol (File-Based)
1. **Mission delivery:** Atomic write (tmp + rename) to `MISSION_FILE`
2. **Completion signal:** Expect brain writes `"done"` to `DONE_FILE`
3. **State persistence:** `tasks/.tom_hum_state.json` tracks Auto-CTO progress

### Expect Brain Protocol
- Spawns CC CLI with `--dangerously-skip-permissions`
- Detects `❯` prompt via regex `(\\xe2\\x9d\\xaf|❯)` with 500ms debounce
- Initial ready timeout: 120 seconds
- Mission timeout: 2700 seconds (45 min)
- Crash recovery: auto-respawn with `--continue`, max 5/hour

## Development Rules (Domain-Specific)

### File Naming
- All lib modules use kebab-case: `brain-process-manager.js`
- Mission files use snake_case: `mission_{project}_{task}.txt` (consumed by regex)

### Modifying the Brain
- Changes to expect script require testing the full spawn→mission→completion cycle
- Never modify `MISSION_FILE` or `DONE_FILE` paths without updating BOTH config.js AND expect script
- IPC is one-way: Node.js writes mission, expect writes done signal

### Adding New Modules
- Create in `lib/` with kebab-case naming
- Export from module, import in `task-watcher.js`
- Keep modules < 100 lines (thin, focused)

### Testing
- No automated test suite (daemon process, not unit-testable)
- Manual testing: write a `tasks/mission_test_*.txt` and watch logs
- Log file: `~/tom_hum_cto.log`

## Quality Gates (Binh Phap)

- All missions must use `/cook` or `/binh-phap` prefix (ĐIỀU 47)
- Sequential processing only (no parallel missions)
- M1 cooling daemon kills resource hogs every 90s
- Auto-CTO generates quality tasks when queue empty for 5min
