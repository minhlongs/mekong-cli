# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Gateway mission create, status, and stream endpoints."""
from __future__ import annotations

import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Literal, cast

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import StreamingResponse

from src.api.gateway_mission_executor import (
    MISSION_STORE, _MISSION_ASYNC_LOCK, _MISSION_STORE_LOCK,
    _MISSION_STORE_MAX, _mission_event_generator, _run_hybrid_router,
)
from src.api.gateway_models import (
    CreateMissionRequest, CreateMissionResponse, MissionStatusResponse,
)
from src.core.error_responses import ErrorCode, error_response
from src.core.gateway_api import MissionRequest, create_mission
from src.core.input_validation import (
    validate_enum_value, validate_required, validate_string_length, validate_url,
)
from src.middleware.license_gate import license_gate

logger = logging.getLogger(__name__)


def _license_gate_required() -> bool:
    """Whether the license gate must run for this request.

    Mirrors the test-detection convention used by the other auth dependencies:
    only pytest or CI may disable the gate. A stray LICENSE_GATE_ENFORCE=0 in a
    production shell is ignored, so the paywall cannot be opened by an env var.
    """
    if os.environ.get("PYTEST_CURRENT_TEST") or os.environ.get("CI"):
        return os.environ.get("LICENSE_GATE_ENFORCE", "0") == "1"
    return True

router = APIRouter(prefix="/v1", tags=["Missions"])


@router.post("/missions", response_model=CreateMissionResponse)
async def create_mission_endpoint(
    request: CreateMissionRequest,
    background_tasks: BackgroundTasks,
    http_request: Request,
) -> CreateMissionResponse:
    """Create a new mission from AgencyOS."""
    request_id = str(uuid.uuid4())

    # The gate may be skipped only while testing, so a stray env var in
    # production can never open the paywall.
    if _license_gate_required():
        request.tenant_id = await license_gate(http_request)

    error = (
        validate_required(request.goal, "goal")
        or validate_required(request.tenant_id, "tenant_id")
        or validate_string_length(request.goal, "goal", min_len=1, max_len=5000)
        or validate_enum_value(
            request.priority, "priority", ["low", "normal", "high"],
            f"Invalid priority '{request.priority}'. Use: low, normal, high",
        )
    )
    if error:
        raise HTTPException(status_code=400, detail=error.to_dict())

    try:
        mission_request = MissionRequest(
            goal=request.goal.strip(),
            tenant_id=request.tenant_id.strip(),
            webhook_url=request.webhook_url.strip() if request.webhook_url else None,
            priority=cast(Literal["low", "normal", "high"], request.priority),
            metadata=request.metadata or {},
        )

        if mission_request.webhook_url:
            error = validate_url(mission_request.webhook_url, "webhook_url")
            if error:
                raise HTTPException(status_code=400, detail=error.to_dict())

        response = create_mission(mission_request)
        mission_id = response.mission_id

        with _MISSION_STORE_LOCK:
            if len(MISSION_STORE) >= _MISSION_STORE_MAX:
                del MISSION_STORE[next(iter(MISSION_STORE))]
            MISSION_STORE[mission_id] = {
                "goal": request.goal, "tenant_id": request.tenant_id,
                "webhook_url": request.webhook_url, "status": response.status.value,
                "created_at": response.created_at, "steps": [], "events": [],
            }

        background_tasks.add_task(
            _run_hybrid_router, mission_id=mission_id, goal=request.goal, tenant_id=request.tenant_id
        )
        logger.info("Mission %s created for tenant %s", mission_id, request.tenant_id)
        return CreateMissionResponse(
            mission_id=mission_id, status=response.status.value, created_at=response.created_at,
            estimated_steps=response.estimated_steps,
            stream_url=response.stream_url or f"/v1/missions/{mission_id}/stream",
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("Mission creation failed: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "Failed to create mission", "request_id": request_id},
        )


@router.get("/missions/{mission_id}", response_model=MissionStatusResponse)
async def get_mission_status(mission_id: str) -> MissionStatusResponse:
    """Get current mission status."""
    if not mission_id or not mission_id.strip():
        raise HTTPException(
            status_code=400, detail={"error": "INVALID_INPUT", "message": "Mission ID cannot be empty"}
        )
    if mission_id not in MISSION_STORE:
        raise HTTPException(status_code=404, detail="Mission not found")

    mission = MISSION_STORE[mission_id]
    steps = mission.get("steps", [])
    return MissionStatusResponse(
        mission_id=mission_id, status=mission["status"], goal=mission["goal"],
        tenant_id=mission["tenant_id"], created_at=mission["created_at"],
        updated_at=datetime.now(timezone.utc).isoformat(), steps_total=len(steps),
        steps_completed=sum(1 for s in steps if s.get("status") == "completed"),
    )


@router.get("/missions/{mission_id}/stream")
async def stream_mission(mission_id: str) -> StreamingResponse:
    """SSE stream for real-time mission progress."""
    if not mission_id or not mission_id.strip():
        raise HTTPException(
            status_code=400,
            detail=error_response(ErrorCode.MISSING_FIELD, "Mission ID is required").to_dict(),
        )
    if mission_id not in MISSION_STORE:
        raise HTTPException(status_code=404, detail="Mission not found")

    return StreamingResponse(
        _mission_event_generator(mission_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )


__all__ = [
    "MISSION_STORE", "_MISSION_ASYNC_LOCK", "_MISSION_STORE_LOCK", "_MISSION_STORE_MAX",
    "_mission_event_generator", "_run_hybrid_router", "create_mission_endpoint",
    "get_mission_status", "router", "stream_mission",
]
