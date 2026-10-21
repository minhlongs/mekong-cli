"""FastAPI sub-router for Invited Pilot Cohort operations (`/v1/pilot/*`).

Exposes:
- POST /v1/pilot/invites
- POST /v1/pilot/redeem
- POST /v1/pilot/missions
- POST /v1/pilot/missions/{mission_id}/feedback
- GET  /v1/pilot/kpis
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

import src.api.vn_pilot_state as _state
from src.core.pilot_client import PilotClient, PilotClientError

invited_pilot_router = APIRouter()


class IssueInviteRequest(BaseModel):
    partner_label: str = Field(default="Pilot Partner", min_length=1, max_length=120)
    max_invites: int = Field(default=5, ge=1, le=5)


class RedeemInviteRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    invite_code: str = Field(..., min_length=6, max_length=64)


class SubmitPilotMissionRequest(BaseModel):
    goal: str = Field(..., min_length=1, max_length=4000)
    mode: str = Field(default="llm", min_length=1, max_length=32)


class SubmitPilotFeedbackRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    comment: str = Field(default="", max_length=2000)


def _client_for_request(request: Request) -> PilotClient:
    override_state = request.headers.get("x-pilot-state-file") or os.environ.get("MEKONG_PILOT_STATE_PATH")
    state_path = Path(override_state) if override_state else (_state.CONFIG_DIR / "invited_pilot_state.json")
    return PilotClient(state_path=state_path, offline=True)


def _raise_http_for_pilot_error(exc: PilotClientError) -> None:
    status_map = {
        "PILOT_INVITE_CAP_REACHED": 409,
        "PILOT_INVITE_INVALID": 403,
        "PILOT_INVITE_ALREADY_REDEEMED": 409,
        "PILOT_LLM_ONLY": 422,
        "VALIDATION_ERROR": 400,
        "NOT_FOUND": 404,
    }
    status_code = status_map.get(exc.code, 400)
    raise HTTPException(
        status_code=status_code,
        detail={"code": exc.code, "message": str(exc)},
    ) from exc


@invited_pilot_router.post("/invites", status_code=201)
def issue_pilot_invite(payload: IssueInviteRequest, request: Request) -> dict[str, Any]:
    """Issue a single-use SHA-256 hashed pilot invite code (capped at 5 partners)."""
    client = _client_for_request(request)
    try:
        return client.issue_invite(partner_label=payload.partner_label, max_invites=payload.max_invites)
    except PilotClientError as exc:
        _raise_http_for_pilot_error(exc)
        raise  # unreachable


@invited_pilot_router.post("/redeem", status_code=201)
def redeem_pilot_invite(payload: RedeemInviteRequest, request: Request) -> dict[str, Any]:
    """Redeem a single-use pilot invite code and provision a 10-credit pilot tenant."""
    client = _client_for_request(request)
    try:
        return client.redeem_invite(name=payload.name, invite_code=payload.invite_code)
    except PilotClientError as exc:
        _raise_http_for_pilot_error(exc)
        raise


@invited_pilot_router.post("/missions", status_code=201)
def submit_pilot_mission(payload: SubmitPilotMissionRequest, request: Request) -> dict[str, Any]:
    """Submit a synthetic-data LLM-only mission to the pilot cohort."""
    client = _client_for_request(request)
    try:
        return client.submit_mission(goal=payload.goal, mode=payload.mode)
    except PilotClientError as exc:
        _raise_http_for_pilot_error(exc)
        raise


@invited_pilot_router.post("/missions/{mission_id}/feedback")
def submit_pilot_feedback(
    mission_id: str,
    payload: SubmitPilotFeedbackRequest,
    request: Request,
) -> dict[str, Any]:
    """Submit 1–5 star partner feedback within the 48-hour SLA window."""
    client = _client_for_request(request)
    try:
        return client.submit_feedback(
            mission_id=mission_id,
            rating=payload.rating,
            comment=payload.comment,
        )
    except PilotClientError as exc:
        _raise_http_for_pilot_error(exc)
        raise


@invited_pilot_router.get("/kpis")
def get_pilot_kpis(request: Request) -> dict[str, Any]:
    """Return operator KPI telemetry (5 partners, 5 missions/partner/week, 48h feedback SLA)."""
    client = _client_for_request(request)
    return client.get_kpis()
