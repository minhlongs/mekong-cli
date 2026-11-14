"""Production-grade pure-stdlib Zalo Official Account (OA) OpenAPI v3 connector.

Enforces:
- 01/06/2026 Zalo OpenAPI OA tier policy (Growth >= 2.5M VND/yr or Enterprise >= 6M VND/yr;
  Basic/Trial/Standard tiers rejected fail-closed with ZaloTierPolicyError).
- Webhook MAC verification: sha256(app_id + data + timestamp + oa_secret_key).
- 48-hour customer service interaction window (172,800s).
- Silent business error detection on HTTP 200 JSON responses where body["error"] != 0.
- Timeout / network interruption -> uncertain_reconciliation_required (never blind retry).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import socket
import urllib.error
import urllib.request
from typing import Any, Callable, Final

from src.opc.connectors.base import ConnectorResult
from src.opc.models import ActionPayload

ZALO_OA_CS_ENDPOINT: Final[str] = "https://openapi.zalo.me/v3.0/oa/message/cs"
ZALO_OA_INTERACTION_WINDOW_S: Final[int] = 48 * 3600
ALLOWED_ZALO_OA_TIERS: Final[frozenset[str]] = frozenset({"growth", "enterprise", "toan_dien", "tang_truong"})
BLOCKED_ZALO_OA_TIERS: Final[frozenset[str]] = frozenset({"basic", "trial", "standard", "free", "co_ban", "tieu_chuan"})

HttpTransportFn = Callable[[str, dict[str, str], bytes, float], tuple[int, bytes]]


class ZaloTierPolicyError(PermissionError):
    """Raised when an OA tier is ineligible for Zalo OpenAPI per 01/06/2026 policy."""


class ZaloWebhookMacError(PermissionError):
    """Raised when a Zalo OA webhook MAC signature fails constant-time verification."""


def verify_zalo_webhook_mac(
    app_id: str,
    raw_data: str | bytes,
    timestamp: str | int,
    oa_secret_key: str,
    received_mac: str,
) -> bool:
    """Verify Zalo OA webhook MAC = sha256(app_id + data + timestamp + oa_secret_key)."""
    secret = (oa_secret_key or "").strip()
    sig = (received_mac or "").strip().lower()
    if sig.startswith("mac="):
        sig = sig[4:]
    if not app_id or not secret or not sig:
        return False
    data_text = raw_data.decode("utf-8") if isinstance(raw_data, bytes) else str(raw_data)
    material = f"{app_id.strip()}{data_text}{str(timestamp).strip()}{secret}".encode("utf-8")
    expected = hashlib.sha256(material).hexdigest().lower()
    return hmac.compare_digest(expected, sig)


def assert_zalo_oa_tier_allowed(oa_tier: str) -> str:
    """Enforce Zalo 01/06/2026 OpenAPI tier gate (Growth / Enterprise only)."""
    norm = (oa_tier or "").strip().lower().replace("-", "_").replace(" ", "_")
    if norm in ALLOWED_ZALO_OA_TIERS:
        return norm
    raise ZaloTierPolicyError(
        f"Zalo OA tier '{oa_tier}' is not eligible for OpenAPI (requires Growth/Enterprise tier per 01/06/2026 policy)."
    )


def _stdlib_http_post(url: str, headers: dict[str, str], body: bytes, timeout_s: float) -> tuple[int, bytes]:
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=timeout_s) as resp:  # noqa: S310
        return int(resp.status), resp.read()


class ZaloOAConnector:
    """Pure-stdlib Zalo OA OpenAPI v3 customer-service message connector."""

    def __init__(
        self,
        access_token: str | None = None,
        oa_tier: str | None = None,
        endpoint: str = ZALO_OA_CS_ENDPOINT,
        timeout_seconds: float = 10.0,
        transport: HttpTransportFn | None = None,
        connector_id: str = "zalo_oa",
    ) -> None:
        self.connector_id = connector_id
        self._access_token = (access_token if access_token is not None else os.getenv("ZALO_OA_ACCESS_TOKEN", "")).strip()
        raw_tier = oa_tier if oa_tier is not None else os.getenv("ZALO_OA_TIER", "growth")
        self.oa_tier = assert_zalo_oa_tier_allowed(raw_tier)
        self.endpoint = endpoint
        self.timeout_seconds = float(timeout_seconds)
        self._transport: HttpTransportFn = transport or _stdlib_http_post
        self.dispatched: dict[str, dict[str, Any]] = {}

    @staticmethod
    def _extract_user_id(recipient: str) -> str:
        clean = (recipient or "").strip()
        return clean.split("zalo:", 1)[1].strip() if clean.startswith("zalo:") else clean

    def dispatch(self, idempotency_key: str, payload: ActionPayload, *, now: int | None = None) -> ConnectorResult:
        """Send an approved CS message within the 48h interaction window with full error inspection."""
        if idempotency_key in self.dispatched:
            return ConnectorResult(True, self.connector_id, "completed", {"deduplicated": True, "record": self.dispatched[idempotency_key]})

        assert_zalo_oa_tier_allowed(self.oa_tier)
        if not self._access_token:
            return ConnectorResult(False, self.connector_id, "failed", {}, "Missing ZALO_OA_ACCESS_TOKEN (fail-closed).")

        age = int(payload.parameters.get("interaction_age_seconds", 0))
        if now is not None and "last_user_interaction_ts" in payload.parameters:
            age = now - int(payload.parameters["last_user_interaction_ts"])
        if age < 0 or age > ZALO_OA_INTERACTION_WINDOW_S:
            return ConnectorResult(False, self.connector_id, "failed", {}, f"Zalo OA 48h window exceeded ({age}s).")

        user_id = self._extract_user_id(payload.recipient)
        if not user_id:
            return ConnectorResult(False, self.connector_id, "failed", {}, "Missing Zalo recipient user_id.")

        body_obj: dict[str, Any] = {
            "recipient": {"user_id": user_id},
            "message": {"text": payload.content},
        }
        headers = {
            "Content-Type": "application/json; charset=utf-8",
            "access_token": self._access_token,
            "X-Idempotency-Key": idempotency_key,
        }
        raw_req = json.dumps(body_obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")

        try:
            status_code, resp_bytes = self._transport(self.endpoint, headers, raw_req, self.timeout_seconds)
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 502, 503, 504):
                return ConnectorResult(
                    False, self.connector_id, "uncertain_reconciliation_required",
                    {"http_status": exc.code}, f"Zalo OA transient HTTP {exc.code}; reconciliation required.",
                )
            return ConnectorResult(False, self.connector_id, "failed", {"http_status": exc.code}, f"Zalo OA HTTP {exc.code}.")
        except (TimeoutError, socket.timeout, urllib.error.URLError, OSError) as exc:
            return ConnectorResult(
                False, self.connector_id, "uncertain_reconciliation_required",
                {}, f"Zalo OA network/timeout error ({type(exc).__name__}); reconciliation required.",
            )

        if status_code in (429, 502, 503, 504):
            return ConnectorResult(
                False, self.connector_id, "uncertain_reconciliation_required",
                {"http_status": status_code}, f"Zalo OA HTTP {status_code}; reconciliation required.",
            )
        if status_code < 200 or status_code >= 300:
            return ConnectorResult(False, self.connector_id, "failed", {"http_status": status_code}, f"Zalo OA HTTP {status_code}.")

        try:
            parsed = json.loads(resp_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return ConnectorResult(False, self.connector_id, "failed", {}, "Invalid JSON from Zalo OpenAPI.")
        if not isinstance(parsed, dict):
            return ConnectorResult(False, self.connector_id, "failed", {}, "Non-object JSON from Zalo OpenAPI.")

        err_code = parsed.get("error", -1)
        if type(err_code) is not int or err_code != 0:
            err_msg = str(parsed.get("message", "Unknown Zalo OpenAPI error"))
            return ConnectorResult(
                False, self.connector_id, "failed",
                {"zalo_error": err_code, "zalo_message": err_msg},
                f"Zalo OpenAPI silent failure (error={err_code}: {err_msg}).",
            )

        data_obj = parsed.get("data")
        msg_id = str(data_obj.get("message_id", "")) if isinstance(data_obj, dict) else ""
        record = {
            "idempotency_key": idempotency_key,
            "recipient": payload.recipient,
            "message_id": msg_id,
            "oa_tier": self.oa_tier,
            "amount_vnd": payload.parameters.get("amount_vnd", 0),
            "vietqr_emvco": payload.parameters.get("vietqr_emvco", ""),
        }
        self.dispatched[idempotency_key] = record
        return ConnectorResult(True, self.connector_id, "completed", {"deduplicated": False, "record": record})
