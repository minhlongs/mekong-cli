# CHANGELOG — 2026-03-16 Factory System Overhaul

## Session Summary

- **Duration**: ~75 minutes (08:37 - 09:50 ICT)
- **Commits**: 15 (+ 2 pre-existing = 17 total on master)
- **New files**: 6,911 lines across 35+ files
- **Tests**: 10/10 passing
- **All pushed to GitHub**: master branch

## Before vs After

### Before (factory-loop.sh v11.10)
- Blind rotation: ALL_CMDS dispatched to ALL projects regardless of state
- Empty projects (sophia-proposal) received `/marketing-content-engine` — useless
- No cascade: analysis output → dead end → more analysis → infinite loop
- No metrics, no learning, no health checks
- Routing bug: `sophia-ai-factory` pointed to non-existent directory
- 305 lines, no error recovery

### After (factory-loop.sh v13.1)
- State-aware dispatch: detect_project_state() checks filesystem before dispatching
- CASCADE BRIDGE: analysis_done → auto-trigger /cook engineering commands
- Priority queue: deployed > scaffolded > needs_install > empty
- Brain learning: records outcomes, evolves every 10 cycles
- Output intelligence: classifies code_written vs analysis_only vs error
- ROI calculator: tracks success rate per project
- Trap/timeout/health: auto-cleanup on exit, 10min command timeout, pane health checks
- Watchdog: auto-restart if loop crashes
- Daily digest: generates reports/factory-daily-{date}.md on shutdown
- --dry-run + --cycles flags for testing
- 700+ lines, fully hardened

## New Commands (15)

| Command | Purpose |
|---------|---------|
| `/raas-scaffold` | Scaffold new SaaS project with auth, billing |
| `/raas-create` | Full pipeline: scaffold → features → deploy |
| `/commands-status` | Dispatch stats from metrics log |
| `/cto-dashboard` | Brain health, ROI scores, active missions |
| `/factory-restart` | Safe restart without killing CC CLI |
| `/factory-intelligence` | Command effectiveness, output patterns |
| `/review:factory` | Full code review checklist for factory-loop.sh |
| `/cto-workforce` | Workers, project states, throughput per pane |
| `/production-status` | Live production board with ROI + git stats |
| `/brain-evolution-log` | Brain evolution timeline, learning trend |
| `/project-matrix` | Business impact ranking (ROI + maturity + activity) |
| `mekong health` | Check all subsystems in one table |
| `mekong metrics` | ANSI terminal dashboard from metrics log |
| `--dry-run` | Simulate dispatch without tmux |
| `--cycles=N` | Exit after N cycles |

## New Modules (7 JS + 1 Python)

| Module | Lines | Purpose |
|--------|-------|---------|
| `factory-roi-calculator.js` | 170 | ROI per project, brain-learning-state.json |
| `output-intelligence.js` | 140 | Classify CC CLI output (code/test/build/analysis) |
| `factory-throughput-optimizer.js` | 150 | Adaptive cooldown based on pane response time |
| `project-priority-matrix.js` | 90 | Business impact score (maturity + ROI + activity) |
| `health_metrics_commands.py` | 200 | mekong health + mekong metrics CLI commands |
| `factory-watchdog.sh` | 35 | Auto-restart factory loop |
| `test_detect_project_state.sh` | 134 | 10 unit tests for state detection |

## Bug Fixes

| Bug | Fix |
|-----|-----|
| sophia-ai-factory routing | Fixed to sophia-proposal in mission-dispatcher + auto-cto-pilot (both copies) |
| Output intelligence stale data | save_pane_output() before classify, not after |
| grep -c crash in daily digest | Used `|| true` instead of `|| echo "0"` |
| 11 ck-* commands missing frontmatter | Added description + argument-hint |

## Architecture

```
factory-loop.sh v13.1
  ├── detect_project_state() → empty|needs_install|scaffolded|deployed
  ├── analyze_output() → analysis_done|fix|bootstrap|continue
  ├── CASCADE BRIDGE: analysis → /cook (auto-trigger)
  ├── Priority Queue: deployed first, empty last
  ├── Output Intelligence: classify code vs reports
  ├── Brain Evolution: promote/demote every 10 cycles
  ├── ROI Learning: record_outcome() → brain-learning-state.json
  ├── Health Check: verify tmux + pane alive
  ├── Timeout: 600s max per command
  ├── Metrics: /tmp/factory-metrics.log
  ├── Daily Digest: reports/factory-daily-{date}.md
  └── Watchdog: factory-watchdog.sh auto-restart
```

## Recipes

| Recipe | File |
|--------|------|
| RaaS Scaffold | recipes/raas/scaffold.json |
| RaaS Create (DAG) | recipes/raas/create.json |

## Docs

| Doc | File |
|-----|------|
| Commands Index | docs/commands-index.md (124 commands categorized) |
| Factory Architecture | docs/factory-system-architecture.md (Mermaid diagrams) |
