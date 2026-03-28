"""ALGO 5 — Local LLM Adapter (MLX / OpenAI-compatible).

Manages local LLM inference via OpenAI-compatible API.
Works with MLX (mlx-lm.server), Ollama, LM Studio, or any local server.
"""

from __future__ import annotations

import json
import logging
import os
from dataclasses import dataclass, field
from typing import AsyncIterator

logger = logging.getLogger(__name__)

LOCAL_LLM_URL = os.getenv(
    "LOCAL_LLM_URL",
    os.getenv("OLLAMA_URL", "http://localhost:11435/v1"),
)

# Legacy compat — keep for reference
QUANTIZATION_MAP: dict[str, str] = {
    "llama3.3:70b": "q4_K_M",
    "deepseek-coder-v2:33b": "q4_K_M",
    "deepseek-coder-v2:16b": "q5_K_M",
    "llama3.2:3b": "q8_0",
    "qwen2.5:7b": "q6_K",
    "mistral:7b": "q5_K_M",
}


@dataclass
class LocalLLMAdapter:
    """Adapter for local LLM inference via OpenAI-compatible API.

    Works with MLX (mlx-lm.server), Ollama (/v1), LM Studio, etc.
    """

    base_url: str = LOCAL_LLM_URL
    pulled_models: set[str] = field(default_factory=set)

    def health_check(self) -> bool:
        """Check if local LLM server is running and responsive."""
        try:
            import urllib.request
            # Use OpenAI-standard /models endpoint
            url = f"{self.base_url}/models"
            if not self.base_url.endswith("/v1"):
                url = f"{self.base_url}/v1/models"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=3) as resp:
                return resp.status == 200
        except Exception as e:
            logger.debug("Local LLM health check failed: %s", e)
            return False

    def list_models(self) -> list[str]:
        """List locally available models via OpenAI-compatible endpoint."""
        try:
            import urllib.request
            url = f"{self.base_url}/models"
            if not self.base_url.endswith("/v1"):
                url = f"{self.base_url}/v1/models"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read())
                return [m["id"] for m in data.get("data", [])]
        except Exception as e:
            logger.debug("Local LLM list_models failed: %s", e)
            return []

    def get_status(self) -> dict:
        """Get basic server status (model list + health)."""
        try:
            models = self.list_models()
            return {
                "healthy": True,
                "models_loaded": len(models),
                "models": models,
            }
        except Exception:
            return {"healthy": False, "models_loaded": 0, "models": []}

    async def generate(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream generate from local LLM via OpenAI-compatible API.

        Args:
            model: Model name.
            messages: Chat messages in OpenAI format.
            temperature: Generation temperature.
            max_tokens: Max output tokens.

        Yields:
            Text chunks from the model.
        """
        import aiohttp

        # Strip provider prefix if present
        for prefix in ("ollama:", "mlx:", "local:"):
            if model.startswith(prefix):
                model = model[len(prefix):]
                break

        payload = {
            "model": model,
            "messages": messages,
            "stream": True,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }

        url = f"{self.base_url}/chat/completions"
        if not self.base_url.endswith("/v1"):
            url = f"{self.base_url}/v1/chat/completions"

        async with aiohttp.ClientSession() as session:
            async with session.post(
                url,
                json=payload,
                timeout=aiohttp.ClientTimeout(total=300),
            ) as resp:
                async for line in resp.content:
                    line_str = line.decode("utf-8", errors="ignore").strip()
                    if not line_str or line_str == "data: [DONE]":
                        continue
                    if line_str.startswith("data: "):
                        line_str = line_str[6:]
                    try:
                        chunk = json.loads(line_str)
                        choices = chunk.get("choices", [])
                        if choices:
                            delta = choices[0].get("delta", {})
                            content = delta.get("content", "")
                            if content:
                                yield content
                    except json.JSONDecodeError:
                        continue

    def generate_sync(
        self,
        model: str,
        messages: list[dict],
        temperature: float = 0.3,
        max_tokens: int = 4096,
    ) -> str:
        """Synchronous generation for simple use cases."""
        import urllib.request

        for prefix in ("ollama:", "mlx:", "local:"):
            if model.startswith(prefix):
                model = model[len(prefix):]
                break

        payload = json.dumps({
            "model": model,
            "messages": messages,
            "stream": False,
            "temperature": temperature,
            "max_tokens": max_tokens,
        }).encode()

        url = f"{self.base_url}/chat/completions"
        if not self.base_url.endswith("/v1"):
            url = f"{self.base_url}/v1/chat/completions"

        req = urllib.request.Request(
            url,
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=300) as resp:
                data = json.loads(resp.read())
                choices = data.get("choices", [])
                if choices:
                    return choices[0].get("message", {}).get("content", "")
                return ""
        except Exception as e:
            logger.error("Local LLM sync generate failed: %s", e)
            return ""


# Backward compatibility alias
OllamaAdapter = LocalLLMAdapter
