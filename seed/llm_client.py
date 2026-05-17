"""Simple Ollama LLM client — stdlib only, no external dependencies."""

from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from typing import Any

from .config import EMBED_MODEL, LLM_MODEL, LLM_TIMEOUT, OLLAMA_BASE_URL

logger = logging.getLogger(__name__)

_client: "LLMClient | None" = None


def _post_json(url: str, payload: dict, timeout: int = 30) -> dict:
    data = json.dumps(payload).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _get_json(url: str, timeout: int = 5) -> dict:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


class LLMClient:
    """Thin wrapper around Ollama /api/chat and /api/embeddings."""

    def __init__(self, base_url: str = OLLAMA_BASE_URL, model: str = LLM_MODEL) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, messages: list[dict[str, str]], model: str | None = None) -> str:
        """Send messages to Ollama chat endpoint, return assistant content."""
        payload = {
            "model": model or self.model,
            "messages": messages,
            "stream": False,
        }
        try:
            result = _post_json(f"{self.base_url}/api/chat", payload, timeout=LLM_TIMEOUT)
            return result["message"]["content"]
        except Exception as e:
            logger.error("LLM chat error: %s", e)
            return ""

    def embed(self, text: str) -> list[float]:
        """Generate embeddings via Ollama."""
        payload = {"model": EMBED_MODEL, "prompt": text}
        try:
            result = _post_json(f"{self.base_url}/api/embeddings", payload, timeout=30)
            return result["embedding"]
        except Exception as e:
            logger.warning("Embed error (non-fatal): %s", e)
            return []

    def is_available(self) -> bool:
        """Check if Ollama is reachable."""
        try:
            _get_json(f"{self.base_url}/api/tags")
            return True
        except Exception:
            return False


def get_llm_client() -> LLMClient:
    """Return singleton LLMClient."""
    global _client
    if _client is None:
        _client = LLMClient()
    return _client
