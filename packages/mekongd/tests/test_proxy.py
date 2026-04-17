"""Proxy tests — non-stream + SSE stream with StubRuntime."""

from __future__ import annotations

import json
from typing import AsyncIterator

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
