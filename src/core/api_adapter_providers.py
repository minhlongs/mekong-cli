# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""API adapter provider helpers — key lookup, URL shaping, and payload shaping.

Split out of the API adapter so the adapter itself stays within the size limit.
"""

from __future__ import annotations

import json
import os

ANTHROPIC_DEFAULT_BASE_URL = "https://api.anthropic.com"


def detect_provider(model_id: str) -> str:
    if model_id.startswith("ollama:"):
        return "ollama"
    for key, prov in (("claude", "anthropic"), ("gemini", "google"), ("gpt", "openai")):
        if key in model_id:
            return prov
    raise ValueError(f"Unknown provider for model: {model_id}")


def get_api_key(provider: str) -> str:
    env_var = {"anthropic": "ANTHROPIC_API_KEY", "google": "GOOGLE_API_KEY", "openai": "OPENAI_API_KEY"}.get(provider, "")
    if key := os.getenv(env_var, ""):
        return key
    raise OSError(f"Missing API key: {env_var}")


def format_for_openai(messages: list[dict], system_prompt: str | None) -> list[dict]:
    return ([{"role": "system", "content": system_prompt}] if system_prompt else []) + list(messages)


def format_for_gemini(messages: list[dict], system_prompt: str | None) -> list[dict]:
    contents = [{"role": "user", "parts": [{"text": system_prompt}]}, {"role": "model", "parts": [{"text": "Understood."}]}] if system_prompt else []
    return contents + [{"role": "model" if m["role"] == "assistant" else "user", "parts": [{"text": m["content"]}]} for m in messages]


def anthropic_messages_url(base_url: str) -> str:
    base = base_url.rstrip("/")
    return base if base.endswith("/messages") else (f"{base}/messages" if ("zunef.com" in base.lower() or base.endswith("/v1")) else f"{base}/v1/messages")


def anthropic_headers(api_key: str) -> dict[str, str]:
    headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"}
    if not (custom := os.getenv("ANTHROPIC_CUSTOM_HEADERS", "").strip()):
        return headers
    try:
        if isinstance(extra := json.loads(custom), dict):
            return {**headers, **extra}
    except json.JSONDecodeError:
        pass
    for line in custom.splitlines():
        for sep in (":", "="):
            if sep in line:
                k, _, v = line.strip().partition(sep)
                headers[k.strip()] = v.strip()
                break
    return headers
