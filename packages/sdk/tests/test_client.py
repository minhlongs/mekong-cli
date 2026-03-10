"""Tests for Mekong SDK."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from mekong_sdk import MekongClient, MekongClientAsync
from mekong_sdk.client import Mission, MissionEvent


class TestMission:
    """Test Mission dataclass."""

    def test_mission_creation(self):
        """Test creating a Mission object."""
        mission = Mission(
            id="test-123",
            goal="Test goal",
            status="completed",
        )

        assert mission.id == "test-123"
        assert mission.goal == "Test goal"
        assert mission.status == "completed"
        assert mission.result == {}
        assert mission.error is None

    def test_mission_with_result(self):
        """Test Mission with result data."""
        mission = Mission(
            id="test-456",
            goal="Deploy app",
            status="completed",
            result={"files": ["main.py", "README.md"]},
        )

        assert mission.result["files"] == ["main.py", "README.md"]


class TestMekongClient:
    """Test synchronous MekongClient."""

    def test_client_initialization(self):
        """Test client initializes with correct parameters."""
        client = MekongClient(
            api_key="test-key",
            base_url="http://localhost:8000",
            tenant_id="tenant-123",
        )

        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:8000"
        assert client.tenant_id == "tenant-123"

    def test_client_default_base_url(self):
        """Test default base URL."""
        client = MekongClient(api_key="test-key")
        assert client.base_url == "https://api.mekong.run"

    @patch("mekong_sdk.client.httpx.Client")
    def test_cook_method(self, mock_client_class):
        """Test cook method sends correct request."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "mission-123",
            "goal": "Test goal",
            "status": "completed",
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.post.return_value = mock_response

        client = MekongClient(api_key="test-key")
        mission = client.cook("Test goal", priority="high")

        mock_client.post.assert_called_once()
        call_args = mock_client.post.call_args
        assert call_args[0][0] == "/v1/missions"
        assert call_args[1]["json"]["goal"] == "Test goal"
        assert call_args[1]["json"]["priority"] == "high"

        assert mission.id == "mission-123"
        assert mission.status == "completed"

    @patch("mekong_sdk.client.httpx.Client")
    def test_get_mission(self, mock_client_class):
        """Test get_mission method."""
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "id": "mission-789",
            "goal": "Check status",
            "status": "in_progress",
        }
        mock_response.raise_for_status = MagicMock()
        mock_client.get.return_value = mock_response

        client = MekongClient(api_key="test-key")
        mission = client.get_mission("mission-789")

        mock_client.get.assert_called_once_with("/v1/missions/mission-789")
        assert mission.id == "mission-789"
        assert mission.status == "in_progress"

    def test_subscribe_method(self):
        """Test webhook subscription."""
        client = MekongClient(api_key="test-key")

        def handler(event: dict) -> None:
            print(event)

        client.subscribe("mission.completed", handler)

        assert "mission.completed" in client._webhooks
        assert handler in client._webhooks["mission.completed"]

    def test_context_manager(self):
        """Test context manager usage."""
        with patch("mekong_sdk.client.httpx.Client"):
            with MekongClient(api_key="test-key") as client:
                assert isinstance(client, MekongClient)


class TestMekongClientAsync:
    """Test asynchronous MekongClientAsync."""

    def test_async_client_initialization(self):
        """Test async client initialization."""
        client = MekongClientAsync(
            api_key="test-key",
            base_url="http://localhost:8000",
        )

        assert client.api_key == "test-key"
        assert client.base_url == "http://localhost:8000"

    @pytest.mark.asyncio
    @patch("mekong_sdk.client.httpx.AsyncClient")
    async def test_async_context_manager(self, mock_client_class):
        """Test async context manager."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        async with MekongClientAsync(api_key="test-key") as client:
            assert isinstance(client, MekongClientAsync)

        mock_client.aclose.assert_called_once()

    @pytest.mark.asyncio
    @patch("mekong_sdk.client.httpx.AsyncClient")
    async def test_get_mission_async(self, mock_client_class):
        """Test async get_mission method."""
        mock_client = AsyncMock()
        mock_client_class.return_value = mock_client

        mock_response = AsyncMock()
        mock_response.json.return_value = {
            "id": "async-mission-123",
            "goal": "Async task",
            "status": "completed",
        }
        mock_response.raise_for_status = AsyncMock()
        mock_client.get.return_value = mock_response

        client = MekongClientAsync(api_key="test-key")
        mission = await client.get_mission("async-mission-123")

        assert mission.id == "async-mission-123"
        assert mission.status == "completed"


class TestMissionEvent:
    """Test MissionEvent dataclass."""

    def test_event_creation(self):
        """Test creating a MissionEvent."""
        event = MissionEvent(
            event_type="mission.step.completed",
            mission_id="mission-123",
            data={"step": 1, "message": "Completed"},
        )

        assert event.event_type == "mission.step.completed"
        assert event.mission_id == "mission-123"
        assert event.data["step"] == 1
        assert isinstance(event.timestamp, datetime)
