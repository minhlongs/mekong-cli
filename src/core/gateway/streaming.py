# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Real-time dual streaming engine for Mekong Gateway.

Provides standard-library-only pub/sub event streaming via Server-Sent Events (SSE)
and pure RFC 6455 duplex WebSocket streaming with client control commands.
Strictly zero external dependencies (no FastAPI, starlette, requests, httpx, websockets).
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
import queue
import socket
import struct
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, Iterator, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# RFC 6455 Constants
WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
OPCODE_CONT = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


class StreamEventType(str, Enum):
    """Typed stream events emitted across the autonomous agent lifecycle."""

    PLAN_CREATED = "plan_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    CHECKPOINT_CAPTURED = "checkpoint_captured"
    MISSION_COMPLETED = "mission_completed"
    COMMAND_ACK = "command_ack"
    ERROR = "error"
    PING = "ping"
    HEARTBEAT = "heartbeat"


class ControlCommand(str, Enum):
    """Client duplex control commands."""

    PAUSE = "pause"
    RESUME = "resume"
    CANCEL = "cancel"


@dataclass
class StreamEvent:
    """Canonical event model for mission execution streaming."""

    event_id: str
    mission_id: str
    event_type: StreamEventType | str
    data: dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> dict[str, Any]:
        """Convert event to JSON-serializable dictionary."""
        evt_type_val = (
            self.event_type.value
            if isinstance(self.event_type, Enum)
            else str(self.event_type)
        )
        return {
            "event_id": self.event_id,
            "mission_id": self.mission_id,
            "event_type": evt_type_val,
            "timestamp": self.timestamp,
            "data": self.data,
        }

    def to_sse_frame(self) -> str:
        """Format as RFC-compliant Server-Sent Event (SSE) frame."""
        payload = json.dumps(self.to_dict())
        evt_type_val = (
            self.event_type.value
            if isinstance(self.event_type, Enum)
            else str(self.event_type)
        )
        return f"id: {self.event_id}\nevent: {evt_type_val}\ndata: {payload}\n\n"

    def to_sse(self) -> str:
        """Alias for to_sse_frame()."""
        return self.to_sse_frame()


class EventSubscriber:
    """Thread-safe subscriber queue isolating client consumers from publisher."""

    def __init__(
        self,
        subscriber_id: str,
        mission_id: str = "",
        max_buffer: int = 1000,
    ) -> None:
        self.subscriber_id = subscriber_id
        self.mission_id = mission_id
        self.queue: queue.Queue[StreamEvent] = queue.Queue(maxsize=max_buffer)
        self.created_at = time.time()

    def push(self, event: StreamEvent) -> bool:
        """Safe non-blocking push handling bounded queue overflow without publisher stall."""
        try:
            self.queue.put_nowait(event)
            return True
        except queue.Full:
            try:
                # Evict oldest event to make room without blocking publisher
                self.queue.get_nowait()
                self.queue.put_nowait(event)
                return True
            except (queue.Empty, queue.Full):
                return False

    def put(self, event: StreamEvent) -> bool:
        """Alias for push()."""
        return self.push(event)

    def get(self, timeout: float = 1.0) -> StreamEvent:
        """Retrieve next event with timeout."""
        return self.queue.get(timeout=timeout)

    def __hash__(self) -> int:
        return hash(self.subscriber_id)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, EventSubscriber):
            return self.subscriber_id == other.subscriber_id
        return False


class MissionControl:
    """Thread-safe mission control state (pause/resume/cancel)."""

    def __init__(self, mission_id: str) -> None:
        self.mission_id = mission_id
        self._pause_event = threading.Event()
        self._pause_event.set()  # Unpaused initially
        self._cancelled = False
        self._lock = threading.Lock()

    def pause(self) -> None:
        with self._lock:
            self._pause_event.clear()

    def resume(self) -> None:
        with self._lock:
            self._pause_event.set()

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True
            self._pause_event.set()  # Unblock paused workers to terminate

    def is_paused(self) -> bool:
        return not self._pause_event.is_set()

    def is_cancelled(self) -> bool:
        return self._cancelled

    def wait_if_paused(self, timeout: Optional[float] = None) -> bool:
        """Block if paused until resumed or timeout expires."""
        return self._pause_event.wait(timeout=timeout)


class MissionStreamingBroker:
    """Thread-safe in-memory pub/sub broker for real-time mission event streaming."""

    def __init__(self, history_limit: int = 500) -> None:
        self._lock = threading.RLock()
        self._subscribers: dict[str, set[EventSubscriber]] = {}
        self._history: dict[str, deque[StreamEvent]] = {}
        self._controls: dict[str, MissionControl] = {}
        self._history_limit = history_limit
        self._seq = 0
        self._sub_seq = 0
        self._total_events_emitted = 0
        self._active_ws_connections = 0
        self._start_time = time.time()

    def publish(
        self,
        mission_id: str,
        event_type: str | StreamEventType,
        data: dict[str, Any],
    ) -> StreamEvent:
        """Broadcasts event to all active subscribers and stores in ring buffer."""
        if isinstance(event_type, str):
            try:
                typed_event: StreamEventType | str = StreamEventType(event_type.lower())
            except ValueError:
                typed_event = event_type
        else:
            typed_event = event_type

        with self._lock:
            self._seq += 1
            evt_id = f"evt_{int(time.time() * 1000)}_{self._seq}"
            event = StreamEvent(
                event_id=evt_id,
                mission_id=mission_id,
                event_type=typed_event,
                data=data,
                timestamp=time.time(),
            )

            if mission_id not in self._history:
                self._history[mission_id] = deque(maxlen=self._history_limit)
            self._history[mission_id].append(event)
            self._total_events_emitted += 1

            subscribers = list(self._subscribers.get(mission_id, set()))

        for sub in subscribers:
            sub.push(event)

        return event

    def subscribe(
        self,
        mission_id: str,
        since_cursor: Optional[str] = None,
        subscriber_id: Optional[str] = None,
    ) -> EventSubscriber:
        """Registers a new subscriber and replays events if since_cursor is provided."""
        with self._lock:
            self._sub_seq += 1
            sub_id = subscriber_id or f"sub_{int(time.time() * 1000)}_{self._sub_seq}_{id(self)}"
            subscriber = EventSubscriber(subscriber_id=sub_id, mission_id=mission_id)

            if mission_id not in self._subscribers:
                self._subscribers[mission_id] = set()
            self._subscribers[mission_id].add(subscriber)

            if since_cursor is not None:
                history = list(self._history.get(mission_id, []))
                cursor_idx = -1
                for idx, ev in enumerate(history):
                    if ev.event_id == since_cursor:
                        cursor_idx = idx
                        break
                replays = history[cursor_idx + 1 :] if cursor_idx != -1 else history
                for ev in replays:
                    subscriber.push(ev)

        return subscriber

    def unsubscribe(self, subscriber: EventSubscriber) -> None:
        """Cleans up subscriber safely."""
        with self._lock:
            mission_id = subscriber.mission_id
            if mission_id in self._subscribers:
                self._subscribers[mission_id].discard(subscriber)
                if not self._subscribers[mission_id]:
                    del self._subscribers[mission_id]

            # Also check across all sets to guarantee cleanup
            for subs in list(self._subscribers.values()):
                subs.discard(subscriber)

    def get_mission_control(self, mission_id: str) -> MissionControl:
        """Retrieve or create thread-safe MissionControl object."""
        with self._lock:
            if mission_id not in self._controls:
                self._controls[mission_id] = MissionControl(mission_id)
            return self._controls[mission_id]

    def handle_command(
        self,
        mission_id: str,
        command: str,
        payload: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        """Handles client duplex commands (pause, resume, cancel) and emits COMMAND_ACK."""
        cmd_clean = command.strip().lower()
        ctrl = self.get_mission_control(mission_id)

        if cmd_clean == ControlCommand.PAUSE.value:
            ctrl.pause()
            status = "paused"
        elif cmd_clean == ControlCommand.RESUME.value:
            ctrl.resume()
            status = "resumed"
        elif cmd_clean == ControlCommand.CANCEL.value:
            ctrl.cancel()
            status = "cancelled"
        else:
            return {
                "ok": False,
                "error": f"Unknown or unsupported command '{command}'",
                "mission_id": mission_id,
            }

        ack_data = {
            "command": cmd_clean,
            "status": status,
            "mission_id": mission_id,
            "payload": payload or {},
        }
        self.publish(mission_id, StreamEventType.COMMAND_ACK, ack_data)

        return {
            "ok": True,
            "command": cmd_clean,
            "status": status,
            "mission_id": mission_id,
            "payload": payload or {},
        }

    def get_history(self, mission_id: str, limit: int = 50) -> list[StreamEvent]:
        """Returns recent events from the ring buffer up to limit."""
        with self._lock:
            history = list(self._history.get(mission_id, []))
        if limit > 0 and len(history) > limit:
            return history[-limit:]
        return history

    def get_stats(self) -> dict[str, Any]:
        """Returns broker health, uptime, subscriber counts, and connection stats."""
        with self._lock:
            uptime = round(time.time() - self._start_time, 2)
            active_subscribers = sum(len(subs) for subs in self._subscribers.values())
            active_missions = len(self._subscribers)
            return {
                "status": "healthy",
                "uptime": uptime,
                "uptime_seconds": uptime,
                "active_missions": active_missions,
                "active_subscribers": active_subscribers,
                "total_events_emitted": self._total_events_emitted,
                "active_ws_connections": self._active_ws_connections,
            }

    def record_ws_connect(self) -> None:
        """Increment active WebSocket connection count."""
        with self._lock:
            self._active_ws_connections += 1

    def record_ws_disconnect(self) -> None:
        """Decrement active WebSocket connection count."""
        with self._lock:
            self._active_ws_connections = max(0, self._active_ws_connections - 1)

    def reset(self) -> None:
        """Resets all internal broker state (useful for tests)."""
        with self._lock:
            self._subscribers.clear()
            self._history.clear()
            self._controls.clear()
            self._seq = 0
            self._total_events_emitted = 0
            self._active_ws_connections = 0
            self._start_time = time.time()


# Global Singleton Broker
_GLOBAL_BROKER: Optional[MissionStreamingBroker] = None
_BROKER_LOCK = threading.Lock()


def get_mission_streaming_broker() -> MissionStreamingBroker:
    """Retrieve global singleton instance of MissionStreamingBroker."""
    global _GLOBAL_BROKER
    with _BROKER_LOCK:
        if _GLOBAL_BROKER is None:
            _GLOBAL_BROKER = MissionStreamingBroker()
        return _GLOBAL_BROKER


def set_mission_streaming_broker(broker: MissionStreamingBroker) -> None:
    """Override or initialize global MissionStreamingBroker."""
    global _GLOBAL_BROKER
    with _BROKER_LOCK:
        _GLOBAL_BROKER = broker


def get_mission_broker() -> MissionStreamingBroker:
    """Convenience alias for get_mission_streaming_broker()."""
    return get_mission_streaming_broker()


# Server-Sent Events (SSE) Engine
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


# Pure Standard-Library RFC 6455 WebSocket Engine
class WebSocketFrameParser:
    """Pure standard-library RFC 6455 WebSocket framing, handshake, and control protocol engine."""

    @staticmethod
    def compute_handshake_accept(sec_websocket_key: str) -> str:
        """Compute Sec-WebSocket-Accept token per RFC 6455 Section 1.3."""
        raw = (sec_websocket_key.strip() + WEBSOCKET_GUID).encode("ascii")
        return base64.b64encode(hashlib.sha1(raw).digest()).decode("ascii")

    @staticmethod
    def build_handshake_response(sec_websocket_key: str) -> bytes:
        """Build standard HTTP 101 Switching Protocols response bytes."""
        accept = WebSocketFrameParser.compute_handshake_accept(sec_websocket_key)
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        )
        return response.encode("ascii")

    @staticmethod
    def decode_frame(data: bytes) -> tuple[Optional[int], Optional[bytes], bytes]:
        """Decodes an RFC 6455 frame from data buffer.

        Returns (opcode, unmasked_payload, remainder_buffer).
        If incomplete frame, returns (None, None, data).
        """
        if len(data) < 2:
            return None, None, data

        b0 = data[0]
        b1 = data[1]
        fin = bool(b0 & 0x80)
        opcode = b0 & 0x0F
        is_masked = bool(b1 & 0x80)
        payload_len = b1 & 0x7F
        offset = 2

        if payload_len == 126:
            if len(data) < offset + 2:
                return None, None, data
            payload_len = struct.unpack("!H", data[offset : offset + 2])[0]
            offset += 2
        elif payload_len == 127:
            if len(data) < offset + 8:
                return None, None, data
            payload_len = struct.unpack("!Q", data[offset : offset + 8])[0]
            offset += 8

        if is_masked:
            if len(data) < offset + 4:
                return None, None, data
            mask = data[offset : offset + 4]
            offset += 4
        else:
            mask = None

        total_frame_len = offset + payload_len
        if len(data) < total_frame_len:
            return None, None, data

        raw_payload = data[offset:total_frame_len]
        remainder = data[total_frame_len:]

        if is_masked and mask is not None:
            unmasked = bytes(b ^ mask[i % 4] for i, b in enumerate(raw_payload))
            payload = unmasked
        else:
            payload = raw_payload

        return opcode, payload, remainder

    @staticmethod
    def encode_frame(
        payload: bytes | str,
        opcode: int = OPCODE_TEXT,
        fin: bool = True,
    ) -> bytes:
        """Encodes an unmasked server-to-client frame per RFC 6455."""
        if isinstance(payload, str):
            data = payload.encode("utf-8")
        elif isinstance(payload, bytes):
            data = payload
        else:
            data = str(payload).encode("utf-8")

        b0 = (0x80 if fin else 0) | (opcode & 0x0F)
        length = len(data)

        if length <= 125:
            header = struct.pack("!BB", b0, length)
        elif length <= 65535:
            header = struct.pack("!BBH", b0, 126, length)
        else:
            header = struct.pack("!BBQ", b0, 127, length)

        return header + data

    @staticmethod
    def encode_client_frame(
        payload: bytes | str,
        opcode: int = OPCODE_TEXT,
        mask: bytes = b"\x12\x34\x56\x78",
        fin: bool = True,
    ) -> bytes:
        """Encodes a masked client-to-server frame per RFC 6455 (ideal for testing)."""
        if isinstance(payload, str):
            data = payload.encode("utf-8")
        elif isinstance(payload, bytes):
            data = payload
        else:
            data = str(payload).encode("utf-8")

        b0 = (0x80 if fin else 0) | (opcode & 0x0F)
        length = len(data)

        if length <= 125:
            header = struct.pack("!BB", b0, 0x80 | length)
        elif length <= 65535:
            header = struct.pack("!BBH", b0, 0x80 | 126, length)
        else:
            header = struct.pack("!BBQ", b0, 0x80 | 127, length)

        masked_data = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        return header + mask + masked_data

    @staticmethod
    def build_ping_frame(payload: bytes = b"") -> bytes:
        """Build RFC 6455 Ping frame (opcode 0x9)."""
        return WebSocketFrameParser.encode_frame(payload, opcode=OPCODE_PING)

    @staticmethod
    def build_pong_frame(payload: bytes = b"") -> bytes:
        """Build RFC 6455 Pong frame (opcode 0xA)."""
        return WebSocketFrameParser.encode_frame(payload, opcode=OPCODE_PONG)

    @staticmethod
    def build_close_frame(code: int = 1000, reason: str = "") -> bytes:
        """Build RFC 6455 Close frame (opcode 0x8)."""
        payload = struct.pack("!H", code) + reason.encode("utf-8")
        return WebSocketFrameParser.encode_frame(payload, opcode=OPCODE_CLOSE)

    @staticmethod
    def is_control_frame(opcode: int) -> bool:
        """Return True if opcode is a control frame (>= 0x8)."""
        return opcode >= 0x8

    @staticmethod
    def handle_control_frame(
        opcode: int,
        payload: bytes,
    ) -> tuple[Optional[bytes], bool]:
        """Handle control frame and return (response_frame_bytes, should_close)."""
        if opcode == OPCODE_CLOSE:
            code = struct.unpack("!H", payload[:2])[0] if len(payload) >= 2 else 1000
            reason = payload[2:].decode("utf-8", errors="replace") if len(payload) > 2 else ""
            close_reply = WebSocketFrameParser.build_close_frame(code, reason)
            return close_reply, True
        elif opcode == OPCODE_PING:
            pong_reply = WebSocketFrameParser.build_pong_frame(payload)
            return pong_reply, False
        elif opcode == OPCODE_PONG:
            return None, False
        return None, False

    @staticmethod
    def parse_client_command(payload: bytes | str) -> dict[str, Any]:
        """Parse JSON command payload from client."""
        if isinstance(payload, bytes):
            text = payload.decode("utf-8", errors="replace")
        else:
            text = payload
        data = json.loads(text)
        if not isinstance(data, dict):
            raise ValueError("WebSocket payload must be a JSON object")
        return data

    @staticmethod
    def process_client_message(
        payload: bytes | str,
        mission_id: str,
        broker: Optional[MissionStreamingBroker] = None,
    ) -> dict[str, Any]:
        """Parse client command and execute against broker."""
        if broker is None:
            broker = get_mission_streaming_broker()
        data = WebSocketFrameParser.parse_client_command(payload)
        command = str(data.get("command", "")).strip().lower()
        sub_payload = data.get("payload")
        if sub_payload is not None and not isinstance(sub_payload, dict):
            sub_payload = {"value": sub_payload}
        return broker.handle_command(mission_id, command, sub_payload)


def handle_websocket_duplex(
    sock: socket.socket,
    mission_id: str,
    broker: Optional[MissionStreamingBroker] = None,
    stop_event: Optional[threading.Event] = None,
) -> None:
    """Duplex RFC 6455 WebSocket session over a connected socket.

    Streams mission events to the client while listening for and processing
    incoming duplex control commands (pause, resume, cancel).
    """
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
