# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VN Payments API — models, memo parser, logging, and subscription sync helpers."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from pydantic import BaseModel, Field

from src.api import vn_pilot_routes as vpr
from src.services.vietqr_recurring import (
    create_subscription,
    get_subscription_status,
    renew_subscription,
)

# Memo format: "MEKONG-{org}-{user_id}" or legacy "MEKONG-{user_id}".
# Two capture groups: optional org (group 1) + required user_id (group 2).
# Negative lookahead (?!opc_) prevents org group from consuming a user_id token.
# Separators: `-`, `_`, ` ` are interchangeable. Case-insensitive.
_MEMO_RE = re.compile(
    r"MEKONG[-_\s]+(?:(?!opc_)([a-z0-9][a-z0-9-]{0,31})[-_\s]+)?(opc_\d{3}_[a-z0-9]+)",
    re.IGNORECASE,
)

_TIER_PRICES_VND = {
    199_000: "starter_vnd",
    299_000: "growth_vnd",
    499_000: "pro_vnd",
}


class VietQRWebhookPayload(BaseModel):
    """Provider-agnostic webhook payload (Sepay + MB + VietQR.io aligned)."""

    tx_ref: str = Field(min_length=4, max_length=128, description="Bank's tx ref / id")
    amount: int = Field(ge=1, description="Transfer amount in VND (integer dong)")
    memo: str = Field(default="", max_length=256, description="Bank memo text")
    bank_code: Optional[str] = Field(default=None, max_length=16)
    timestamp: Optional[str] = Field(default=None, description="Bank's ISO timestamp")


def _webhook_log_path() -> Path:
    """Append-only webhook attempt log. JSONL via vpr._append_jsonl (flock'd)."""
    return vpr.CONFIG_DIR / "vietqr_webhook.log"


def _log_webhook(entry: dict) -> None:
    """Persist every webhook attempt (success or failure) for audit."""
    try:
        vpr._append_jsonl(_webhook_log_path(), entry)
    except Exception as exc:  # noqa: BLE001 — log path must never break webhook
        logging.warning("Failed to log webhook attempt: %s", exc)


def _parse_memo(memo: str) -> Optional[tuple[str, str]]:
    """Extract (org_id, user_id) from bank memo. Returns None if no match."""
    if not memo:
        return None
    m = _MEMO_RE.search(memo)
    if not m:
        return None
    org_raw, user_raw = m.group(1), m.group(2)
    org_id = org_raw.lower() if org_raw else "default"
    user_id = user_raw.lower()
    return org_id, user_id


def _sync_vietqr_subscription(
    user_id: str,
    org_id: str,
    tier_key: str,
    amount: int,
    tx_ref: str,
) -> str:
    """Create or renew VietQR subscription without raising on error."""
    try:
        existing_status = get_subscription_status(user_id)
    except Exception:  # noqa: BLE001
        existing_status = "none"

    today_iso = datetime.now(timezone.utc).date().isoformat()
    try:
        if existing_status in ("none", "expired", "cancelled"):
            create_subscription(
                user_id=user_id,
                org_id=org_id,
                tier=tier_key,
                monthly_vnd=amount,
                bank_tx_ref=tx_ref,
                started_at=today_iso,
            )
            logging.info(
                '{"event": "subscription_created", "user_id": "%s", "tier": "%s"}',
                user_id,
                tier_key,
            )
            return "created"

        renew_subscription(
            user_id=user_id,
            bank_tx_ref=tx_ref,
            paid_at=today_iso,
        )
        logging.info(
            '{"event": "subscription_renewed", "user_id": "%s", "tier": "%s"}',
            user_id,
            tier_key,
        )
        return "renewed"
    except Exception as sub_exc:  # noqa: BLE001
        logging.warning(
            '{"event": "subscription_error", "user_id": "%s", "error": "%s"}',
            user_id,
            sub_exc,
        )
        return "failed"


__all__ = [
    "_MEMO_RE",
    "_TIER_PRICES_VND",
    "VietQRWebhookPayload",
    "_webhook_log_path",
    "_log_webhook",
    "_parse_memo",
    "_sync_vietqr_subscription",
]
