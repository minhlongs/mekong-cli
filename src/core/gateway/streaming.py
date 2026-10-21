# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Real-time dual streaming engine facade for Mekong Gateway."""

from __future__ import annotations

import json
import logging
import queue
import socket
import threading
import time
from typing import Iterator, Optional

from .streaming_broker import (
    MissionStreamingBroker,
    get_mission_broker,
    get_mission_streaming_broker,
    set_mission_streaming_broker,
)
from .streaming_types import (
    ControlCommand,
    EventSubscriber,
    MissionControl,
    StreamEvent,
    StreamEventType,
)
from .streaming_ws import (
    OPCODE_BINARY,
    OPCODE_CLOSE,
    OPCODE_CONT,
    OPCODE_PING,
    OPCODE_PONG,
    OPCODE_TEXT,
    WEBSOCKET_GUID,
    WebSocketFrameParser,
)

logger = logging.getLogger(__name__)


def format_sse_event(event: StreamEvent) -> str:
    """Format a StreamEvent into an RFC-compliant SSE frame chunk."""
    return event.to_sse_frame()


def stream_events_sse(
    mission_id: str,
    since_cursor: Optional[str] = None,
    heartbeat_interval: float = 15.0,
    broker: Optional[MissionStreamingBroker] = None,
    stop_event: Optional[threading.Event] = None,
) -> Iterator[str]:
    """Generator yielding SSE frames and periodic heartbeat comment pings."""
    if broker is None:
        broker = get_mission_streaming_broker()

    subscriber = broker.subscribe(mission_id, since_cursor=since_cursor)
    last_heartbeat = time.time()

    try:
        while stop_event is None or not stop_event.is_set():
            try:
                event = subscriber.get(timeout=min(1.0, heartbeat_interval))
                yield format_sse_event(event)
                last_heartbeat = time.time()
            except queue.Empty:
                now = time.time()
                if now - last_heartbeat >= heartbeat_interval:
                    yield ": ping\n\n"
                    last_heartbeat = now
    finally:
        broker.unsubscribe(subscriber)


def handle_websocket_duplex(
    sock: socket.socket,
    mission_id: str,
    broker: Optional[MissionStreamingBroker] = None,
    stop_event: Optional[threading.Event] = None,
) -> None:
    """Duplex RFC 6455 WebSocket session over a connected socket."""
    if broker is None:
        broker = get_mission_streaming_broker()

    if stop_event is None:
        stop_event = threading.Event()

    broker.record_ws_connect()
    subscriber = broker.subscribe(mission_id)
    sock.settimeout(1.0)

    def _writer() -> None:
        try:
            while not stop_event.is_set():
                try:
                    event = subscriber.get(timeout=0.5)
                    payload_json = json.dumps(event.to_dict())
                    frame = WebSocketFrameParser.encode_frame(payload_json, opcode=OPCODE_TEXT)
                    sock.sendall(frame)
                except queue.Empty:
                    continue
                except (BrokenPipeError, ConnectionResetError, OSError):
                    stop_event.set()
                    break
        finally:
            pass

    writer_thread = threading.Thread(target=_writer, daemon=True)
    writer_thread.start()

    recv_buffer = bytearray()
    try:
        while not stop_event.is_set():
            try:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                recv_buffer.extend(chunk)
            except socket.timeout:
                continue
            except (BrokenPipeError, ConnectionResetError, OSError):
                break

            while recv_buffer:
                opcode, payload, remainder = WebSocketFrameParser.decode_frame(bytes(recv_buffer))
                if opcode is None or payload is None:
                    break
                recv_buffer = bytearray(remainder)

                if WebSocketFrameParser.is_control_frame(opcode):
                    reply, should_close = WebSocketFrameParser.handle_control_frame(opcode, payload)
                    if reply:
                        try:
                            sock.sendall(reply)
                        except OSError:
                            pass
                    if should_close:
                        stop_event.set()
                        break
                elif opcode == OPCODE_TEXT:
                    try:
                        WebSocketFrameParser.process_client_message(payload, mission_id, broker)
                    except Exception as e:
                        logger.warning(f"Error handling client command: {e}")
    finally:
        stop_event.set()
        broker.unsubscribe(subscriber)
        broker.record_ws_disconnect()
        try:
            sock.close()
        except OSError:
            pass


__all__ = [
    "ControlCommand",
    "EventSubscriber",
    "MissionControl",
    "MissionStreamingBroker",
    "OPCODE_BINARY",
    "OPCODE_CLOSE",
    "OPCODE_CONT",
    "OPCODE_PING",
    "OPCODE_PONG",
    "OPCODE_TEXT",
    "StreamEvent",
    "StreamEventType",
    "WEBSOCKET_GUID",
    "WebSocketFrameParser",
    "format_sse_event",
    "get_mission_broker",
    "get_mission_streaming_broker",
    "handle_websocket_duplex",
    "set_mission_streaming_broker",
    "stream_events_sse",
]
