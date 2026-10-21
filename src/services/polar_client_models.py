# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Polar.sh client exceptions, constants, header lookup, and event parsing."""
from __future__ import annotations

import json
from typing import Any

_POLAR_API_BASE = "https://api.polar.sh/v1"
_REPLAY_WINDOW_SECONDS = 300  # 5 minutes


class PolarAPIError(Exception):
    """Non-2xx response from Polar.sh API."""

    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"Polar API returned {status}: {body[:200]}")
        self.status = status
        self.body = body


class PolarEventInvalid(Exception):
    """Malformed or unparseable webhook event."""


def _header_get(headers: dict[str, str], key: str) -> str:
    """Case-insensitive header lookup."""
    key_lower = key.lower()
    for k, v in headers.items():
        if k.lower() == key_lower:
            return v
    return ""


def parse_event(raw_body: bytes) -> dict[str, Any]:
    """Parse a Polar webhook event body."""
    try:
        data = json.loads(raw_body)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise PolarEventInvalid(f"Malformed JSON: {exc}") from exc

    event_type = data.get("type")
    event_id = data.get("data", {}).get("id") or data.get("id", "")

    if not event_type:
        raise PolarEventInvalid("Missing 'type' field in webhook event")

    return {
        "event_id": event_id,
        "event_type": event_type,
        "payload": data,
    }


__all__ = [
    "_POLAR_API_BASE",
    "_REPLAY_WINDOW_SECONDS",
    "PolarAPIError",
    "PolarEventInvalid",
    "_header_get",
    "parse_event",
]
