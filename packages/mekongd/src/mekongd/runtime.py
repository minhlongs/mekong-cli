"""Runtime adapters — MLX (Apple Silicon) + OpenAI compatibility + Stub (CI/dev)."""

from __future__ import annotations

import asyncio
import json
import logging
import socket
import time
from typing import AsyncIterator, Protocol
from urllib.parse import urlparse

import httpx

from mekongd.config import MekongdConfig
from mekongd.schemas import MessagesRequest

log = logging.getLogger(__name__)

# Granular timeouts tuned for local LLM inference on Apple Silicon.
# Qwen-35B with large Claude Code system prompts (50K+ tokens) can take
# 3-5 min for first token; read timeout must be generous.
_LLM_TIMEOUT = httpx.Timeout(
    connect=10.0,   # Fast local connect — fail early if server is down
    read=600.0,     # 10 min read — accommodates large prompt prefill
    write=30.0,     # Payload send should be fast over loopback
    pool=30.0,      # Connection pool acquire timeout
)

_MAX_RETRIES = 2
_RETRY_BACKOFF = 1.0  # seconds, doubled each attempt


class BaseRuntime(Protocol):
    """Runtime interface — generate and stream completions."""

    name: str

    async def generate(self, request: MessagesRequest) -> str: ...

    async def stream(self, request: MessagesRequest) -> AsyncIterator[str]: ...


def _flatten_prompt(request: MessagesRequest) -> str:
    """Collapse system + messages into a single prompt string for MLX."""
    parts: list[str] = []
    system_text = request.get_system_text()
    if system_text:
        parts.append(f"<system>\n{system_text}\n</system>\n")
    for m in request.messages:
        if isinstance(m.content, str):
            text = m.content
        else:
            text = "".join(cb.text for cb in m.content)
        parts.append(f"<{m.role}>\n{text}\n</{m.role}>\n")
    parts.append("<assistant>\n")
    return "".join(parts)


class StubRuntime:
    """Deterministic fake — for CI / non-Apple-Silicon dev."""

    name = "stub"

    def __init__(self, config: MekongdConfig):
        self.config = config

    async def generate(self, request: MessagesRequest) -> str:
        return f"[stub] mekongd received {len(request.messages)} messages (max_tokens={request.max_tokens})"

    async def stream(self, request: MessagesRequest) -> AsyncIterator[str]:
        text = await self.generate(request)
        for chunk in text.split(" "):
            yield chunk + " "


class MLXRuntime:
    """Qwen3.6 via mlx-lm — Apple Silicon only."""

    name = "mlx"

    def __init__(self, config: MekongdConfig):
        self.config = config
        self._model = None
        self._tokenizer = None

    def _lazy_load(self):
        if self._model is not None:
            return
        from mlx_lm import load  # type: ignore[import-not-found]

        model_ref = self.config.mlx_path or self.config.model_name
        log.info("Loading MLX model: %s", model_ref)
        self._model, self._tokenizer = load(model_ref)

    async def generate(self, request: MessagesRequest) -> str:
        from mlx_lm import generate as mlx_generate  # type: ignore[import-not-found]

        self._lazy_load()
        prompt = _flatten_prompt(request)
        return mlx_generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=request.max_tokens,
            temp=request.temperature or 0.7,
            verbose=False,
        )

    async def stream(self, request: MessagesRequest) -> AsyncIterator[str]:
        from mlx_lm import stream_generate  # type: ignore[import-not-found]

        self._lazy_load()
        prompt = _flatten_prompt(request)
        for token_piece in stream_generate(
            self._model,
            self._tokenizer,
            prompt=prompt,
            max_tokens=request.max_tokens,
        ):
            yield token_piece


class OpenAIRuntime:
    """OpenAI-compatible local server runtime (e.g. rapid-mlx, llama.cpp, Ollama)."""

    name = "openai"

    def __init__(self, config: MekongdConfig):
        self.config = config
        self.url = f"{self.config.local_api_url.rstrip('/')}/chat/completions"
        self.headers = {}
        if self.config.local_api_key:
            self.headers["Authorization"] = f"Bearer {self.config.local_api_key}"
        # Reuse a single client for connection pooling (loopback → keep-alive)
        self._client = httpx.AsyncClient(
            timeout=_LLM_TIMEOUT,
            limits=httpx.Limits(
                max_connections=4,
                max_keepalive_connections=2,
                keepalive_expiry=120,
            ),
        )

    def _to_openai_payload(self, request: MessagesRequest) -> dict:
        messages = []
        system_text = request.get_system_text()
        if system_text:
            messages.append({"role": "system", "content": system_text})
        for m in request.messages:
            if isinstance(m.content, str):
                text = m.content
            else:
                text = "".join(cb.text for cb in m.content)
            messages.append({"role": m.role, "content": text})

        payload = {
            "model": self.config.model_name,
            "messages": messages,
            "max_tokens": min(request.max_tokens, self.config.local_max_tokens),
            "temperature": request.temperature if request.temperature is not None else 0.7,
            "stream": request.stream,
        }
        if request.top_p is not None:
            payload["top_p"] = request.top_p
        if request.stop_sequences:
            payload["stop"] = request.stop_sequences
        return payload

    async def generate(self, request: MessagesRequest) -> str:
        payload = self._to_openai_payload(request)
        t0 = time.monotonic()
        last_err: Exception | None = None
        for attempt in range(_MAX_RETRIES + 1):
            try:
                resp = await self._client.post(
                    self.url, headers=self.headers, json=payload
                )
                resp.raise_for_status()
                data = resp.json()
                elapsed = time.monotonic() - t0
                log.info(
                    "generate OK: %.1fs, attempt=%d, tokens_est=%d",
                    elapsed, attempt + 1, len(data["choices"][0]["message"]["content"]) // 4,
                )
                return data["choices"][0]["message"]["content"]
            except (httpx.ReadTimeout, httpx.ConnectTimeout, httpx.PoolTimeout) as exc:
                last_err = exc
                wait = _RETRY_BACKOFF * (2 ** attempt)
                log.warning(
                    "generate timeout (attempt %d/%d): %s — retrying in %.1fs",
                    attempt + 1, _MAX_RETRIES + 1, exc, wait,
                )
                if attempt < _MAX_RETRIES:
                    await asyncio.sleep(wait)
        raise last_err  # type: ignore[misc]

    async def stream(self, request: MessagesRequest) -> AsyncIterator[str]:
        payload = self._to_openai_payload(request)
        t0 = time.monotonic()
        ttft_logged = False
        async with self._client.stream(
            "POST", self.url, headers=self.headers, json=payload
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data:"):
                    data_str = line[5:].strip()
                    if data_str == "[DONE]":
                        break
                    try:
                        chunk = json.loads(data_str)
                        delta = chunk["choices"][0]["delta"]
                        if "content" in delta:
                            if not ttft_logged:
                                log.info("stream TTFT: %.1fs", time.monotonic() - t0)
                                ttft_logged = True
                            yield delta["content"]
                    except (ValueError, KeyError):
                        continue
        log.info("stream complete: %.1fs total", time.monotonic() - t0)


def get_runtime(config: MekongdConfig) -> BaseRuntime:
    """Select OpenAI local endpoint if socket is listening, else MLX, else Stub."""
    # First: Check if local OpenAI/MLX endpoint socket is reachable
    try:
        parsed = urlparse(config.local_api_url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or (80 if parsed.scheme == "http" else 443)
        with socket.create_connection((host, port), timeout=0.5):
            log.info("Using local OpenAI-compatible endpoint: %s", config.local_api_url)
            return OpenAIRuntime(config)
    except Exception:
        pass

    # Fallback to MLX in-process loading
    try:
        import platform

        if platform.system() == "Darwin" and platform.machine() == "arm64":
            import importlib.util

            if importlib.util.find_spec("mlx_lm") is not None:
                return MLXRuntime(config)
    except Exception as e:
        log.warning("MLX runtime unavailable: %s — falling back to Stub", e)
    return StubRuntime(config)

