"""VN Pilot — poll response route."""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, status

from src.api.vn_pilot_common import (
    PollResponseRequest,
    _append_jsonl,
    _current_iso_week,
    _load_pilots,
    _responses_path,
)

polls_router = APIRouter(tags=["VN Pilot"])


@polls_router.post("/response", status_code=status.HTTP_201_CREATED)
async def poll_response(req: PollResponseRequest) -> dict[str, object]:
    """Capture poll response from Zalo webhook / web form."""
    if not any(p["user_id"] == req.user_id for p in _load_pilots()):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown user_id: {req.user_id}",
        )
    iso_week = req.iso_week or _current_iso_week()
    record = {
        "user_id": req.user_id,
        "score": req.score,
        "comment": req.comment,
        "recorded_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "iso_week": iso_week,
    }
    _append_jsonl(_responses_path(), record)
    return {
        "recorded": True,
        "user_id": req.user_id,
        "score": req.score,
        "iso_week": iso_week,
        "low_nps_alert": req.score < 4,
    }
