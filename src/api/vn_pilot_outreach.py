"""VN Pilot Outreach — minimal contact tracking API.

Endpoints:
- POST /v1/pilot/outreach/log   — record a contact attempt
- GET  /v1/pilot/outreach/{user_id} — get last contact + outreach history

Storage: ~/.mekong/outreach.jsonl (append-only, one event per line).
No authentication required — this is for internal operational use.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

import src.api.vn_pilot_common as _common
import src.api.vn_pilot_state as _state

outreach_router = APIRouter()


class OutreachLogRequest(BaseModel):
    user_id: str = Field(min_length=4, max_length=50)
    channel: str = Field(default="zalo", pattern=r"^(zalo|phone|email|other)$")
    day_offset: int = Field(default=7, ge=3, le=14, description="Days since signup when contacting")
    outcome: str = Field(default="sent", description="sent|no_reply|interested|not_interested|callback")


class OutreachLogResponse(BaseModel):
    user_id: str
    channel: str
    day_offset: int
    outcome: str
    ts: str


class OutreachHistoryResponse(BaseModel):
    user_id: str
    total_contacts: int
    history: list[dict]


def _outreach_path() -> Path:
    return _state.CONFIG_DIR / "outreach.jsonl"


def _load_outreach() -> list[dict]:
    return _common._load_jsonl(_outreach_path())


def _append_outreach(record: dict) -> None:
    record.setdefault("ts", datetime.now(timezone.utc).isoformat(timespec="microseconds"))
    _common._append_jsonl(_outreach_path(), record)


@outreach_router.post(
    "/outreach/log",
    response_model=OutreachLogResponse,
    summary="Log an outreach contact attempt for a pilot user",
)
async def log_outreach(req: OutreachLogRequest) -> OutreachLogResponse:
    if not req.user_id.startswith("opc_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id must start with 'opc_'",
        )

    pilots = _common._load_pilots()
    if not any(p.get("user_id") == req.user_id for p in pilots):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pilot user not found",
        )

    record = {
        "type": "contact",
        "user_id": req.user_id,
        "channel": req.channel,
        "day_offset": req.day_offset,
        "outcome": req.outcome,
    }
    _append_outreach(record)
    return OutreachLogResponse(
        user_id=req.user_id,
        channel=req.channel,
        day_offset=req.day_offset,
        outcome=req.outcome,
        ts=record["ts"],
    )


@outreach_router.get(
    "/outreach/{user_id}",
    response_model=OutreachHistoryResponse,
    summary="Get outreach history for a pilot user",
)
async def get_outreach(user_id: str) -> OutreachHistoryResponse:
    if not user_id.startswith("opc_"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="user_id must start with 'opc_'",
        )

    pilots = _common._load_pilots()
    if not any(p.get("user_id") == user_id for p in pilots):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Pilot user not found",
        )

    events = [e for e in _load_outreach() if e.get("user_id") == user_id and e.get("type") == "contact"]
    events.sort(key=lambda e: e.get("ts", ""), reverse=True)

    return OutreachHistoryResponse(
        user_id=user_id,
        total_contacts=len(events),
        history=[
            {
                "ts": e.get("ts", ""),
                "channel": e.get("channel", "?"),
                "day_offset": e.get("day_offset"),
                "outcome": e.get("outcome", "?"),
            }
            for e in events
        ],
    )
