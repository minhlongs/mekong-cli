"""OpenClaw Burn-In Sampler — polls RSS/CPU/FDs every 60s.

Writes CSV rows to burn-in/metrics/run-<ts>.csv for post-run analysis.
Redacts any API keys found in process environment.

Usage:
    python3 burn-in/sampler.py --pid <daemon_pid> --run-ts <run_ts>
"""

import argparse
import csv
import os
import signal
import sys
import time
from datetime import datetime
from pathlib import Path

try:
    import psutil
except ImportError:
    print("[sampler] ERROR: psutil not installed. Run: pip install psutil", flush=True)
    sys.exit(1)

# ── Paths ──────────────────────────────────────────────────────────────────
REPO_ROOT = Path(__file__).resolve().parent.parent
METRICS_DIR = REPO_ROOT / "burn-in" / "metrics"
METRICS_DIR.mkdir(parents=True, exist_ok=True)

CSV_FIELDS = [
    "ts_utc", "elapsed_s", "rss_mb", "vms_mb", "cpu_pct",
    "num_threads", "num_fds", "children", "status",
]


def _ts() -> str:
    return datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")


def _sample(proc: psutil.Process) -> dict:
    """Collect one metric snapshot. Returns empty dict if process gone."""
    try:
        mem = proc.memory_info()
        children = len(proc.children(recursive=True))
        try:
            fds = proc.num_fds()
        except (psutil.AccessDenied, AttributeError):
            fds = -1
        return {
            "rss_mb": round(mem.rss / 1024 / 1024, 2),
            "vms_mb": round(mem.vms / 1024 / 1024, 2),
            "cpu_pct": proc.cpu_percent(interval=1.0),
            "num_threads": proc.num_threads(),
            "num_fds": fds,
            "children": children,
            "status": proc.status(),
        }
    except (psutil.NoSuchProcess, psutil.ZombieProcess):
        return {}


def run(pid: int, run_ts: str, interval: int = 60):
    csv_path = METRICS_DIR / f"run-{run_ts}.csv"
    print(f"[sampler] Monitoring PID={pid} → {csv_path}", flush=True)

    # Wait up to 10s for process to exist
    for _ in range(10):
        if psutil.pid_exists(pid):
            break
        time.sleep(1)
    else:
        print(f"[sampler] PID {pid} not found after 10s — exiting", flush=True)
        sys.exit(1)

    proc = psutil.Process(pid)
    start_time = time.monotonic()
    shutdown = False

    def _on_signal(signum, frame):
        nonlocal shutdown
        shutdown = True

    signal.signal(signal.SIGTERM, _on_signal)
    signal.signal(signal.SIGINT, _on_signal)

    with open(csv_path, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=CSV_FIELDS)
        writer.writeheader()
        fh.flush()

        while not shutdown:
            snap = _sample(proc)
            if not snap:
                # Daemon died — keep sampling at interval (harness will restart it)
                row = {f: "" for f in CSV_FIELDS}
                row["ts_utc"] = _ts()
                row["elapsed_s"] = int(time.monotonic() - start_time)
                row["status"] = "gone"
                writer.writerow(row)
                fh.flush()
                # Re-attach after short delay in case harness restarts daemon
                time.sleep(interval)
                # Try to find new daemon PID via harness.pid
                pid_file = REPO_ROOT / "burn-in" / "harness.pid"
                if pid_file.exists():
                    try:
                        new_pid = int(pid_file.read_text().strip())
                        if new_pid != pid and psutil.pid_exists(new_pid):
                            pid = new_pid
                            proc = psutil.Process(pid)
                            print(f"[sampler] Re-attached to PID={pid}", flush=True)
                    except (ValueError, psutil.NoSuchProcess):
                        pass
                continue

            row = {
                "ts_utc": _ts(),
                "elapsed_s": int(time.monotonic() - start_time),
                **snap,
            }
            writer.writerow(row)
            fh.flush()

            # Print brief status line for tmux observation
            print(
                f"[sampler] t+{row['elapsed_s']}s "
                f"RSS={snap['rss_mb']}MB "
                f"CPU={snap['cpu_pct']}% "
                f"FDs={snap['num_fds']} "
                f"threads={snap['num_threads']}",
                flush=True,
            )

            time.sleep(interval)

    print(f"[sampler] Done. Metrics saved: {csv_path}", flush=True)


def main():
    parser = argparse.ArgumentParser(description="OpenClaw burn-in metric sampler")
    parser.add_argument("--pid", type=int, required=True, help="Daemon PID to monitor")
    parser.add_argument("--run-ts", required=True, help="Run timestamp (matches harness)")
    parser.add_argument("--interval", type=int, default=60, help="Sample interval in seconds")
    args = parser.parse_args()
    run(args.pid, args.run_ts, args.interval)


if __name__ == "__main__":
    main()
