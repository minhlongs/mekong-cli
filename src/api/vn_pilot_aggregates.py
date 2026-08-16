# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""VN Pilot — stats, recent, and health aggregate routes."""
from __future__ import annotations

from fastapi import APIRouter, Query

from src.api.vn_pilot_common import (
    _count_by_key,
    _load_conversions,
    _load_pilots,
    _load_responses,
    _org_filter,
)
import src.api.vn_pilot_state as _state

aggregates_router = APIRouter(tags=["VN Pilot"])


@aggregates_router.get("/health")
async def health() -> dict[str, object]:
    """Health check. Includes per_org pilot count breakdown."""
    pilots = _load_pilots()
    per_org: dict[str, int] = {}
    for p in pilots:
        oid = p.get("org_id", "default")
        per_org[oid] = per_org.get(oid, 0) + 1
    return {"status": "ok", "service": "vn-pilot", "per_org": per_org}


@aggregates_router.get("/stats")
async def stats(org_id: str = Query(default="default")) -> dict[str, object]:
    """Aggregate stats — for founder dashboard, scoped to org_id."""
    all_pilots = _load_pilots()
    pilots = _org_filter(all_pilots, org_id)
    active = [p for p in pilots if p.get("status", "active") == "active"]
    pilot_user_ids = {p.get("user_id") for p in pilots}
    converted_user_ids = {c["user_id"] for c in _load_conversions()} & pilot_user_ids
    trial = [p for p in active if p.get("user_id") not in converted_user_ids]
    return {
        "total_pilots": len(pilots),
        "active_pilots": len(active),
        "converted_pilots": len(converted_user_ids),
        "trial_pilots": len(trial),
        "capacity_remaining": max(0, _state.MAX_PILOTS - len(pilots)),
        "by_type": _count_by_key(pilots, "business_type"),
        "by_source": _count_by_key(pilots, "source"),
    }


@aggregates_router.get("/recent")
async def recent(
    limit: int = Query(default=10, ge=1, le=100),
    org_id: str = Query(default="default"),
) -> dict[str, list]:
    """Recent signups + NPS responses for founder dashboard. No PII exposed."""
    pilots = sorted(
        _org_filter(_load_pilots(), org_id),
        key=lambda p: p.get("onboarded_at", ""),
        reverse=True,
    )
    responses = sorted(_load_responses(), key=lambda r: r.get("recorded_at", ""), reverse=True)
    return {
        "signups": [
            {
                "business_type": p.get("business_type"),
                "city": p.get("city"),
                "source": p.get("source"),
                "onboarded_at": p.get("onboarded_at"),
            }
            for p in pilots[:limit]
        ],
        "nps_responses": [
            {
                "score": r.get("score"),
                "iso_week": r.get("iso_week"),
                "recorded_at": r.get("recorded_at"),
                "comment_preview": (r.get("comment") or "")[:80],
            }
            for r in responses[:limit]
        ],
    }
