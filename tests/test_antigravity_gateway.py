# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
tests/test_antigravity_gateway.py — Comprehensive Test Suite for Phase 12.

Phase 12: Production Gateway & Real-Time Event Streaming Hub.
Verifies:
1. TestEventBroker: Pub/sub decoupling, fanout, isolation, cleanup, overflow, typed events, cursor replay.
2. TestSSEStreaming: Standards-compliant SSE framing, generator lifecycle, keep-alive heartbeat.
3. TestWebSocketDuplex: RFC 6455 handshake, frame encoding/decoding, duplex control commands, ping/pong/close.
4. TestSlidingWindowRateLimiter: Multi-tier quotas, token consumption, 429 rejection, RFC headers, replenishment.
5. TestGatewayTelemetry: Telemetry hub, latency percentiles (p50/p90/p99), stream lifecycle, health/metrics.
6. TestCLIGatewayCommand: Typer gateway command surface (--help, --status, --json, offline & online modes).
7. TestMCPGatewayTools: Native MCP tools (mekong_gateway_status, mekong_gateway_rate_limit) dual-engine parity.
8. TestCoreBoundaryCompliance: Standard-library-only AST boundary enforcement on new gateway modules.
"""

from __future__ import annotations

import ast
import json
import queue
import threading
import time
from pathlib import Path
from unittest.mock import patch

import pytest
from typer.testing import CliRunner

from scripts.mcp_server import (
    CORE_HANDLERS,
    CORE_TOOLS_SPEC,
    handle_gateway_rate_limit,
    handle_gateway_status,
)
from src.cli.app_setup import build_app
from src.core.gateway.rate_limiter import (
    TIER_QUOTAS,
    GatewayTelemetryHub,
    RateLimitDecision,
    SlidingWindowRateLimiter,
    TenantTier,
)
from src.core.gateway.streaming import (
    OPCODE_CLOSE,
    OPCODE_PING,
    OPCODE_PONG,
    OPCODE_TEXT,
    EventSubscriber,
    MissionStreamingBroker,
    StreamEvent,
    StreamEventType,
    WebSocketFrameParser,
    format_sse_event,
    stream_events_sse,
)
from src.core.mcp_server import MekongMcpServer

runner = CliRunner()


class TestEventBroker:
    """Test Suite for MissionStreamingBroker in-memory pub/sub engine."""

    def test_broker_subscribe_and_publish_single(self) -> None:
        """Verify subscription creation and direct event delivery to subscriber queue."""
        broker = MissionStreamingBroker()
        sub = broker.subscribe("mission-single-01")

        event = broker.publish(
            mission_id="mission-single-01",
            event_type=StreamEventType.TASK_STARTED,
            data={"task_id": "task_1", "role": "eng", "step": 1},
        )

        received = sub.get(timeout=1.0)
        assert received is not None
        assert received.event_id == event.event_id
        assert received.mission_id == "mission-single-01"
        assert received.event_type == StreamEventType.TASK_STARTED
        assert received.data["task_id"] == "task_1"
        assert received.data["role"] == "eng"
        assert received.data["step"] == 1

    def test_broker_multi_subscribers_fanout(self) -> None:
        """Verify fanout delivery across multiple concurrent listeners for the same mission."""
        broker = MissionStreamingBroker()
        sub1 = broker.subscribe("mission-fanout-02", subscriber_id="sub_fanout_1")
        sub2 = broker.subscribe("mission-fanout-02", subscriber_id="sub_fanout_2")
        sub3 = broker.subscribe("mission-fanout-02", subscriber_id="sub_fanout_3")

        event = broker.publish(
            mission_id="mission-fanout-02",
            event_type=StreamEventType.PLAN_CREATED,
            data={"dag_tasks": ["t1", "t2", "t3"], "total": 3},
        )

        r1 = sub1.get(timeout=1.0)
        r2 = sub2.get(timeout=1.0)
        r3 = sub3.get(timeout=1.0)

        assert r1.event_id == event.event_id
        assert r2.event_id == event.event_id
        assert r3.event_id == event.event_id
        assert r1.data["dag_tasks"] == ["t1", "t2", "t3"]
        assert r2.data["dag_tasks"] == ["t1", "t2", "t3"]
        assert r3.data["dag_tasks"] == ["t1", "t2", "t3"]

    def test_broker_mission_isolation(self) -> None:
        """Verify events published to mission A do not leak to subscribers of mission B."""
        broker = MissionStreamingBroker()
        sub_a = broker.subscribe("mission-alpha")
        sub_b = broker.subscribe("mission-beta")

        broker.publish(
            mission_id="mission-alpha",
            event_type=StreamEventType.TASK_STARTED,
            data={"confidential": "alpha-data"},
        )

        rec_a = sub_a.get(timeout=1.0)
        assert rec_a.data["confidential"] == "alpha-data"
        assert sub_b.queue.empty()

        with pytest.raises(queue.Empty):
            sub_b.get(timeout=0.1)

    def test_broker_subscriber_disconnect_cleanup(self) -> None:
        """Verify unsubscribing releases subscriber queue and cleans broker tracking sets."""
        broker = MissionStreamingBroker()
        sub = broker.subscribe("mission-cleanup-03")
        stats_before = broker.get_stats()
        assert stats_before["active_subscribers"] == 1
        assert stats_before["active_missions"] == 1

        broker.unsubscribe(sub)
        stats_after = broker.get_stats()
        assert stats_after["active_subscribers"] == 0
        assert stats_after["active_missions"] == 0

    def test_broker_queue_overflow_non_blocking(self) -> None:
        """Verify publishing never blocks or fails even when a subscriber queue buffer is full."""
        broker = MissionStreamingBroker()
        # Instantiate small buffer queue (capacity = 2)
        sub = EventSubscriber(subscriber_id="sub-overflow", mission_id="mission-over", max_buffer=2)
        with broker._lock:
            broker._subscribers["mission-over"] = {sub}

        # Rapidly publish 5 events (3 more than queue capacity)
        for i in range(5):
            broker.publish("mission-over", StreamEventType.TASK_STARTED, {"seq": i})

        # Queue size must remain bounded at max_buffer
        assert sub.queue.qsize() == 2

        # Oldest events (seq 0, 1, 2) must be evicted to preserve newest events (seq 3, 4)
        e3 = sub.get(timeout=0.1)
        e4 = sub.get(timeout=0.1)
        assert e3.data["seq"] == 3
        assert e4.data["seq"] == 4
        assert sub.queue.empty()

    def test_broker_typed_events_emission(self) -> None:
        """Verify strongly typed stream events across the autonomous agent lifecycle."""
        broker = MissionStreamingBroker()
        sub = broker.subscribe("mission-typed")

        typed_specs = [
            (StreamEventType.PLAN_CREATED, {"tasks": ["t1", "t2"], "budget": 24000}),
            (StreamEventType.TASK_STARTED, {"task_id": "t1", "agent": "eng"}),
            (StreamEventType.TASK_COMPLETED, {"task_id": "t1", "duration_ms": 42.5}),
            (StreamEventType.TASK_FAILED, {"task_id": "t2", "error": "timeout"}),
            (StreamEventType.CHECKPOINT_CAPTURED, {"checkpoint_id": "cp_101", "files": 4}),
            (StreamEventType.MISSION_COMPLETED, {"resilience_score": 98.2, "status": "success"}),
        ]

        for evt_type, data in typed_specs:
            broker.publish("mission-typed", evt_type, data)

        for expected_type, expected_data in typed_specs:
            ev = sub.get(timeout=1.0)
            assert ev.event_type == expected_type
            assert ev.data == expected_data
            d = ev.to_dict()
            assert d["event_type"] == expected_type.value
            assert d["data"] == expected_data

    def test_broker_cursor_history_replay(self) -> None:
        """Verify late-subscribing clients can replay events from a cursor ID."""
        broker = MissionStreamingBroker()
        e1 = broker.publish("mission-replay", StreamEventType.TASK_STARTED, {"seq": 1})
        e2 = broker.publish("mission-replay", StreamEventType.TASK_COMPLETED, {"seq": 1})
        e3 = broker.publish("mission-replay", StreamEventType.TASK_STARTED, {"seq": 2})

        # Late subscriber connecting with cursor of e1: should receive e2 and e3
        sub = broker.subscribe("mission-replay", since_cursor=e1.event_id)
        r2 = sub.get(timeout=1.0)
        r3 = sub.get(timeout=1.0)

        assert r2.event_id == e2.event_id
        assert r3.event_id == e3.event_id
        assert r2.data["seq"] == 1
        assert r3.data["seq"] == 2
        assert sub.queue.empty()

        # Late subscriber connecting with since_cursor='0' (replay all events)
        sub_all = broker.subscribe("mission-replay", since_cursor="0")
        assert sub_all.get(timeout=1.0).event_id == e1.event_id
        assert sub_all.get(timeout=1.0).event_id == e2.event_id
        assert sub_all.get(timeout=1.0).event_id == e3.event_id


class TestSSEStreaming:
    """Test Suite for Server-Sent Events (SSE) streaming formatting and lifecycle."""

    def test_sse_event_formatting(self) -> None:
        """Verify RFC-compliant text/event-stream formatting with id, event, and data lines."""
        evt = StreamEvent(
            event_id="evt_test_sse_100",
            mission_id="mission-sse",
            event_type=StreamEventType.PLAN_CREATED,
            data={"dag": ["plan", "exec", "verify"], "nested": {"key": "value"}},
        )

        formatted = evt.to_sse_frame()
        assert formatted.startswith("id: evt_test_sse_100\n")
        assert "event: plan_created\n" in formatted
        assert 'data: {"event_id": "evt_test_sse_100"' in formatted
        assert formatted.endswith("\n\n")

        # Verify format_sse_event helper function parity
        assert format_sse_event(evt) == formatted

    def test_sse_stream_generator_finite_read(self) -> None:
        """Verify stream_events_sse() yields proper events and exits cleanly without hanging."""
        broker = MissionStreamingBroker()
        stop = threading.Event()

        # Seed broker history before opening generator
        e1 = broker.publish("mission-sse-gen", StreamEventType.TASK_STARTED, {"step": 1})
        e2 = broker.publish("mission-sse-gen", StreamEventType.TASK_COMPLETED, {"step": 1})

        gen = stream_events_sse(
            mission_id="mission-sse-gen",
            since_cursor="0",
            broker=broker,
            stop_event=stop,
            heartbeat_interval=10.0,
        )

        f1 = next(gen)
        assert f"id: {e1.event_id}" in f1
        assert "event: task_started" in f1

        f2 = next(gen)
        assert f"id: {e2.event_id}" in f2
        assert "event: task_completed" in f2

        # Terminate generator cleanly
        stop.set()
        with pytest.raises(StopIteration):
            next(gen)

        # Broker subscriber must be automatically cleaned up
        assert broker.get_stats()["active_subscribers"] == 0

    def test_sse_keepalive_heartbeat(self) -> None:
        """Verify ': ping\\n\\n' keep-alive comment emission during idle periods."""
        broker = MissionStreamingBroker()
        stop = threading.Event()

        # Short heartbeat interval to trigger idle ping
        gen = stream_events_sse(
            mission_id="mission-sse-ping",
            heartbeat_interval=0.05,
            broker=broker,
            stop_event=stop,
        )

        time.sleep(0.06)
        ping_chunk = next(gen)
        assert ping_chunk == ": ping\n\n"

        stop.set()
        with pytest.raises(StopIteration):
            next(gen)


class TestWebSocketDuplex:
    """Test Suite for RFC 6455 WebSocket duplex framing, handshake, and control plane."""

    def test_ws_handshake_key_derivation(self) -> None:
        """Test RFC 6455 Section 1.3 compute_handshake_accept with standard test vectors."""
        # Standard RFC 6455 test vector
        client_key = "dGhlIHNhbXBsZSBub25jZQ=="
        expected_accept = "s3pPLMBiTxaQ9kYGzzhZRbK+xOo="

        derived_accept = WebSocketFrameParser.compute_handshake_accept(client_key)
        assert derived_accept == expected_accept

        # Verify full HTTP 101 Switching Protocols response
        resp_bytes = WebSocketFrameParser.build_handshake_response(client_key)
        resp_str = resp_bytes.decode("ascii")
        assert "HTTP/1.1 101 Switching Protocols\r\n" in resp_str
        assert "Upgrade: websocket\r\n" in resp_str
        assert "Connection: Upgrade\r\n" in resp_str
        assert f"Sec-WebSocket-Accept: {expected_accept}\r\n\r\n" in resp_str

    def test_ws_frame_encode_decode(self) -> None:
        """Test client frame unmasking and server frame encoding across small, medium, and large payloads."""
        payload_cases = [
            b"Small RFC payload < 126 bytes",
            b"Medium payload " * 100,  # ~1500 bytes (126 to 65535)
            b"Large payload chunk " * 4000,  # ~76000 bytes (> 65535)
        ]

        for payload in payload_cases:
            # 1. Masked client-to-server frame
            client_frame = WebSocketFrameParser.encode_client_frame(
                payload=payload,
                opcode=OPCODE_TEXT,
                mask=b"\xaa\xbb\xcc\xdd",
            )
            opcode, decoded_payload, remainder = WebSocketFrameParser.decode_frame(client_frame)
            assert opcode == OPCODE_TEXT
            assert decoded_payload == payload
            assert len(remainder) == 0

            # 2. Unmasked server-to-client frame
            server_frame = WebSocketFrameParser.encode_frame(
                payload=payload,
                opcode=OPCODE_TEXT,
            )
            s_opcode, s_payload, s_remainder = WebSocketFrameParser.decode_frame(server_frame)
            assert s_opcode == OPCODE_TEXT
            assert s_payload == payload
            assert len(s_remainder) == 0

    def test_ws_control_commands_dispatch(self) -> None:
        """Test duplex control commands (pause, resume, cancel) and command_ack event emission."""
        broker = MissionStreamingBroker()
        sub = broker.subscribe("mission-ws-ctrl")

        # 1. Pause command
        ack_pause = broker.handle_command("mission-ws-ctrl", "pause", {"reason": "user_requested"})
        assert ack_pause["ok"] is True
        assert ack_pause["command"] == "pause"
        assert ack_pause["status"] == "paused"
        assert broker.get_mission_control("mission-ws-ctrl").is_paused() is True

        event_pause = sub.get(timeout=1.0)
        assert event_pause.event_type == StreamEventType.COMMAND_ACK
        assert event_pause.data["command"] == "pause"
        assert event_pause.data["status"] == "paused"

        # 2. Resume command
        ack_resume = broker.handle_command("mission-ws-ctrl", "resume")
        assert ack_resume["ok"] is True
        assert ack_resume["status"] == "resumed"
        assert broker.get_mission_control("mission-ws-ctrl").is_paused() is False

        event_resume = sub.get(timeout=1.0)
        assert event_resume.event_type == StreamEventType.COMMAND_ACK
        assert event_resume.data["command"] == "resume"

        # 3. Cancel command
        ack_cancel = broker.handle_command("mission-ws-ctrl", "cancel")
        assert ack_cancel["ok"] is True
        assert ack_cancel["status"] == "cancelled"
        assert broker.get_mission_control("mission-ws-ctrl").is_cancelled() is True

        event_cancel = sub.get(timeout=1.0)
        assert event_cancel.event_type == StreamEventType.COMMAND_ACK
        assert event_cancel.data["status"] == "cancelled"

        # 4. JSON message processing through WebSocketFrameParser
        msg_bytes = json.dumps({"command": "pause", "payload": {"meta": 123}}).encode("utf-8")
        parsed_ack = WebSocketFrameParser.process_client_message(msg_bytes, "mission-ws-ctrl", broker)
        assert parsed_ack["ok"] is True
        assert parsed_ack["command"] == "pause"

        # 5. Invalid command handling
        bad_ack = broker.handle_command("mission-ws-ctrl", "invalid_action")
        assert bad_ack["ok"] is False
        assert "Unknown or unsupported" in bad_ack["error"]

    def test_ws_control_frames_ping_pong_close(self) -> None:
        """Test ping 0x9, pong 0xA, and close 0x8 RFC control frames."""
        # 1. Ping frame handling -> responds with Pong frame (opcode 0xA)
        ping_frame = WebSocketFrameParser.build_ping_frame(b"heartbeat_check")
        op, payload, rem = WebSocketFrameParser.decode_frame(ping_frame)
        assert op == OPCODE_PING
        assert payload == b"heartbeat_check"

        pong_reply, should_close = WebSocketFrameParser.handle_control_frame(op, payload)
        assert pong_reply is not None
        assert should_close is False
        op_pong, payload_pong, _ = WebSocketFrameParser.decode_frame(pong_reply)
        assert op_pong == OPCODE_PONG
        assert payload_pong == b"heartbeat_check"

        # 2. Pong frame handling -> no reply, do not close
        pong_frame = WebSocketFrameParser.build_pong_frame(b"heartbeat_ack")
        op_p, pl_p, _ = WebSocketFrameParser.decode_frame(pong_frame)
        assert op_p == OPCODE_PONG
        reply, should_close = WebSocketFrameParser.handle_control_frame(op_p, pl_p)
        assert reply is None
        assert should_close is False

        # 3. Close frame handling -> responds with Close frame, signals should_close
        close_frame = WebSocketFrameParser.build_close_frame(1000, "client_bye")
        op_c, pl_c, _ = WebSocketFrameParser.decode_frame(close_frame)
        assert op_c == OPCODE_CLOSE
        reply_close, should_close = WebSocketFrameParser.handle_control_frame(op_c, pl_c)
        assert reply_close is not None
        assert should_close is True
        op_cr, pl_cr, _ = WebSocketFrameParser.decode_frame(reply_close)
        assert op_cr == OPCODE_CLOSE


class TestSlidingWindowRateLimiter:
    """Test Suite for Sliding-Window Token Bucket Rate Limiter and Tier Enforcement."""

    def test_rate_limiter_tier_quotas(self) -> None:
        """Test free (60 req/min), pro (600 req/min), enterprise (3,000 req/min) quotas."""
        limiter = SlidingWindowRateLimiter()

        assert TIER_QUOTAS[TenantTier.FREE].capacity == 60
        assert TIER_QUOTAS[TenantTier.FREE].refill_rate == 1.0

        assert TIER_QUOTAS[TenantTier.PRO].capacity == 600
        assert TIER_QUOTAS[TenantTier.PRO].refill_rate == 10.0

        assert TIER_QUOTAS[TenantTier.ENTERPRISE].capacity == 3000
        assert TIER_QUOTAS[TenantTier.ENTERPRISE].refill_rate == 50.0

        limiter.set_tenant_tier("free_tenant", TenantTier.FREE)
        limiter.set_tenant_tier("pro_tenant", TenantTier.PRO)
        limiter.set_tenant_tier("ent_tenant", TenantTier.ENTERPRISE)

        assert limiter.get_quota("free_tenant")["limit"] == 60
        assert limiter.get_quota("pro_tenant")["limit"] == 600
        assert limiter.get_quota("ent_tenant")["limit"] == 3000

    def test_token_consumption_and_remaining(self) -> None:
        """Test token decrementing and remaining count calculation."""
        limiter = SlidingWindowRateLimiter()
        limiter.set_tenant_tier("tenant_consume", TenantTier.FREE)

        # First request consumes 1 token
        d1 = limiter.check_rate_limit("tenant_consume", cost=1)
        assert d1.allowed is True
        assert d1.limit == 60
        assert d1.remaining == 59

        # Second request consumes 5 tokens
        d2 = limiter.check_rate_limit("tenant_consume", cost=5)
        assert d2.allowed is True
        assert d2.remaining == 54

        # get_quota inspects state without consuming
        q = limiter.get_quota("tenant_consume")
        assert q["remaining"] == 54
        assert q["limit"] == 60

    def test_rate_limit_exceeded_429_rejection(self) -> None:
        """Test rejection when quota is exhausted and calculation of retry_after."""
        limiter = SlidingWindowRateLimiter()
        limiter.set_tenant_tier("tenant_busy", TenantTier.FREE)

        # Exhaust all 60 tokens
        for _ in range(60):
            dec = limiter.check_rate_limit("tenant_busy", cost=1)
            assert dec.allowed is True

        # 61st request must be rejected
        blocked = limiter.check_rate_limit("tenant_busy", cost=1)
        assert blocked.allowed is False
        assert blocked.remaining == 0
        assert blocked.retry_after >= 1
        assert blocked.reset_timestamp >= int(time.time())

    def test_rfc_headers_generation(self) -> None:
        """Verify X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset, and Retry-After."""
        limiter = SlidingWindowRateLimiter()
        limiter.set_tenant_tier("tenant_headers", TenantTier.PRO)

        decision = limiter.check_rate_limit("tenant_headers", cost=1)
        headers = decision.to_headers()

        assert headers["X-RateLimit-Limit"] == "600"
        assert int(headers["X-RateLimit-Remaining"]) == 599
        assert "X-RateLimit-Reset" in headers
        assert "Retry-After" not in headers  # Not rate limited

        # Rejected decision headers
        rej_decision = RateLimitDecision(
            allowed=False,
            tier="free",
            limit=60,
            remaining=0,
            reset_timestamp=int(time.time()) + 45,
            retry_after=45,
        )
        rej_headers = rej_decision.to_headers()
        assert rej_headers["X-RateLimit-Limit"] == "60"
        assert rej_headers["X-RateLimit-Remaining"] == "0"
        assert rej_headers["Retry-After"] == "45"

    def test_sliding_window_replenishment(self) -> None:
        """Test token refill over elapsed time and sliding window request expiration."""
        limiter = SlidingWindowRateLimiter()
        t0 = 1000.0

        with patch("time.time", return_value=t0):
            limiter.check_rate_limit("tenant_replenish", cost=10)
            bucket = limiter._buckets["tenant_replenish"]
            assert bucket.tokens == 50.0

        # After 5 seconds elapsed (refill rate = 1.0 token/s), 5 tokens are replenished
        with patch("time.time", return_value=t0 + 5.0):
            limiter.get_quota("tenant_replenish")
            assert bucket.tokens == 55.0

        # After 61 seconds (past 60s sliding window), all window requests expire and tokens cap at capacity
        with patch("time.time", return_value=t0 + 61.0):
            quota = limiter.get_quota("tenant_replenish")
            assert quota["remaining"] == 60
            assert bucket.tokens == 60.0


class TestGatewayTelemetry:
    """Test Suite for GatewayTelemetryHub metrics collection and latency calculations."""

    def test_record_request_and_latency_percentiles(self) -> None:
        """Test request recording and p50, p90, p99 ms calculation."""
        hub = GatewayTelemetryHub()

        # Record 10 requests with linearly spaced latencies: 10ms, 20ms, ..., 100ms
        for lat in range(10, 110, 10):
            hub.record_request(path="/api/v1/missions", duration_ms=float(lat), status_code=200)

        pcts = hub.get_latency_percentiles()
        assert pcts["p50_ms"] >= 50.0
        assert pcts["p90_ms"] >= 90.0
        assert pcts["p99_ms"] >= 98.0
        assert pcts["p50_ms"] <= pcts["p90_ms"] <= pcts["p99_ms"]

    def test_record_rate_limit_rejection(self) -> None:
        """Test rejection counter incrementing."""
        hub = GatewayTelemetryHub()
        hub.record_rate_limit_rejection("tenant_rej_1")
        hub.record_request(path="/api/v1/stream", duration_ms=1.5, status_code=429, tenant_id="tenant_rej_1")

        metrics = hub.get_metrics()
        assert metrics["rate_limit_rejections"] == 2

    def test_record_stream_lifecycle(self) -> None:
        """Test stream opened and closed metrics."""
        hub = GatewayTelemetryHub()
        assert hub.get_health()["active_streams"] == 0

        hub.record_stream_opened()
        hub.record_stream_opened()
        assert hub.get_health()["active_streams"] == 2

        hub.record_stream_closed()
        assert hub.get_health()["active_streams"] == 1

        hub.record_stream_closed()
        assert hub.get_health()["active_streams"] == 0

        # Safe non-negative clamping
        hub.record_stream_closed()
        assert hub.get_health()["active_streams"] == 0

    def test_get_health_and_metrics(self) -> None:
        """Test /health structure and /api/v1/gateway/metrics dictionary outputs."""
        hub = GatewayTelemetryHub()
        hub.record_request("/health", 2.0, 200)
        hub.record_stream_opened()

        health = hub.get_health()
        assert health["status"] == "healthy"
        assert health["uptime_seconds"] >= 0.0
        assert health["version"] == "0.1.0"
        assert health["active_streams"] == 1
        assert "timestamp" in health

        metrics = hub.get_metrics()
        assert metrics["status"] == "healthy"
        assert metrics["total_requests"] == 1
        assert metrics["active_streams"] == 1
        assert "tier_quotas" in metrics
        assert metrics["tier_quotas"]["free"] == 60
        assert metrics["tier_quotas"]["pro"] == 600
        assert metrics["tier_quotas"]["enterprise"] == 3000
        assert "p50_ms" in metrics
        assert "p90_ms" in metrics
        assert "p99_ms" in metrics


class TestCLIGatewayCommand:
    """Test Suite for mekong gateway CLI command surface."""

    def test_cli_gateway_help(self) -> None:
        """Verify mekong gateway --help outputs --host, --port, --status, --json."""
        app = build_app()
        res = runner.invoke(app, ["gateway", "--help"])
        assert res.exit_code == 0
        assert "--host" in res.stdout or "-H" in res.stdout
        assert "--port" in res.stdout or "-p" in res.stdout
        assert "--status" in res.stdout
        assert "--json" in res.stdout

    def test_cli_gateway_status_offline_json(self) -> None:
        """Verify --status --json against offline port returns JSON error and exit code 1."""
        app = build_app()
        with patch("src.cli.commands.gateway_command.query_gateway_status", return_value=(False, None, None)):
            res = runner.invoke(app, ["gateway", "--status", "--json", "--port", "59123"])
            assert res.exit_code == 1
            data = json.loads(res.stdout)
            assert data["ok"] is False
            assert data["status"] == "offline"
            assert "error" in data
            assert data["port"] == 59123

    def test_cli_gateway_status_offline_interactive(self) -> None:
        """Verify --status against offline port prints error and exit code 1."""
        app = build_app()
        with patch("src.cli.commands.gateway_command.query_gateway_status", return_value=(False, None, None)):
            res = runner.invoke(app, ["gateway", "--status", "--port", "59123"])
            assert res.exit_code == 1
            assert "OFFLINE" in res.stdout or "not reachable" in res.stdout

    def test_cli_gateway_status_online_mocked(self) -> None:
        """Mock health/metrics probe and verify --status and --status --json display full telemetry and exit code 0."""
        app = build_app()
        health_mock = {
            "status": "healthy",
            "uptime_seconds": 3600.0,
            "version": "1.0.0",
            "active_streams": 3,
        }
        metrics_mock = {
            "active_streams": 3,
            "active_ws_connections": 2,
            "rate_limit_rejections": 0,
            "total_requests": 250,
            "latency_percentiles": {"p50_ms": 1.25, "p90_ms": 3.4, "p99_ms": 8.1},
        }

        with patch("src.cli.commands.gateway_command.query_gateway_status", return_value=(True, health_mock, metrics_mock)):
            # 1. Interactive output mode
            res_int = runner.invoke(app, ["gateway", "--status"])
            assert res_int.exit_code == 0
            assert "ONLINE" in res_int.stdout
            assert "http://127.0.0.1:8000" in res_int.stdout

            # 2. JSON machine-readable mode
            res_json = runner.invoke(app, ["gateway", "--status", "--json"])
            assert res_json.exit_code == 0
            data = json.loads(res_json.stdout)
            assert data["ok"] is True
            assert data["status"] == "online"
            assert data["uptime"] == 3600.0
            assert data["streams"] == 3
            assert data["ws_connections"] == 2


class TestMCPGatewayTools:
    """Test Suite for Native MCP Gateway Tools dual-engine parity."""

    def test_mcp_gateway_status_handler_in_process(self) -> None:
        """Test handle_gateway_status from scripts/mcp_server.py."""
        raw = handle_gateway_status({})
        data = json.loads(raw)

        assert data["ok"] is True
        assert "status" in data
        assert "uptime_seconds" in data
        assert "active_streams" in data
        assert "system_metrics" in data
        metrics = data["system_metrics"]
        assert "rate_limit_rejections" in metrics
        assert "total_requests" in metrics
        assert "latency_percentiles" in metrics

    def test_mcp_gateway_rate_limit_handler_in_process(self) -> None:
        """Test handle_gateway_rate_limit with default and custom tenant IDs."""
        # 1. Default tenant
        raw_def = handle_gateway_rate_limit({})
        data_def = json.loads(raw_def)
        assert data_def["ok"] is True
        assert data_def["tenant_id"] == "default"
        assert data_def["tier"] == "free"
        assert data_def["quota_limit"] == 60
        assert data_def["tokens_remaining"] <= 60

        # 2. Custom enterprise tenant
        raw_cust = handle_gateway_rate_limit({"tenant_id": "enterprise_partner"})
        data_cust = json.loads(raw_cust)
        assert data_cust["ok"] is True
        assert data_cust["tenant_id"] == "enterprise_partner"
        assert "reset_timestamp" in data_cust
        assert "retry_after" in data_cust

    def test_core_mcp_server_gateway_tools(self) -> None:
        """Test _handle_gateway_status and _handle_gateway_rate_limit on MekongMcpServer."""
        server = MekongMcpServer()

        # Status handler & alias
        status_res = json.loads(server._handle_gateway_status())
        assert status_res["ok"] is True
        assert "system_metrics" in status_res
        assert server._handle_mekong_gateway_status == server._handle_gateway_status

        # Rate limit handler & alias
        rl_res = json.loads(server._handle_gateway_rate_limit(tenant_id="custom_client"))
        assert rl_res["ok"] is True
        assert rl_res["tenant_id"] == "custom_client"
        assert server._handle_mekong_gateway_rate_limit == server._handle_gateway_rate_limit

    def test_mcp_tool_parity_schemas(self) -> None:
        """Test that both FastMCP and PureJsonRpcServer expose identical parameter schemas and names."""
        # PureJsonRpcServer tool spec
        spec_map = {tool["name"]: tool for tool in CORE_TOOLS_SPEC}
        assert "mekong_gateway_status" in spec_map
        assert "mekong_gateway_rate_limit" in spec_map

        assert CORE_HANDLERS["mekong_gateway_status"] == handle_gateway_status
        assert CORE_HANDLERS["mekong_gateway_rate_limit"] == handle_gateway_rate_limit

        rl_spec = spec_map["mekong_gateway_rate_limit"]
        assert "tenant_id" in rl_spec["inputSchema"]["properties"]
        assert rl_spec["inputSchema"]["properties"]["tenant_id"]["type"] == "string"

        # FastMCP Server tool registrations
        server = MekongMcpServer()
        app = server.create_app()
        fastmcp_tools = app._tool_manager._tools

        assert "mekong_gateway_status" in fastmcp_tools
        assert "mekong_gateway_rate_limit" in fastmcp_tools

        fastmcp_rl = fastmcp_tools["mekong_gateway_rate_limit"]
        props = fastmcp_rl.parameters.get("properties", {})
        assert "tenant_id" in props
        assert props["tenant_id"]["type"] == "string"
        assert props["tenant_id"]["default"] == "default"


class TestCoreBoundaryCompliance:
    """Test Suite for Core Boundary Invariant Compliance."""

    def test_gateway_core_modules_ast_boundary(self) -> None:
        """Programmatically parse AST of gateway core modules to assert ZERO vendor SDK and third-party HTTP imports."""
        target_files = [
            Path("src/core/gateway/streaming.py"),
            Path("src/core/gateway/rate_limiter.py"),
        ]

        forbidden_vendor_sdks = frozenset({"anthropic", "openai"})
        forbidden_http_ws = frozenset({
            "requests",
            "httpx",
            "fastapi",
            "starlette",
            "aiohttp",
            "websockets",
        })

        for file_path in target_files:
            assert file_path.exists(), f"Target module {file_path} does not exist"
            tree = ast.parse(file_path.read_text(encoding="utf-8"))

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        root = alias.name.split(".")[0]
                        assert root not in forbidden_vendor_sdks, (
                            f"Prohibited vendor SDK '{root}' imported in {file_path}"
                        )
                        assert root not in forbidden_http_ws, (
                            f"Prohibited third-party HTTP/WS library '{root}' imported in {file_path}"
                        )
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        root = node.module.split(".")[0]
                        assert root not in forbidden_vendor_sdks, (
                            f"Prohibited vendor SDK '{root}' imported in {file_path}"
                        )
                        assert root not in forbidden_http_ws, (
                            f"Prohibited third-party HTTP/WS library '{root}' imported in {file_path}"
                        )
