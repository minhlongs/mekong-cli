# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - Network Agent

Network & API testing agent for connectivity and latency checks.
"""

import socket
import subprocess
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.agent_base import AgentBase, Result, Task
from .network_agent_executors import NetworkAgentExecutorsMixin


@dataclass
class NetworkTestResult:
    """Result of network test."""

    target: str
    test_type: str
    success: bool
    latency_ms: Optional[float] = None
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class NetworkAgent(NetworkAgentExecutorsMixin, AgentBase):
    """
    Network testing agent for connectivity and performance.

    Capabilities:
    - HTTP/API latency testing
    - Ping/connectivity tests
    - Port scanning
    - DNS resolution checks
    - Network path tracing
    """

    def __init__(self, name: str = "network", max_retries: int = 2) -> None:
        super().__init__(name, max_retries)
        self.timeout_secs = 10

    def plan(self, input_data: str) -> List[Task]:
        """Parse network test input into tasks."""
        tasks: List[Task] = []
        input_lower = input_data.lower()

        if "ping" in input_lower or "connectivity" in input_lower:
            tasks.append(Task(
                id="ping_test",
                description="Test network connectivity",
                input={"type": "ping", "query": input_data},
            ))

        if "latency" in input_lower or "response" in input_lower:
            tasks.append(Task(
                id="latency_test",
                description="Test endpoint latency",
                input={"type": "latency", "query": input_data},
            ))

        if "scan" in input_lower and "port" in input_lower:
            tasks.append(Task(
                id="port_scan",
                description="Scan open ports",
                input={"type": "port_scan", "query": input_data},
            ))

        if "dns" in input_lower or "resolve" in input_lower:
            tasks.append(Task(
                id="dns_check",
                description="Check DNS resolution",
                input={"type": "dns", "query": input_data},
            ))

        if "trace" in input_lower or "traceroute" in input_lower:
            tasks.append(Task(
                id="trace_route",
                description="Trace network path",
                input={"type": "traceroute", "query": input_data},
            ))

        if not tasks:
            tasks.append(Task(
                id="connectivity",
                description="Run connectivity test",
                input={"type": "ping", "query": input_data},
            ))

        return tasks

    def execute(self, task: Task) -> Result:
        """Execute network test task."""
        task_type = task.input.get("type", "ping")

        try:
            if task_type == "ping":
                return self._execute_ping(task)
            elif task_type == "latency":
                return self._execute_latency(task)
            elif task_type == "port_scan":
                return self._execute_port_scan(task)
            elif task_type == "dns":
                return self._execute_dns_check(task)
            elif task_type == "traceroute":
                return self._execute_traceroute(task)
            else:
                return Result(
                    task_id=task.id,
                    success=False,
                    output=None,
                    error=f"Unknown task type: {task_type}",
                )
        except Exception as e:
            return Result(
                task_id=task.id,
                success=False,
                output=None,
                error=str(e),
            )


__all__ = ["NetworkAgent", "NetworkTestResult", "socket", "subprocess"]
