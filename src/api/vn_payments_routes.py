"""
VN Payments API — bank webhook handlers for auto-conversion.

POST /v1/payments/vietqr/webhook  → Sepay/MB/etc forward bank transfer
                                   confirmations here; we map memo→user_id,
                                   amount→tier, call internal conversion.

Design contract:
- ALWAYS return 200 to bank (even on application errors) so bank doesn't
  retry-storm. Real errors logged + alertable, not surfaced as HTTP.
- EXCEPTION: signature verification failure → 401 (banks expect this for
  invalid auth; they retry with a different signature is impossible →
  401 stops the retry cycle).
- 503 only if feature is disabled at gateway level (no secret configured).
- Idempotency via bank_tx_ref — same ref returns previous record.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.api import vn_pilot_routes as vpr
from src.services.vietqr_verifier import get_verifier

router = APIRouter(prefix="/v1/payments", tags=["VN Payments"])

# Memo format: "MEKONG-{org}-{user_id}" or legacy "MEKONG-{user_id}".
# Two capture groups: optional org (group 1) + required user_id (group 2).
# Negative lookahead (?!opc_) prevents org group from consuming a user_id token.
# Separators: `-`, `_`, ` ` are interchangeable. Case-insensitive.
_MEMO_RE = re.compile(
    r"MEKONG[-_\s]+(?:(?!opc_)([a-z0-9][a-z0-9-]{0,31})[-_\s]+)?(opc_\d{3}_[a-z0-9]+)",
    re.IGNORECASE,
)

# Phase 6 VN tier prices. Real source of truth is factory/contracts/pricing.json
# but for webhook latency we hardcode the 3 supported tiers. Mismatched amounts
# → log + 200, don't fail (founder reviews log).
_TIER_PRICES_VND = {
    199_000: "starter_vnd",
    299_000: "growth_vnd",
    499_000: "pro_vnd",
}


class VietQRWebhookPayload(BaseModel):
    """Provider-agnostic webhook payload (Sepay + MB + VietQR.io aligned).

    Fields below are the union of common bank webhook formats. Extra fields
    accepted but ignored — Pydantic's default model_config allows them.
    """
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
    """Extract (org_id, user_id) from bank memo. Returns None if no match.

    Two formats accepted indefinitely (no sunset):
    - Legacy single-tenant: `MEKONG-opc_001_abc` → ("default", "opc_001_abc")
    - Multi-tenant:         `MEKONG-acme-opc_001_abc` → ("acme", "opc_001_abc")

    Tolerant: case-insensitive; separators `-`, `_`, ` ` interchangeable.
    Negative lookahead `(?!opc_)` prevents the org group from stealing user_id.
    Org name max 32 chars `[a-z0-9-]`; names exceeding this cause no match.
    """
    if not memo:
        return None
    m = _MEMO_RE.search(memo)
    if not m:
        return None
    org_raw, user_raw = m.group(1), m.group(2)
    org_id = org_raw.lower() if org_raw else "default"
    user_id = user_raw.lower()
    return org_id, user_id


@router.post("/vietqr/webhook")
async def vietqr_webhook(payload: VietQRWebhookPayload, request: Request) -> dict:
    """Receive bank transfer notification, map to pilot conversion.

    Flow:
    1. Verify HMAC signature (provider-specific) — 401 on fail
    2. Parse memo → user_id
    3. Match amount → tier_key
    4. Call vpr._record_conversion(..., bank_tx_ref=tx_ref) (idempotent)
    5. Log result, return 200

    Bank-friendly error policy: anything beyond signature failure returns
    200 with `status` describing the outcome. Bank doesn't retry, founder
    reviews `~/.mekong/vietqr_webhook.log`.
    """
    # 1. Verify signature (gate must pass before we trust ANY payload field)
    try:
        verifier = get_verifier()
    except RuntimeError as exc:
        logging.error("VietQR webhook config error: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )

    body = await request.body()
    headers = {k.lower(): v for k, v in request.headers.items()}
    if not verifier.verify(body, headers):
        _log_webhook({
            "outcome": "signature_invalid",
            "tx_ref": payload.tx_ref,
            "bank_code": payload.bank_code,
        })
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid webhook signature",
        )

    # 2. Parse memo → (org_id, user_id)
    parsed = _parse_memo(payload.memo)
    if not parsed:
        _log_webhook({
            "outcome": "memo_unparseable",
            "tx_ref": payload.tx_ref,
            "memo_preview": payload.memo[:20],
        })
        logging.warning(
            '{"event": "vietqr_parse_failed", "memo_preview": "%s", "memo_len": %d}',
            payload.memo[:20],
            len(payload.memo),
        )
        return {"status": "memo_unparseable", "tx_ref": payload.tx_ref}
    org_id, user_id = parsed
    logging.info(
        '{"event": "vietqr_parse", "org_id": "%s", "user_id": "%s"}',
        org_id,
        user_id,
    )

    # 3. Match amount → tier (exact match; mismatches logged + accepted)
    tier_key = _TIER_PRICES_VND.get(payload.amount)
    if not tier_key:
        _log_webhook({
            "outcome": "amount_no_tier",
            "tx_ref": payload.tx_ref,
            "user_id": user_id,
            "org_id": org_id,
            "amount": payload.amount,
        })
        return {
            "status": "amount_no_tier",
            "tx_ref": payload.tx_ref,
            "amount": payload.amount,
            "org_id": org_id,
        }

    # 4. Record conversion (idempotent via bank_tx_ref)
    try:
        result = vpr._record_conversion(
            user_id=user_id,
            tier=tier_key,
            monthly_vnd=payload.amount,
            bank_tx_ref=payload.tx_ref,
            org_id=org_id,
        )
    except ValueError as exc:
        # User_id not found in pilots.jsonl — log + accept (don't retry-storm)
        _log_webhook({
            "outcome": "user_not_found",
            "tx_ref": payload.tx_ref,
            "user_id": user_id,
            "org_id": org_id,
            "detail": str(exc),
        })
        return {
            "status": "user_not_found",
            "tx_ref": payload.tx_ref,
            "user_id": user_id,
            "org_id": org_id,
        }

    outcome = "already_processed" if not result.get("is_new") else "converted"
    _log_webhook({
        "outcome": outcome,
        "tx_ref": payload.tx_ref,
        "user_id": user_id,
        "org_id": org_id,
        "tier": tier_key,
        "amount": payload.amount,
    })
    return {
        "status": outcome,
        "tx_ref": payload.tx_ref,
        "user_id": user_id,
        "org_id": org_id,
        "tier": tier_key,
    }
