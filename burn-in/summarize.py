"""Burn-in run summarizer — parses JSONL log + CSV metrics → Markdown report.

Usage:
    python3 burn-in/summarize.py [--run-ts 20260417-120000]

If --run-ts omitted, picks the latest run automatically.
Output: burn-in/reports/run-<ts>-summary.md
"""

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = REPO_ROOT / "burn-in" / "logs"
METRICS_DIR = REPO_ROOT / "burn-in" / "metrics"
REPORTS_DIR = REPO_ROOT / "burn-in" / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


def _pick_run_ts(run_ts: str | None) -> str:
    if run_ts:
        return run_ts
    logs = sorted(LOGS_DIR.glob("run-*.jsonl"), key=lambda p: p.stat().st_mtime)
    if not logs:
        print("[summarize] No log files found in burn-in/logs/")
        sys.exit(1)
    # Extract ts from filename: run-<ts>.jsonl
    return logs[-1].stem[4:]  # strip "run-"


def _parse_log(log_path: Path) -> dict:
    events = []
    if not log_path.exists():
        return {"events": events, "error": f"Log not found: {log_path}"}
    with open(log_path) as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                pass

    starts = [e for e in events if e.get("event") == "harness_start"]
    ends = [e for e in events if e.get("event") == "harness_end"]
    restarts = [e for e in events if e.get("event") == "daemon_restart"]
    exits = [e for e in events if e.get("event") == "daemon_exit"]
    stdout_lines = [e for e in events if e.get("event") == "daemon_stdout"]
    errors = [e for e in stdout_lines if "[ERROR]" in e.get("msg", "") or
              "[FATAL]" in e.get("msg", "") or "[CYCLE_ERROR]" in e.get("msg", "")]

    uptime_s = 0
    if ends:
        uptime_s = ends[-1].get("uptime_s", 0)
    elif starts:
        # Still running — estimate from last event
        try:
            t0 = datetime.fromisoformat(starts[0]["ts"].replace("Z", "+00:00"))
            last_ts = events[-1]["ts"].replace("Z", "+00:00")
            t1 = datetime.fromisoformat(last_ts)
            uptime_s = int((t1 - t0).total_seconds())
        except Exception:
            pass

    return {
        "events": events,
        "total_events": len(events),
        "uptime_s": uptime_s,
        "restart_count": len(restarts),
        "exit_count": len(exits),
        "stdout_lines": len(stdout_lines),
        "error_count": len(errors),
        "top_errors": [e.get("msg", "") for e in errors[:10]],
        "harness_ended_cleanly": bool(ends),
    }


def _parse_metrics(csv_path: Path) -> dict:
    if not csv_path.exists():
        return {"error": f"Metrics CSV not found: {csv_path}"}
    rows = []
    with open(csv_path, newline="") as fh:
        reader = csv.DictReader(fh)
        for row in reader:
            rows.append(row)
    if not rows:
        return {"error": "Empty CSV"}

    rss_vals = []
    cpu_vals = []
    for row in rows:
        try:
            rss_vals.append(float(row["rss_mb"]))
        except (ValueError, KeyError):
            pass
        try:
            cpu_vals.append(float(row["cpu_pct"]))
        except (ValueError, KeyError):
            pass

    # Memory drift: linear regression slope (MB/hr)
    drift_mb_per_hr = 0.0
    if len(rss_vals) >= 2:
        n = len(rss_vals)
        xs = list(range(n))  # sample index (each = 1 min)
        mx = sum(xs) / n
        my = sum(rss_vals) / n
        num = sum((x - mx) * (y - my) for x, y in zip(xs, rss_vals))
        den = sum((x - mx) ** 2 for x in xs)
        slope_per_sample = num / den if den else 0
        drift_mb_per_hr = round(slope_per_sample * 60, 3)  # 60 samples/hr

    return {
        "sample_count": len(rows),
        "rss_baseline_mb": round(rss_vals[0], 1) if rss_vals else 0,
        "rss_peak_mb": round(max(rss_vals), 1) if rss_vals else 0,
        "rss_final_mb": round(rss_vals[-1], 1) if rss_vals else 0,
        "rss_drift_mb_per_hr": drift_mb_per_hr,
        "cpu_avg_pct": round(sum(cpu_vals) / len(cpu_vals), 1) if cpu_vals else 0,
        "cpu_peak_pct": round(max(cpu_vals), 1) if cpu_vals else 0,
    }


def _go_nogo(log_data: dict, metrics: dict, uptime_target_s: int = 43200) -> tuple[str, list[str]]:
    """Evaluate GO/NO-GO. Target = 12h for smoke, 24h for full run."""
    reasons = []
    verdict = "GO"

    uptime_s = log_data.get("uptime_s", 0)
    if uptime_s < uptime_target_s:
        verdict = "NO-GO"
        reasons.append(f"Uptime {uptime_s}s < target {uptime_target_s}s")

    restart_count = log_data.get("restart_count", 0)
    if restart_count > 3:
        verdict = "NO-GO"
        reasons.append(f"Restart count {restart_count} > 3")

    error_rate = log_data.get("error_count", 0) / max(uptime_s / 3600, 1)
    if error_rate > 1:
        verdict = "NO-GO"
        reasons.append(f"Error rate {error_rate:.2f}/hr > 1/hr threshold")

    rss_drift = metrics.get("rss_drift_mb_per_hr", 0)
    if rss_drift > 50:
        verdict = "NO-GO"
        reasons.append(f"RSS drift {rss_drift} MB/hr > 50 MB/hr threshold")

    rss_peak = metrics.get("rss_peak_mb", 0)
    if rss_peak > 2048:
        verdict = "NO-GO"
        reasons.append(f"Peak RSS {rss_peak} MB > 2048 MB limit")

    if verdict == "GO" and not reasons:
        reasons.append("All thresholds met")

    return verdict, reasons


def render_report(run_ts: str, log_data: dict, metrics: dict) -> str:
    uptime_s = log_data.get("uptime_s", 0)
    uptime_h = uptime_s / 3600
    verdict, reasons = _go_nogo(log_data, metrics)
    generated = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    lines = [
        f"# OpenClaw Burn-In Summary — {run_ts}",
        f"",
        f"**Generated:** {generated}  ",
        f"**Verdict:** {'✅ GO' if verdict == 'GO' else '❌ NO-GO'}",
        f"",
        f"## Uptime & Stability",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Uptime | {uptime_h:.2f}h ({uptime_s}s) |",
        f"| Daemon restarts | {log_data.get('restart_count', 0)} |",
        f"| Clean shutdown | {'Yes' if log_data.get('harness_ended_cleanly') else 'No'} |",
        f"| Total log events | {log_data.get('total_events', 0)} |",
        f"| Error log lines | {log_data.get('error_count', 0)} |",
        f"",
        f"## Memory & CPU",
        f"| Metric | Value |",
        f"|--------|-------|",
    ]
    if "error" not in metrics:
        lines += [
            f"| RSS baseline | {metrics.get('rss_baseline_mb', 'N/A')} MB |",
            f"| RSS peak | {metrics.get('rss_peak_mb', 'N/A')} MB |",
            f"| RSS final | {metrics.get('rss_final_mb', 'N/A')} MB |",
            f"| RSS drift | {metrics.get('rss_drift_mb_per_hr', 'N/A')} MB/hr |",
            f"| CPU avg | {metrics.get('cpu_avg_pct', 'N/A')}% |",
            f"| CPU peak | {metrics.get('cpu_peak_pct', 'N/A')}% |",
            f"| Samples collected | {metrics.get('sample_count', 0)} |",
        ]
    else:
        lines.append(f"| Metrics | {metrics['error']} |")

    lines += [
        f"",
        f"## GO/NO-GO Assessment",
        f"**Verdict: {verdict}**",
        f"",
    ]
    for r in reasons:
        lines.append(f"- {r}")

    top_errors = log_data.get("top_errors", [])
    if top_errors:
        lines += [f"", f"## Top Errors (up to 10)", f"```"]
        lines += top_errors
        lines.append("```")

    lines += [
        f"",
        f"## Files",
        f"- Log: `burn-in/logs/run-{run_ts}.jsonl`",
        f"- Metrics CSV: `burn-in/metrics/run-{run_ts}.csv`",
    ]
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Summarize a burn-in run")
    parser.add_argument("--run-ts", default=None, help="Run timestamp to summarize")
    args = parser.parse_args()

    run_ts = _pick_run_ts(args.run_ts)
    log_path = LOGS_DIR / f"run-{run_ts}.jsonl"
    csv_path = METRICS_DIR / f"run-{run_ts}.csv"

    print(f"[summarize] Parsing log: {log_path}")
    print(f"[summarize] Parsing metrics: {csv_path}")

    log_data = _parse_log(log_path)
    metrics = _parse_metrics(csv_path)
    report = render_report(run_ts, log_data, metrics)

    out_path = REPORTS_DIR / f"run-{run_ts}-summary.md"
    out_path.write_text(report)
    print(f"[summarize] Report saved: {out_path}")
    print(report)


if __name__ == "__main__":
    main()
