"""Tests for Qwen Image Generator (DashScope API)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import requests

import src.core.image_generator as img_gen_mod
from src.core.image_generator import (
    DASHSCOPE_IMAGE_URL,
    MODEL_MAX,
    MODEL_PLUS,
    SIZES,
    QwenImageGenerator,
    get_image_generator,
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
            gen = QwenImageGenerator(api_key="")
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

    def test_hd_landscape_size(self):
        assert SIZES["hd_landscape"] == "1920*1080"


class TestGenerate:
    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_generate_success(self, mock_post, mock_get):
        """Test full async flow: submit → poll → get URLs."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {
            "output": {"task_id": "task-abc123", "task_status": "PENDING"}
        }
        submit_resp.raise_for_status = MagicMock()

        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "output": {
                "task_id": "task-abc123",
                "task_status": "SUCCEEDED",
                "results": [
                    {"url": "https://example.com/image1.png"},
                    {"url": ""},  # empty url filtered out
                ],
            }
        }
        poll_resp.raise_for_status = MagicMock()

        mock_post.return_value = submit_resp
        mock_get.return_value = poll_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate(
            "a beautiful sunset",
            style="photography",
            negative_prompt="low quality",
            seed=42,
        )

        assert len(urls) == 1
        assert urls[0] == "https://example.com/image1.png"

        # Verify submit call payload
        mock_post.assert_called_once()
        call_kwargs = mock_post.call_args
        assert call_kwargs[0][0] == DASHSCOPE_IMAGE_URL
        payload = call_kwargs[1]["json"]
        assert payload["input"]["negative_prompt"] == "low quality"
        assert payload["parameters"]["style"] == "photography"
        assert payload["parameters"]["seed"] == 42

    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_generate_multiple_images(self, mock_post, mock_get):
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

        mock_post.return_value = submit_resp
        mock_get.return_value = poll_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("product photos", n=2)
        assert len(urls) == 2

    def test_generate_no_api_key(self):
        """Should return empty list when no API key."""
        with patch.dict("os.environ", {}, clear=True):
            gen = QwenImageGenerator(api_key="")
            urls = gen.generate("test prompt")
            assert urls == []

    @patch("src.core.image_generator.requests.post")
    def test_generate_no_task_id_in_response(self, mock_post):
        """Submit response missing task_id returns empty list."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {"output": {}}
        submit_resp.raise_for_status = MagicMock()
        mock_post.return_value = submit_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("prompt without task id")
        assert urls == []

    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_generate_task_failed(self, mock_post, mock_get):
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

        mock_post.return_value = submit_resp
        mock_get.return_value = poll_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("test prompt")
        assert urls == []

    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_generate_task_canceled(self, mock_post, mock_get):
        """Test handling of CANCELED task."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {
            "output": {"task_id": "task-cancel"}
        }
        submit_resp.raise_for_status = MagicMock()

        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "output": {
                "task_status": "CANCELED",
                "message": "User canceled",
            }
        }
        poll_resp.raise_for_status = MagicMock()

        mock_post.return_value = submit_resp
        mock_get.return_value = poll_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("test prompt")
        assert urls == []

    @patch("src.core.image_generator.time.sleep")
    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_generate_poll_running_then_success(self, mock_post, mock_get, mock_sleep):
        """Test polling when status is RUNNING before SUCCEEDED."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {"output": {"task_id": "task-running"}}
        submit_resp.raise_for_status = MagicMock()

        running_resp = MagicMock()
        running_resp.json.return_value = {"output": {"task_status": "RUNNING"}}
        running_resp.raise_for_status = MagicMock()

        success_resp = MagicMock()
        success_resp.json.return_value = {
            "output": {
                "task_status": "SUCCEEDED",
                "results": [{"url": "https://example.com/ok.png"}],
            }
        }
        success_resp.raise_for_status = MagicMock()

        mock_post.return_value = submit_resp
        mock_get.side_effect = [running_resp, success_resp]

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("test prompt")
        assert urls == ["https://example.com/ok.png"]
        mock_sleep.assert_called_once()

    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_generate_poll_network_exception(self, mock_post, mock_get):
        """Test RequestException during polling."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {"output": {"task_id": "task-poll-err"}}
        submit_resp.raise_for_status = MagicMock()

        mock_post.return_value = submit_resp
        mock_get.side_effect = requests.RequestException("Poll connection reset")

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("test prompt")
        assert urls == []

    @patch("src.core.image_generator.time.sleep")
    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_generate_poll_timeout_attempts(self, mock_post, mock_get, mock_sleep):
        """Test timeout after exceeding MAX_POLL_ATTEMPTS."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {"output": {"task_id": "task-timeout"}}
        submit_resp.raise_for_status = MagicMock()

        pending_resp = MagicMock()
        pending_resp.json.return_value = {"output": {"task_status": "PENDING"}}
        pending_resp.raise_for_status = MagicMock()

        mock_post.return_value = submit_resp
        mock_get.return_value = pending_resp

        with patch.object(img_gen_mod, "MAX_POLL_ATTEMPTS", 2):
            gen = QwenImageGenerator(api_key="sk-test")
            urls = gen.generate("test prompt")
            assert urls == []
            assert mock_sleep.call_count == 2

    @patch("src.core.image_generator.requests.post")
    def test_generate_api_error(self, mock_post):
        """Test handling of request exception on submit."""
        mock_post.side_effect = requests.RequestException("timeout")

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.generate("test prompt")
        assert urls == []


class TestGenerateAndDownload:
    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_download_success(self, mock_post, mock_get, tmp_path):
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
        download_resp.content = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        download_resp.raise_for_status = MagicMock()

        mock_post.return_value = submit_resp
        mock_get.side_effect = [poll_resp, download_resp]

        out_path = str(tmp_path / "test_product.png")
        gen = QwenImageGenerator(api_key="sk-test")
        result = gen.generate_and_download("a product photo", out_path)

        assert result is not None
        assert "test_product.png" in result

    def test_download_no_api_key(self, tmp_path):
        """Should return None when no API key."""
        with patch.dict("os.environ", {}, clear=True):
            gen = QwenImageGenerator(api_key="")
            result = gen.generate_and_download("test", str(tmp_path / "out.png"))
            assert result is None

    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_download_request_failure(self, mock_post, mock_get, tmp_path):
        """Download requests.get raises RequestException."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {"output": {"task_id": "task-dl"}}
        submit_resp.raise_for_status = MagicMock()

        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "output": {
                "task_status": "SUCCEEDED",
                "results": [{"url": "https://example.com/fail.png"}],
            }
        }
        poll_resp.raise_for_status = MagicMock()

        mock_post.return_value = submit_resp
        mock_get.side_effect = [
            poll_resp,
            requests.RequestException("Download connection error"),
        ]

        gen = QwenImageGenerator(api_key="sk-test")
        result = gen.generate_and_download("test", str(tmp_path / "out.png"))
        assert result is None

    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_download_oserror(self, mock_post, mock_get, tmp_path):
        """Writing image raises OSError."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {"output": {"task_id": "task-dl"}}
        submit_resp.raise_for_status = MagicMock()

        poll_resp = MagicMock()
        poll_resp.json.return_value = {
            "output": {
                "task_status": "SUCCEEDED",
                "results": [{"url": "https://example.com/fail.png"}],
            }
        }
        poll_resp.raise_for_status = MagicMock()

        download_resp = MagicMock()
        download_resp.content = b"fake-png-bytes"
        download_resp.raise_for_status = MagicMock()

        mock_post.return_value = submit_resp
        mock_get.side_effect = [poll_resp, download_resp]

        gen = QwenImageGenerator(api_key="sk-test")
        with patch("pathlib.Path.write_bytes", side_effect=OSError("Disk full")):
            result = gen.generate_and_download("test", str(tmp_path / "out.png"))
            assert result is None


class TestEdit:
    @patch("src.core.image_generator.requests.get")
    @patch("src.core.image_generator.requests.post")
    def test_edit_success(self, mock_post, mock_get):
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

        mock_post.return_value = submit_resp
        mock_get.return_value = poll_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.edit("https://example.com/original.png", "change background to pink")
        assert len(urls) == 1
        assert urls[0] == "https://example.com/edited.png"

    def test_edit_no_api_key(self):
        """Edit returns empty list if no API key."""
        with patch.dict("os.environ", {}, clear=True):
            gen = QwenImageGenerator(api_key="")
            urls = gen.edit("https://example.com/img.png", "edit prompt")
            assert urls == []

    @patch("src.core.image_generator.requests.post")
    def test_edit_no_task_id(self, mock_post):
        """Edit returns empty list if response missing task_id."""
        submit_resp = MagicMock()
        submit_resp.json.return_value = {"output": {}}
        submit_resp.raise_for_status = MagicMock()
        mock_post.return_value = submit_resp

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.edit("https://example.com/img.png", "edit prompt")
        assert urls == []

    @patch("src.core.image_generator.requests.post")
    def test_edit_request_exception(self, mock_post):
        """Edit handles RequestException on post."""
        mock_post.side_effect = requests.RequestException("Network timeout")

        gen = QwenImageGenerator(api_key="sk-test")
        urls = gen.edit("https://example.com/img.png", "edit prompt")
        assert urls == []


class TestGetImageGenerator:
    def test_singleton(self):
        """get_image_generator should return same instance."""
        import src.core.image_generator as mod
        mod._default_generator = None
        g1 = get_image_generator()
        g2 = get_image_generator()
        assert g1 is g2
        mod._default_generator = None
