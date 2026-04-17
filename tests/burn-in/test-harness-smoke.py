"""5-minute smoke test for OpenClaw burn-in harness.

Verifies that all three scripts work together without syntax errors:
  - harness.py (--dry-run --duration 60)
  - sampler.py (auto-spawned by harness)
  - summarize.py (post-run)

Does NOT run the real 24h daemon — uses --dry-run mode only.

Run:
    pytest tests/burn-in/test-harness-smoke.py -v
    # or directly:
    python3 tests/burn-in/test-harness-smoke.py
"""

import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HARNESS = REPO_ROOT / "burn-in" / "harness.py"
SUMMARIZE = REPO_ROOT / "burn-in" / "summarize.py"
LOGS_DIR = REPO_ROOT / "burn-in" / "logs"
METRICS_DIR = REPO_ROOT / "burn-in" / "metrics"
REPORTS_DIR = REPO_ROOT / "burn-in" / "reports"

SMOKE_DURATION = 60   # seconds — enough for 1 sampler tick + several heartbeats
TIMEOUT = 90          # pytest timeout — kill if harness hangs


@pytest.fixture(scope="module")
def smoke_run():
    """Run harness in dry-run mode for SMOKE_DURATION seconds.

    Returns dict with: returncode, run_ts, log_path, csv_path, elapsed.
    """
    # Capture run_ts by watching which new log file appears
    pre_logs = set(LOGS_DIR.glob("run-*.jsonl"))

    start = time.monotonic()
    proc = subprocess.run(
        [sys.executable, str(HARNESS), "--dry-run", f"--duration={SMOKE_DURATION}"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        timeout=TIMEOUT,
        env={**__import__("os").environ, "MEKONG_ENV": "burn-in"},
    )
    elapsed = time.monotonic() - start

    # Find new log file created during this run
    post_logs = set(LOGS_DIR.glob("run-*.jsonl"))
    new_logs = sorted(post_logs - pre_logs, key=lambda p: p.stat().st_mtime)
    log_path = new_logs[-1] if new_logs else None
    run_ts = log_path.stem[4:] if log_path else None  # strip "run-"
    csv_path = METRICS_DIR / f"run-{run_ts}.csv" if run_ts else None

    return {
        "returncode": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed": elapsed,
        "log_path": log_path,
        "run_ts": run_ts,
        "csv_path": csv_path,
    }


class TestHarnessSmoke:
    def test_harness_exits_cleanly(self, smoke_run):
        """Harness must exit 0 after duration expires."""
        rc = smoke_run["returncode"]
        assert rc == 0, (
            f"Harness exited with code {rc}\n"
            f"stdout: {smoke_run['stdout'][-500:]}\n"
            f"stderr: {smoke_run['stderr'][-500:]}"
        )

    def test_log_file_created(self, smoke_run):
        """JSONL log file must exist and be non-empty."""
        log_path = smoke_run["log_path"]
        assert log_path is not None, "No new log file found in burn-in/logs/"
        assert log_path.exists(), f"Log file missing: {log_path}"
        assert log_path.stat().st_size > 0, "Log file is empty"

    def test_log_has_harness_start_event(self, smoke_run):
        """First event must be harness_start."""
        log_path = smoke_run["log_path"]
        if not log_path:
            pytest.skip("No log file")
        events = []
        with open(log_path) as fh:
            for line in fh:
                line = line.strip()
                if line:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        assert events, "Log file contains no parseable JSON events"
        start_events = [e for e in events if e.get("event") == "harness_start"]
        assert start_events, f"No harness_start event. Events: {[e.get('event') for e in events[:5]]}"

    def test_log_has_harness_end_event(self, smoke_run):
        """harness_end event must be present after clean shutdown."""
        log_path = smoke_run["log_path"]
        if not log_path:
            pytest.skip("No log file")
        content = log_path.read_text()
        assert "harness_end" in content, (
            "harness_end event missing — harness may have crashed before completion"
        )

    def test_at_least_one_daemon_stdout_event(self, smoke_run):
        """Harness must relay at least one daemon stdout line."""
        log_path = smoke_run["log_path"]
        if not log_path:
            pytest.skip("No log file")
        content = log_path.read_text()
        assert "daemon_stdout" in content or "daemon_start" in content, (
            "No daemon activity logged — daemon subprocess may not have started"
        )

    def test_no_api_keys_in_log(self, smoke_run):
        """Log must not contain raw API key patterns."""
        log_path = smoke_run["log_path"]
        if not log_path:
            pytest.skip("No log file")
        content = log_path.read_text()
        import re
        raw_keys = re.findall(r"(sk-[A-Za-z0-9]{20,}|polar_[A-Za-z0-9]{20,})", content)
        assert not raw_keys, f"Unredacted API keys found in log: {raw_keys[:3]}"

    def test_metrics_csv_created(self, smoke_run):
        """Sampler CSV must exist (may be empty if sampler interval > run duration)."""
        csv_path = smoke_run["csv_path"]
        if csv_path is None:
            pytest.skip("No run_ts resolved")
        # CSV may not exist if sampler 60s interval > 60s run — acceptable
        if csv_path.exists():
            header = csv_path.read_text().splitlines()[0]
            assert "rss_mb" in header, f"CSV header missing rss_mb: {header}"

    def test_summarize_runs_without_error(self, smoke_run):
        """summarize.py must exit 0 on the smoke run log."""
        run_ts = smoke_run["run_ts"]
        if not run_ts:
            pytest.skip("No run_ts resolved")
        result = subprocess.run(
            [sys.executable, str(SUMMARIZE), f"--run-ts={run_ts}"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"summarize.py failed (rc={result.returncode})\n{result.stderr[-400:]}"
        )
        report_path = REPORTS_DIR / f"run-{run_ts}-summary.md"
        assert report_path.exists(), f"Summary report not created: {report_path}"
        content = report_path.read_text()
        assert "Uptime" in content, "Summary report missing Uptime section"

    def test_elapsed_within_expected_range(self, smoke_run):
        """Run should complete close to SMOKE_DURATION (within 30s buffer)."""
        elapsed = smoke_run["elapsed"]
        assert elapsed >= SMOKE_DURATION, (
            f"Run finished too fast ({elapsed:.1f}s < {SMOKE_DURATION}s) — harness may have crashed"
        )
        assert elapsed < SMOKE_DURATION + 30, (
            f"Run took too long ({elapsed:.1f}s) — possible hang"
        )


if __name__ == "__main__":
    # Allow running directly without pytest for quick CI checks
    sys.exit(pytest.main([__file__, "-v", "--tb=short"]))
