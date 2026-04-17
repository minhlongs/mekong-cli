"""LLMClient — Anthropic-compat client targeting mekongd by default.

Default base_url = http://127.0.0.1:8765 (mekongd). Falls through to mekongd's
routing: local Qwen or Anthropic cloud, depending on mekongd policy.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass

import httpx

log = logging.getLogger(__name__)

DEFAULT_BASE_URL = os.getenv("MEKONGD_URL", "http://127.0.0.1:8765")
DEFAULT_MODEL = os.getenv("AGENT_CORE_MODEL", "claude-opus-4-7")
DEFAULT_MAX_TOKENS = 1024
DEFAULT_TIMEOUT = 120.0


@dataclass
class ChatMessage:
    role: str
    content: str

    def as_dict(self) -> dict:
        return {"role": self.role, "content": self.content}


class LLMClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.timeout = timeout

    def _headers(self) -> dict:
        return {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        }

    def chat(
        self,
        messages: list[ChatMessage] | list[dict],
        system: str | None = None,
        max_tokens: int = DEFAULT_MAX_TOKENS,
    ) -> str:
        """Send Anthropic-compat /v1/messages request. Returns assistant text."""
        msgs = [m.as_dict() if isinstance(m, ChatMessage) else m for m in messages]
        body: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "messages": msgs,
        }
        if system:
            body["system"] = system
        url = f"{self.base_url}/v1/messages"
        with httpx.Client(timeout=self.timeout) as client:
            resp = client.post(url, json=body, headers=self._headers())
            resp.raise_for_status()
            data = resp.json()
        return _extract_text(data)

    def healthz(self) -> dict:
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(f"{self.base_url}/healthz")
            resp.raise_for_status()
            return resp.json()

    def send_signal(self, kind: str, note: str = "") -> dict:
        """Pillar 3 feedback — POST {kind: good|bad, note} to mekongd /v1/signals."""
        if kind not in ("good", "bad"):
            raise ValueError(f"kind must be 'good' or 'bad', got {kind!r}")
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(
                f"{self.base_url}/v1/signals",
                json={"kind": kind, "note": note},
            )
            resp.raise_for_status()
            return resp.json()


def _extract_text(data: dict) -> str:
    blocks = data.get("content") or []
    parts: list[str] = []
    for b in blocks:
        if isinstance(b, dict) and b.get("type") == "text":
            parts.append(b.get("text") or "")
    return "".join(parts).strip()
