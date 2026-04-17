"""Integration tests — end-to-end routing + stats."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest
import respx
from fastapi.testclient import TestClient

from mekongd.config import MekongdConfig
from mekongd.proxy import app, set_runtime
from mekongd.runtime import StubRuntime
from mekongd.stats import aggregate_stats


@pytest.fixture
def tmp_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> MekongdConfig:
    monkeypatch.setenv("MEKONGD_ANTHROPIC_API_KEY", "sk-test-dummy")
    cfg = MekongdConfig()
    cfg.stats_db_path = tmp_path / "stats.sqlite"
    return cfg


@pytest.fixture
def client(tmp_config: MekongdConfig) -> TestClient:
    set_runtime(StubRuntime(tmp_config), tmp_config)
    return TestClient(app)


def test_routing_local_records_stats(client: TestClient, tmp_config: MekongdConfig):
    body = {
        "model": "claude-opus-4-7",
        "system": "Read the file and list imports",
        "messages": [{"role": "user", "content": "go"}],
        "max_tokens": 32,
    }
    r = client.post("/v1/messages", json=body)
    assert r.status_code == 200
    assert "[stub]" in r.json()["content"][0]["text"]

    s = aggregate_stats(tmp_config.stats_db_path)
    assert s.total_requests == 1
    assert s.local_requests == 1
    assert s.cloud_requests == 0
    assert s.total_cost_saved_usd > 0  # local saved $


@respx.mock
def test_routing_cloud_forwards_and_records(
    client: TestClient, tmp_config: MekongdConfig
):
    cloud_response = {
        "id": "msg_cloud123",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": "cloud answer"}],
        "model": "claude-opus-4-7",
        "stop_reason": "end_turn",
        "usage": {"input_tokens": 42, "output_tokens": 7},
    }
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(200, json=cloud_response)
    )

    body = {
        "model": "claude-opus-4-7",
        "system": "Plan the migration",  # matches cloud pattern
        "messages": [{"role": "user", "content": "start"}],
        "max_tokens": 64,
    }
    r = client.post("/v1/messages", json=body)
    assert r.status_code == 200
    assert r.json()["content"][0]["text"] == "cloud answer"

    s = aggregate_stats(tmp_config.stats_db_path)
    assert s.cloud_requests == 1
    assert s.local_requests == 0
    assert s.total_tokens_in == 42
    assert s.total_tokens_out == 7
    assert s.total_cost_saved_usd == 0.0


@respx.mock
def test_cloud_streaming_passthrough(client: TestClient, tmp_config: MekongdConfig):
    """When stream=true and route=cloud, mekongd pipes SSE bytes from Anthropic."""
    sse_body = (
        "event: message_start\n"
        'data: {"type":"message_start","message":{}}\n\n'
        "event: message_delta\n"
        'data: {"type":"message_delta","delta":{"stop_reason":"end_turn"},'
        '"usage":{"output_tokens":42}}\n\n'
        "event: message_stop\n"
        'data: {"type":"message_stop"}\n\n'
    )
    respx.post("https://api.anthropic.com/v1/messages").mock(
        return_value=httpx.Response(
            200,
            content=sse_body,
            headers={"content-type": "text/event-stream"},
        )
    )
    body = {
        "model": "claude-opus-4-7",
        "system": "Architect the migration",  # cloud pattern
        "messages": [{"role": "user", "content": "go"}],
        "max_tokens": 64,
        "stream": True,
    }
    with client.stream("POST", "/v1/messages", json=body) as r:
        assert r.status_code == 200
        raw = b"".join(r.iter_bytes()).decode("utf-8")
    assert "message_start" in raw
    assert "message_delta" in raw
    assert "message_stop" in raw

    s = aggregate_stats(tmp_config.stats_db_path)
    assert s.cloud_requests == 1
    assert s.total_tokens_out == 42  # parsed from SSE message_delta


def test_cloud_without_api_key_returns_501(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    # Override the config used by proxy — API key missing this time.
    monkeypatch.delenv("MEKONGD_ANTHROPIC_API_KEY", raising=False)
    cfg = MekongdConfig()
    cfg.stats_db_path = tmp_path / "stats.sqlite"
    cfg.anthropic_api_key = None
    set_runtime(StubRuntime(cfg), cfg)
    c = TestClient(app)

    body = {
        "model": "claude-opus-4-7",
        "system": "Review this code",
        "messages": [{"role": "user", "content": "go"}],
    }
    r = c.post("/v1/messages", json=body)
    assert r.status_code == 501
    assert "ANTHROPIC_API_KEY" in r.json()["detail"]
