"""SSE parser + OmniClient tests using httpx MockTransport."""

from __future__ import annotations

import httpx
import pytest

from src.cli.tui.chat_config import MODELS, resolve_model
from src.cli.tui.omni_client import OmniClient


def _mock_transport(events: list[str], status: int = 200) -> httpx.MockTransport:
    body = "".join(events).encode()

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(status, content=body, request=request)

    return httpx.MockTransport(handler)


async def _collect(events: list[str], status: int = 200) -> list:
    client = OmniClient(
        base_url="http://test", token="t", transport=_mock_transport(events, status)
    )
    chunks: list = []

    async def on_delta(chunk) -> None:
        chunks.append(chunk)

    final = await client.stream_chat(
        "m", [{"role": "user", "content": "hi"}], on_delta
    )
    return chunks, final


@pytest.mark.asyncio
async def test_content_delta():
    events = [
        'data: {"choices":[{"delta":{"content":"Hel"}}]}\n\n',
        'data: {"choices":[{"delta":{"content":"lo"}}]}\n\n',
        "data: [DONE]\n\n",
    ]
    chunks, final = await _collect(events)
    texts = [c.text for c in chunks if c.text]
    assert "".join(texts) == "Hello"
    assert final.text == "lo"


@pytest.mark.asyncio
async def test_reasoning_content_claude_style():
    events = [
        'data: {"choices":[{"delta":{"reasoning_content":"think..."}}]}\n\n',
        "data: [DONE]\n\n",
    ]
    chunks, _ = await _collect(events)
    assert any(c.reasoning_text == "think..." for c in chunks)


@pytest.mark.asyncio
async def test_reasoning_details_pmv_style():
    events = [
        'data: {"choices":[{"delta":{"reasoning_details":[{"text":"step1"}]}}]}\n\n',
        "data: [DONE]\n\n",
    ]
    chunks, _ = await _collect(events)
    assert any("step1" in c.reasoning_text for c in chunks)


@pytest.mark.asyncio
async def test_keepalive_and_partial_line():
    events = [
        ":\n\n",
        'data: {"choices":[{"delta":{"content":"ab"}}]}\n\n',
        'data: {"choices":[{"delta":{"content":"cd"}}]}\n\n',
        "data: [DONE]\n\n",
    ]
    chunks, final = await _collect(events)
    texts = [c.text for c in chunks if c.text]
    assert "".join(texts) == "abcd"


@pytest.mark.asyncio
async def test_actual_model_and_provider():
    events = [
        'data: {"model":"nvidia/nemotron-3.5-lightning:free","provider":"Nvidia",'
        '"choices":[{"delta":{"content":"x"}}]}\n\n',
        "data: [DONE]\n\n",
    ]
    chunks, final = await _collect(events)
    assert final.actual_model == "nvidia/nemotron-3.5-lightning:free"
    assert final.provider == "Nvidia"


@pytest.mark.asyncio
async def test_usage_chunk():
    events = [
        'data: {"choices":[{"delta":{"content":"x"}}],"usage":{"total_tokens":42}}\n\n',
        "data: [DONE]\n\n",
    ]
    _, final = await _collect(events)
    assert final.usage.get("total_tokens") == 42


@pytest.mark.asyncio
async def test_error_status():
    client = OmniClient(
        base_url="http://test", token="t", transport=_mock_transport([], status=401)
    )

    async def noop(_chunk) -> None:
        return None

    with pytest.raises(RuntimeError, match="401"):
        await client.stream_chat(
            "m", [{"role": "user", "content": "hi"}], noop
        )

def test_resolve_model_alias():
    assert resolve_model("default") == MODELS["default"]
    assert resolve_model("minimax") == MODELS["minimax"]
    assert resolve_model("pmv/kimchi/kimi-k2.7") == "pmv/kimchi/kimi-k2.7"
    assert resolve_model(None) == MODELS["default"]


def test_resolve_model_unknown_alias_is_raw():
    assert resolve_model("gpt-whatever") == "gpt-whatever"
