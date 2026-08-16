# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VN Pilot — conversion recording, /convert route, /revenue route."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.vn_pilot_auth import _require_scope
from src.api.vn_pilot_common import (
    ConversionRequest,
    _append_conversion,
    _load_conversions,
    _load_pilots,
    _org_filter,
)

conversions_router = APIRouter(tags=["VN Pilot"])

# Module-level dependency instance — exposed for test overrides via dep_override
_convert_auth = _require_scope(["founder", "cs"])

# Org_id query param pattern — reused across convert + revenue routes
_ORG_ID_PATTERN = r"^[a-z0-9][a-z0-9-]{0,31}$"


def _record_conversion(
    user_id: str,
    tier: str,
    monthly_vnd: int,
    started_at: Optional[str] = None,
    bank_tx_ref: Optional[str] = None,
    org_id: str = "default",
) -> dict:
    """Internal conversion writer — shared by /convert endpoint + VietQR webhook.

    Idempotency keys (in order):
    1. bank_tx_ref — if provided (webhook path), canonical; same ref returns existing.
    2. (user_id, started_at) — manual /convert fallback when no bank ref.

    org_id is stored on the record for per-tenant isolation (Phase 8 P02).

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
        "org_id": org_id,
    }
    if bank_tx_ref:
        record["bank_tx_ref"] = bank_tx_ref
    _append_conversion(record)
    return {"is_new": True, **record}


@conversions_router.post(
    "/convert",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(_convert_auth)],
)
async def convert(
    req: ConversionRequest,
    org_id: str = Query(default="default", pattern=_ORG_ID_PATTERN),
) -> dict[str, object]:
    """Mark a pilot user as paid within a given org. Records tier + MRR contribution.

    Requires Authorization: Bearer <token> with founder/cs scope for the org.
    org_id defaults to "default" for back-compat.
    """
    # Scope org boundary: verify user_id exists in this org's pilot list
    org_pilots = _org_filter(_load_pilots(), org_id)
    if not any(p.get("user_id") == req.user_id for p in org_pilots):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"user_id not found in org {org_id}",
        )

    try:
        return _record_conversion(
            user_id=req.user_id,
            tier=req.tier,
            monthly_vnd=req.monthly_vnd,
            started_at=req.started_at,
            org_id=org_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@conversions_router.get("/revenue")
async def revenue(
    org_id: str = Query(default="default", pattern=_ORG_ID_PATTERN),
) -> dict[str, object]:
    """Conversion + MRR snapshot for founder dashboard, scoped to org_id.

    Defaults to "default" org — does NOT aggregate across orgs (cross-tenant
    leak prevention). Pass org_id explicitly for multi-tenant deployments.
    """
    pilots = _org_filter(_load_pilots(), org_id)
    conversions = _org_filter(_load_conversions(), org_id)
    total_pilots = len(pilots)
    converted_user_ids = {c["user_id"] for c in conversions}
    mrr_vnd = sum(c.get("monthly_vnd", 0) for c in conversions)
    by_tier: dict[str, int] = {}
    for c in conversions:
        by_tier[c.get("tier") or "unknown"] = by_tier.get(c.get("tier") or "unknown", 0) + 1
    return {
        "org_id": org_id,
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
