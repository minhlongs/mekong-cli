"""Tests for Qwen Image Generator (DashScope API)."""

from __future__ import annotations

import json
from unittest.mock import patch, MagicMock

import pytest

from src.core.image_generator import (
    QwenImageGenerator,
    get_image_generator,
    SIZES,
    MODEL_PLUS,
    MODEL_MAX,
    DASHSCOPE_IMAGE_URL,
)


class TestQwenImageGeneratorInit:
    def test_default_model(self):
        gen = QwenImageGenerator(api_key="sk-test")
        assert gen.model == MODEL_PLUS

    def test_custom_model(self):
        gen = QwenImageGenerator(api_key="sk-test", model=MODEL_MAX)
        assert gen.model == MODEL_MAX

    def test_api_key_from_env(self):
        with patch.dict("os.environ", {"DASHSCOPE_API_KEY": "sk-env"}):
            gen = QwenImageGenerator()
            assert gen.api_key == "sk-env"

    def test_no_api_key(self):
        with patch.dict("os.environ", {}, clear=True):
            gen = QwenImageGenerator()
            assert gen.is_available is False

    def test_is_available_with_key(self):
        gen = QwenImageGenerator(api_key="sk-test")
        assert gen.is_available is True


class TestSizes:
    def test_portrait_size(self):
        assert SIZES["portrait"] == "720*1280"

    def test_square_size(self):
        assert SIZES["square"] == "1024*1024"

    def test_landscape_size(self):
        assert SIZES["landscape"] == "1280*720"

    def test_hd_portrait_size(self):
        assert SIZES["hd_portrait"] == "1080*1920"


class TestGenerate:
    @patch("src.core.image_generator.requests")
    def test_generate_success(self, mock_requests):
        """Test full async flow: submit → poll → get URLs."""
        # Mock submit response
        submit_resp = MagicMock()
        submit_resp.json.return_value = {
            "output": {"task_id": "task-abc123", "task_status": "PENDING"}
        }
        submit_resp.raise_for_status = MagicMock()

        # Mock poll response (SUCCEEDED)
        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "output": {
                "task_id": "task-abc123",
                "task_status": "SUCCEEDED",
                "results": [
                    {"url": "https://example.com/image1.png"},
                ],
            }
        }
        poll_resp.raise_for_status = MagicMock()

        mock_requests.post.return_value = submit_resp
        mock_requests.get.return_value = poll_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("a beautiful sunset")

        assert len(urls) == 1
        assert urls[0] == "https://example.com/image1.png"

        # Verify submit call
        mock_requests.post.assert_called_once()
        call_kwargs = mock_requests.post.call_args
        assert call_kwargs[0][0] == DASHSCOPE_IMAGE_URL

    @patch("src.core.image_generator.requests")
    def test_generate_multiple_images(self, mock_requests):
        """Test generating multiple images."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {
            "output": {"task_id": "task-multi"}
        }
        submit_resp.raise_for_status = MagicMock()

        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "output": {
                "task_status": "SUCCEEDED",
                "results": [
                    {"url": "https://example.com/img1.png"},
                    {"url": "https://example.com/img2.png"},
                ],
            }
        }
        poll_resp.raise_for_status = MagicMock()

        mock_requests.post.return_value = submit_resp
        mock_requests.get.return_value = poll_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("product photos", n=2)
        assert len(urls) == 2

    def test_generate_no_api_key(self):
        """Should return empty list when no API key."""
        gen = QwenImageGenerator(api_key="")
        urls = gen.generate("test prompt")
        assert urls == []

    @patch("src.core.image_generator.requests")
    def test_generate_task_failed(self, mock_requests):
        """Test handling of FAILED task."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {
            "output": {"task_id": "task-fail"}
        }
        submit_resp.raise_for_status = MagicMock()

        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "output": {
                "task_status": "FAILED",
                "message": "Content policy violation",
            }
        }
        poll_resp.raise_for_status = MagicMock()

        mock_requests.post.return_value = submit_resp
        mock_requests.get.return_value = poll_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("test prompt")
        assert urls == []

    @patch("src.core.image_generator.requests")
    def test_generate_api_error(self, mock_requests):
        """Test handling of request exception."""
        import requests as real_requests
        mock_requests.post.side_effect = real_requests.RequestException("timeout")
        mock_requests.RequestException = real_requests.RequestException

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("test prompt")
        assert urls == []


class TestGenerateAndDownload:
    @patch("src.core.image_generator.requests")
    def test_download_success(self, mock_requests, tmp_path):
        """Test generate + download to disk."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {
            "output": {"task_id": "task-dl"}
        }
        submit_resp.raise_for_status = MagicMock()

        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "output": {
                "task_status": "SUCCEEDED",
                "results": [{"url": "https://example.com/product.png"}],
            }
        }
        poll_resp.raise_for_status = MagicMock()

        download_resp = MagicMock()
        download_resp.content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100  # Fake PNG
        download_resp.raise_for_status = MagicMock()

        # post → submit, get calls: 1st → poll, 2nd → download
        mock_requests.post.return_value = submit_resp
        mock_requests.get.side_effect = [poll_resp, download_resp]

        out_path = str(tmp_path / "test_product.png")
        gen = QwenImageGenerator(api_key="sk-test")
        result = gen.generate_and_download("a product photo", out_path)

        assert result is not None
        assert "test_product.png" in result

    def test_download_no_api_key(self, tmp_path):
        """Should return None when no API key."""
        gen = QwenImageGenerator(api_key="")
        result = gen.generate_and_download("test", str(tmp_path / "out.png"))
        assert result is None


class TestEdit:
    @patch("src.core.image_generator.requests")
    def test_edit_success(self, mock_requests):
        """Test image editing flow."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {
            "output": {"task_id": "task-edit"}
        }
        submit_resp.raise_for_status = MagicMock()

        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "output": {
                "task_status": "SUCCEEDED",
                "results": [{"url": "https://example.com/edited.png"}],
            }
        }
        poll_resp.raise_for_status = MagicMock()

        mock_requests.post.return_value = submit_resp
        mock_requests.get.return_value = poll_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.edit("https://example.com/original.png", "change background to pink")
        assert len(urls) == 1

    def test_edit_no_api_key(self):
        gen = QwenImageGenerator(api_key="")
        urls = gen.edit("https://example.com/img.png", "edit prompt")
        assert urls == []


class TestGetImageGenerator:
    def test_singleton(self):
        """get_image_generator should return same instance."""
        import src.core.image_generator as mod
        mod._default_generator = None  # Reset
        g1 = get_image_generator()
        g2 = get_image_generator()
        assert g1 is g2
        mod._default_generator = None  # Cleanup
