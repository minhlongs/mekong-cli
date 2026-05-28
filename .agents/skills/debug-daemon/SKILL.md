---
name: debug-daemon
description: Diagnose CTO daemon (Tôm Hùm) and tmux worker crashes on the M1 Max. Trigger when user reports "daemon crashed", "tmux worker died", "death-respawn loop", or when container logs show rapid restart patterns. Contains the root cause analysis from the documented flag mismatch incident and branch divergence.
---

# Debug CTO Daemon (Tôm Hùm)

## Overview
The CTO daemon (cto-daemon-latest.sh) runs inside tmux and has a documented history of crash loops. This runbook codifies the debugging steps that resolved the flag mismatch and branch divergence incidents.

## Symptom → Diagnosis Map

| Symptom | Likely Cause | Check |
|---|---|---|
| Rapid restart (< 5s cycle) | Flag mismatch in launch-pane-cc.sh | `grep -- '--provider\|--quiet\|--tool' launch-pane-cc.sh` |
| Slow restart (30-60s cycle) | OOM or model timeout | `htop` + check mlx_lm.server logs |
| Single crash, no restart | s6-overlay service marked "down" | `s6-svc -u /etc/s6-overlay/s6-rc.d/mekong-gateway` |
| Runs but no output | Branch divergence (missing fixes) | `git log --oneline main..master \| wc -l` |

## Root Cause #1: Flag Mismatch (verified)
`launch-pane-cc.sh` passed `--provider` and `--quiet` flags.
The wrapper's parser rejected with `exit 1` → respawn → reject → infinite loop.

**Fix**: Alias `--provider` to `--tool` in the parser.

## Root Cause #2: Branch Divergence (verified)
Master branch was missing ~578 lines of resilience fixes present on main.
Daemon ran from master → crashed on fixed edge cases → respawned → crashed again.

**Fix**: `git merge main` to recover hardening logic.

## Scripts
- `scripts/check-daemon-health.sh` — PID, uptime, restart count, last error
- `scripts/tail-daemon-logs.sh` — Last 50 lines of daemon + tmux worker logs
- `scripts/compare-branches.sh` — Diff main vs master for divergence

## Gotchas
- The daemon log is in tmux — check with `tmux capture-pane` not `docker logs`.
- s6-overlay auto-restarts mask the root cause. Disable auto-restart temporarily to see the actual error.
- Branch names: this repo uses BOTH `main` and `master`. Always check which one has the latest fixes.
- The wrapper script has multiple layers of flag parsing. A flag valid at one layer may be rejected by an inner layer.
