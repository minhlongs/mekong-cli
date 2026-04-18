"""Tests for forest_client + format_forest_status + forest_status_cmd CLI."""

from __future__ import annotations

import httpx
import respx

from agent_core import cli
from agent_core.forest_client import fetch_forest_status, parse_prom_metrics
from agent_core.formatters import format_forest_status

_METRICS_SAMPLE = """\
# HELP agent_forest_queue_depth Current length of Redis task_queue list
# TYPE agent_forest_queue_depth gauge
agent_forest_queue_depth 7
# HELP agent_forest_up Service liveness indicator (1=up)
# TYPE agent_forest_up gauge
agent_forest_up 1
# HELP agent_forest_workers_alive Workers with fresh heartbeat (TTL<60s)
# TYPE agent_forest_workers_alive gauge
agent_forest_workers_alive 3
# HELP agent_forest_worker_last_seen_timestamp Max unix-ts of any live heartbeat
# TYPE agent_forest_worker_last_seen_timestamp gauge
agent_forest_worker_last_seen_timestamp 1744934400
"""


def test_parse_prom_metrics_extracts_wanted():
    m = parse_prom_metrics(_METRICS_SAMPLE)
    assert m["agent_forest_queue_depth"] == 7
    assert m["agent_forest_up"] == 1
    assert m["agent_forest_workers_alive"] == 3
    assert m["agent_forest_worker_last_seen_timestamp"] == 1744934400


def test_parse_prom_metrics_ignores_unknown():
    txt = "unknown_metric 42\nagent_forest_up 1\n"
    m = parse_prom_metrics(txt)
    assert "unknown_metric" not in m
    assert m["agent_forest_up"] == 1


def test_parse_prom_metrics_skips_malformed_lines():
    txt = "# comment\n\nagent_forest_up not_a_number\nagent_forest_queue_depth 5\n"
    m = parse_prom_metrics(txt)
    assert m == {"agent_forest_queue_depth": 5}


def test_parse_prom_metrics_strips_label_suffix():
    txt = 'agent_forest_queue_depth{env="prod"} 9\n'
    m = parse_prom_metrics(txt)
    assert m["agent_forest_queue_depth"] == 9


@respx.mock
def test_fetch_forest_status_prefers_json_endpoint():
    """PR #128 added /status JSON — client should use it over /metrics text parse."""
    base = "http://fake-forest.test:8000"
    respx.get(f"{base}/healthz").mock(
        return_value=httpx.Response(200, json={"status": "ok", "service": "agent-forest"})
    )
    respx.get(f"{base}/status").mock(
        return_value=httpx.Response(
            200,
            json={
                "service": "agent-forest",
                "version": "0.1.0",
                "up": True,
                "queue_depth": 7,
                "workers_alive": 3,
                "worker_last_seen_ts": 1744934400,
            },
        )
    )
    # /metrics should NOT be called when /status succeeds
    data = fetch_forest_status(base)
    assert data["error"] is None
    assert data["metrics"]["agent_forest_workers_alive"] == 3
    assert data["metrics"]["agent_forest_up"] == 1.0


@respx.mock
def test_fetch_forest_status_falls_back_to_metrics_on_404():
    """Older gateway versions expose /metrics only — fallback should work."""
    base = "http://old-forest.test:8000"
    respx.get(f"{base}/healthz").mock(
        return_value=httpx.Response(200, json={"status": "ok", "service": "agent-forest"})
    )
    respx.get(f"{base}/status").mock(return_value=httpx.Response(404))
    respx.get(f"{base}/metrics").mock(
        return_value=httpx.Response(200, text=_METRICS_SAMPLE)
    )
    data = fetch_forest_status(base)
    assert data["error"] is None
    assert data["metrics"]["agent_forest_workers_alive"] == 3


@respx.mock
def test_fetch_forest_status_happy_path():
    """Legacy alias — still hits /status first per new behaviour."""
    base = "http://fake-forest.test:8000"
    respx.get(f"{base}/healthz").mock(
        return_value=httpx.Response(200, json={"status": "ok", "service": "agent-forest"})
    )
    respx.get(f"{base}/status").mock(return_value=httpx.Response(404))
    respx.get(f"{base}/metrics").mock(
        return_value=httpx.Response(200, text=_METRICS_SAMPLE)
    )
    data = fetch_forest_status(base)
    assert data["error"] is None
    assert data["healthz"]["status_code"] == 200
    assert data["metrics"]["agent_forest_workers_alive"] == 3


@respx.mock
def test_fetch_forest_status_connection_error_captured():
    base = "http://dead-forest.test:8000"
    respx.get(f"{base}/healthz").mock(side_effect=httpx.ConnectError("refused"))
    data = fetch_forest_status(base)
    assert data["error"] is not None
    assert "ConnectError" in data["error"]


def test_format_forest_status_happy():
    data = {
        "base_url": "http://x:8000",
        "healthz": {"status_code": 200, "body": {"status": "ok", "service": "agent-forest"}},
        "metrics": {
            "agent_forest_queue_depth": 7,
            "agent_forest_up": 1,
            "agent_forest_workers_alive": 3,
            "agent_forest_worker_last_seen_timestamp": 1744934400,
        },
        "error": None,
    }
    out = format_forest_status(data)
    assert "HTTP 200" in out
    assert "queue depth         : 7" in out
    assert "workers alive       : 3" in out
    assert "service up          : yes" in out
    assert "2025" in out  # Formatted ISO timestamp


def test_format_forest_status_error_path():
    data = {"base_url": "http://x:8000", "error": "ConnectError: refused"}
    out = format_forest_status(data)
    assert "error: ConnectError" in out


def test_format_forest_status_no_last_seen():
    data = {
        "base_url": "http://x:8000",
        "healthz": {"status_code": 200, "body": {"service": "agent-forest"}},
        "metrics": {"agent_forest_up": 1, "agent_forest_worker_last_seen_timestamp": 0},
        "error": None,
    }
    out = format_forest_status(data)
    assert "(none)" in out


@respx.mock
def test_forest_status_cmd_renders(monkeypatch, capsys):
    base = "http://stub-forest.test:8000"
    respx.get(f"{base}/healthz").mock(
        return_value=httpx.Response(200, json={"status": "ok", "service": "agent-forest"})
    )
    # Exercise /metrics fallback path in CLI render test
    respx.get(f"{base}/status").mock(return_value=httpx.Response(404))
    respx.get(f"{base}/metrics").mock(
        return_value=httpx.Response(200, text=_METRICS_SAMPLE)
    )
    cli.forest_status_cmd(url=base, timeout=5.0, as_json=False)
    out = capsys.readouterr().out
    assert "agent-forest @" in out
    assert "workers alive       : 3" in out


@respx.mock
def test_forest_status_cmd_json_output(monkeypatch, capsys):
    import json as _json

    base = "http://stub-forest.test:8000"
    respx.get(f"{base}/healthz").mock(
        return_value=httpx.Response(200, json={"status": "ok", "service": "agent-forest"})
    )
    respx.get(f"{base}/status").mock(return_value=httpx.Response(404))
    respx.get(f"{base}/metrics").mock(
        return_value=httpx.Response(200, text=_METRICS_SAMPLE)
    )
    cli.forest_status_cmd(url=base, timeout=5.0, as_json=True)
    out = capsys.readouterr().out
    parsed = _json.loads(out)
    assert parsed["base_url"] == base
    assert parsed["healthz"]["status_code"] == 200
    assert parsed["metrics"]["agent_forest_workers_alive"] == 3
    assert parsed["error"] is None
