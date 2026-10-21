# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Mekong RaaS SDK — Python client aligned with /v1/ API endpoints."""
from __future__ import annotations

from typing import Any, AsyncIterator, Dict, Iterator, List, Optional

import httpx

from src.raas.sdk_marketing import SDKAsyncMarketingMixin, SDKMarketingMixin
from src.raas.sdk_models import (
    AgentInfo,
    AgentResult,
    ContentTemplate,
    MekongAPIError,
    PerformanceData,
    RenderedContent,
    StepDetail,
    Task,
    TaskResult,
    TemplateMetadata,
    _parse_sse_line,
    _parse_step,
    _parse_task,
    _raise_for_status,
)


def _build_task_payload(
    goal: str,
    agent: Optional[str] = None,
    recipe: Optional[str] = None,
    options: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {"goal": goal}
    if agent is not None:
        payload["agent"] = agent
    if recipe is not None:
        payload["recipe"] = recipe
    if options:
        payload["options"] = options
    return payload


class MekongClient(SDKMarketingMixin):
    """Synchronous HTTP client for the Mekong RaaS /v1/ API."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    @property
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        with httpx.Client(timeout=self._timeout) as client:
            r = client.request(method, f"{self._base_url}{path}", headers=self._headers, **kwargs)
        _raise_for_status(r)
        return r.json()

    def submit_task(
        self,
        goal: str,
        agent: Optional[str] = None,
        recipe: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        data = self._request("POST", "/v1/tasks", json=_build_task_payload(goal, agent, recipe, options))
        return TaskResult(data["task_id"], data["status"], data["tenant_id"])

    def get_task(self, task_id: str) -> Task:
        return _parse_task(self._request("GET", f"/v1/tasks/{task_id}"))

    def stream_task(self, task_id: str) -> Iterator[dict]:
        url = f"{self._base_url}/v1/tasks/{task_id}/stream"
        with httpx.Client(timeout=None) as client:
            with client.stream("GET", url, headers=self._headers) as r:
                _raise_for_status(r)
                for line in r.iter_lines():
                    event = _parse_sse_line(line)
                    if event is not None:
                        yield event

    def list_agents(self) -> List[AgentInfo]:
        return [AgentInfo(name=a["name"], description=a["description"]) for a in self._request("GET", "/v1/agents")]

    def run_agent(
        self, name: str, goal: str, options: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        data = self._request("POST", f"/v1/agents/{name}/run", json=_build_task_payload(goal, options=options))
        return AgentResult(data["agent"], data["status"], data["output"], data.get("errors", []))


class MekongAsyncClient(SDKAsyncMarketingMixin):
    """Async HTTP client for the Mekong RaaS /v1/ API."""

    def __init__(self, base_url: str, api_key: str, timeout: float = 30.0) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout

    @property
    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self._api_key}"}

    async def _request(self, method: str, path: str, **kwargs: Any) -> dict:
        async with httpx.AsyncClient(timeout=self._timeout) as client:
            r = await client.request(method, f"{self._base_url}{path}", headers=self._headers, **kwargs)
        _raise_for_status(r)
        return r.json()

    async def submit_task(
        self,
        goal: str,
        agent: Optional[str] = None,
        recipe: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> TaskResult:
        data = await self._request("POST", "/v1/tasks", json=_build_task_payload(goal, agent, recipe, options))
        return TaskResult(data["task_id"], data["status"], data["tenant_id"])

    async def get_task(self, task_id: str) -> Task:
        return _parse_task(await self._request("GET", f"/v1/tasks/{task_id}"))

    async def stream_task(self, task_id: str) -> AsyncIterator[dict]:
        url = f"{self._base_url}/v1/tasks/{task_id}/stream"
        async with httpx.AsyncClient(timeout=None) as client:
            async with client.stream("GET", url, headers=self._headers) as r:
                _raise_for_status(r)
                async for line in r.aiter_lines():
                    event = _parse_sse_line(line)
                    if event is not None:
                        yield event

    async def list_agents(self) -> List[AgentInfo]:
        return [AgentInfo(name=a["name"], description=a["description"]) for a in await self._request("GET", "/v1/agents")]

    async def run_agent(
        self, name: str, goal: str, options: Optional[Dict[str, Any]] = None
    ) -> AgentResult:
        data = await self._request("POST", f"/v1/agents/{name}/run", json=_build_task_payload(goal, options=options))
        return AgentResult(data["agent"], data["status"], data["output"], data.get("errors", []))


__all__ = [
    "AgentInfo", "AgentResult", "ContentTemplate", "MekongAPIError",
    "MekongAsyncClient", "MekongClient", "PerformanceData", "RenderedContent",
    "StepDetail", "Task", "TaskResult", "TemplateMetadata",
    "_parse_sse_line", "_parse_step", "_parse_task", "_raise_for_status",
]
