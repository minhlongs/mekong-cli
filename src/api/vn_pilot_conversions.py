"""VN Pilot — conversion recording, /convert route, /revenue route."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from src.api.vn_pilot_auth import _require_admin_token
from src.api.vn_pilot_common import (
    ConversionRequest,
    _append_jsonl,
    _conversions_path,
    _load_conversions,
    _load_pilots,
)

conversions_router = APIRouter(tags=["VN Pilot"])


def _record_conversion(
    user_id: str,
    tier: str,
    monthly_vnd: int,
    started_at: Optional[str] = None,
    bank_tx_ref: Optional[str] = None,
) -> dict:
    """Internal conversion writer — shared by /convert endpoint + VietQR webhook.

    Idempotency keys (in order):
    1. bank_tx_ref — if provided (webhook path), canonical; same ref returns existing.
    2. (user_id, started_at) — manual /convert fallback when no bank ref.

    Raises ValueError if user_id not in pilots.jsonl.
    Returns dict with is_new flag + full conversion record fields.
    """
    pilots = _load_pilots()
    if not any(p.get("user_id") == user_id for p in pilots):
        raise ValueError(f"Unknown user_id: {user_id}")

    started_at = started_at or datetime.now(timezone.utc).date().isoformat()
    conversions = _load_conversions()

    if bank_tx_ref:
        existing = next(
            (c for c in conversions if c.get("bank_tx_ref") == bank_tx_ref),
            None,
        )
        if existing:
            return {"is_new": False, **existing}

    existing = next(
        (
            c for c in conversions
            if c.get("user_id") == user_id and c.get("started_at") == started_at
        ),
        None,
    )
    if existing:
        return {"is_new": False, **existing}

    record = {
        "user_id": user_id,
        "tier": tier,
        "monthly_vnd": monthly_vnd,
        "started_at": started_at,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    if bank_tx_ref:
        record["bank_tx_ref"] = bank_tx_ref
    _append_jsonl(_conversions_path(), record)
    return {"is_new": True, **record}


@conversions_router.post(
    "/convert",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_require_admin_token)],
)
async def convert(req: ConversionRequest) -> dict[str, object]:
    """Mark a pilot user as paid. Records tier + MRR contribution.

    Requires Authorization: Bearer <MEKONG_ADMIN_TOKEN>.
    """
    try:
        return _record_conversion(
            user_id=req.user_id,
            tier=req.tier,
            monthly_vnd=req.monthly_vnd,
            started_at=req.started_at,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@conversions_router.get("/revenue")
async def revenue() -> dict[str, object]:
    """Conversion + MRR snapshot for founder dashboard."""
    pilots = _load_pilots()
    conversions = _load_conversions()
    total_pilots = len(pilots)
    converted_user_ids = {c["user_id"] for c in conversions}
    mrr_vnd = sum(c.get("monthly_vnd", 0) for c in conversions)
    by_tier: dict[str, int] = {}
    for c in conversions:
        by_tier[c.get("tier") or "unknown"] = by_tier.get(c.get("tier") or "unknown", 0) + 1
    return {
        "conversions": len(conversions),
        "unique_converted_users": len(converted_user_ids),
        "conversion_rate": (
            round(len(converted_user_ids) / total_pilots, 3) if total_pilots else 0.0
        ),
        "mrr_vnd": mrr_vnd,
        "by_tier": by_tier,
        "target_mrr_vnd": 1_000_000,
        "target_conversions": 5,
    }
