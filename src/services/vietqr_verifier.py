# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
VietQR webhook signature verifiers — pluggable per provider.

Phase 7 default: Sepay (free tier, HMAC-SHA256). Future verifiers can be
added without touching the route layer; `get_verifier()` reads
`MEKONG_VIETQR_PROVIDER` env var and returns the right strategy.

Each verifier accepts raw request body bytes + headers dict and returns
bool. Use `hmac.compare_digest` to prevent timing attacks.
"""
from __future__ import annotations

import hashlib
import hmac
import logging
import os
from typing import Protocol


class VietQRVerifier(Protocol):
    """Strategy interface — verifies a webhook payload is authentic."""

    def verify(self, body: bytes, headers: dict) -> bool: ...


class SepayVerifier:
    """HMAC-SHA256 over raw body, signature in `Sepay-Signature` header.

    Sepay docs: https://sepay.vn/docs/webhook (signature scheme).
    Header name is case-insensitive per HTTP spec; we look up via
    lowercase to be robust to ASGI middleware lowercasing.
    """

    HEADER_NAME = "sepay-signature"

    def __init__(self, secret: str) -> None:
        if not secret:
            raise ValueError("SepayVerifier requires non-empty secret")
        self._secret = secret.encode("utf-8")

    def verify(self, body: bytes, headers: dict) -> bool:
        received = self._extract_signature(headers)
        if not received:
            return False
        expected = hmac.new(self._secret, body, hashlib.sha256).hexdigest()
        # Timing-safe comparison — equal-length both sides
        return hmac.compare_digest(expected, received)

    def _extract_signature(self, headers: dict) -> str:
        # Headers dict may be case-mixed; normalize keys to lowercase
        for k, v in headers.items():
            if k.lower() == self.HEADER_NAME:
                return v.strip()
        return ""


class NoOpVerifier:
    """Allow-all verifier — for local dev only.

    Activated when MEKONG_VIETQR_PROVIDER=insecure_dev. Logs a warning on
    every verify() call so production misconfiguration is loud. NEVER use
    in prod — gateway should refuse to start if this is set with a public
    URL bound, but enforcing that is the operator's job.
    """

    def verify(self, body: bytes, headers: dict) -> bool:
        logging.warning(
            "NoOpVerifier accepted webhook body=%d bytes — "
            "MEKONG_VIETQR_PROVIDER=insecure_dev is set. Do not use in production.",
            len(body),
        )
        return True


def get_verifier() -> VietQRVerifier:
    """Factory — reads MEKONG_VIETQR_PROVIDER env + corresponding secret.

    Returns:
        Configured verifier instance. Raises RuntimeError if provider is
        recognized but secret env var is missing — route layer translates
        to HTTP 503 (feature disabled at config level).
    """
    provider = os.environ.get("MEKONG_VIETQR_PROVIDER", "sepay").lower()
    if provider == "sepay":
        secret = os.environ.get("MEKONG_VIETQR_WEBHOOK_SECRET", "")
        if not secret:
            raise RuntimeError(
                "MEKONG_VIETQR_WEBHOOK_SECRET not set — VietQR webhook disabled"
            )
        return SepayVerifier(secret)
    if provider == "insecure_dev":
        return NoOpVerifier()
    raise RuntimeError(
        f"Unknown MEKONG_VIETQR_PROVIDER={provider!r} — "
        "supported: sepay, insecure_dev"
    )
