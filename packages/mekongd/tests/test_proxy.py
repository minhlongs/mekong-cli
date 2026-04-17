"""Proxy tests — non-stream + SSE stream with StubRuntime."""

from __future__ import annotations

import json

import pytest
from fastapi.testclient import TestClient

from mekongd.config import MekongdConfig
from mekongd.proxy import app, set_runtime
from mekongd.runtime import StubRuntime
from mekongd.schemas import MessagesRequest


@pytest.fixture
def client(tmp_path):
    config = MekongdConfig()
    config.stats_db_path = tmp_path / "stats.sqlite"
    set_runtime(StubRuntime(config), config)
    return TestClient(app)


def test_healthz(client: TestClient):
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"
    assert data["runtime"] == "stub"


def test_metrics_empty(client: TestClient):
    r = client.get("/metrics")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/plain")
    body = r.text
    assert "mekongd_requests_total" in body
    assert 'mekongd_requests_total{destination="local"} 0' in body
    assert 'mekongd_requests_total{destination="cloud"} 0' in body
    assert "mekongd_tokens_in_total 0" in body
    assert "mekongd_cost_saved_usd_total 0" in body
    assert "mekongd_local_ratio 0" in body
    assert "mekongd_cloud_spent_usd_today 0" in body


def test_signals_accepts_good_and_bad(client: TestClient):
    r = client.post("/v1/signals", json={"kind": "good", "note": "local Qwen nailed it"})
    assert r.status_code == 202
    assert r.json() == {"accepted": True, "kind": "good"}

    r = client.post("/v1/signals", json={"kind": "bad"})
    assert r.status_code == 202
    assert r.json() == {"accepted": True, "kind": "bad"}

    m = client.get("/metrics").text
    assert 'mekongd_signals_total{kind="good"} 1' in m
    assert 'mekongd_signals_total{kind="bad"} 1' in m
    assert "mekongd_signals_ratio 0.500000" in m


def test_signals_ratio_zero_when_no_signals(client: TestClient):
    m = client.get("/metrics").text
    assert "mekongd_signals_ratio 0" in m


def test_signals_ratio_one_when_all_good(client: TestClient):
    for _ in range(3):
        client.post("/v1/signals", json={"kind": "good"})
    m = client.get("/metrics").text
    assert "mekongd_signals_ratio 1.000000" in m


def test_signals_rejects_invalid_kind(client: TestClient):
    r = client.post("/v1/signals", json={"kind": "maybe"})
    assert r.status_code == 422


def test_signals_breakdown_empty_when_no_signals(client: TestClient):
    r = client.get("/v1/signals/breakdown")
    assert r.status_code == 200
    assert r.json() == {"by_model": {}}


def test_signals_breakdown_groups_by_model(client: TestClient):
    client.post("/v1/signals", json={"kind": "good", "model": "qwen3-8b"})
    client.post("/v1/signals", json={"kind": "bad", "model": "qwen3-8b"})
    client.post("/v1/signals", json={"kind": "good", "model": "claude-sonnet-4-6"})
    client.post("/v1/signals", json={"kind": "bad"})  # legacy-style, no model

    data = client.get("/v1/signals/breakdown").json()["by_model"]
    assert data["qwen3-8b"] == {"good": 1, "bad": 1}
    assert data["claude-sonnet-4-6"] == {"good": 1, "bad": 0}
    assert data[""] == {"good": 0, "bad": 1}


def test_signals_breakdown_accepts_hours_query(client: TestClient):
    client.post("/v1/signals", json={"kind": "good", "model": "qwen3-8b"})
    # hours=1 at test time → the just-posted signal falls inside window
    data = client.get("/v1/signals/breakdown?hours=1").json()["by_model"]
    assert data["qwen3-8b"] == {"good": 1, "bad": 0}


def test_signals_recent_returns_newest_first(client: TestClient):
    client.post("/v1/signals", json={"kind": "good", "note": "A", "model": "qwen3-8b"})
    client.post("/v1/signals", json={"kind": "bad", "note": "B"})
    payload = client.get("/v1/signals/recent?limit=5").json()
    notes = [s["note"] for s in payload["signals"]]
    assert notes == ["B", "A"]


def test_signals_recent_honors_limit_default(client: TestClient):
    for i in range(3):
        client.post("/v1/signals", json={"kind": "good", "note": f"n{i}"})
    payload = client.get("/v1/signals/recent").json()
    assert len(payload["signals"]) == 3


def test_metrics_after_request(client: TestClient):
    body = {
        "model": "claude-opus-4-7",
        "messages": [{"role": "user", "content": "hello metrics"}],
        "max_tokens": 32,
    }
    r = client.post("/v1/messages", json=body)
    assert r.status_code == 200

    r2 = client.get("/metrics")
    assert r2.status_code == 200
    text = r2.text
    assert 'mekongd_requests_total{destination="local"} 1' in text
    assert "mekongd_tokens_in_total" in text
    assert "mekongd_local_ratio 1.000000" in text


def test_messages_non_stream(client: TestClient):
    body = {
        "model": "claude-opus-4-7",
        "messages": [{"role": "user", "content": "hi"}],
        "max_tokens": 64,
    }
    r = client.post("/v1/messages", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["type"] == "message"
    assert data["role"] == "assistant"
    assert data["model"] == "claude-opus-4-7"
    assert len(data["content"]) == 1
    assert data["content"][0]["type"] == "text"
    assert "[stub]" in data["content"][0]["text"]
    assert data["stop_reason"] == "end_turn"
    assert data["usage"]["input_tokens"] >= 1


def test_messages_stream(client: TestClient):
    body = {
        "model": "claude-sonnet-4-6",
        "messages": [{"role": "user", "content": "stream please"}],
        "max_tokens": 32,
        "stream": True,
    }
    with client.stream("POST", "/v1/messages", json=body) as r:
        assert r.status_code == 200
        events: list[str] = []
        payloads: list[dict] = []
        for line in r.iter_lines():
            if not line:
                continue
            if line.startswith("event:"):
                events.append(line.split(":", 1)[1].strip())
            if line.startswith("data:"):
                raw = line.split(":", 1)[1].strip()
                try:
                    payloads.append(json.loads(raw))
                except json.JSONDecodeError:
                    pass
    # Core Anthropic SSE lifecycle
    assert events[0] == "message_start"
    assert "content_block_start" in events
    assert any(e == "content_block_delta" for e in events)
    assert "content_block_stop" in events
    assert events[-2] == "message_delta"
    assert events[-1] == "message_stop"


def test_flatten_prompt_handles_string_and_blocks():
    from mekongd.runtime import _flatten_prompt

    req = MessagesRequest(
        model="x",
        system="sys",
        messages=[
            {"role": "user", "content": "hi"},
            {"role": "assistant", "content": [{"type": "text", "text": "hello"}]},
        ],
    )
    prompt = _flatten_prompt(req)
    assert "<system>" in prompt
    assert "sys" in prompt
    assert "hi" in prompt
    assert "hello" in prompt
    assert prompt.endswith("<assistant>\n")
