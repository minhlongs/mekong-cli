# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Seed LLM client — Ollama-compatible, mocked in tests."""
from __future__ import annotations

import json
import urllib.request
from typing import Any


def _post_json(url: str, payload: dict, headers: dict | None = None) -> Any:
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers=headers or {"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


def _get_json(url: str, headers: dict | None = None) -> Any:
    req = urllib.request.Request(url, headers=headers or {}, method="GET")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read())


class LLMClient:
    """Ollama-compatible LLM client."""

    def __init__(self, api_key: str = "", base_url: str = "http://localhost:11434", model: str = "llama3") -> None:
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.model = model

    def chat(self, messages: list[dict]) -> str:
        body = {"model": "llama3", "messages": messages, "stream": False}
        try:
            resp = _post_json(f"{self.base_url}/api/chat", body)
        except Exception:
            return ""
        return resp.get("message", {}).get("content", "")

    def embed(self, text: str) -> list[float]:
        body = {"model": "llama3", "prompt": text}
        try:
            resp = _post_json(f"{self.base_url}/api/embed", body)
        except Exception:
            return []
        return resp.get("embedding", [])

    def is_available(self) -> bool:
        try:
            _get_json(f"{self.base_url}/api/tags")
            return True
        except Exception:
            return False
