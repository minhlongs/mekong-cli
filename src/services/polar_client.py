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

logger = logging.getLogger(__name__)

# ---------- Custom exceptions ----------


class PolarAPIError(Exception):
    """Non-2xx response from Polar.sh API."""

    def __init__(self, status: int, body: str) -> None:
        super().__init__(f"Polar API returned {status}: {body[:200]}")
        self.status = status
        self.body = body


class PolarEventInvalid(Exception):
    """Malformed or unparseable webhook event."""


# ---------- Checkout session ----------

_POLAR_API_BASE = "https://api.polar.sh/v1"


def create_checkout_session(
    org_id: str,
    customer_email: str,
    product_id: str,
    success_url: str = "",
    cancel_url: str = "",
) -> dict[str, Any]:
    """Create a Polar.sh checkout session for an org platform fee.

    Args:
        org_id: Mekong org slug (stored in Polar metadata).
        customer_email: Email from JWT sub claim.
        product_id: Polar product ID (env: POLAR_PRODUCT_ID_ORG_PLATFORM_FEE).
        success_url: Redirect after payment.
        cancel_url: Redirect after cancel.

    Returns:
        Polar response dict with 'url' and 'id' keys.

    Raises:
        PolarAPIError: On non-2xx response.
        RuntimeError: If POLAR_API_KEY env not set.
    """
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


# ---------- Webhook signature verification ----------

_REPLAY_WINDOW_SECONDS = 300  # 5 minutes


def verify_webhook_signature(
    headers: dict[str, str],
    raw_body: bytes,
    secret: str,
) -> bool:
    """Verify a Polar.sh Standard Webhooks signature.

    Standard Webhooks spec:
      hmac(secret, "{webhook_id}.{webhook_timestamp}.{body}", sha256) → base64
    Header: webhook-signature: v1,{base64-sig}

    Args:
        headers: Request headers (case-insensitive lookup).
        raw_body: Exact raw request body bytes.
        secret: POLAR_WEBHOOK_SECRET env value.

    Returns:
        True if signature is valid and within replay window.

    Raises:
        ValueError: If timestamp is older than 5 minutes (replay attack).
    """
    webhook_id = _header_get(headers, "webhook-id")
    webhook_ts = _header_get(headers, "webhook-timestamp")
    webhook_sig = _header_get(headers, "webhook-signature")

    if not (webhook_id and webhook_ts and webhook_sig):
        logger.warning("Polar webhook: missing signature headers")
        return False

    # Replay window check
    try:
        ts = int(webhook_ts)
    except ValueError:
        logger.warning("Polar webhook: invalid timestamp %r", webhook_ts)
        return False

    if abs(time.time() - ts) > _REPLAY_WINDOW_SECONDS:
        raise ValueError("replay_window_expired")

    # Compute expected signature
    signing_input = f"{webhook_id}.{webhook_ts}.{raw_body.decode('utf-8')}"
    expected = base64.b64encode(
        hmac.new(
            secret.encode("utf-8"),
            signing_input.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    # Extract v1,{sig} → compare sig part
    sig_parts = webhook_sig.split(",", 1)
    if len(sig_parts) != 2 or sig_parts[0] != "v1":
        logger.warning("Polar webhook: invalid signature format %r", webhook_sig)
        return False

    received_sig = sig_parts[1]
    return hmac.compare_digest(expected, received_sig)


def _header_get(headers: dict[str, str], key: str) -> str:
    """Case-insensitive header lookup."""
    key_lower = key.lower()
    for k, v in headers.items():
        if k.lower() == key_lower:
            return v
    return ""


# ---------- Event parsing ----------


def parse_event(raw_body: bytes) -> dict[str, Any]:
    """Parse a Polar webhook event body.

    Args:
        raw_body: Raw request body bytes.

    Returns:
        Dict with keys: event_id, event_type, payload.

    Raises:
        PolarEventInvalid: On malformed JSON or missing required fields.
    """
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
