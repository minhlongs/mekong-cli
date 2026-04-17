"""OpenClaw 24h Burn-In Harness.

Orchestrates: daemon subprocess + sampler process + structured JSONL log.
Designed to run unattended on M1 Max via tmux.

Usage:
    python3 burn-in/harness.py [--duration 86400] [--dry-run]

Environment guards:
    MEKONG_ENV=burn-in   (set automatically — prevents prod calls)
    DAEMON_LLM_MODEL=qwen2.5-coder:7b (fast local model for burn-in)
"""

import argparse
import json
import os
import re
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
BURN_IN_DIR = REPO_ROOT / "burn-in"
LOGS_DIR = BURN_IN_DIR / "logs"
METRICS_DIR = BURN_IN_DIR / "metrics"
REPORTS_DIR = BURN_IN_DIR / "reports"
SAMPLER = BURN_IN_DIR / "sampler.py"

for d in (LOGS_DIR, METRICS_DIR, REPORTS_DIR):
    d.mkdir(parents=True, exist_ok=True)

# ── Config ─────────────────────────────────────────────────────────────────
DEFAULT_DURATION = 86400          # 24h in seconds
MAX_LOG_BYTES = 100 * 1024 * 1024 # 100MB rotation threshold
SAMPLE_INTERVAL = 60              # sampler polls every 60s
API_KEY_PATTERN = re.compile(r"(sk-[A-Za-z0-9]+|polar_[A-Za-z0-9]+)")


def _ts() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")


def _redact(line: str) -> str:
    """Strip API keys from log lines before writing."""
    return API_KEY_PATTERN.sub("[REDACTED]", line)


def _write_event(log_fh, event_type: str, **payload):
    """Append a JSON event line to the run log."""
    record = {"ts": _ts(), "event": event_type, **payload}
    log_fh.write(json.dumps(record) + "\n")
    log_fh.flush()


def _rotate_if_needed(log_path: Path, log_fh):
    """Rotate log file if it exceeds MAX_LOG_BYTES."""
    if log_path.stat().st_size > MAX_LOG_BYTES:
        log_fh.close()
        rotated = log_path.with_suffix(f".{_ts()}.jsonl.bak")
        log_path.rename(rotated)
        # Keep only last 5 rotated files
        baks = sorted(log_path.parent.glob("*.jsonl.bak"), key=lambda p: p.stat().st_mtime)
        for old in baks[:-5]:
            old.unlink(missing_ok=True)
        return open(log_path, "a", buffering=1)
    return log_fh


def _launch_daemon(dry_run: bool) -> subprocess.Popen:
    """Start the openclaw daemon subprocess with burn-in env guards."""
    env = os.environ.copy()
    env["MEKONG_ENV"] = "burn-in"
    env["DAEMON_LLM_MODEL"] = env.get("DAEMON_LLM_MODEL", "qwen2.5-coder:7b")
    # Prevent GitHub publish during burn-in
    env.pop("GITHUB_TOKEN", None)

    if dry_run:
        # Lightweight stand-in: just echo heartbeats every 10s
        cmd = [sys.executable, "-c",
               "import time, sys\n"
               "for i in range(720):\n"
               "  print(f'[DAEMON] heartbeat {i}', flush=True)\n"
               "  time.sleep(10)\n"]
    else:
        cmd = [sys.executable, "-m", "scripts.openclaw-daemon"]
        # Fall back to the daemon script directly
        daemon_script = REPO_ROOT / "scripts" / "openclaw-daemon.py"
        if daemon_script.exists():
            cmd = [sys.executable, str(daemon_script)]

    return subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env=env,
        cwd=str(REPO_ROOT),
    )


def _launch_sampler(pid: int, run_ts: str) -> subprocess.Popen:
    """Start sampler process targeting daemon PID."""
    return subprocess.Popen(
        [sys.executable, str(SAMPLER), "--pid", str(pid), "--run-ts", run_ts],
        cwd=str(REPO_ROOT),
    )


def run(duration: int, dry_run: bool):
    run_ts = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    log_path = LOGS_DIR / f"run-{run_ts}.jsonl"
    pid_file = BURN_IN_DIR / "harness.pid"

    print(f"[harness] Starting burn-in run {run_ts} | duration={duration}s dry_run={dry_run}")
    print(f"[harness] Log: {log_path}")

    log_fh = open(log_path, "a", buffering=1)
    _write_event(log_fh, "harness_start", duration=duration, dry_run=dry_run, run_ts=run_ts)

    daemon_proc = _launch_daemon(dry_run)
    pid_file.write_text(str(daemon_proc.pid))
    _write_event(log_fh, "daemon_start", pid=daemon_proc.pid)
    print(f"[harness] Daemon PID={daemon_proc.pid}")

    sampler_proc = _launch_sampler(daemon_proc.pid, run_ts)
    _write_event(log_fh, "sampler_start", pid=sampler_proc.pid)

    restart_count = 0
    start_time = time.monotonic()
    shutdown_requested = False

    def _on_sigterm(signum, frame):
        nonlocal shutdown_requested
        shutdown_requested = True
        print("[harness] SIGTERM received — initiating graceful shutdown")

    signal.signal(signal.SIGTERM, _on_sigterm)
    signal.signal(signal.SIGINT, _on_sigterm)

    try:
        while not shutdown_requested:
            elapsed = time.monotonic() - start_time
            if elapsed >= duration:
                _write_event(log_fh, "duration_reached", elapsed_s=int(elapsed))
                break

            # Stream daemon stdout into log (non-blocking)
            if daemon_proc.stdout:
                line = daemon_proc.stdout.readline()
                if line:
                    _write_event(log_fh, "daemon_stdout",
                                 msg=_redact(line.rstrip()))

            # Check if daemon died — restart it
            if daemon_proc.poll() is not None:
                exit_code = daemon_proc.returncode
                _write_event(log_fh, "daemon_exit", exit_code=exit_code,
                             restart_count=restart_count)
                print(f"[harness] Daemon exited (code={exit_code}), restarting...")
                time.sleep(5)
                daemon_proc = _launch_daemon(dry_run)
                pid_file.write_text(str(daemon_proc.pid))
                restart_count += 1
                _write_event(log_fh, "daemon_restart", new_pid=daemon_proc.pid,
                             restart_count=restart_count)

            log_fh = _rotate_if_needed(log_path, log_fh)

    finally:
        # Graceful shutdown
        _write_event(log_fh, "harness_shutdown_begin", restart_count=restart_count)
        daemon_proc.terminate()
        sampler_proc.terminate()
        try:
            daemon_proc.wait(timeout=15)
        except subprocess.TimeoutExpired:
            daemon_proc.kill()
        sampler_proc.wait(timeout=5)
        elapsed = time.monotonic() - start_time
        _write_event(log_fh, "harness_end", uptime_s=int(elapsed),
                     restart_count=restart_count)
        log_fh.close()
        pid_file.unlink(missing_ok=True)
        print(f"[harness] Run complete. Uptime={int(elapsed)}s restarts={restart_count}")
        print(f"[harness] Log saved: {log_path}")


def main():
    parser = argparse.ArgumentParser(description="OpenClaw 24h burn-in harness")
    parser.add_argument("--duration", type=int, default=DEFAULT_DURATION,
                        help="Run duration in seconds (default 86400 = 24h)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Use dummy daemon (no real LLM calls)")
    args = parser.parse_args()
    run(args.duration, args.dry_run)


if __name__ == "__main__":
    main()
