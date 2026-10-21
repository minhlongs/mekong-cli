# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
Mekong CLI - Monitor Agent

Monitoring & health check agent for services and system resources.
"""

import platform
import subprocess
from typing import Dict, List

from src.core.agent_base import AgentBase, Result, Task
from .monitor_agent_checks import HealthCheckResult, MonitorAgentChecksMixin


class MonitorAgent(MonitorAgentChecksMixin, AgentBase):
    """
    Monitoring agent for service health checks and system resources.

    Capabilities:
    - HTTP endpoint health checks
    - Port availability checks
    - System resource monitoring (CPU, RAM, disk)
    - Alert on threshold violations
    """

    def __init__(self, name: str = "monitor", max_retries: int = 2) -> None:
        super().__init__(name, max_retries)
        self.thresholds = {
            "cpu_percent": 80.0,
            "memory_percent": 85.0,
            "disk_percent": 90.0,
            "response_time_ms": 1000.0,
        }

    def plan(self, input_data: str) -> List[Task]:
        """Parse monitoring input into tasks."""
        tasks: List[Task] = []
        input_lower = input_data.lower()

        if "health" in input_lower and ("http" in input_lower or "endpoint" in input_lower):
            tasks.append(Task(
                id="health_check",
                description="Check HTTP endpoint health",
                input={"type": "http_health", "query": input_data},
            ))

        if "port" in input_lower:
            tasks.append(Task(
                id="port_check",
                description="Check port availability",
                input={"type": "port_check", "query": input_data},
            ))

        if "system" in input_lower or "resource" in input_lower or "cpu" in input_lower or "memory" in input_lower:
            tasks.append(Task(
                id="system_resources",
                description="Monitor system resources",
                input={"type": "system_resources", "query": input_data},
            ))

        if not tasks:
            tasks.append(Task(
                id="full_health",
                description="Run full system health check",
                input={"type": "full_health", "query": input_data},
            ))

        return tasks

    def execute(self, task: Task) -> Result:
        """Execute monitoring task."""
        task_type = task.input.get("type", "health_check")

        try:
            if task_type == "http_health":
                return self._execute_http_health(task)
            elif task_type == "port_check":
                return self._execute_port_check(task)
            elif task_type == "system_resources":
                return self._execute_system_resources(task)
            elif task_type == "full_health":
                return self._execute_full_health(task)
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

    def set_threshold(self, metric: str, value: float) -> None:
        """Update alert threshold."""
        if metric in self.thresholds:
            self.thresholds[metric] = value

    def get_thresholds(self) -> Dict[str, float]:
        """Return current thresholds."""
        return self.thresholds.copy()


__all__ = ["MonitorAgent", "HealthCheckResult", "platform", "subprocess"]
