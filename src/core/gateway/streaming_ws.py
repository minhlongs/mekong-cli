# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Pure standard-library RFC 6455 WebSocket framing, handshake, and protocol engine."""

from __future__ import annotations

import base64
import hashlib
import logging
import struct
from typing import Optional

from src.core.gateway.streaming_ws_cmds import parse_client_command, process_client_message

logger = logging.getLogger(__name__)

WEBSOCKET_GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
OPCODE_CONT = 0x0
OPCODE_TEXT = 0x1
OPCODE_BINARY = 0x2
OPCODE_CLOSE = 0x8
OPCODE_PING = 0x9
OPCODE_PONG = 0xA


class WebSocketFrameParser:
    """Pure standard-library RFC 6455 WebSocket framing, handshake, and control protocol engine."""

    parse_client_command = staticmethod(parse_client_command)
    process_client_message = staticmethod(process_client_message)

    @staticmethod
    def compute_handshake_accept(sec_websocket_key: str) -> str:
        raw = (sec_websocket_key.strip() + WEBSOCKET_GUID).encode("ascii")
        return base64.b64encode(hashlib.sha1(raw).digest()).decode("ascii")

    @staticmethod
    def build_handshake_response(sec_websocket_key: str) -> bytes:
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
        if len(data) < 2:
            return None, None, data

        b0 = data[0]
        b1 = data[1]
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
    def encode_frame(payload: bytes | str, opcode: int = OPCODE_TEXT, fin: bool = True) -> bytes:
        data = payload if isinstance(payload, bytes) else str(payload).encode("utf-8")
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
        payload: bytes | str, opcode: int = OPCODE_TEXT, mask: bytes = b"\x12\x34\x56\x78", fin: bool = True,
    ) -> bytes:
        data = payload if isinstance(payload, bytes) else str(payload).encode("utf-8")
        b0 = (0x80 if fin else 0) | (opcode & 0x0F)
        length = len(data)
        if length <= 125:
            header = struct.pack("!BB", b0, 0x80 | length)
        elif length <= 65535:
            header = struct.pack("!BBH", b0, 0x80 | 126, length)
        else:
            header = struct.pack("!BBQ", b0, 0x80 | 127, length)
        return header + mask + bytes(b ^ mask[i % 4] for i, b in enumerate(data))

    @staticmethod
    def build_ping_frame(payload: bytes = b"") -> bytes:
        return WebSocketFrameParser.encode_frame(payload, opcode=OPCODE_PING)

    @staticmethod
    def build_pong_frame(payload: bytes = b"") -> bytes:
        return WebSocketFrameParser.encode_frame(payload, opcode=OPCODE_PONG)

    @staticmethod
    def build_close_frame(code: int = 1000, reason: str = "") -> bytes:
        return WebSocketFrameParser.encode_frame(struct.pack("!H", code) + reason.encode("utf-8"), opcode=OPCODE_CLOSE)

    @staticmethod
    def is_control_frame(opcode: int) -> bool:
        return opcode >= 0x8

    @staticmethod
    def handle_control_frame(opcode: int, payload: bytes) -> tuple[Optional[bytes], bool]:
        if opcode == OPCODE_CLOSE:
            code = struct.unpack("!H", payload[:2])[0] if len(payload) >= 2 else 1000
            reason = payload[2:].decode("utf-8", errors="replace") if len(payload) > 2 else ""
            return WebSocketFrameParser.build_close_frame(code, reason), True
        if opcode == OPCODE_PING:
            return WebSocketFrameParser.build_pong_frame(payload), False
        return None, False


__all__ = [
    "OPCODE_BINARY", "OPCODE_CLOSE", "OPCODE_CONT", "OPCODE_PING",
    "OPCODE_PONG", "OPCODE_TEXT", "WEBSOCKET_GUID", "WebSocketFrameParser",
]
