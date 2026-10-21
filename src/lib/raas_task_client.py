# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""RaaS Task Client — Subagent Delegation via Gateway."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Dict, List, Optional

import requests

from src.core.raas_audit_logger import get_audit_logger
from src.core.raas_auth import RaaSAuthClient, get_auth_client
from src.lib.raas_task_models import (
    GatewayConfig,
    SubagentType,
    TaskRequest,
    TaskResult,
    TaskStatus,
)

logger = logging.getLogger(__name__)


class RaasTaskClient:
    """RaaS Task Client for subagent delegation."""

    def __init__(
        self,
        gateway_url: Optional[str] = None,
        auth_client: Optional[RaaSAuthClient] = None,
        config: Optional[GatewayConfig] = None,
    ):
        self.config = config or GatewayConfig()
        if gateway_url:
            self.config.base_url = gateway_url
        self.auth_client = auth_client or get_auth_client()
        self._audit_logger = get_audit_logger()
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
            "User-Agent": "mekong-cli/0.2.0",
        })

    def _get_base_url(self) -> str:
        return f"{self.config.base_url}/{self.config.api_version}"

    def _get_auth_headers(self) -> Dict[str, str]:
        headers: Dict[str, str] = {}
        token = self.auth_client._load_credentials().get("token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        cert_headers = self.auth_client._get_certificate_headers()
        if cert_headers:
            headers.update(cert_headers)
        return headers

    def _make_request(
        self, method: str, endpoint: str,
        data: Optional[Dict[str, Any]] = None, timeout: Optional[int] = None,
    ) -> requests.Response:
        url = f"{self._get_base_url()}/{endpoint.lstrip('/')}"
        response = self._session.request(
            method=method, url=url, headers=self._get_auth_headers(),
            json=data, timeout=timeout or self.config.timeout_seconds,
        )
        response.raise_for_status()
        return response

    def delegate_task(
        self, subagent_type: SubagentType, goal: str, complexity: str = "moderate",
        context: Optional[Dict[str, Any]] = None, options: Optional[Dict[str, Any]] = None,
        timeout_seconds: int = 300,
    ) -> TaskResult:
        """Delegate task to subagent via RaaS Gateway."""
        start_time = time.time()
        request = TaskRequest(
            subagent_type=subagent_type, goal=goal, complexity=complexity,
            context=context, options=options or {}, timeout_seconds=timeout_seconds,
        )
        self._audit_logger.log_event(
            event_type="subagent_delegation",
            data={"subagent_type": subagent_type.value, "goal": goal[:100], "complexity": complexity},
        )
        try:
            resp = self._make_request("POST", "/tasks/delegate", request.to_dict(), timeout_seconds + 10).json()
            ms = (time.time() - start_time) * 1000
            res = TaskResult(
                task_id=resp.get("task_id", "unknown"), status=TaskStatus(resp.get("status", "completed")),
                output=resp.get("output"), error=resp.get("error"), subagent_type=subagent_type.value,
                execution_time_ms=ms, credits_consumed=resp.get("credits_consumed", 1),
                metadata=resp.get("metadata", {}),
            )
            self._audit_logger.log_event(
                event_type="subagent_result",
                data={"task_id": res.task_id, "status": res.status.value, "execution_time_ms": ms, "credits_consumed": res.credits_consumed},
            )
            return res
        except requests.HTTPError as e:
            ms = (time.time() - start_time) * 1000
            err_data = e.response.json() if e.response.content else {}
            err_msg = err_data.get("error", str(e))
            self._audit_logger.log_event(
                event_type="subagent_error",
                data={"subagent_type": subagent_type.value, "error": err_msg, "status_code": e.response.status_code},
            )
            return TaskResult(task_id="unknown", status=TaskStatus.FAILED, error=err_msg, subagent_type=subagent_type.value, execution_time_ms=ms)
        except requests.RequestException as e:
            return TaskResult(task_id="unknown", status=TaskStatus.FAILED, error=f"Gateway unavailable: {str(e)}", subagent_type=subagent_type.value, execution_time_ms=(time.time() - start_time) * 1000)

    async def delegate_task_async(self, subagent_type: SubagentType, goal: str, **kwargs: Any) -> TaskResult:
        return await asyncio.get_event_loop().run_in_executor(None, lambda: self.delegate_task(subagent_type, goal, **kwargs))

    def get_task_status(self, task_id: str) -> TaskResult:
        try:
            d = self._make_request("GET", f"/tasks/{task_id}").json()
            return TaskResult(
                task_id=task_id, status=TaskStatus(d.get("status", "pending")), output=d.get("output"),
                error=d.get("error"), subagent_type=d.get("subagent_type"), execution_time_ms=d.get("execution_time_ms"),
                credits_consumed=d.get("credits_consumed", 0), metadata=d.get("metadata", {}),
            )
        except requests.RequestException as e:
            return TaskResult(task_id=task_id, status=TaskStatus.FAILED, error=f"Status check failed: {str(e)}")

    def cancel_task(self, task_id: str) -> bool:
        try:
            self._make_request("POST", f"/tasks/{task_id}/cancel")
            return True
        except requests.RequestException:
            return False

    def get_available_subagents(self) -> List[Dict[str, Any]]:
        try:
            return self._make_request("GET", "/subagents").json().get("subagents", [])
        except requests.RequestException:
            return [{"type": t.value, "name": t.value.replace("-", " ").title()} for t in SubagentType]

    def get_usage_summary(self) -> Dict[str, Any]:
        try:
            return self._make_request("GET", "/usage/summary").json()
        except requests.RequestException as e:
            return {"error": str(e), "available": False}


_task_client: Optional[RaasTaskClient] = None


def get_task_client(gateway_url: Optional[str] = None, auth_client: Optional[RaaSAuthClient] = None) -> RaasTaskClient:
    global _task_client
    if _task_client is None:
        _task_client = RaasTaskClient(gateway_url=gateway_url, auth_client=auth_client)
    return _task_client


def reset_task_client() -> None:
    global _task_client
    _task_client = None


def delegate_to_subagent(subagent_type: str, goal: str, complexity: str = "moderate", context: Optional[Dict[str, Any]] = None) -> TaskResult:
    try:
        agent_type = SubagentType(subagent_type.lower().replace("_", "-"))
    except ValueError:
        return TaskResult(task_id="unknown", status=TaskStatus.FAILED, error=f"Unknown subagent type: {subagent_type}")
    return get_task_client().delegate_task(subagent_type=agent_type, goal=goal, complexity=complexity, context=context)


__all__ = [
    "RaasTaskClient", "SubagentType", "TaskStatus", "TaskRequest",
    "TaskResult", "GatewayConfig", "get_task_client", "delegate_to_subagent",
]
