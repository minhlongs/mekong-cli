# OpenClaw 24h Burn-In Runbook

Operator guide for running and interpreting the unattended burn-in test.
**Target machine:** M1 Max via `ssh m1max-cf`

---

## Directory Layout

```
burn-in/
├── harness.py          # Main orchestrator (spawns daemon + sampler)
├── sampler.py          # psutil RSS/CPU poller → metrics CSV
├── summarize.py        # Post-run report generator
├── kill-switch-test.sh # T+12h SIGTERM verification
├── expected-signals.md # Healthy baseline reference
├── logs/               # run-<ts>.jsonl (gitignored — too large)
├── metrics/            # run-<ts>.csv   (gitignored)
└── reports/            # run-<ts>-summary.md (committed after run)

scripts/burn-in/
├── start-openclaw-burn-in.sh  # Entry point (launches harness)
├── monitor-openclaw.sh        # Live dashboard poller
└── stop-and-report.sh         # Graceful stop + generate report
```

---

## Quick Start (M1 Max)

### Step 1 — SSH to M1 Max

```bash
ssh m1max-cf
cd ~/mekong-cli
git pull origin worktree-agent-a99e3e39  # or main after merge
```

### Step 2 — Start burn-in in tmux

```bash
tmux new-session -d -s burn-in-260417 \
  'bash scripts/burn-in/start-openclaw-burn-in.sh 2>&1 | tee burn-in/start.log'
```

### Step 3 — Attach to watch live output

```bash
tmux attach -t burn-in-260417
# Detach without stopping: Ctrl-B then D
```

### Step 4 — Monitor from a second pane

```bash
tmux split-window -t burn-in-260417 \
  'bash scripts/burn-in/monitor-openclaw.sh'
```

---

## Remote Monitoring (from M1 Pro)

```bash
# Tail the live log
ssh m1max-cf 'tail -f ~/mekong-cli/burn-in/logs/$(ls -t ~/mekong-cli/burn-in/logs/*.jsonl | head -1)'

# Quick status snapshot
ssh m1max-cf 'bash ~/mekong-cli/scripts/burn-in/monitor-openclaw.sh --once'

# Check harness is alive
ssh m1max-cf 'cat ~/mekong-cli/burn-in/harness.pid | xargs kill -0 && echo ALIVE || echo DEAD'
```

---

## T+12h Kill-Switch Test (mandatory checkpoint)

```bash
ssh m1max-cf 'bash ~/mekong-cli/burn-in/kill-switch-test.sh'
# Expected output: "Kill-switch test PASSED"
# Then restart harness for the remaining 12h:
ssh m1max-cf 'tmux new-session -d -s burn-in-2 \
  "bash ~/mekong-cli/scripts/burn-in/start-openclaw-burn-in.sh 2>&1 | tee -a ~/mekong-cli/burn-in/start.log"'
```

---

## Stop + Generate Report

```bash
ssh m1max-cf 'bash ~/mekong-cli/scripts/burn-in/stop-and-report.sh'
# Report saved to: burn-in/reports/run-<ts>-summary.md
```

Retrieve the report locally:

```bash
scp m1max-cf:~/mekong-cli/burn-in/reports/run-\*-summary.md ./burn-in/reports/
```

---

## Interpreting Results

See `burn-in/expected-signals.md` for full thresholds. Summary:

| What to look for | Where |
|------------------|-------|
| Uptime & restart count | `harness_end` event in JSONL log |
| Memory drift slope | `rss_drift_mb_per_hr` in summary report |
| Error rate | `error_count` / `uptime_s` in summary |
| Task completions | `daemon_stdout` lines containing `Report:` |
| Kill-switch result | Output of `kill-switch-test.sh` |

---

## GO / NO-GO Criteria

The burn-in **passes** (GO) when ALL of the following are true:

- Uptime >= 23.9h (86040s)
- Daemon restarts <= 3
- Error rate < 1 per hour
- Peak RSS < 2 GB
- RSS drift < 50 MB/hr
- `harness_end` event present (clean shutdown confirmed)

**If GO:** commit the summary report and update the README claim with a link.
**If NO-GO:** file a bug with the top errors, fix, restart the 24h clock.

---

## Dry-Run / Smoke Test (5 min, no real LLM)

```bash
# Local (M1 Pro) — verify scripts work without syntax errors
pytest tests/burn-in/test-harness-smoke.py -v

# Or manually:
python3 burn-in/harness.py --dry-run --duration 60
```

---

## Environment Variables

| Variable | Default | Purpose |
|----------|---------|---------|
| `MEKONG_ENV` | `burn-in` (auto-set) | Prevents prod API calls |
| `DAEMON_LLM_MODEL` | `qwen2.5-coder:7b` | Fast local model for burn-in |
| `GITHUB_TOKEN` | unset (auto-cleared) | Prevents auto-publish during test |
| `GATEWAY_URL` | `http://localhost:8000` | Local gateway only |

---

## Troubleshooting

**Harness exits immediately:**
Check `burn-in/logs/run-*.jsonl` for `daemon_exit` event with `exit_code`.
Usually means the daemon script path is wrong — verify `scripts/openclaw-daemon.py` exists.

**sampler.py not collecting metrics:**
`psutil` may not be installed. Run: `pip install psutil` in the repo venv.

**caffeinate not found:**
Only available on macOS. On Linux, use `systemd-inhibit` or ignore — M1 Max won't sleep during SSH.

**Log file grows > 100MB:**
Rotation is automatic. Old files saved as `*.jsonl.bak`, only last 5 kept.
