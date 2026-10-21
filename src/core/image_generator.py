# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.
"""Mekong CLI — Qwen Image Generator (DashScope API)."""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

DASHSCOPE_IMAGE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
DASHSCOPE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks"

MODEL_PLUS = "qwen-image-plus"
MODEL_MAX = "qwen-image-max"
MODEL_DEFAULT = MODEL_PLUS

SIZES = {
    "square": "1024*1024", "portrait": "720*1280", "landscape": "1280*720",
    "hd_portrait": "1080*1920", "hd_landscape": "1920*1080",
}

MAX_POLL_ATTEMPTS = 60
POLL_INTERVAL_SECS = 2.0


class QwenImageGenerator:
    """Text-to-image generation using Qwen Image 20B via DashScope API."""

    def __init__(self, api_key: Optional[str] = None, model: str = MODEL_DEFAULT, timeout: int = 30):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.model = model
        self.timeout = timeout

    @property
    def is_available(self) -> bool:
        return bool(self.api_key)

    def _headers(self, async_mode: bool = True) -> dict[str, str]:
        headers = {"Authorization": f"Bearer {self.api_key}"}
        if async_mode:
            headers.update({"Content-Type": "application/json", "X-DashScope-Async": "enable"})
        return headers

    def generate(
        self, prompt: str, size: str = "square", n: int = 1,
        style: Optional[str] = None, negative_prompt: Optional[str] = None, seed: Optional[int] = None,
    ) -> list[str]:
        if not self.is_available:
            logger.warning("[QwenImage] No DASHSCOPE_API_KEY — cannot generate images")
            return []
        payload: dict[str, object] = {
            "model": self.model,
            "input": {"prompt": prompt, **({"negative_prompt": negative_prompt} if negative_prompt else {})},
            "parameters": {
                "size": SIZES.get(size, size), "n": min(n, 4),
                **({"style": style} if style else {}), **({"seed": seed} if seed is not None else {}),
            },
        }
        try:
            logger.info("[QwenImage] Submitting image generation task: %s", prompt[:80])
            resp = requests.post(DASHSCOPE_IMAGE_URL, json=payload, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            task_id = data.get("output", {}).get("task_id")
            if not task_id:
                logger.error("[QwenImage] No task_id in response: %s", data)
                return []
            return self._poll_task(task_id)
        except requests.RequestException as e:
            logger.error("[QwenImage] API request failed: %s", e)
            return []

    def _poll_task(self, task_id: str) -> list[str]:
        headers = self._headers(async_mode=False)
        task_url = f"{DASHSCOPE_TASK_URL}/{task_id}"
        for attempt in range(MAX_POLL_ATTEMPTS):
            try:
                resp = requests.get(task_url, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                output = resp.json().get("output", {})
                status = output.get("task_status", "")
                if status == "SUCCEEDED":
                    urls = [r.get("url", "") for r in output.get("results", []) if r.get("url")]
                    logger.info("[QwenImage] Generated %d image(s)", len(urls))
                    return urls
                if status in ("FAILED", "CANCELED"):
                    logger.error("[QwenImage] Task %s: %s — %s", status, task_id, output.get("message", "unknown error"))
                    return []
                logger.debug("[QwenImage] Task %s — attempt %d/%d", status, attempt + 1, MAX_POLL_ATTEMPTS)
                time.sleep(POLL_INTERVAL_SECS)
            except requests.RequestException as e:
                logger.error("[QwenImage] Poll failed: %s", e)
                return []
        logger.error("[QwenImage] Task %s timed out after %d attempts", task_id, MAX_POLL_ATTEMPTS)
        return []

    def generate_and_download(
        self, prompt: str, output_path: str, size: str = "square",
        style: Optional[str] = None, negative_prompt: Optional[str] = None,
    ) -> Optional[str]:
        urls = self.generate(prompt=prompt, size=size, n=1, style=style, negative_prompt=negative_prompt)
        if not urls:
            return None
        try:
            resp = requests.get(urls[0], timeout=30)
            resp.raise_for_status()
            out = Path(output_path)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_bytes(resp.content)
            logger.info("[QwenImage] Saved image to %s (%d KB)", out, len(resp.content) // 1024)
            return str(out.resolve())
        except (requests.RequestException, OSError) as e:
            logger.error("[QwenImage] Download/save failed: %s", e)
            return None

    def edit(self, image_url: str, prompt: str, size: str = "square") -> list[str]:
        if not self.is_available:
            logger.warning("[QwenImage] No DASHSCOPE_API_KEY — cannot edit images")
            return []
        payload = {
            "model": self.model,
            "input": {"prompt": prompt, "base_image_url": image_url},
            "parameters": {"size": SIZES.get(size, size), "n": 1},
        }
        try:
            resp = requests.post(DASHSCOPE_IMAGE_URL, json=payload, headers=self._headers(), timeout=self.timeout)
            resp.raise_for_status()
            data = resp.json()
            task_id = data.get("output", {}).get("task_id")
            if not task_id:
                logger.error("[QwenImage] No task_id in edit response: %s", data)
                return []
            return self._poll_task(task_id)
        except requests.RequestException as e:
            logger.error("[QwenImage] Edit request failed: %s", e)
            return []


_default_generator: QwenImageGenerator | None = None


def get_image_generator() -> QwenImageGenerator:
    global _default_generator
    if _default_generator is None:
        _default_generator = QwenImageGenerator()
    return _default_generator


__all__ = ["MODEL_MAX", "MODEL_PLUS", "QwenImageGenerator", "SIZES", "get_image_generator"]
