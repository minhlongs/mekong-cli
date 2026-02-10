# OpenClaw Worker — TOM HUM Autonomous Daemon

> **Chapter 9 Xing Jun** — On the march, seek high ground and reliable water sources
>
> This file governs CC CLI behavior ONLY when working inside `apps/openclaw-worker/`.
> Inherits from root `CLAUDE.md` (Constitution) and `~/.claude/CLAUDE.md` (Global).

## Identity

**Codename:** Tom Hum (Lobster)
**Role:** General / Dai Tuong — autonomous task dispatch daemon
**DIEU 54:** Tom Hum Tu Tri (Autonomous Self-Governance)

## Tech Stack

| Component | Technology |
|-----------|------------|
| Runtime | Node.js |
| Language | JavaScript (CommonJS) |
| Brain Control | Dual-mode: `direct` (claude -p) or `tmux` (v26.0) |
| Engine | Dual-engine: `antigravity` (port 8080) or `qwen` (port 8081) |
| Proxy | Antigravity Proxy (port 8080) / Qwen Bridge (port 8081) |
| Model | claude-opus-4-6-thinking (antigravity) / qwen-coder-plus (qwen) |

## Architecture (v26.0 Dual-Mode, Dual-Engine Brain)

```
apps/openclaw-worker/
├── task-watcher.js              # Thin orchestrator: boot + shutdown (entry point)
├── config.js                    # All constants, paths, env vars, project registry
└── lib/
    ├── brain-process-manager.js # Dual-mode, dual-engine brain v26.0
    ├── mission-dispatcher.js    # Prompt building, project routing, runMission()
    ├── task-queue.js            # File watching (fs.watch + poll), FIFO queue
    ├── auto-cto-pilot.js        # Self-CTO: generates Binh Phap quality tasks
    ├── m1-cooling-daemon.js     # M1 thermal/RAM protection
    └── live-mission-viewer.js   # Real-time colored log viewer for VS Code terminal
```

## Key Files & Contracts

### config.js — Single Source of Truth
- `MEKONG_DIR` — Root project directory
- `WATCH_DIR` — `tasks/` directory for mission files
- `PROCESSED_DIR` — `tasks/processed/` for completed missions
- `TASK_PATTERN` — `/^mission_.*\.txt$/` (file naming convention)
- `MISSION_TIMEOUT_MS` — 45 minutes per mission
- `BRAIN_MODE` — `'direct'` (default) or `'tmux'` (fallback), set via `TOM_HUM_BRAIN_MODE`
- `ENGINE` — `'antigravity'` (default, port 8080) or `'qwen'` (port 8081), set via `TOM_HUM_ENGINE`
- `QWEN_PROXY_PORT` — 8081 (Qwen Bridge Flask server)
- `QWEN_MODEL_NAME` — `'qwen-coder-plus'` (mapped by bridge to DashScope model)
- `TMUX_SESSION` — Tmux session name (only used in tmux mode)
- `PROJECTS` — Array of sub-project names for routing

### Brain Modes (v26.0)

#### Mode 1: Direct (DEFAULT) — `claude -p`
- Each mission runs: `claude -p "<prompt>" --model X --dangerously-skip-permissions`
- stdin set to `'ignore'` (critical: piped stdin causes hang)
- All ClaudeKit agents, tools, and skills fully supported
- Output streamed to log file in real-time
- User watches via: `node lib/live-mission-viewer.js` in VS Code terminal
- No persistent session — fresh process per mission

#### Mode 2: Tmux (FALLBACK) — persistent session
- CC CLI runs inside tmux session `tom-hum-brain`
- User can `tmux attach -t tom-hum-brain` to watch
- Missions injected via `tmux send-keys -l`
- Completion detected via `tmux capture-pane -p` polling
- Set via: `TOM_HUM_BRAIN_MODE=tmux node task-watcher.js`

### Engines (v26.0)

#### Engine 1: Antigravity (DEFAULT) — port 8080
- Routes through Antigravity Proxy (load balancing, failover)
- Model: `claude-opus-4-6-thinking`
- Default for all missions

#### Engine 2: Qwen — port 8081
- Routes through Qwen Bridge (`scripts/qwen_bridge.py`)
- Converts Anthropic Messages API → DashScope OpenAI Chat Completions API
- Model: `qwen-coder-plus` (mapped to DashScope model by bridge)
- Start bridge: `scripts/start-qwen-bridge.sh`
- Set via: `TOM_HUM_ENGINE=qwen node task-watcher.js`

### Live Mission Viewer
Run in any terminal (VS Code recommended) to watch missions:
```bash
node apps/openclaw-worker/lib/live-mission-viewer.js
```
- Colored output: cyan=mission start, green=complete, red=error, yellow=timeout
- Shows last 20 log lines on start, then live-tails new output

## Development Rules (Domain-Specific)

### File Naming
- All lib modules use kebab-case: `brain-process-manager.js`
- Mission files use snake_case: `mission_{project}_{task}.txt` (consumed by regex)

### Modifying the Brain
- Changes to `brain-process-manager.js` require testing the full mission cycle
- Test direct mode:
  ```bash
  node -e "
    const { spawnBrain, runMission } = require('./lib/brain-process-manager');
    spawnBrain();
    runMission('Reply with: TEST_OK', '.', 60000).then(r => console.log(JSON.stringify(r)));
  "
  ```
- Test tmux mode: `TOM_HUM_BRAIN_MODE=tmux node task-watcher.js`
- Test qwen engine: `TOM_HUM_ENGINE=qwen node -e "const c = require('./config'); console.log(c.ENGINE, c.QWEN_PROXY_PORT)"`

### Adding New Modules
- Create in `lib/` with kebab-case naming
- Export from module, import in `task-watcher.js`
- Keep modules < 200 lines

### Testing
- No automated test suite (daemon process, not unit-testable)
- Manual testing: write a `tasks/mission_test_*.txt` and watch logs
- Log file: `~/tom_hum_cto.log`

## Quality Gates (Binh Phap)

- All missions must use `/cook` or `/binh-phap` prefix (DIEU 47)
- Sequential processing only (no parallel missions)
- M1 cooling daemon kills resource hogs every 90s
- Auto-CTO generates quality tasks when queue empty for 5min
