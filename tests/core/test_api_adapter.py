# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Tests for ALGO 6 — API Adapter (src/core/api_adapter.py).

Comprehensive unit tests ensuring 100% statement and branch coverage
across provider detection, message formatting, custom headers,
connection reuse/session lifecycle, streaming generation, and sync fallbacks.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

import src.core.api_adapter as api_adapter_mod
from src.core.api_adapter import (
    APIAdapter,
    _anthropic_headers,
    _anthropic_messages_url,
    _get_api_key,
    detect_provider,
    format_for_gemini,
    format_for_openai,
    get_adapter,
)
from src.core.model_selector import ModelConfig


# ===========================================================================
# Helpers & Mocks
# ===========================================================================

def _make_config(
    model_id: str = "claude-sonnet-4-6",
    provider: str = "anthropic",
    max_tokens: int = 256,
    temperature: float = 0.7,
) -> ModelConfig:
    return ModelConfig(
        model_id=model_id,
        provider=provider,
        max_tokens=max_tokens,
        temperature=temperature,
    )


class MockAsyncContent:
    """Async iterator simulating aiohttp response stream content."""

    def __init__(self, lines: list[bytes]) -> None:
        self._lines = lines

    def __aiter__(self) -> MockAsyncContent:
        self._iter = iter(self._lines)
        return self

    async def __anext__(self) -> bytes:
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class MockPostContextManager:
    """Async context manager mocking session.post()."""

    def __init__(self, lines: list[bytes]) -> None:
        self.resp = MagicMock()
        self.resp.content = MockAsyncContent(lines)

    async def __aenter__(self) -> MagicMock:
        return self.resp

    async def __aexit__(self, *args) -> None:
        pass


def _make_urlopen_mock(response_data: dict | None = None, error: Exception | None = None) -> MagicMock:
    """Create a mock for urllib.request.urlopen."""
    if error is not None:
        return MagicMock(side_effect=error)
    cm = MagicMock()
    cm.__enter__.return_value = cm
    cm.__exit__.return_value = False
    cm.read.return_value = json.dumps(response_data or {}).encode("utf-8")
    return MagicMock(return_value=cm)


# ===========================================================================
# Provider Detection
# ===========================================================================

class TestDetectProvider:
    def test_anthropic_models(self):
        assert detect_provider("claude-sonnet-4-6") == "anthropic"
        assert detect_provider("claude-opus-4-6") == "anthropic"
        assert detect_provider("claude-3-haiku-20240307") == "anthropic"

    def test_google_models(self):
        assert detect_provider("gemini-2.0-flash") == "google"
        assert detect_provider("gemini-2.0-pro") == "google"
        assert detect_provider("gemini-1.5-flash") == "google"

    def test_openai_models(self):
        assert detect_provider("gpt-4o") == "openai"
        assert detect_provider("gpt-4o-mini") == "openai"
        assert detect_provider("gpt-3.5-turbo") == "openai"

    def test_ollama_models(self):
        assert detect_provider("ollama:llama3.2:3b") == "ollama"
        assert detect_provider("ollama:mistral:7b") == "ollama"

    def test_unknown_model_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown provider for model"):
            detect_provider("unknown-model-xyz")


# ===========================================================================
# API Key Lookup
# ===========================================================================

class TestGetApiKey:
    def test_anthropic_key(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key-123")
        assert _get_api_key("anthropic") == "ant-key-123"

    def test_google_key(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "ggl-key-456")
        assert _get_api_key("google") == "ggl-key-456"

    def test_openai_key(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "oai-key-789")
        assert _get_api_key("openai") == "oai-key-789"

    def test_missing_key_raises_oserror(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises(OSError, match="Missing API key: ANTHROPIC_API_KEY"):
            _get_api_key("anthropic")

    def test_unknown_provider_raises_oserror(self, monkeypatch):
        with pytest.raises(OSError, match="Missing API key"):
            _get_api_key("unknown_provider")


# ===========================================================================
# Message Formatting
# ===========================================================================

class TestFormatForOpenAI:
    def test_with_system_prompt(self):
        messages = [{"role": "user", "content": "hi"}]
        result = format_for_openai(messages, "You are helpful.")
        assert len(result) == 2
        assert result[0] == {"role": "system", "content": "You are helpful."}
        assert result[1] == {"role": "user", "content": "hi"}

    def test_without_system_prompt(self):
        messages = [{"role": "user", "content": "hi"}]
        result = format_for_openai(messages, None)
        assert len(result) == 1
        assert result[0]["role"] == "user"

    def test_preserves_message_order(self):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi"},
            {"role": "user", "content": "bye"},
        ]
        result = format_for_openai(messages, None)
        assert len(result) == 3
        assert result[0]["content"] == "hello"
        assert result[1]["content"] == "hi"
        assert result[2]["content"] == "bye"

    def test_empty_messages_with_system_prompt(self):
        result = format_for_openai([], "system prompt only")
        assert len(result) == 1
        assert result[0] == {"role": "system", "content": "system prompt only"}


class TestFormatForGemini:
    def test_with_system_prompt(self):
        messages = [{"role": "user", "content": "hi"}]
        result = format_for_gemini(messages, "Be helpful.")
        assert len(result) == 3
        assert result[0] == {"role": "user", "parts": [{"text": "Be helpful."}]}
        assert result[1] == {"role": "model", "parts": [{"text": "Understood."}]}
        assert result[2] == {"role": "user", "parts": [{"text": "hi"}]}

    def test_without_system_prompt(self):
        messages = [{"role": "user", "content": "hi"}]
        result = format_for_gemini(messages, None)
        assert len(result) == 1
        assert result[0] == {"role": "user", "parts": [{"text": "hi"}]}

    def test_assistant_role_mapped_to_model(self):
        messages = [
            {"role": "user", "content": "hello"},
            {"role": "assistant", "content": "hi there"},
        ]
        result = format_for_gemini(messages, None)
        assert result[0]["role"] == "user"
        assert result[1]["role"] == "model"
        assert result[1]["parts"][0]["text"] == "hi there"


# ===========================================================================
# Anthropic URL & Header Builders
# ===========================================================================

class TestAnthropicURLAndHeaders:
    def test_anthropic_messages_url_variants(self):
        # Base url already ending with /messages
        assert _anthropic_messages_url("https://api.anthropic.com/messages") == "https://api.anthropic.com/messages"
        assert _anthropic_messages_url("https://api.anthropic.com/messages/") == "https://api.anthropic.com/messages"

        # zunef.com proxy endpoint
        assert _anthropic_messages_url("https://api.zunef.com/v1") == "https://api.zunef.com/v1/messages"
        assert _anthropic_messages_url("https://API.ZUNEF.COM/test") == "https://API.ZUNEF.COM/test/messages"

        # Base ending with /v1
        assert _anthropic_messages_url("https://custom.endpoint.org/v1") == "https://custom.endpoint.org/v1/messages"
        assert _anthropic_messages_url("https://custom.endpoint.org/v1/") == "https://custom.endpoint.org/v1/messages"

        # Standard base URL
        assert _anthropic_messages_url("https://api.anthropic.com") == "https://api.anthropic.com/v1/messages"

    def test_anthropic_headers_defaults(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_CUSTOM_HEADERS", raising=False)
        headers = _anthropic_headers("secret-key")
        assert headers == {
            "x-api-key": "secret-key",
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def test_anthropic_headers_json_format(self, monkeypatch):
        custom_json = json.dumps({
            "X-ZUNEF-CLIENT": "claude-code",
            "X-Device-Id": "dev-456",
        })
        monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS", custom_json)
        headers = _anthropic_headers("secret-key")
        assert headers["x-api-key"] == "secret-key"
        assert headers["X-ZUNEF-CLIENT"] == "claude-code"
        assert headers["X-Device-Id"] == "dev-456"

    def test_anthropic_headers_json_not_dict_fallback_to_pseudo_headers(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS", '["not", "a", "dict"]')
        headers = _anthropic_headers("secret-key")
        assert headers["x-api-key"] == "secret-key"
        assert len(headers) == 3

    def test_anthropic_headers_pseudo_header_lines(self, monkeypatch):
        pseudo = """
        X-Custom-Auth: token_123

        X-Client-Version=v2.5
        EmptySeparatorLine
        """
        monkeypatch.setenv("ANTHROPIC_CUSTOM_HEADERS", pseudo)
        headers = _anthropic_headers("secret-key")
        assert headers["X-Custom-Auth"] == "token_123"
        assert headers["X-Client-Version"] == "v2.5"
        assert "EmptySeparatorLine" not in headers


# ===========================================================================
# APIAdapter Lifecycle & Context Manager
# ===========================================================================

class TestAPIAdapterLifecycle:
    @pytest.mark.asyncio
    async def test_session_lifecycle(self):
        adapter = APIAdapter()
        try:
            assert adapter._session is None
            session1 = await adapter._get_session()
            assert not session1.closed

            # Reuse session
            session2 = await adapter._get_session()
            assert session1 is session2

            # Close session
            await adapter.close()
            assert session1.closed

            # Second close is idempotent
            await adapter.close()

            # Calling _get_session after close recreates a fresh session
            session3 = await adapter._get_session()
            assert not session3.closed
            assert session3 is not session1
            await adapter.close()
        finally:
            await adapter.close()

    @pytest.mark.asyncio
    async def test_async_context_manager(self):
        async with APIAdapter() as adapter:
            session = await adapter._get_session()
            assert not session.closed
        assert session.closed


# ===========================================================================
# Streaming Generation (Async)
# ===========================================================================

class TestStreamingGeneration:
    @pytest.mark.asyncio
    async def test_generate_anthropic_streaming(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        adapter = APIAdapter()

        lines = [
            b"",  # Empty line skipped
            b": keep-alive\n",  # Non-data line skipped
            b"data: " + json.dumps({"delta": {"text": "Hello "}}).encode("utf-8") + b"\n",
            b"data: {malformed json\n",  # JSONDecodeError branch skipped
            b"data: " + json.dumps({"delta": {}}).encode("utf-8") + b"\n",  # No text
            b"data: " + json.dumps({"delta": {"text": "world!"}}).encode("utf-8") + b"\n",
            b"data: [DONE]\n",  # Break sentinel
            b"data: " + json.dumps({"delta": {"text": "ignored"}}).encode("utf-8") + b"\n",
        ]

        mock_session = MagicMock()
        mock_session.post.return_value = MockPostContextManager(lines)

        with patch.object(adapter, "_get_session", return_value=mock_session):
            config = _make_config("claude-sonnet-4-6", provider="anthropic")
            tokens = []
            async for token in adapter._generate_anthropic(
                config, [{"role": "user", "content": "hi"}], system_prompt="System instructions"
            ):
                tokens.append(token)

            assert "".join(tokens) == "Hello world!"
            mock_session.post.assert_called_once()
            _, kwargs = mock_session.post.call_args
            assert kwargs["json"]["system"] == "System instructions"
            assert kwargs["json"]["stream"] is True

    @pytest.mark.asyncio
    async def test_generate_google_streaming(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "ggl-test-key")
        adapter = APIAdapter()

        lines = [
            b"",
            b"data: {invalid json\n",
            b"data: " + json.dumps({
                "candidates": [
                    {"content": {"parts": [{"text": "Part 1 "}, {"text": "Part 2"}]}}
                ]
            }).encode("utf-8") + b"\n",
            b"data: " + json.dumps({"candidates": []}).encode("utf-8") + b"\n",
            b"data: " + json.dumps({
                "candidates": [{"content": {"parts": [{"other": 123}]}}]
            }).encode("utf-8") + b"\n",
        ]

        mock_session = MagicMock()
        mock_session.post.return_value = MockPostContextManager(lines)

        with patch.object(adapter, "_get_session", return_value=mock_session):
            config = _make_config("gemini-2.0-flash", provider="google")
            tokens = []
            async for token in adapter._generate_google(
                config, [{"role": "user", "content": "hi"}], system_prompt=None
            ):
                tokens.append(token)

            assert "".join(tokens) == "Part 1 Part 2"
            mock_session.post.assert_called_once()

    @pytest.mark.asyncio
    async def test_generate_openai_streaming(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "oai-test-key")
        adapter = APIAdapter()

        lines = [
            b"",
            b": ping\n",
            b"data: " + json.dumps({"choices": [{"delta": {"content": "GPT "}}]}).encode("utf-8") + b"\n",
            b"data: broken json\n",
            b"data: " + json.dumps({"choices": [{"delta": {}}]}).encode("utf-8") + b"\n",
            b"data: " + json.dumps({"choices": []}).encode("utf-8") + b"\n",  # IndexError
            b"data: " + json.dumps({}).encode("utf-8") + b"\n",  # KeyError
            b"data: " + json.dumps({"choices": [{"delta": {"content": "stream"}}]}).encode("utf-8") + b"\n",
            b"data: [DONE]\n",
            b"data: " + json.dumps({"choices": [{"delta": {"content": "not delivered"}}]}).encode("utf-8") + b"\n",
        ]

        mock_session = MagicMock()
        mock_session.post.return_value = MockPostContextManager(lines)

        with patch.object(adapter, "_get_session", return_value=mock_session):
            config = _make_config("gpt-4o", provider="openai")
            tokens = []
            async for token in adapter._generate_openai(
                config, [{"role": "user", "content": "hi"}], system_prompt="Answer concisely"
            ):
                tokens.append(token)

            assert "".join(tokens) == "GPT stream"
            mock_session.post.assert_called_once()
            _, kwargs = mock_session.post.call_args
            assert kwargs["headers"]["Authorization"] == "Bearer oai-test-key"

    @pytest.mark.asyncio
    async def test_generate_dispatch_all_providers(self):
        adapter = APIAdapter()

        async def _mock_anthropic(*args, **kwargs):
            yield "ant_token"

        async def _mock_google(*args, **kwargs):
            yield "ggl_token"

        async def _mock_openai(*args, **kwargs):
            yield "oai_token"

        with patch.object(adapter, "_generate_anthropic", side_effect=_mock_anthropic):
            config = _make_config("claude-sonnet-4-6", provider="anthropic")
            tokens = [t async for t in adapter.generate(config, [])]
            assert tokens == ["ant_token"]

        with patch.object(adapter, "_generate_google", side_effect=_mock_google):
            config = _make_config("gemini-2.0-flash", provider="google")
            tokens = [t async for t in adapter.generate(config, [])]
            assert tokens == ["ggl_token"]

        with patch.object(adapter, "_generate_openai", side_effect=_mock_openai):
            config = _make_config("gpt-4o", provider="openai")
            tokens = [t async for t in adapter.generate(config, [])]
            assert tokens == ["oai_token"]

    @pytest.mark.asyncio
    async def test_generate_unsupported_provider_raises_value_error(self):
        adapter = APIAdapter()
        config = _make_config("ollama:llama3", provider="ollama")
        with pytest.raises(ValueError, match="Unsupported provider: ollama"):
            async for _ in adapter.generate(config, []):
                pass


# ===========================================================================
# Synchronous Generation (urllib sync fallbacks)
# ===========================================================================

class TestGenerateSync:
    def test_sync_anthropic_success(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")
        monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com")
        adapter = APIAdapter()
        config = _make_config("claude-sonnet-4-6", provider="anthropic")
        response = {"content": [{"text": "Hello "}, {"text": "from Claude!"}]}

        with patch("urllib.request.urlopen", _make_urlopen_mock(response)):
            result = adapter.generate_sync(config, [{"role": "user", "content": "hi"}], "be helpful")
            assert result == "Hello from Claude!"

    def test_sync_anthropic_error_returns_empty_string(self, monkeypatch):
        monkeypatch.setenv("ANTHROPIC_API_KEY", "ant-key")
        adapter = APIAdapter()
        config = _make_config("claude-sonnet-4-6", provider="anthropic")

        with patch("urllib.request.urlopen", _make_urlopen_mock(error=OSError("Network failure"))):
            result = adapter._sync_anthropic(config, [], None, "ant-key")
            assert result == ""

    def test_sync_google_success(self, monkeypatch):
        monkeypatch.setenv("GOOGLE_API_KEY", "ggl-key")
        adapter = APIAdapter()
        config = _make_config("gemini-2.0-flash", provider="google")
        response = {
            "candidates": [
                {"content": {"parts": [{"text": "Google "}, {"text": "response"}]}}
            ]
        }

        with patch("urllib.request.urlopen", _make_urlopen_mock(response)):
            result = adapter.generate_sync(config, [{"role": "user", "content": "hi"}], "be fast")
            assert result == "Google response"

    def test_sync_google_empty_candidates_returns_empty_string(self):
        adapter = APIAdapter()
        config = _make_config("gemini-2.0-flash", provider="google")
        response = {"candidates": []}

        with patch("urllib.request.urlopen", _make_urlopen_mock(response)):
            result = adapter._sync_google(config, [], None, "ggl-key")
            assert result == ""

    def test_sync_google_error_returns_empty_string(self):
        adapter = APIAdapter()
        config = _make_config("gemini-2.0-flash", provider="google")

        with patch("urllib.request.urlopen", _make_urlopen_mock(error=OSError("Timeout"))):
            result = adapter._sync_google(config, [], None, "ggl-key")
            assert result == ""

    def test_sync_openai_success(self, monkeypatch):
        monkeypatch.setenv("OPENAI_API_KEY", "oai-key")
        adapter = APIAdapter()
        config = _make_config("gpt-4o", provider="openai")
        response = {
            "choices": [
                {"message": {"content": "OpenAI generated answer"}}
            ]
        }

        with patch("urllib.request.urlopen", _make_urlopen_mock(response)):
            result = adapter.generate_sync(config, [{"role": "user", "content": "hi"}], None)
            assert result == "OpenAI generated answer"

    def test_sync_openai_error_returns_empty_string(self):
        adapter = APIAdapter()
        config = _make_config("gpt-4o", provider="openai")

        with patch("urllib.request.urlopen", _make_urlopen_mock(error=OSError("Refused"))):
            result = adapter._sync_openai(config, [], None, "oai-key")
            assert result == ""

    def test_sync_unsupported_provider_returns_empty_string(self):
        adapter = APIAdapter()
        config = _make_config("ollama:llama3", provider="ollama")
        with patch("src.core.api_adapter._get_api_key", return_value="dummy_key"):
            result = adapter.generate_sync(config, [])
            assert result == ""


# ===========================================================================
# Singleton Getter
# ===========================================================================

class TestGetAdapterSingleton:
    def test_get_adapter_creates_and_caches_instance(self):
        api_adapter_mod._adapter = None
        adapter1 = get_adapter()
        assert isinstance(adapter1, APIAdapter)
        adapter2 = get_adapter()
        assert adapter1 is adapter2
        api_adapter_mod._adapter = None
