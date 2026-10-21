# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Gateway mission in-memory store, hybrid router executor, and SSE generator."""
from __future__ import annotations

import asyncio
import json
import logging
import threading
from datetime import datetime, timezone
from typing import AsyncGenerator

logger = logging.getLogger(__name__)

# In-memory mission store (shared with other modules via import)
MISSION_STORE: dict[str, dict] = {}
_MISSION_STORE_MAX = 1000
_MISSION_STORE_LOCK = threading.Lock()
_MISSION_ASYNC_LOCK = asyncio.Lock()


async def _run_hybrid_router(mission_id: str, goal: str, tenant_id: str) -> None:
    """Background task: run hybrid LLM router for a mission."""
    try:
        from src.core.hybrid_router import route_and_execute

        result = await route_and_execute(goal=goal, tenant_id=tenant_id, mission_id=mission_id)

        async with _MISSION_ASYNC_LOCK:
            if mission_id in MISSION_STORE:
                MISSION_STORE[mission_id]["status"] = "completed" if result.success else "failed"
                MISSION_STORE[mission_id]["events"].append({
                    "event_type": "mission.completed" if result.success else "mission.failed",
                    "mission_id": mission_id,
                    "data": {
                        "model_used": result.model_used,
                        "mcu_charged": result.mcu_charged,
                        "output_preview": result.output[:200] if result.output else "",
                    },
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                })
    except Exception as e:
        logger.error("Hybrid router failed for mission %s: %s", mission_id, e)
        if mission_id in MISSION_STORE:
            MISSION_STORE[mission_id]["status"] = "failed"


async def _mission_event_generator(mission_id: str) -> AsyncGenerator[str, None]:
    """Yield SSE events for real-time mission progress."""
    mission = MISSION_STORE[mission_id]
    max_poll_duration = 300
    start_time = asyncio.get_event_loop().time()

    try:
        event = {
            "event_type": "mission.state",
            "mission_id": mission_id,
            "data": {
                "status": mission["status"],
                "goal": mission["goal"],
                "steps": mission.get("steps", []),
            },
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        yield f"data: {json.dumps(event)}\n\n"

        last_event_idx = 0
        while True:
            if (asyncio.get_event_loop().time() - start_time) > max_poll_duration:
                break

            events = mission.get("events", [])
            if len(events) > last_event_idx:
                for evt in events[last_event_idx:]:
                    yield f"data: {json.dumps(evt)}\n\n"
                last_event_idx = len(events)

            if mission["status"] in ["completed", "failed", "cancelled"]:
                final_event = {
                    "event_type": f"mission.{mission['status']}",
                    "mission_id": mission_id,
                    "data": {"final_state": mission},
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                yield f"data: {json.dumps(final_event)}\n\n"
                break

            await asyncio.sleep(0.5)

    except asyncio.CancelledError:
        logger.info("Stream cancelled for mission %s", mission_id)
    except Exception as e:
        logger.error("Stream error for mission %s: %s", mission_id, str(e))
        error_evt = {
            "event_type": "mission.error",
            "mission_id": mission_id,
            "data": {"error": str(e)},
        }
        yield f"data: {json.dumps(error_evt)}\n\n"


__all__ = [
    "MISSION_STORE",
    "_MISSION_STORE_MAX",
    "_MISSION_STORE_LOCK",
    "_MISSION_ASYNC_LOCK",
    "_run_hybrid_router",
    "_mission_event_generator",
]
