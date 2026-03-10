"""Mekong API Client - Sync and Async implementations."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import httpx


@dataclass
class Mission:
    """Mission object returned after creation."""

    id: str
    goal: str
    status: str
    tenant_id: str | None = None
    created_at: datetime | None = None
    completed_at: datetime | None = None
    result: dict | None = field(default_factory=dict)
    error: str | None = None


@dataclass
class MissionEvent:
    """Event emitted during async streaming."""

    event_type: str
    mission_id: str
    data: dict
    timestamp: datetime = field(default_factory=datetime.now)


class MekongClient:
    """Sync client for Mekong CLI API.

    Usage:
        client = MekongClient(api_key="your-api-key")
        mission = client.cook("Deploy landing page")
        print(f"Mission {mission.id} completed: {mission.status}")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.mekong.run",
        tenant_id: str | None = None,
    ):
        """Initialize Mekong client.

        Args:
            api_key: API key for authentication
            base_url: Base URL for Mekong API
            tenant_id: Optional tenant ID for multi-tenant setups

        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id
        self._webhooks: dict[str, list[Callable]] = {}

        self._client = httpx.Client(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=300.0,  # 5 minutes for long-running missions
        )

    def cook(
        self,
        goal: str,
        priority: str = "normal",
        webhook_url: str | None = None,
        **kwargs: Any,
    ) -> Mission:
        """Execute a goal synchronously.

        Args:
            goal: The goal to achieve (e.g., "Deploy landing page")
            priority: Priority level - low, normal, high
            webhook_url: Optional webhook URL for notifications
            **kwargs: Additional parameters

        Returns:
            Mission object with execution result

        """
        payload = {
            "goal": goal,
            "priority": priority,
            "tenant_id": self.tenant_id,
            "webhook_url": webhook_url,
            **kwargs,
        }

        response = self._client.post("/v1/missions", json=payload)
        response.raise_for_status()
        data = response.json()

        return self._parse_mission(data)

    def get_mission(self, mission_id: str) -> Mission:
        """Get mission status and result.

        Args:
            mission_id: Mission ID to retrieve

        Returns:
            Mission object with current status

        """
        response = self._client.get(f"/v1/missions/{mission_id}")
        response.raise_for_status()
        data = response.json()

        return self._parse_mission(data)

    def subscribe(self, event: str, handler: Callable) -> None:
        """Register a webhook handler for events.

        Args:
            event: Event type to subscribe to
            handler: Callback function to handle event

        Supported events:
            - mission.created
            - mission.planning
            - mission.step.started
            - mission.step.completed
            - mission.step.failed
            - mission.completed
            - mission.failed
            - credits.low

        """
        if event not in self._webhooks:
            self._webhooks[event] = []
        self._webhooks[event].append(handler)

    def _parse_mission(self, data: dict) -> Mission:
        """Parse API response into Mission object."""
        created_at = None
        completed_at = None

        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        return Mission(
            id=data.get("id", ""),
            goal=data.get("goal", ""),
            status=data.get("status", "unknown"),
            tenant_id=data.get("tenant_id"),
            created_at=created_at,
            completed_at=completed_at,
            result=data.get("result", {}),
            error=data.get("error"),
        )

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._client.close()

    def __enter__(self) -> MekongClient:
        """Context manager entry."""
        return self

    def __exit__(self, *args: Any) -> None:
        """Context manager exit."""
        self.close()


class MekongClientAsync:
    """Async client for Mekong CLI API with streaming support.

    Usage:
        async with MekongClientAsync(api_key="your-api-key") as client:
            async for event in client.cook_async("Deploy landing page"):
                print(f"Event: {event.event_type} - {event.data}")
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.mekong.run",
        tenant_id: str | None = None,
    ):
        """Initialize async Mekong client.

        Args:
            api_key: API key for authentication
            base_url: Base URL for Mekong API
            tenant_id: Optional tenant ID for multi-tenant setups

        """
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.tenant_id = tenant_id

        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            timeout=300.0,
        )

    async def cook_async(
        self,
        goal: str,
        priority: str = "normal",
        webhook_url: str | None = None,
        **kwargs: Any,
    ) -> AsyncIterator[MissionEvent]:
        """Execute a goal asynchronously with event streaming.

        Args:
            goal: The goal to achieve
            priority: Priority level - low, normal, high
            webhook_url: Optional webhook URL for notifications
            **kwargs: Additional parameters

        Yields:
            MissionEvent objects streaming progress updates

        """
        payload = {
            "goal": goal,
            "priority": priority,
            "tenant_id": self.tenant_id,
            "webhook_url": webhook_url,
            **kwargs,
        }

        # Create mission
        response = await self._client.post("/v1/missions", json=payload)
        response.raise_for_status()
        data = response.json()

        mission_id = data.get("id", "")

        # Stream progress via SSE
        async with self._client.stream(
            "GET", f"/v1/missions/{mission_id}/stream"
        ) as stream_response:
            async for line in stream_response.aiter_lines():
                if line.startswith("data:"):
                    event_data = self._parse_sse_data(line[5:].strip())
                    if event_data:
                        yield MissionEvent(
                            event_type=event_data.get("type", "unknown"),
                            mission_id=mission_id,
                            data=event_data.get("data", {}),
                        )

    async def get_mission(self, mission_id: str) -> Mission:
        """Get mission status asynchronously.

        Args:
            mission_id: Mission ID to retrieve

        Returns:
            Mission object with current status

        """
        response = await self._client.get(f"/v1/missions/{mission_id}")
        response.raise_for_status()
        data = response.json()

        return self._parse_mission(data)

    async def _parse_sse_data(self, data: str) -> dict | None:
        """Parse SSE data line into dict."""
        import json

        try:
            return json.loads(data)
        except json.JSONDecodeError:
            return None

    def _parse_mission(self, data: dict) -> Mission:
        """Parse API response into Mission object."""
        created_at = None
        completed_at = None

        if data.get("created_at"):
            created_at = datetime.fromisoformat(data["created_at"])
        if data.get("completed_at"):
            completed_at = datetime.fromisoformat(data["completed_at"])

        return Mission(
            id=data.get("id", ""),
            goal=data.get("goal", ""),
            status=data.get("status", "unknown"),
            tenant_id=data.get("tenant_id"),
            created_at=created_at,
            completed_at=completed_at,
            result=data.get("result", {}),
            error=data.get("error"),
        )

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._client.aclose()

    async def __aenter__(self) -> MekongClientAsync:
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.close()


# Fix for AsyncIterator type hint
try:
    from collections.abc import AsyncIterator
except ImportError:
    from collections.abc import AsyncIterator  # type: ignore
