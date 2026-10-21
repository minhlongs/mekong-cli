# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong CLI - Gateway Server (OpenClaw Hybrid Commander) entrypoint and app factory."""

from __future__ import annotations

import asyncio
import contextlib
import os
import threading
from collections.abc import AsyncGenerator
from dataclasses import asdict
from typing import Any

from fastapi import FastAPI, HTTPException, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from src.core.event_bus import get_event_bus
from src.core.gateway.gateway_dash_router import (
    GATEWAY_CONFIG, PRESET_ACTIONS, VERSION, dash_router,
)
from src.core.gateway.gateway_gov_router import gov_router
from src.core.gateway.gateway_helpers import (
    build_human_summary, require_swarm_token, scan_projects, verify_token,
)
from src.core.gateway.gateway_recipe_agi_router import router as recipe_agi_router
from src.core.gateway.gateway_sub_router import sub_router
from src.core.gateway.gateway_ws_handlers import (
    build_cmd_response, build_orchestrator, handle_ws_execute, handle_ws_mission,
)
from src.core.gateway.models import (  # noqa: F401
    AutoRecipeInfo, CommandRequest, CommandResponse, GovernanceCheckRequest,
    HaltRequest, HealthResponse, HumanSummary, MemoryEntryInfo, MemoryStatsResponse,
    NLUParseRequest, NLUParseResponse, PresetAction, ProjectInfo, RecipeGenerateRequest,
    RecipeGenerateResponse, RecipeValidateRequest, RecipeValidateResponse,
    ScheduleAddRequest, ScheduleJobInfo, StepSummary, SwarmDispatchRequest,
    SwarmNodeInfo, SwarmRegisterRequest,
)
from src.core.gateway.rate_limiter import get_telemetry_hub
from src.core.gateway.streaming import stream_events_sse

_build_cmd_response = build_cmd_response
_build_orchestrator = build_orchestrator
_scan_projects = scan_projects


def create_app() -> FastAPI:
    """Create and configure the gateway FastAPI application."""
    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
        telegram_token = os.environ.get("MEKONG_TELEGRAM_TOKEN", "")
        app.state.bot = None
        if telegram_token:
            try:
                from src.core.notifier import Notifier
                from src.core.telegram_bot import MekongBot
                app.state.bot = MekongBot(token=telegram_token)
                Notifier(bot=app.state.bot).subscribe(get_event_bus())
                asyncio.create_task(app.state.bot.start())
            except ImportError:
                pass
        yield
        if app.state.bot:
            await app.state.bot.stop()

    gateway = FastAPI(
        title="Mekong Gateway",
        description="OpenClaw Hybrid Commander — Cloud Ra Lenh, Local Thuc Thi",
        version=VERSION,
        lifespan=lifespan,
    )
    _allowed_origins = [
        o.strip()
        for o in os.environ.get("CORS_ALLOWED_ORIGINS", "http://localhost:3000,http://localhost:8080").split(",")
        if o.strip()
    ]
    gateway.add_middleware(
        CORSMiddleware,
        allow_origins=_allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @gateway.get("/api/v1/missions/{mission_id}/stream")
    def sse_mission_stream(mission_id: str, request: Request) -> StreamingResponse:
        hub = get_telemetry_hub()
        hub.record_stream_opened()
        since_cursor = request.query_params.get("since_cursor")
        stop_event = threading.Event()

        def sync_generator():
            try:
                for chunk in stream_events_sse(mission_id, since_cursor=since_cursor, heartbeat_interval=15.0, stop_event=stop_event):
                    yield chunk
            finally:
                stop_event.set()
                hub.record_stream_closed()

        return StreamingResponse(
            sync_generator(), media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
        )

    @gateway.websocket("/ws/missions/{mission_id}")
    async def ws_mission_endpoint(websocket: WebSocket, mission_id: str) -> None:
        await handle_ws_mission(websocket, mission_id)

    @gateway.post("/cmd")
    def execute_command(req: CommandRequest) -> CommandResponse:
        verify_token(req.token)
        try:
            orchestrator = _build_orchestrator()
            result = orchestrator.run_from_goal(req.goal)
            return _build_cmd_response(result, req.goal, orchestrator)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @gateway.websocket("/ws")
    async def ws_execute(websocket: WebSocket) -> None:
        await handle_ws_execute(websocket)

    @gateway.get("/telegram/status")
    def telegram_status() -> dict[str, Any]:
        bot = getattr(gateway.state, "bot", None)
        return {"running": bot.is_running() if bot else False, "configured": bool(os.environ.get("MEKONG_TELEGRAM_TOKEN", ""))}

    gateway.include_router(dash_router)
    gateway.include_router(sub_router)
    gateway.include_router(recipe_agi_router)
    gateway.include_router(gov_router)
    return gateway


app = create_app()

from src.api.raas_router import router as _raas_router  # noqa: E402
app.include_router(_raas_router)
from src.api.tier_config_routes import router as _tier_config_router  # noqa: E402
app.include_router(_tier_config_router)
from src.api.quota_status_endpoints import quota_router as _quota_router  # noqa: E402
app.include_router(_quota_router)

__all__ = [
    "GATEWAY_CONFIG", "PRESET_ACTIONS", "VERSION", "AutoRecipeInfo",
    "CommandRequest", "CommandResponse", "GovernanceCheckRequest", "HaltRequest",
    "HealthResponse", "HumanSummary", "MemoryEntryInfo", "MemoryStatsResponse",
    "NLUParseRequest", "NLUParseResponse", "PresetAction", "ProjectInfo",
    "RecipeGenerateRequest", "RecipeGenerateResponse", "RecipeValidateRequest",
    "RecipeValidateResponse", "ScheduleAddRequest", "ScheduleJobInfo",
    "StepSummary", "SwarmDispatchRequest", "SwarmNodeInfo", "SwarmRegisterRequest",
    "_build_cmd_response", "_build_orchestrator", "_scan_projects", "app",
    "asdict", "build_human_summary", "create_app", "require_swarm_token", "verify_token",
]
