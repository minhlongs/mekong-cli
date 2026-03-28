"""Mekong CLI — Qwen Image Generator.

Text-to-image generation via DashScope API (Qwen Image 20B MMDiT).
Uses the same DASHSCOPE_API_KEY as the chat/coding endpoint.

Usage:
    from src.core.image_generator import QwenImageGenerator

    gen = QwenImageGenerator()
    urls = gen.generate("a beautiful K-beauty product on pink background")
    gen.generate_and_download("sunset over mountains", "/tmp/sunset.png")
"""

from __future__ import annotations

import logging
import os
import time
from io import BytesIO
from pathlib import Path
from typing import Optional

import requests

logger = logging.getLogger(__name__)

# ── DashScope Image API ──
DASHSCOPE_IMAGE_URL = "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis"
DASHSCOPE_TASK_URL = "https://dashscope.aliyuncs.com/api/v1/tasks"

# Model variants
MODEL_PLUS = "qwen-image-plus"       # Fast, good quality (~¥0.04/image)
MODEL_MAX = "qwen-image-max"         # Highest quality (~¥0.16/image)
MODEL_DEFAULT = MODEL_PLUS

# Supported sizes (width*height)
SIZES = {
    "square": "1024*1024",
    "portrait": "720*1280",      # 9:16 TikTok vertical
    "landscape": "1280*720",     # 16:9 horizontal
    "hd_portrait": "1080*1920",  # Full HD vertical
    "hd_landscape": "1920*1080", # Full HD horizontal
}

# Polling config
MAX_POLL_ATTEMPTS = 60
POLL_INTERVAL_SECS = 2.0


class QwenImageGenerator:
    """Text-to-image generation using Qwen Image 20B via DashScope API.

    The DashScope image API is async (submit task → poll for result).
    This class handles the full lifecycle transparently.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = MODEL_DEFAULT,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("DASHSCOPE_API_KEY", "")
        self.model = model
        self.timeout = timeout

    @property
    def is_available(self) -> bool:
        """True if API key is configured."""
        return bool(self.api_key)

    def generate(
        self,
        prompt: str,
        size: str = "square",
        n: int = 1,
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        seed: Optional[int] = None,
    ) -> list[str]:
        """Generate image(s) from text prompt.

        Args:
            prompt: Text description of the image to generate.
            size: One of 'square', 'portrait', 'landscape',
                  'hd_portrait', 'hd_landscape', or raw 'WxH' string.
            n: Number of images to generate (1-4).
            style: Optional style preset (e.g., 'photography', 'anime').
            negative_prompt: Things to avoid in the generated image.
            seed: Random seed for reproducibility.

        Returns:
            List of image URLs. Empty list on failure.
        """
        if not self.is_available:
            logger.warning("[QwenImage] No DASHSCOPE_API_KEY — cannot generate images")
            return []

        # Resolve size alias
        resolved_size = SIZES.get(size, size)

        # Build request payload (DashScope async task format)
        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt,
            },
            "parameters": {
                "size": resolved_size,
                "n": min(n, 4),
            },
        }

        if negative_prompt:
            payload["input"]["negative_prompt"] = negative_prompt
        if style:
            payload["parameters"]["style"] = style
        if seed is not None:
            payload["parameters"]["seed"] = seed

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        try:
            # Step 1: Submit async task
            logger.info("[QwenImage] Submitting image generation task: %s", prompt[:80])
            resp = requests.post(
                DASHSCOPE_IMAGE_URL,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            resp.raise_for_status()
            data = resp.json()

            task_id = data.get("output", {}).get("task_id")
            if not task_id:
                logger.error("[QwenImage] No task_id in response: %s", data)
                return []

            # Step 2: Poll for completion
            return self._poll_task(task_id)

        except requests.RequestException as e:
            logger.error("[QwenImage] API request failed: %s", e)
            return []

    def _poll_task(self, task_id: str) -> list[str]:
        """Poll DashScope task until completion."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
        }
        task_url = f"{DASHSCOPE_TASK_URL}/{task_id}"

        for attempt in range(MAX_POLL_ATTEMPTS):
            try:
                resp = requests.get(task_url, headers=headers, timeout=self.timeout)
                resp.raise_for_status()
                data = resp.json()

                status = data.get("output", {}).get("task_status", "")

                if status == "SUCCEEDED":
                    results = data.get("output", {}).get("results", [])
                    urls = [r.get("url", "") for r in results if r.get("url")]
                    logger.info("[QwenImage] Generated %d image(s)", len(urls))
                    return urls

                if status in ("FAILED", "CANCELED"):
                    error_msg = data.get("output", {}).get("message", "unknown error")
                    logger.error("[QwenImage] Task %s: %s — %s", status, task_id, error_msg)
                    return []

                # PENDING or RUNNING — keep polling
                logger.debug("[QwenImage] Task %s — attempt %d/%d", status, attempt + 1, MAX_POLL_ATTEMPTS)
                time.sleep(POLL_INTERVAL_SECS)

            except requests.RequestException as e:
                logger.error("[QwenImage] Poll failed: %s", e)
                return []

        logger.error("[QwenImage] Task %s timed out after %d attempts", task_id, MAX_POLL_ATTEMPTS)
        return []

    def generate_and_download(
        self,
        prompt: str,
        output_path: str,
        size: str = "square",
        style: Optional[str] = None,
        negative_prompt: Optional[str] = None,
    ) -> Optional[str]:
        """Generate an image and save it to disk.

        Args:
            prompt: Text description.
            output_path: Where to save the image (e.g., '/tmp/product.png').
            size: Size preset or raw WxH string.
            style: Optional style preset.
            negative_prompt: Things to avoid.

        Returns:
            Absolute path to saved image, or None on failure.
        """
        urls = self.generate(
            prompt=prompt,
            size=size,
            n=1,
            style=style,
            negative_prompt=negative_prompt,
        )

        if not urls:
            return None

        try:
            # Download the first image
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

    def edit(
        self,
        image_url: str,
        prompt: str,
        size: str = "square",
    ) -> list[str]:
        """Edit an existing image using Qwen Image.

        Args:
            image_url: URL of the source image to edit.
            prompt: Editing instruction (e.g., 'change background to pink').
            size: Output size preset.

        Returns:
            List of edited image URLs. Empty list on failure.
        """
        if not self.is_available:
            logger.warning("[QwenImage] No DASHSCOPE_API_KEY — cannot edit images")
            return []

        resolved_size = SIZES.get(size, size)

        payload = {
            "model": self.model,
            "input": {
                "prompt": prompt,
                "base_image_url": image_url,
            },
            "parameters": {
                "size": resolved_size,
                "n": 1,
            },
        }

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-DashScope-Async": "enable",
        }

        try:
            resp = requests.post(
                DASHSCOPE_IMAGE_URL,
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
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


# ---------------------------------------------------------------------------
# Module-level convenience
# ---------------------------------------------------------------------------

_default_generator: QwenImageGenerator | None = None


def get_image_generator() -> QwenImageGenerator:
    """Get or create default image generator."""
    global _default_generator
    if _default_generator is None:
        _default_generator = QwenImageGenerator()
    return _default_generator


__all__ = [
    "QwenImageGenerator",
    "get_image_generator",
    "MODEL_PLUS",
    "MODEL_MAX",
    "SIZES",
]
