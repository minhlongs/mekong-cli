"""Tests for ALGO 5 — Local LLM Adapter (MLX / OpenAI-compatible)."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock


from src.core.local_adapter import LocalLLMAdapter, OllamaAdapter, QUANTIZATION_MAP


class TestQuantizationMap:
    def test_all_models_have_quant(self):
        expected = [
            "llama3.3:70b", "deepseek-coder-v2:33b", "deepseek-coder-v2:16b",
            "llama3.2:3b", "qwen2.5:7b", "mistral:7b",
        ]
        for model in expected:
            assert model in QUANTIZATION_MAP

    def test_small_model_higher_quant(self):
        assert QUANTIZATION_MAP["llama3.2:3b"] == "q8_0"  # full quant for tiny

    def test_large_model_lower_quant(self):
        assert QUANTIZATION_MAP["llama3.3:70b"] == "q4_K_M"  # save VRAM


class TestBackwardCompat:
    def test_ollama_adapter_alias(self):
        """OllamaAdapter should be an alias for LocalLLMAdapter."""
        assert OllamaAdapter is LocalLLMAdapter


class TestLocalLLMAdapterInit:
    def test_default_base_url(self):
        adapter = LocalLLMAdapter()
        assert "11435" in adapter.base_url or "11434" in adapter.base_url

    def test_custom_base_url(self):
        adapter = LocalLLMAdapter(base_url="http://custom:8080/v1")
        assert adapter.base_url == "http://custom:8080/v1"

    def test_empty_pulled_models(self):
        adapter = LocalLLMAdapter()
        assert len(adapter.pulled_models) == 0


class TestHealthCheck:
    @patch("urllib.request.urlopen")
    def test_healthy(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        adapter = LocalLLMAdapter(base_url="http://localhost:11435/v1")
        assert adapter.health_check() is True

    @patch("urllib.request.urlopen", side_effect=ConnectionError("refused"))
    def test_unhealthy(self, mock_urlopen):
        adapter = LocalLLMAdapter()
        assert adapter.health_check() is False

    @patch("urllib.request.urlopen", side_effect=TimeoutError("timeout"))
    def test_timeout(self, mock_urlopen):
        adapter = LocalLLMAdapter()
        assert adapter.health_check() is False


class TestListModels:
    @patch("urllib.request.urlopen")
    def test_lists_models(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "object": "list",
            "data": [
                {"id": "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit", "object": "model"},
                {"id": "mlx-community/Qwen2.5-Coder-32B-4bit", "object": "model"},
            ]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        adapter = LocalLLMAdapter(base_url="http://localhost:11435/v1")
        models = adapter.list_models()
        assert "mlx-community/DeepSeek-R1-Distill-Qwen-32B-4bit" in models
        assert "mlx-community/Qwen2.5-Coder-32B-4bit" in models

    @patch("urllib.request.urlopen", side_effect=ConnectionError)
    def test_returns_empty_on_error(self, mock_urlopen):
        adapter = LocalLLMAdapter()
        assert adapter.list_models() == []


class TestGetStatus:
    @patch("urllib.request.urlopen")
    def test_healthy_status(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "object": "list",
            "data": [{"id": "test-model", "object": "model"}]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        adapter = LocalLLMAdapter(base_url="http://localhost:11435/v1")
        status = adapter.get_status()
        assert status["healthy"] is True
        assert status["models_loaded"] == 1

    @patch.object(LocalLLMAdapter, "list_models", side_effect=ConnectionError)
    def test_unhealthy_status(self, mock_list):
        adapter = LocalLLMAdapter()
        status = adapter.get_status()
        assert status["healthy"] is False


class TestSyncGenerate:
    @patch("urllib.request.urlopen")
    def test_strips_mlx_prefix(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Hello world"}}]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        adapter = LocalLLMAdapter(base_url="http://localhost:11435/v1")
        result = adapter.generate_sync("mlx:test-model", [{"role": "user", "content": "hi"}])
        assert result == "Hello world"

    @patch("urllib.request.urlopen")
    def test_strips_ollama_prefix(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.read.return_value = json.dumps({
            "choices": [{"message": {"content": "Hello world"}}]
        }).encode()
        mock_resp.__enter__ = lambda s: s
        mock_resp.__exit__ = MagicMock(return_value=False)
        mock_urlopen.return_value = mock_resp

        adapter = LocalLLMAdapter(base_url="http://localhost:11435/v1")
        result = adapter.generate_sync("ollama:llama3.2:3b", [{"role": "user", "content": "hi"}])
        assert result == "Hello world"

    @patch("urllib.request.urlopen", side_effect=ConnectionError)
    def test_returns_empty_on_error(self, mock_urlopen):
        adapter = LocalLLMAdapter()
        result = adapter.generate_sync("test-model", [{"role": "user", "content": "hi"}])
        assert result == ""
