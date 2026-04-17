"""Runtime adapters — MLX (Apple Silicon) + Stub (CI/dev)."""

from __future__ import annotations

import logging
from typing import AsyncIterator, Protocol

from mekongd.config import MekongdConfig
from mekongd.schemas import MessagesRequest

log = logging.getLogger(__name__)


class BaseRuntime(Protocol):
    """Runtime interface — generate and stream completions."""

    name: str

    async def generate(self, request: MessagesRequest) -> str: ...

    async def stream(self, request: MessagesRequest) -> AsyncIterator[str]: ...


def _flatten_prompt(request: MessagesRequest) -> str:
    """Collapse system + messages into a single prompt string for MLX."""
    parts: list[str] = []
    if request.system:
        parts.append(f"<system>\n{request.system}\n</system>\n")
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


def get_runtime(config: MekongdConfig) -> BaseRuntime:
    """Select MLX on Apple Silicon if importable, else Stub."""
    try:
        import platform

        if platform.system() == "Darwin" and platform.machine() == "arm64":
            import importlib.util

            if importlib.util.find_spec("mlx_lm") is not None:
                return MLXRuntime(config)
    except Exception as e:
        log.warning("MLX runtime unavailable: %s — falling back to Stub", e)
    return StubRuntime(config)
