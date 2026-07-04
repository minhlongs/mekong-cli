"""Tests for `agent-core doctor` — env + memory + connectivity triage."""

from __future__ import annotations

import httpx
import respx

from agent_core import cli
from agent_core.memory import SeedMemory


def test_doctor_no_urls_skips_mekongd_pings_forest(tmp_path, monkeypatch, capsys):
    """No MEKONGD_URL + unreachable forest: output renders, exit 0."""
    mem = SeedMemory(root=tmp_path / "ac")
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    monkeypatch.delenv("MEKONGD_URL", raising=False)
    monkeypatch.delenv("AGENT_CORE_SESSION_RETENTION", raising=False)
    cli.doctor_cmd(
        mekongd_url=None, forest_url="http://127.0.0.1:1", timeout=0.2, as_json=False
    )
    out = capsys.readouterr().out
    assert "agent-core doctor" in out
    assert "[env]" in out
    assert "[memory]" in out
    assert "[connectivity]" in out
    assert "(skipped — no URL)" in out
    assert "FAIL" in out  # forest unreachable
    assert "[package]" in out
    assert "agent-core:" in out


@respx.mock
def test_doctor_pings_both_services_ok(tmp_path, monkeypatch, capsys):
    """Mock both /healthz: output shows OK lines."""
    mem = SeedMemory(root=tmp_path / "ac")
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    respx.get("http://mekongd:8765/healthz").mock(return_value=httpx.Response(200, json={}))
    respx.get("http://forest:8000/healthz").mock(return_value=httpx.Response(200, json={}))
    cli.doctor_cmd(
        mekongd_url="http://mekongd:8765",
        forest_url="http://forest:8000",
        timeout=1.0,
        as_json=False,
    )
    out = capsys.readouterr().out
    assert "mekongd /healthz     : OK (HTTP 200)" in out
    assert "agent-forest /healthz: OK (HTTP 200)" in out


def test_doctor_env_reflects_set_vars(tmp_path, monkeypatch, capsys):
    """AGENT_CORE_SESSION_RETENTION + MEKONGD_URL render in [env]."""
    mem = SeedMemory(root=tmp_path / "ac")
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    monkeypatch.setenv("AGENT_CORE_SESSION_RETENTION", "50")
    monkeypatch.setenv("MEKONGD_URL", "http://m.example:8765")
    cli.doctor_cmd(
        mekongd_url=None, forest_url="http://127.0.0.1:1", timeout=0.2, as_json=False
    )
    out = capsys.readouterr().out
    assert "MEKONGD_URL                  : http://m.example:8765" in out
    assert "AGENT_CORE_SESSION_RETENTION : 50" in out


def test_doctor_memory_counts_total_rows(tmp_path, monkeypatch, capsys):
    """Seeded memory shows agents + total row count."""
    mem = SeedMemory(root=tmp_path / "ac")
    for _ in range(3):
        mem.remember(agent_id="CEO", content="x", metadata={})
    for _ in range(2):
        mem.remember(agent_id="Developer", content="x", metadata={})
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    monkeypatch.delenv("MEKONGD_URL", raising=False)
    cli.doctor_cmd(
        mekongd_url=None, forest_url="http://127.0.0.1:1", timeout=0.2, as_json=False
    )
    out = capsys.readouterr().out
    assert "agents    : 2" in out
    assert "total rows: 5" in out


def test_doctor_json_emits_parseable_payload(tmp_path, monkeypatch, capsys):
    """--json emits dict with env/memory/connectivity/package keys."""
    import json as _json

    mem = SeedMemory(root=tmp_path / "ac")
    for _ in range(4):
        mem.remember(agent_id="CEO", content="x", metadata={})
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    monkeypatch.setenv("MEKONGD_URL", "http://m.example:8765")
    monkeypatch.setenv("AGENT_CORE_SESSION_RETENTION", "25")
    cli.doctor_cmd(
        mekongd_url=None, forest_url="http://127.0.0.1:1", timeout=0.2, as_json=True
    )
    payload = _json.loads(capsys.readouterr().out)
    assert set(payload.keys()) == {"env", "memory", "connectivity", "package"}
    assert payload["env"]["MEKONGD_URL"] == "http://m.example:8765"
    assert payload["env"]["AGENT_CORE_SESSION_RETENTION"] == "25"
    assert payload["memory"]["agents"] == 1
    assert payload["memory"]["total_rows"] == 4
    assert "FAIL" in payload["connectivity"]["agent_forest"]
    assert payload["package"]["agent_core"]


def test_doctor_json_no_text_mixed(tmp_path, monkeypatch, capsys):
    """--json output parseable as pure JSON (no text banner leakage)."""
    import json as _json

    mem = SeedMemory(root=tmp_path / "ac")
    monkeypatch.setattr(cli, "SeedMemory", lambda: mem)
    monkeypatch.delenv("MEKONGD_URL", raising=False)
    cli.doctor_cmd(
        mekongd_url=None, forest_url="http://127.0.0.1:1", timeout=0.2, as_json=True
    )
    out = capsys.readouterr().out
    # Must parse as JSON from first char; no "agent-core doctor" banner.
    _json.loads(out)
    assert "agent-core doctor" not in out
    assert "[env]" not in out
