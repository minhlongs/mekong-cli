"""Tests the 30-minute release monitor against deterministic probe responses."""

from __future__ import annotations

import os
import subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

_CURL_STUB = r'''#!/usr/bin/env bash
set -euo pipefail
output_file=""
write_out=""
url=""
while (($#)); do
  case "$1" in
    --output) output_file="$2"; shift 2 ;;
    --write-out) write_out="$2"; shift 2 ;;
    --max-time|--retry|--retry-delay|-H) shift 2 ;;
    --silent|--show-error|--fail|--retry-all-errors) shift ;;
    *) url="$1"; shift ;;
  esac
done

kind=other
case "$url" in
  *alerts.example*) kind=alert ;;
  *api.example*) kind=api ;;
  *dashboard.example*) kind=dashboard ;;
  *site.example*) kind=site ;;
esac
count_file="$MONITOR_TEST_COUNTER_DIR/$kind"
count=0
if [[ -f "$count_file" ]]; then count="$(cat "$count_file")"; fi
count=$((count + 1))
printf '%s' "$count" > "$count_file"

status=200
case "$kind" in
  alert)
    if [[ "${MONITOR_TEST_ACTIVE_ALERT:-0}" == "1" ]]; then
      body='{"active":true}'
    else
      body='{"active":false}'
    fi
    ;;
  api)
    body='{"status":"ok","database":{"connected":true},"bindings":{"d1":true,"kv":true,"queue":true},"pilot":{"invite_only":true,"llm_only":true}}'
    ;;
  dashboard) body='Synthetic dashboard' ;;
  site)
    body='Interactive demo only'
    if [[ "${MONITOR_TEST_FAIL_SITE:-0}" == "1" && "$count" -le 2 ]]; then status=500; fi
    ;;
  *) body='ok' ;;
esac

if [[ -n "$output_file" ]]; then printf '%s' "$body" > "$output_file"; fi
if [[ "$write_out" == '%{http_code}' ]]; then
  printf '%s' "$status"
else
  printf '%s 0.01' "$status"
fi
'''


def _run_monitor(tmp_path: Path, **extra_env: str) -> subprocess.CompletedProcess[str]:
    bin_dir = tmp_path / "bin"
    counter_dir = tmp_path / "counts"
    bin_dir.mkdir()
    counter_dir.mkdir()
    curl = bin_dir / "curl"
    curl.write_text(_CURL_STUB, encoding="utf-8")
    curl.chmod(0o755)

    env = os.environ.copy()
    env.update(
        {
            "PATH": f"{bin_dir}:{env['PATH']}",
            "MONITOR_TEST_COUNTER_DIR": str(counter_dir),
            "MONITOR_SAMPLE_COUNT": "20",
            "MONITOR_INTERVAL_SECONDS": "0",
            "MONITOR_PROBES_PER_TARGET": "1",
            "API_URL": "https://api.example",
            "DASHBOARD_URL": "https://dashboard.example",
            "SITE_URL": "https://site.example",
            "API_BASELINE_MS": "100",
            "DASHBOARD_BASELINE_MS": "100",
            "SITE_BASELINE_MS": "100",
            "SECURITY_ALERT_URL": "https://alerts.example/status",
            "RELEASE_TMP_ROOT": str(tmp_path),
        }
    )
    env.update(extra_env)
    return subprocess.run(
        ["bash", "ci/helpers/monitor-30m.sh"],
        cwd=REPO_ROOT,
        env=env,
        check=False,
        capture_output=True,
        text=True,
    )


def test_monitor_completes_with_healthy_endpoints_and_no_alert(tmp_path: Path) -> None:
    result = _run_monitor(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "Completed 20 production monitor samples" in result.stdout


def test_monitor_fails_when_one_service_exceeds_five_percent_errors(tmp_path: Path) -> None:
    result = _run_monitor(tmp_path, MONITOR_TEST_FAIL_SITE="1")

    assert result.returncode != 0
    assert "site synthetic probe error rate: 10.00% (2/20)" in result.stdout


def test_monitor_fails_immediately_when_security_alert_feed_is_active(tmp_path: Path) -> None:
    result = _run_monitor(tmp_path, MONITOR_TEST_ACTIVE_ALERT="1")

    assert result.returncode != 0
    assert "security alert feed is active" in result.stderr
