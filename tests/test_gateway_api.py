"""Tests for Gateway API — Clean API contract for AgencyOS."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.gateway_api import (
    MissionEvent,
    MissionRequest,
    MissionResponse,
    MissionStatus,
    WEBHOOK_EVENTS,
    create_mission,
    get_webhook_schema,
    validate_webhook_url,
)


class TestMissionStatus:
    def test_all_statuses(self) -> None:
        assert MissionStatus.PENDING == "pending"
        assert MissionStatus.COMPLETED == "completed"
        assert MissionStatus.FAILED == "failed"

    def test_status_values(self) -> None:
        assert len(MissionStatus) == 7


class TestMissionRequest:
    def test_minimal_request(self) -> None:
        req = MissionRequest(goal="Deploy app", tenant_id="t-123")
        assert req.goal == "Deploy app"
        assert req.tenant_id == "t-123"
        assert req.priority == "normal"
        assert req.webhook_url is None

    def test_full_request(self) -> None:
        req = MissionRequest(
            goal="Build API",
            tenant_id="t-456",
            webhook_url="https://example.com/hook",
            priority="high",
            metadata={"source": "dashboard"},
        )
        assert req.priority == "high"
        assert req.metadata["source"] == "dashboard"


class TestMissionResponse:
    def test_to_dict(self) -> None:
        resp = MissionResponse(
            mission_id="m-001",
            status=MissionStatus.PENDING,
            created_at="2026-03-10T00:00:00Z",
            estimated_steps=5,
            stream_url="/v1/missions/m-001/stream",
        )
        data = resp.to_dict()
        assert data["mission_id"] == "m-001"
        assert data["status"] == "pending"
        assert data["stream_url"] == "/v1/missions/m-001/stream"


class TestMissionEvent:
    def test_sse_format(self) -> None:
        evt = MissionEvent(
            event_type="mission.created",
            mission_id="m-001",
            data={"goal": "test"},
        )
        sse = evt.to_sse()
        assert sse.startswith("event: mission.created\n")
        assert "m-001" in sse
        assert sse.endswith("\n\n")

    def test_auto_timestamp(self) -> None:
        evt = MissionEvent(event_type="test", mission_id="m-002")
        assert evt.timestamp != ""


class TestCreateMission:
    def test_creates_mission(self) -> None:
        req = MissionRequest(goal="Deploy", tenant_id="t-123")
        resp = create_mission(req)

        assert resp.mission_id is not None
        assert len(resp.mission_id) == 36  # UUID format
        assert resp.status == MissionStatus.PENDING
        assert resp.stream_url is not None
        assert resp.mission_id in resp.stream_url

    def test_unique_ids(self) -> None:
        req = MissionRequest(goal="Test", tenant_id="t-1")
        r1 = create_mission(req)
        r2 = create_mission(req)
        assert r1.mission_id != r2.mission_id


class TestWebhookSchema:
    def test_schema_contains_events(self) -> None:
        schema = get_webhook_schema()
        assert "mission.created" in schema
        assert "mission.completed" in schema
        assert "mission.failed" in schema
        assert len(schema) == 7

    def test_webhook_events_constant(self) -> None:
        assert isinstance(WEBHOOK_EVENTS, dict)
        assert all(isinstance(v, str) for v in WEBHOOK_EVENTS.values())


class TestValidateWebhookUrl:
    def test_invalid_protocol(self) -> None:
        ok, msg = validate_webhook_url("ftp://example.com")
        assert not ok
        assert "http" in msg.lower()

    def test_unreachable_url(self) -> None:
        ok, msg = validate_webhook_url("https://nonexistent.invalid.test")
        assert not ok


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
