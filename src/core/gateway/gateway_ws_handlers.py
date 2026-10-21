# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""WebSocket streaming and execution handlers for Mekong Gateway."""

from __future__ import annotations

import asyncio
import contextlib
import json
import queue
from dataclasses import asdict
from typing import Any

from fastapi import HTTPException, WebSocket, WebSocketDisconnect

from src.core.gateway.gateway_helpers import build_human_summary, verify_token
from src.core.gateway.models import CommandResponse, StepSummary
from src.core.gateway.rate_limiter import get_telemetry_hub
from src.core.gateway.streaming import get_mission_streaming_broker
from src.core.orchestrator import OrchestrationResult, RecipeOrchestrator
from src.providers.llm.client import get_client


def build_orchestrator() -> RecipeOrchestrator:
    llm_client = get_client()
    return RecipeOrchestrator(
        llm_client=llm_client if llm_client.is_available else None,
        strict_verification=True,
        enable_rollback=True,
    )


def build_cmd_response(result: OrchestrationResult, goal: str, orchestrator: RecipeOrchestrator) -> CommandResponse:
    steps = [
        StepSummary(
            order=sr.step.order,
            title=sr.step.title,
            passed=sr.verification.passed,
            exit_code=sr.execution.exit_code,
            summary=sr.verification.summary,
        )
        for sr in result.step_results
    ]
    trace = None
    trace_obj = orchestrator.telemetry.get_trace()
    if trace_obj:
        trace = asdict(trace_obj)

    return CommandResponse(
        status=result.status.value, goal=goal, total_steps=result.total_steps,
        completed_steps=result.completed_steps, failed_steps=result.failed_steps,
        success_rate=result.success_rate, errors=result.errors, warnings=result.warnings,
        steps=steps, trace=trace, human_summary=build_human_summary(result),
    )


async def handle_ws_mission(websocket: WebSocket, mission_id: str) -> None:
    await websocket.accept()
    broker = get_mission_streaming_broker()
    hub = get_telemetry_hub()
    subscriber = broker.subscribe(mission_id)
    broker.record_ws_connect()
    hub.record_stream_opened()
    stop_event = asyncio.Event()

    async def event_sender() -> None:
        while not stop_event.is_set():
            try:
                event = await asyncio.to_thread(subscriber.get, timeout=0.5)
                await websocket.send_json(event.to_dict())
            except queue.Empty:
                continue
            except Exception:
                stop_event.set()
                break

    async def command_receiver() -> None:
        while not stop_event.is_set():
            try:
                raw_text = await websocket.receive_text()
                try:
                    msg_data = json.loads(raw_text)
                except Exception:
                    msg_data = {"command": raw_text}
                command = str(msg_data.get("command", "")).strip().lower()
                payload = msg_data.get("payload")
                if payload is not None and not isinstance(payload, dict):
                    payload = {"value": payload}
                ack = broker.handle_command(mission_id, command, payload)
                await websocket.send_json({"type": "command_ack", "command": command, "result": ack})
            except (WebSocketDisconnect, Exception):
                stop_event.set()
                break

    sender_task = asyncio.create_task(event_sender())
    receiver_task = asyncio.create_task(command_receiver())
    try:
        done, pending = await asyncio.wait([sender_task, receiver_task], return_when=asyncio.FIRST_COMPLETED)
        for task in pending:
            task.cancel()
    finally:
        stop_event.set()
        broker.unsubscribe(subscriber)
        broker.record_ws_disconnect()
        hub.record_stream_closed()
        with contextlib.suppress(Exception):
            await websocket.close()


async def handle_ws_execute(websocket: WebSocket) -> None:
    await websocket.accept()
    try:
        data = await websocket.receive_json()
        goal = data.get("goal", "")
        token = data.get("token", "")
        if not goal or not token:
            await websocket.send_json({"type": "error", "message": "Missing goal or token"})
            return
        try:
            verify_token(token)
        except HTTPException as exc:
            await websocket.send_json({"type": "error", "message": exc.detail})
            return
        await websocket.send_json({"type": "status", "message": "Planning..."})
        loop = asyncio.get_running_loop()

        def progress_cb(step_result: Any, current_result: Any) -> None:
            msg = {
                "type": "step", "order": step_result.step.order, "title": step_result.step.title,
                "passed": step_result.verification.passed, "exit_code": step_result.execution.exit_code,
                "summary": step_result.verification.summary, "completed": current_result.completed_steps,
                "total": current_result.total_steps,
            }
            future = asyncio.run_coroutine_threadsafe(websocket.send_json(msg), loop)
            future.result(timeout=10)

        def run_goal() -> tuple[OrchestrationResult, RecipeOrchestrator]:
            orchestrator = build_orchestrator()
            result = orchestrator.run_from_goal(goal, progress_callback=progress_cb)
            return result, orchestrator

        result, _orchestrator = await asyncio.to_thread(run_goal)
        hs = build_human_summary(result)
        await websocket.send_json({
            "type": "complete", "status": result.status.value, "goal": goal,
            "total_steps": result.total_steps, "completed_steps": result.completed_steps,
            "failed_steps": result.failed_steps, "success_rate": result.success_rate,
            "errors": result.errors, "human_summary": {"en": hs.en, "vi": hs.vi},
        })
    except WebSocketDisconnect:
        pass
    except Exception as e:
        with contextlib.suppress(Exception):
            await websocket.send_json({"type": "error", "message": str(e)})


__all__ = [
    "build_cmd_response",
    "build_orchestrator",
    "handle_ws_execute",
    "handle_ws_mission",
]
