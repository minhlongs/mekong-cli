"""Tests for src.core.llm_router_adapter — LLMRouterAdapter."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock, PropertyMock, patch

import pytest

from src.core.adapters.llm.client import LLMClient, LLMResponse
from src.core.llm_router_adapter import LLMRouterAdapter
from src.core.protocols import LLMRouter
from src.core.providers import LLMProvider, OfflineProvider, OpenAICompatibleProvider


class TestDualProviderProtocol:
    """Prove at least 2 provider configs satisfy the same LLMRouter Protocol."""

    def test_two_providers_satisfy_same_protocol(self):
        """Two different LLMClient configs wrapped in adapter both satisfy Protocol."""
        provider_a = OpenAICompatibleProvider(
            base_url="https://api.openai.com/v1",
            api_key="sk-test",
            model="gpt-test",
            provider_name="openai-direct",
        )
        provider_b = OfflineProvider()
        client_a = LLMClient(providers=[provider_a])
        client_b = LLMClient(providers=[provider_b])

        adapter_a = LLMRouterAdapter(client=client_a)
        adapter_b = LLMRouterAdapter(client=client_b)

        assert isinstance(adapter_a, LLMRouter)
        assert isinstance(adapter_b, LLMRouter)

    def test_init_default_client(self):
        """Adapter uses get_client() when client is not passed."""
        with patch("src.core.llm_router_adapter.get_client") as mock_get:
            mock_client = MagicMock()
            mock_get.return_value = mock_client
            adapter = LLMRouterAdapter()
            assert adapter._llm_client is mock_client

    def test_is_available_reflects_client(self):
        """is_available property reflects underlying client state."""
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.is_available = True
        adapter._llm_client = mock_client

        assert adapter.is_available is True

        mock_client.is_available = False
        assert adapter.is_available is False

    def test_chat_direct_call(self):
        """chat() delegates directly to LLMClient.chat()."""
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.chat.return_value = LLMResponse(content="chat output")
        adapter._llm_client = mock_client

        messages = [{"role": "user", "content": "hi"}]
        res = adapter.chat(messages, model="gpt-4", temperature=0.7)

        assert res.content == "chat output"
        mock_client.chat.assert_called_once_with(messages, model="gpt-4", temperature=0.7)


class TestRoutingAndCostEstimation:
    def test_classify_with_available_providers(self):
        adapter = LLMRouterAdapter()
        p1 = MagicMock(name="p1")
        p1.name = "mock-provider-1"
        p1.is_available.return_value = True
        mock_client = MagicMock(spec=LLMClient)
        mock_client.providers = [p1]
        adapter._llm_client = mock_client

        cls_res = adapter.classify("build an app")
        assert cls_res["task"] == "build an app"
        assert cls_res["model"] == "mock-provider-1"
        assert cls_res["capability"] == "standard"
        assert cls_res["tier"] == "basic"

    def test_classify_with_no_available_providers(self):
        adapter = LLMRouterAdapter()
        p1 = MagicMock()
        p1.is_available.return_value = False
        mock_client = MagicMock(spec=LLMClient)
        mock_client.providers = [p1]
        adapter._llm_client = mock_client

        cls_res = adapter.classify("build an app")
        assert cls_res["model"] == "unknown"

    def test_select_model_with_available_providers(self):
        adapter = LLMRouterAdapter()
        p1 = MagicMock()
        p1.name = "fast-llm"
        p1.is_available.return_value = True
        mock_client = MagicMock(spec=LLMClient)
        mock_client.providers = [p1]
        adapter._llm_client = mock_client

        selected = adapter.select_model({"task": "code"}, "premium")
        assert selected == "fast-llm"

    def test_select_model_without_available_providers(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.providers = []
        adapter._llm_client = mock_client

        selected = adapter.select_model({"task": "code"}, "basic")
        assert selected == "default"

    def test_estimate_cost(self):
        adapter = LLMRouterAdapter()
        cost = adapter.estimate_cost("qwen-max", 1000)
        assert cost["model"] == "qwen-max"
        assert cost["tokens"] == 1000
        assert cost["cost_usd"] == 0.01
        assert cost["currency"] == "USD"


class TestGenerationAndStreaming:
    def test_generate_without_model(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.generate.return_value = "generated text"
        adapter._llm_client = mock_client

        out = adapter.generate("write test", temperature=0.2)
        assert out == "generated text"
        mock_client.generate.assert_called_once_with("write test", temperature=0.2)

    def test_generate_with_model(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.generate.return_value = "delegated output"
        adapter._llm_client = mock_client

        result = adapter.generate("hello", model="claude-3", temperature=0.5)
        assert result == "delegated output"
        mock_client.generate.assert_called_once_with(
            "hello", model="claude-3", temperature=0.5,
        )

    def test_stream_success(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.chat.return_value = LLMResponse(content="streamed chunk")
        adapter._llm_client = mock_client

        chunks = list(adapter.stream("hello", model="claude-3"))
        assert chunks == ["streamed chunk"]
        mock_client.chat.assert_called_once()
        _, kwargs = mock_client.chat.call_args
        assert kwargs.get("model") == "claude-3"

    def test_stream_exception_fallback(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.chat.side_effect = RuntimeError("Network error")
        adapter._llm_client = mock_client

        chunks = list(adapter.stream("hello " * 50))
        assert len(chunks) == 1
        assert "[OFFLINE MODE] LLM unavailable." in chunks[0]


class TestStructuredOutputAndHealth:
    def test_structured_output_dict_response(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.generate_json.return_value = {
            "raw_content": '{"key": "val"}',
            "data": "val",
        }
        adapter._llm_client = mock_client

        schema = {"type": "object"}
        res = adapter.structured_output("give json", schema, model="qwen-2.5")
        assert res["text"] == '{"key": "val"}'
        assert res["parsed"] == {"raw_content": '{"key": "val"}', "data": "val"}
        assert res["schema"] == schema

    def test_structured_output_non_dict_response(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.generate_json.return_value = ["item1", "item2"]
        adapter._llm_client = mock_client

        schema = {"type": "array"}
        res = adapter.structured_output("give array", schema)
        assert res["text"] == "['item1', 'item2']"
        assert res["parsed"] == ["item1", "item2"]

    def test_structured_output_exception(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        mock_client.generate_json.side_effect = ValueError("JSON decode error")
        adapter._llm_client = mock_client

        schema = {"type": "object"}
        res = adapter.structured_output("give json", schema)
        assert res["text"] == ""
        assert res["parsed"] is None
        assert res["schema"] == schema

    def test_health_success(self):
        adapter = LLMRouterAdapter()
        p1 = MagicMock()
        p1.name = "provider-a"
        p2 = MagicMock()
        p2.name = "provider-b"
        mock_client = MagicMock(spec=LLMClient)
        mock_client.providers = [p1, p2]
        adapter._llm_client = mock_client

        h = adapter.health()
        assert h["status"] == "ok"
        assert h["providers"] == ["provider-a", "provider-b"]

    def test_health_exception(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        # Accessing providers raises an exception
        type(mock_client).providers = property(lambda self: (_ for _ in ()).throw(RuntimeError("Health crash")))
        adapter._llm_client = mock_client

        h = adapter.health()
        assert h["status"] == "error"
        assert "Health crash" in h["error"]


class TestToolCalling:
    def test_tool_call_no_capable_providers_raises(self):
        adapter = LLMRouterAdapter()
        p1 = MagicMock()
        p1.name = "simple-llm"
        p1.is_available.return_value = True
        p1.supports_tool_calling.return_value = False
        mock_client = MagicMock(spec=LLMClient)
        mock_client.providers = [p1]
        adapter._llm_client = mock_client

        with pytest.raises(RuntimeError, match="No available provider supports tool calling"):
            adapter.tool_call(
                [{"role": "user", "content": "check weather"}],
                tools=[{"name": "get_weather"}],
            )

    def test_tool_call_success_with_tool_calls(self):
        adapter = LLMRouterAdapter()
        p1 = MagicMock()
        p1.name = "tools-llm"
        p1.is_available.return_value = True
        p1.supports_tool_calling.return_value = True
        mock_client = MagicMock(spec=LLMClient)
        mock_client.providers = [p1]

        mock_resp = MagicMock()
        mock_resp.tool_calls = [{"id": "call_1", "function": {"name": "test_fn"}}]
        mock_client.chat.return_value = mock_resp
        adapter._llm_client = mock_client

        tools = [{"type": "function", "function": {"name": "test_fn"}}]
        calls = adapter.tool_call(
            [{"role": "user", "content": "run fn"}],
            tools=tools,
            model="gpt-4o",
        )
        assert len(calls) == 1
        assert calls[0]["id"] == "call_1"

    def test_tool_call_success_with_none_tool_calls(self):
        adapter = LLMRouterAdapter()
        p1 = MagicMock()
        p1.name = "tools-llm"
        p1.is_available.return_value = True
        p1.supports_tool_calling.return_value = True
        mock_client = MagicMock(spec=LLMClient)
        mock_client.providers = [p1]

        mock_resp = MagicMock()
        mock_resp.tool_calls = None
        mock_client.chat.return_value = mock_resp
        adapter._llm_client = mock_client

        tools = [{"type": "function"}]
        calls = adapter.tool_call(
            [{"role": "user", "content": "hi"}],
            tools=tools,
        )
        assert calls == []


# ---------------------------------------------------------------------------
# E4 Conformance Suite & Protocol Invariants across Multiple Providers
# ---------------------------------------------------------------------------

class FakeOpenRouterProvider(LLMProvider):
    """OpenRouter-compatible provider. Supports tool calling."""

    def __init__(self, tool_calls: list[dict[str, Any]] | None = None) -> None:
        self._tool_calls = tool_calls or []

    @property
    def name(self) -> str:
        return "openrouter"

    def is_available(self) -> bool:
        return True

    def supports_tool_calling(self) -> bool:
        return True

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        if tools is not None:
            return LLMResponse(
                content="",
                model=model,
                tool_calls=list(self._tool_calls),
            )
        content = "openrouter-response"
        if json_mode:
            content = '{"ok": true}'
        return LLMResponse(content=content, model=model)


class FakeClaudeFableProvider(LLMProvider):
    """Claude-Fable-shaped provider. Supports tool calling."""

    def __init__(self, tool_calls: list[dict[str, Any]] | None = None) -> None:
        self._tool_calls = tool_calls or []

    @property
    def name(self) -> str:
        return "claude_fable"

    def is_available(self) -> bool:
        return True

    def supports_tool_calling(self) -> bool:
        return True

    def chat(
        self,
        messages: list[dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        json_mode: bool,
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        if tools is not None:
            return LLMResponse(
                content="",
                model=model,
                tool_calls=list(self._tool_calls),
            )
        content = "claude-fable-response"
        if json_mode:
            content = '{"ok": true}'
        return LLMResponse(content=content, model=model)


_MOCK_TOOL_CALLS = [
    {
        "id": "call_1",
        "type": "function",
        "function": {"name": "read_file", "arguments": '{"path": "a.txt"}'},
    },
]


def _make_adapter_for(provider: LLMProvider) -> LLMRouterAdapter:
    client = LLMClient(
        providers=[provider],
        enable_cache=False,
        enable_hooks=False,
    )
    return LLMRouterAdapter(client=client)


class TestE4ConformanceAndCrossProvider:
    @pytest.mark.parametrize("provider_cls", [FakeOpenRouterProvider, FakeClaudeFableProvider])
    def test_e4_conformance_five_methods(self, provider_cls):
        prov = provider_cls(tool_calls=_MOCK_TOOL_CALLS)
        adapter = _make_adapter_for(prov)

        # 1. generate() -> str
        gen_res = adapter.generate("prompt")
        assert isinstance(gen_res, str)
        assert len(gen_res) > 0

        # 2. stream() -> iterator yielding str chunks
        stream_res = list(adapter.stream("prompt"))
        assert len(stream_res) >= 1
        assert all(isinstance(c, str) for c in stream_res)

        # 3. structured_output() -> dict carrying schema
        schema = {"type": "object", "properties": {"res": {"type": "string"}}}
        so_res = adapter.structured_output("prompt", schema=schema)
        assert isinstance(so_res, dict)
        assert so_res["schema"] == schema

        # 4. tool_call() -> list[dict]
        tools = [{"type": "function", "function": {"name": "read_file"}}]
        tc_res = adapter.tool_call([{"role": "user", "content": "read"}], tools=tools)
        assert isinstance(tc_res, list)
        assert tc_res == _MOCK_TOOL_CALLS

        # 5. health() -> dict with status "ok"
        h_res = adapter.health()
        assert isinstance(h_res, dict)
        assert h_res["status"] == "ok"

    def test_cross_provider_invariants(self):
        a = _make_adapter_for(FakeOpenRouterProvider(tool_calls=_MOCK_TOOL_CALLS))
        b = _make_adapter_for(FakeClaudeFableProvider(tool_calls=_MOCK_TOOL_CALLS))
        tools = [{"type": "function", "function": {"name": "read_file"}}]
        msgs = [{"role": "user", "content": "read"}]
        assert a.tool_call(msgs, tools=tools) == b.tool_call(msgs, tools=tools)
        assert set(a.health().keys()) == set(b.health().keys())

    def test_router_property_mock_health(self):
        adapter = LLMRouterAdapter()
        mock_client = MagicMock(spec=LLMClient)
        type(mock_client).providers = PropertyMock(side_effect=RuntimeError("client down"))
        adapter._llm_client = mock_client
        res = adapter.health()
        assert res["status"] == "error"
        assert "client down" in res["error"]

