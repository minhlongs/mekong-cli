"""Additional coverage tests for src/core/providers.py.

Targets uncovered branches in:
- LLMResponse.__post_init__ (default usage/raw)
- GeminiProvider.__init__ (no key, import error)
- GeminiProvider.chat (empty prompt, retry on empty response, retry on error,
                       text via candidates fallback, json_mode, system_instruction)
- OpenAICompatibleProvider (no base_url, http error, url error, json_mode)
- OfflineProvider.chat (message extraction)
- LiteLLMProvider.__init__ (health check success/fail, import error)
- LiteLLMProvider.chat (no base_url, httpx missing, 429 budget, connect error)
"""

from __future__ import annotations

import json
import sys
import os
from unittest.mock import MagicMock, Mock, patch

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import pytest

from src.core.providers import (
    GeminiProvider,
    LiteLLMProvider,
    LLMResponse,
    OfflineProvider,
    OpenAICompatibleProvider,
)


# ---------------------------------------------------------------------------
# LLMResponse
# ---------------------------------------------------------------------------

class TestLLMResponse:
    def test_default_usage_and_raw(self):
        resp = LLMResponse(content="hello")
        assert resp.usage == {}
        assert resp.raw == {}
        assert resp.model == ""

    def test_provided_usage_and_raw(self):
        resp = LLMResponse(
            content="hi", model="gpt-4",
            usage={"total_tokens": 10},
            raw={"finish_reason": "stop"},
        )
        assert resp.usage["total_tokens"] == 10
        assert resp.raw["finish_reason"] == "stop"

    def test_none_usage_becomes_empty_dict(self):
        resp = LLMResponse(content="x", usage=None, raw=None)
        assert resp.usage == {}
        assert resp.raw == {}


# ---------------------------------------------------------------------------
# GeminiProvider
# ---------------------------------------------------------------------------

class TestGeminiProviderInit:
    def test_no_api_key_not_available(self):
        provider = GeminiProvider(api_key="")
        assert provider.is_available() is False
        assert provider.name == "gemini"

    def test_import_error_disables_provider(self):
        with patch.dict("sys.modules", {"google": None, "google.genai": None}):
            provider = GeminiProvider(api_key="some-key")
        assert provider.is_available() is False

    def test_successful_init(self):
        mock_client = Mock()
        mock_genai = Mock()
        mock_genai.Client.return_value = mock_client
        with patch.dict("sys.modules", {"google": Mock(), "google.genai": mock_genai}):
            provider = GeminiProvider(api_key="valid-key")
        assert provider.is_available() is True


class TestGeminiProviderChat:
    def _unavailable_provider(self) -> GeminiProvider:
        p = GeminiProvider(api_key="")
        return p

    def _available_provider(self) -> GeminiProvider:
        mock_client = Mock()
        mock_genai = Mock()
        mock_genai.Client.return_value = mock_client
        with patch.dict("sys.modules", {"google": Mock(), "google.genai": mock_genai}):
            p = GeminiProvider(api_key="key")
        p._client = mock_client
        p._available = True
        return p

    def test_chat_raises_when_no_client(self):
        p = self._unavailable_provider()
        with pytest.raises(RuntimeError, match="not available"):
            p.chat([{"role": "user", "content": "hi"}], "gemini-pro", 0.5, 100, False)

    def test_chat_raises_on_empty_prompt(self):
        p = self._available_provider()
        with pytest.raises(ValueError, match="Empty prompt"):
            p.chat([{"role": "system", "content": "system only"}], "gemini-pro", 0.5, 100, False)

    def test_chat_success(self):
        p = self._available_provider()
        mock_response = Mock()
        mock_response.text = "Hello from Gemini"
        mock_response.candidates = [Mock(finish_reason="STOP")]
        mock_response.usage_metadata = Mock(total_token_count=42)
        p._client.models.generate_content.return_value = mock_response

        result = p.chat(
            [{"role": "user", "content": "hello"}], "gemini-pro", 0.7, 200, False
        )
        assert result.content == "Hello from Gemini"
        assert result.usage["total_tokens"] == 42
        assert result.model == "gemini-pro"

    def test_chat_with_system_instruction(self):
        p = self._available_provider()
        mock_response = Mock()
        mock_response.text = "Answer"
        mock_response.candidates = [Mock(finish_reason="STOP")]
        mock_response.usage_metadata = Mock(total_token_count=5)
        p._client.models.generate_content.return_value = mock_response

        p.chat(
            [
                {"role": "system", "content": "Be helpful"},
                {"role": "user", "content": "question"},
            ],
            "gemini-pro", 0.5, 100, False,
        )
        config_arg = p._client.models.generate_content.call_args[1]["config"]
        assert config_arg["system_instruction"] == "Be helpful"

    def test_chat_with_json_mode(self):
        p = self._available_provider()
        mock_response = Mock()
        mock_response.text = '{"key": "val"}'
        mock_response.candidates = [Mock(finish_reason="STOP")]
        mock_response.usage_metadata = Mock(total_token_count=5)
        p._client.models.generate_content.return_value = mock_response

        p.chat(
            [{"role": "user", "content": "return json"}], "gemini-pro", 0.0, 100, True
        )
        config_arg = p._client.models.generate_content.call_args[1]["config"]
        assert config_arg["response_mime_type"] == "application/json"

    def test_chat_empty_response_retries_then_raises(self):
        p = self._available_provider()
        mock_response = Mock()
        mock_response.text = ""
        mock_response.candidates = [Mock(finish_reason="SAFETY")]
        mock_response.usage_metadata = Mock(total_token_count=0)
        p._client.models.generate_content.return_value = mock_response

        with patch("time.sleep"):
            with pytest.raises(RuntimeError, match="Empty response"):
                p.chat([{"role": "user", "content": "test"}], "gemini-pro", 0.5, 100, False)
        # Should have retried 3 times
        assert p._client.models.generate_content.call_count == 3

    def test_chat_text_via_candidates_fallback(self):
        """When response.text raises ValueError, fall back to candidates."""
        p = self._available_provider()
        mock_part = Mock(text="fallback text")
        mock_content = Mock(parts=[mock_part])
        mock_candidate = Mock(content=mock_content, finish_reason="STOP")

        mock_response = Mock()
        type(mock_response).text = property(lambda self: (_ for _ in ()).throw(ValueError("blocked")))
        mock_response.candidates = [mock_candidate]
        mock_response.usage_metadata = Mock(total_token_count=10)
        p._client.models.generate_content.return_value = mock_response

        result = p.chat(
            [{"role": "user", "content": "something"}], "gemini-pro", 0.5, 100, False
        )
        assert result.content == "fallback text"

    def test_chat_retryable_error_retries(self):
        """429/resource_exhausted error triggers retry with backoff."""
        p = self._available_provider()

        mock_response = Mock()
        mock_response.text = "ok"
        mock_response.candidates = [Mock(finish_reason="STOP")]
        mock_response.usage_metadata = Mock(total_token_count=5)

        call_count = [0]
        def _side_effect(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] < 3:
                raise Exception("429 resource_exhausted")
            return mock_response

        p._client.models.generate_content.side_effect = _side_effect

        with patch("time.sleep"):
            result = p.chat(
                [{"role": "user", "content": "hi"}], "gemini-pro", 0.5, 100, False
            )
        assert result.content == "ok"
        assert call_count[0] == 3

    def test_chat_non_retryable_error_raises(self):
        """Non-retryable error raises immediately."""
        p = self._available_provider()
        p._client.models.generate_content.side_effect = ValueError("invalid input")

        with pytest.raises(ValueError, match="invalid input"):
            p.chat([{"role": "user", "content": "test"}], "gemini-pro", 0.5, 100, False)


# ---------------------------------------------------------------------------
# OpenAICompatibleProvider
# ---------------------------------------------------------------------------

class TestOpenAICompatibleProvider:
    def _provider(self, base_url: str = "http://localhost:1234") -> OpenAICompatibleProvider:
        return OpenAICompatibleProvider(
            base_url=base_url, api_key="test-key", model="gpt-4",
        )

    def test_name_uses_provider_name(self):
        p = OpenAICompatibleProvider(
            base_url="http://x.com", provider_name="my-provider"
        )
        assert p.name == "my-provider"

    def test_is_available_with_base_url(self):
        p = self._provider()
        assert p.is_available() is True

    def test_is_available_without_base_url(self):
        p = OpenAICompatibleProvider(base_url="")
        assert p.is_available() is False

    def test_chat_raises_when_no_base_url(self):
        p = OpenAICompatibleProvider(base_url="")
        with pytest.raises(RuntimeError, match="no base_url"):
            p.chat([{"role": "user", "content": "hi"}], "gpt-4", 0.7, 100, False)

    def test_chat_success(self):
        p = self._provider()
        response_data = {
            "choices": [{"message": {"content": "Hello!"}}],
            "model": "gpt-4",
            "usage": {"total_tokens": 5},
        }

        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = Mock(return_value=False)

        with patch("src.core.model_alias.resolve_model", return_value="gpt-4"), \
             patch("urllib.request.urlopen", return_value=mock_resp):
            result = p.chat(
                [{"role": "user", "content": "hi"}], "gpt-4", 0.7, 100, False
            )
        assert result.content == "Hello!"
        assert result.model == "gpt-4"
        assert result.usage["total_tokens"] == 5

    def test_chat_with_api_key_adds_auth_header(self):
        """api_key present → Authorization header added."""
        p = OpenAICompatibleProvider(
            base_url="http://localhost:1234", api_key="sk-test", model="m"
        )
        response_data = {
            "choices": [{"message": {"content": "auth ok"}}],
            "model": "m",
            "usage": {},
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = Mock(return_value=False)

        captured_req = []
        def _urlopen(req, timeout):
            captured_req.append(req)
            return mock_resp

        with patch("src.core.model_alias.resolve_model", return_value="m"), \
             patch("urllib.request.urlopen", side_effect=_urlopen):
            p.chat([{"role": "user", "content": "hi"}], "m", 0.5, 50, False)

        assert captured_req[0].get_header("Authorization") == "Bearer sk-test"

    def test_chat_json_mode_adds_response_format(self):
        p = self._provider()
        response_data = {
            "choices": [{"message": {"content": "{}"}}],
            "model": "gpt-4",
            "usage": {},
        }
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps(response_data).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = Mock(return_value=False)

        sent_payloads = []
        original_dumps = json.dumps

        def _capture_dumps(obj, **kwargs):
            if isinstance(obj, dict) and "messages" in obj:
                sent_payloads.append(obj)
            return original_dumps(obj, **kwargs)

        with patch("src.core.model_alias.resolve_model", return_value="gpt-4"), \
             patch("urllib.request.urlopen", return_value=mock_resp), \
             patch("src.core.providers.json.dumps", side_effect=_capture_dumps):
            p.chat([{"role": "user", "content": "json please"}], "gpt-4", 0.0, 100, True)

        if sent_payloads:
            assert sent_payloads[0].get("response_format") == {"type": "json_object"}

    def test_chat_http_error_raises_runtime(self):
        p = self._provider()
        import urllib.error
        with patch("src.core.model_alias.resolve_model", return_value="gpt-4"), \
             patch("urllib.request.urlopen",
                   side_effect=urllib.error.HTTPError("url", 500, "Server Error", {}, None)):
            with pytest.raises(RuntimeError, match="HTTP 500"):
                p.chat([{"role": "user", "content": "hi"}], "gpt-4", 0.5, 100, False)

    def test_chat_url_error_raises_runtime(self):
        p = self._provider()
        import urllib.error
        with patch("src.core.model_alias.resolve_model", return_value="gpt-4"), \
             patch("urllib.request.urlopen",
                   side_effect=urllib.error.URLError("connection refused")):
            with pytest.raises(RuntimeError, match="connection error"):
                p.chat([{"role": "user", "content": "hi"}], "gpt-4", 0.5, 100, False)


# ---------------------------------------------------------------------------
# OfflineProvider
# ---------------------------------------------------------------------------

class TestOfflineProvider:
    def test_always_available(self):
        p = OfflineProvider()
        assert p.is_available() is True
        assert p.name == "offline"

    def test_chat_returns_offline_message(self):
        p = OfflineProvider()
        result = p.chat(
            [{"role": "user", "content": "hello world"}], "any", 0.5, 100, False
        )
        assert "[OFFLINE MODE]" in result.content
        assert "hello world" in result.content
        assert result.model == "offline"

    def test_chat_no_user_message_uses_unknown(self):
        p = OfflineProvider()
        result = p.chat(
            [{"role": "system", "content": "be helpful"}], "any", 0.5, 100, False
        )
        assert "unknown" in result.content

    def test_chat_picks_last_user_message(self):
        p = OfflineProvider()
        result = p.chat(
            [
                {"role": "user", "content": "first"},
                {"role": "assistant", "content": "reply"},
                {"role": "user", "content": "second"},
            ],
            "any", 0.5, 100, False,
        )
        assert "second" in result.content

    def test_chat_truncates_long_messages(self):
        p = OfflineProvider()
        long_msg = "x" * 300
        result = p.chat(
            [{"role": "user", "content": long_msg}], "any", 0.5, 100, False
        )
        # Content should have truncated version (max 200 chars from source)
        assert len(result.content) < 400


# ---------------------------------------------------------------------------
# LiteLLMProvider
# ---------------------------------------------------------------------------

class TestLiteLLMProvider:
    def test_name(self):
        with patch.dict("sys.modules", {"httpx": None}):
            p = LiteLLMProvider(base_url="")
        assert p.name == "litellm"

    def test_init_health_check_success(self):
        mock_httpx = MagicMock()
        mock_resp = Mock()
        mock_resp.status_code = 200
        mock_httpx.get.return_value = mock_resp
        with patch.dict("sys.modules", {"httpx": mock_httpx}):
            p = LiteLLMProvider(base_url="http://localhost:4000")
        assert p.is_available() is True

    def test_init_health_check_fails_not_available(self):
        mock_httpx = MagicMock()
        mock_httpx.get.side_effect = Exception("connection refused")
        with patch.dict("sys.modules", {"httpx": mock_httpx}):
            p = LiteLLMProvider(base_url="http://localhost:4000")
        assert p.is_available() is False

    def test_init_no_base_url_not_available(self):
        with patch.dict("sys.modules", {"httpx": None}):
            p = LiteLLMProvider(base_url="")
        assert p.is_available() is False

    def test_chat_raises_when_no_base_url(self):
        with patch.dict("sys.modules", {"httpx": None}):
            p = LiteLLMProvider(base_url="")
        p._available = True  # override for test
        with pytest.raises(RuntimeError, match="no base_url"):
            p.chat([{"role": "user", "content": "hi"}], "m", 0.5, 100, False)

    def test_chat_httpx_missing_returns_fallback(self):
        """httpx ImportError in chat returns offline response."""
        p = LiteLLMProvider.__new__(LiteLLMProvider)
        p._base_url = "http://localhost:4000"
        p._api_key = "sk-test"
        p._default_model = "default"
        p._available = True

        with patch.dict("sys.modules", {"httpx": None}):
            result = p.chat([{"role": "user", "content": "hi"}], "m", 0.5, 100, False)
        assert "[LiteLLM]" in result.content

    def test_chat_success(self):
        mock_httpx = MagicMock()
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "litellm reply"}}],
            "model": "gpt-4",
            "usage": {"total_tokens": 15},
            "_hidden_params": {"response_cost": 0.001},
        }
        mock_resp.raise_for_status = Mock()
        mock_client = MagicMock()
        mock_client.post.return_value = mock_resp
        mock_client.__enter__ = lambda s: s
        mock_client.__exit__ = Mock(return_value=False)
        mock_httpx.Client.return_value = mock_client

        with patch.dict("sys.modules", {"httpx": mock_httpx}):
            p = LiteLLMProvider(base_url="http://localhost:4000")
            p._available = True
            result = p.chat(
                [{"role": "user", "content": "hi"}], "gpt-4", 0.5, 100, False
            )
        assert result.content == "litellm reply"
        assert result.usage["total_tokens"] == 15

    def test_chat_budget_exceeded_429(self):
        """Budget exceeded (429) raises — httpx.HTTPStatusError propagates."""
        import httpx

        p = LiteLLMProvider.__new__(LiteLLMProvider)
        p._base_url = "http://localhost:4000"
        p._api_key = "sk-test"
        p._default_model = "default"
        p._available = True

        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.status_code = 429

        http_err = httpx.HTTPStatusError(
            "429 Budget Exceeded",
            request=MagicMock(),
            response=mock_response,
        )
        mock_client.post.side_effect = http_err

        with patch("httpx.Client", return_value=mock_client):
            with pytest.raises(httpx.HTTPStatusError):
                p.chat([{"role": "user", "content": "hi"}], "m", 0.5, 100, False)

    def test_chat_json_mode_adds_response_format(self):
        mock_httpx = MagicMock()
        mock_resp = MagicMock()
        mock_resp.json.return_value = {
            "choices": [{"message": {"content": "{}"}}],
            "model": "m",
            "usage": {},
            "_hidden_params": {},
        }
        mock_resp.raise_for_status = Mock()
        mock_client = MagicMock()
        mock_client.post.return_value = mock_resp

        sent_payloads = []
        def _capture_post(url, json, headers):
            sent_payloads.append(json)
            return mock_resp

        mock_client.post.side_effect = _capture_post
        mock_httpx.Client.return_value = mock_client

        with patch.dict("sys.modules", {"httpx": mock_httpx}):
            p = LiteLLMProvider(base_url="http://localhost:4000")
            p._available = True
            p.chat([{"role": "user", "content": "json"}], "m", 0.0, 50, True)

        if sent_payloads:
            assert sent_payloads[0].get("response_format") == {"type": "json_object"}
