"""Unit tests for seed/llm_client.py — mocked HTTP, no real Ollama needed."""

import json
from unittest.mock import MagicMock, patch


from seed.llm_client import LLMClient, _post_json, _get_json


def _mock_urlopen(response_dict: dict, status: int = 200):
    """Return a context-manager mock for urllib.request.urlopen."""
    body = json.dumps(response_dict).encode()
    resp = MagicMock()
    resp.read.return_value = body
    resp.status = status
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    return resp


class TestPostJson:
    def test_returns_parsed_dict(self):
        expected = {"key": "value"}
        with patch("seed.llm_client.urllib.request.urlopen") as mock_open:
            mock_open.return_value = _mock_urlopen(expected)
            result = _post_json("http://localhost:11434/api/chat", {"model": "test"})
        assert result == expected

    def test_sends_json_content_type(self):
        with patch("seed.llm_client.urllib.request.urlopen") as mock_open:
            mock_open.return_value = _mock_urlopen({"ok": True})
            _post_json("http://localhost:11434/api/chat", {"x": 1})
            req = mock_open.call_args[0][0]
            assert req.headers.get("Content-type") == "application/json"


class TestGetJson:
    def test_returns_parsed_dict(self):
        expected = {"models": []}
        with patch("seed.llm_client.urllib.request.urlopen") as mock_open:
            mock_open.return_value = _mock_urlopen(expected)
            result = _get_json("http://localhost:11434/api/tags")
        assert result == expected


class TestLLMClient:
    def _client(self):
        return LLMClient(base_url="http://localhost:11434", model="test-model")

    def test_chat_returns_string(self):
        response_body = {
            "message": {"content": "Hello world"},
            "done": True,
        }
        with patch("seed.llm_client.urllib.request.urlopen") as mock_open:
            mock_open.return_value = _mock_urlopen(response_body)
            client = self._client()
            result = client.chat([{"role": "user", "content": "hi"}])
        assert result == "Hello world"

    def test_chat_returns_empty_string_on_error(self):
        with patch("seed.llm_client.urllib.request.urlopen", side_effect=Exception("timeout")):
            client = self._client()
            result = client.chat([{"role": "user", "content": "hi"}])
        assert result == ""

    def test_embed_returns_list_of_floats(self):
        response_body = {"embedding": [0.1, 0.2, 0.3]}
        with patch("seed.llm_client.urllib.request.urlopen") as mock_open:
            mock_open.return_value = _mock_urlopen(response_body)
            client = self._client()
            result = client.embed("test text")
        assert isinstance(result, list)
        assert len(result) == 3

    def test_embed_returns_empty_list_on_error(self):
        with patch("seed.llm_client.urllib.request.urlopen", side_effect=Exception("conn")):
            client = self._client()
            result = client.embed("test text")
        assert result == []

    def test_is_available_true(self):
        with patch("seed.llm_client.urllib.request.urlopen") as mock_open:
            mock_open.return_value = _mock_urlopen({"models": []})
            client = self._client()
            assert client.is_available() is True

    def test_is_available_false_on_error(self):
        with patch("seed.llm_client.urllib.request.urlopen", side_effect=Exception("conn")):
            client = self._client()
            assert client.is_available() is False
