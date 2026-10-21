# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Polar.sh HTTP client — checkout sessions + webhook verification + event parsing.

Zero new pip deps: stdlib urllib.request + hmac + base64 + json.
Adapts HMAC idiom from vietqr_verifier.py (Phase 7 P02).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import time
import urllib.error
import urllib.request
from typing import Any

from src.services.polar_client_models import (
    PolarAPIError,
    PolarEventInvalid,
    _POLAR_API_BASE,
    _REPLAY_WINDOW_SECONDS,
    _header_get,
    parse_event,
)

logger = logging.getLogger(__name__)


def create_checkout_session(
    org_id: str,
    customer_email: str,
    product_id: str,
    success_url: str = "",
    cancel_url: str = "",
) -> dict[str, Any]:
    """Create a Polar.sh checkout session for an org platform fee."""
    api_key = os.environ.get("POLAR_API_KEY", "")
    if not api_key:
        raise RuntimeError("POLAR_API_KEY not set")

    body = json.dumps({
        "product_id": product_id,
        "customer_email": customer_email,
        "metadata": {"mekong_org_id": org_id},
        "success_url": success_url,
        "cancel_url": cancel_url,
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{_POLAR_API_BASE}/checkouts/",
        data=body,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        resp_body = exc.read().decode("utf-8", errors="replace")
        raise PolarAPIError(exc.code, resp_body) from exc


def verify_webhook_signature(
    headers: dict[str, str],
    raw_body: bytes,
    secret: str,
) -> bool:
    """Verify a Polar.sh Standard Webhooks signature."""
    webhook_id = _header_get(headers, "webhook-id")
    webhook_ts = _header_get(headers, "webhook-timestamp")
    webhook_sig = _header_get(headers, "webhook-signature")

    if not (webhook_id and webhook_ts and webhook_sig):
        logger.warning("Polar webhook: missing signature headers")
        return False

    try:
        ts = int(webhook_ts)
    except ValueError:
        logger.warning("Polar webhook: invalid timestamp %r", webhook_ts)
        return False

    if abs(time.time() - ts) > _REPLAY_WINDOW_SECONDS:
        raise ValueError("replay_window_expired")

    signing_input = f"{webhook_id}.{webhook_ts}.{raw_body.decode('utf-8')}"
    expected = base64.b64encode(
        hmac.new(
            secret.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    sig_parts = webhook_sig.split(",", 1)
    if len(sig_parts) != 2 or sig_parts[0] != "v1":
        logger.warning("Polar webhook: invalid signature format %r", webhook_sig)
        return False

    received_sig = sig_parts[1]
    return hmac.compare_digest(expected, received_sig)


__all__ = [
    "PolarAPIError",
    "PolarEventInvalid",
    "_POLAR_API_BASE",
    "_REPLAY_WINDOW_SECONDS",
    "create_checkout_session",
    "verify_webhook_signature",
    "_header_get",
    "parse_event",
]
