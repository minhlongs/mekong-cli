"""Tests for LLMClient against a mocked mekongd endpoint."""

from __future__ import annotations

import httpx
import pytest
import respx

from agent_core.llm_client import ChatMessage, LLMClient, _extract_text


@respx.mock
def test_chat_sends_anthropic_compat_body():
    route = respx.post("http://127.0.0.1:8765/v1/messages").mock(
        return_value=httpx.Response(
            200,
            json={
                "content": [{"type": "text", "text": "xin chào"}],
                "usage": {"input_tokens": 5, "output_tokens": 2},
            },
        )
    )
    client = LLMClient(base_url="http://127.0.0.1:8765", api_key="sk-test")
    reply = client.chat(messages=[ChatMessage(role="user", content="chào")], system="you are nice")

    assert reply == "xin chào"
    assert route.called
    sent = route.calls[0].request
    import json

    body = json.loads(sent.content)
    assert body["model"] == client.model
    assert body["system"] == "you are nice"
    assert body["messages"][0] == {"role": "user", "content": "chào"}


@respx.mock
def test_chat_raises_on_http_error():
    respx.post("http://127.0.0.1:8765/v1/messages").mock(
        return_value=httpx.Response(500, json={"error": "boom"})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    with pytest.raises(httpx.HTTPStatusError):
        client.chat(messages=[ChatMessage(role="user", content="x")])


@respx.mock
def test_healthz_returns_json():
    respx.get("http://127.0.0.1:8765/healthz").mock(
        return_value=httpx.Response(200, json={"status": "ok", "runtime": "stub"})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    assert client.healthz()["status"] == "ok"


def test_extract_text_joins_multiple_blocks():
    data = {
        "content": [
            {"type": "text", "text": "hello "},
            {"type": "text", "text": "world"},
            {"type": "tool_use", "text": "ignored"},
        ]
    }
    assert _extract_text(data) == "hello world"


def test_extract_text_empty_when_no_blocks():
    assert _extract_text({"content": []}) == ""
    assert _extract_text({}) == ""


def test_chat_dict_messages_accepted():
    client = LLMClient(base_url="http://127.0.0.1:8765")
    with respx.mock:
        respx.post("http://127.0.0.1:8765/v1/messages").mock(
            return_value=httpx.Response(200, json={"content": [{"type": "text", "text": "ok"}]})
        )
        reply = client.chat(messages=[{"role": "user", "content": "raw dict"}])
    assert reply == "ok"


@respx.mock
def test_send_signal_posts_kind_and_note():
    import json as _json

    route = respx.post("http://127.0.0.1:8765/v1/signals").mock(
        return_value=httpx.Response(202, json={"accepted": True, "kind": "good"})
    )
    client = LLMClient(base_url="http://127.0.0.1:8765")
    resp = client.send_signal("good", "Qwen nailed it")
    assert resp == {"accepted": True, "kind": "good"}
    assert route.called
    body = _json.loads(route.calls[0].request.content)
    assert body == {"kind": "good", "note": "Qwen nailed it"}


def test_send_signal_rejects_invalid_kind():
    client = LLMClient(base_url="http://127.0.0.1:8765")
    with pytest.raises(ValueError, match="good"):
        client.send_signal("maybe")
