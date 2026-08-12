"""Async WebSocket client for OpenOPC Office UI (Tab OPC realtime)."""

from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Any, Awaitable, Callable

import websockets

# Inbound envelope types we care about
WS_URL = "ws://127.0.0.1:18790/ws"

EventHandler = Callable[[dict[str, Any]], Awaitable[None]]


@dataclass
class WSState:
    """Current snapshot + recent events from the OPC server."""

    snapshot: dict[str, Any] = field(default_factory=dict)
    events: list[dict[str, Any]] = field(default_factory=list)
    connected: bool = False
    last_error: str = ""
    latency_ms: int = 0


class OpcWSClient:
    """WebSocket client: connects, receives snapshot + event stream, sends replies.

    Designed for Textual worker usage: start() runs the read loop; UI reads
    self.state; replies via send().
    """

    def __init__(
        self,
        url: str = WS_URL,
        on_snapshot: EventHandler | None = None,
        on_event: EventHandler | None = None,
    ) -> None:
        self.url = url
        self.state = WSState()
        self._on_snapshot = on_snapshot
        self._on_event = on_event
        self._ws: Any = None
        self._running = False
        self._ping_task: asyncio.Task[Any] | None = None

    async def connect(self) -> None:
        """Connect + receive initial snapshot. Raises on failure (caller retries)."""
        self._ws = await websockets.connect(self.url, open_timeout=10, ping_interval=20)
        self.state.connected = True
        self.state.last_error = ""
        # initial messages: snapshot, project_index_push, collab_sync_push, org_info
        for _ in range(8):
            msg = await asyncio.wait_for(self._ws.recv(), timeout=15)
            data = json.loads(msg)
            if data.get("type") == "snapshot":
                self.state.snapshot = data.get("payload") or {}
                if self._on_snapshot:
                    await self._on_snapshot(self.state.snapshot)
                break

    async def run(self) -> None:
        """Read loop — call in a worker; exits on disconnect."""
        self._ping_task = asyncio.create_task(self._ping_loop())
        try:
            async for raw in self._ws:
                try:
                    data = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                etype = data.get("type", "")
                if etype == "pong":
                    continue
                if etype in {"event", "session_message", "chat_new_message", "collab_sync_push"}:
                    payload = data.get("payload") or {}
                    if etype == "collab_sync_push":
                        continue  # noisy; skip for v1
                    if etype == "session_message":
                        payload = data  # session_message carries fields at top level
                    entry = {"type": etype, "payload": payload, "ts": time.time()}
                    self.state.events.append(entry)
                    self.state.events = self.state.events[-200:]
                    if self._on_event:
                        await self._on_event(entry)
        finally:
            self.state.connected = False
            if self._ping_task:
                self._ping_task.cancel()

    async def _ping_loop(self) -> None:
        while self._ws is not None:
            try:
                start = time.monotonic()
                await self._ws.send(json.dumps({"type": "ping", "ts": time.time()}))
                await asyncio.sleep(15)
                self.state.latency_ms = int((time.monotonic() - start) * 1000)
            except Exception:
                break

    async def send_session_message(
        self, task_id: str, content: str, reply_metadata: dict[str, Any] | None = None
    ) -> None:
        """Send a user message / escalation reply to a task session."""
        if self._ws is None:
            raise RuntimeError("not connected")
        body: dict[str, Any] = {
            "type": "session_send",
            "task_id": task_id,
            "content": content,
            "client_message_id": f"tui-{time.time_ns()}",
        }
        if reply_metadata:
            body["reply_metadata"] = reply_metadata
        await self._ws.send(json.dumps(body))

    async def close(self) -> None:
        self._running = False
        if self._ping_task:
            self._ping_task.cancel()
        if self._ws is not None:
            await self._ws.close()
            self._ws = None
        self.state.connected = False
