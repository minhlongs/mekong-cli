# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Resend.com REST API client — stdlib urllib.request only (no new pip deps).

Sends transactional email via POST https://api.resend.com/emails.
Auth: Bearer $RESEND_API_KEY (read at call time; raises RuntimeError if missing).
Sender domain: $MEKONG_MAGIC_LINK_FROM (default: noreply@mekong.dev).
Timeout: 10s. No retry loop — caller decides on failure policy.
"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from src.services.resend_templates import (
    _VN_MAGIC_LINK_SENTENCE,
    _VN_MEKONG_HUB,
    _VN_SUPPORT_LINE,
    send_drip_email,
    send_magic_link_email,
    send_welcome_email,
)

_RESEND_API_URL = "https://api.resend.com/emails"
_DEFAULT_FROM = "noreply@mekong.dev"
_TIMEOUT_SECONDS = 10


class ResendError(Exception):
    """Raised on non-2xx Resend API response."""

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"Resend API error {status_code}: {body}")


def _api_key() -> str:
    """Read RESEND_API_KEY at call time. Raises RuntimeError if unset."""
    key = os.getenv("RESEND_API_KEY")
    if not key:
        raise RuntimeError(
            "RESEND_API_KEY env var is required to send email. "
            "Set it in your launchd plist EnvironmentVariables."
        )
    return key


def _from_address() -> str:
    return os.getenv("MEKONG_MAGIC_LINK_FROM", _DEFAULT_FROM)


def send_email(to: str, subject: str, html: str) -> dict[str, Any]:
    """POST one email to Resend REST API.

    Args:
        to: Recipient email address.
        subject: Email subject line (Vietnamese OK).
        html: HTML body (Vietnamese OK — ensure_ascii=False).

    Returns:
        Parsed JSON response dict from Resend (contains 'id' on success).

    Raises:
        RuntimeError: RESEND_API_KEY not set.
        ResendError: Non-2xx HTTP response from Resend API.
        urllib.error.URLError: Network/timeout failure.
    """
    api_key = _api_key()
    payload = {
        "from": _from_address(),
        "to": [to],
        "subject": subject,
        "html": html,
    }
    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url=_RESEND_API_URL,
        data=body_bytes,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json; charset=utf-8",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=_TIMEOUT_SECONDS) as resp:
            resp_body = resp.read().decode("utf-8")
            return json.loads(resp_body)
    except urllib.error.HTTPError as exc:
        error_body = exc.read().decode("utf-8") if exc.fp else ""
        raise ResendError(exc.code, error_body) from exc


__all__ = [
    "_RESEND_API_URL",
    "_DEFAULT_FROM",
    "_TIMEOUT_SECONDS",
    "ResendError",
    "_api_key",
    "_from_address",
    "send_email",
    "_VN_MEKONG_HUB",
    "_VN_MAGIC_LINK_SENTENCE",
    "_VN_SUPPORT_LINE",
    "send_welcome_email",
    "send_magic_link_email",
    "send_drip_email",
]
