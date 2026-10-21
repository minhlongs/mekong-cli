# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""MonitorAgent health check executors for HTTP, port, and system resources."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.agent_base import Result, Task


@dataclass
class HealthCheckResult:
    """Result of a health check."""

    service: str
    status: str  # "healthy", "unhealthy", "unknown"
    response_time_ms: Optional[float] = None
    error: Optional[str] = None
    metrics: Optional[Dict[str, Any]] = None


def _mon_mod() -> Any:
    import src.agents.monitor_agent as _mod
    return _mod


class MonitorAgentChecksMixin:
    """Mixin providing health check and system resource monitoring methods."""

    thresholds: Dict[str, float]

    def _execute_http_health(self, task: Task) -> Result:
        """Check HTTP endpoint health using curl."""
        url_match = re.search(r"https?://\S+", task.input.get("query", ""))
        if not url_match:
            return Result(task_id=task.id, success=False, output=None, error="No HTTP URL found in query")
        url = url_match.group(0).strip()
        sub = _mon_mod().subprocess
        cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code} %{time_total}", "--max-time", "10", url]
        try:
            proc = sub.run(cmd, capture_output=True, text=True, timeout=15)
            parts = proc.stdout.strip().split()
            if len(parts) >= 2:
                status_code = int(parts[0])
                response_time = float(parts[1]) * 1000
                is_healthy = 200 <= status_code < 400
                result = HealthCheckResult(
                    service=url,
                    status="healthy" if is_healthy else "unhealthy",
                    response_time_ms=response_time,
                    metrics={"status_code": status_code},
                )
                alert = ""
                if response_time > self.thresholds["response_time_ms"]:
                    alert = f"SLOW: {response_time:.0f}ms > {self.thresholds['response_time_ms']:.0f}ms threshold"
                return Result(
                    task_id=task.id,
                    success=is_healthy,
                    output={
                        "service": url,
                        "status": result.status,
                        "status_code": status_code,
                        "response_time_ms": response_time,
                        "alert": alert,
                    },
                )
            return Result(task_id=task.id, success=False, output=None, error=f"Failed to parse curl output: {proc.stdout}")
        except sub.TimeoutExpired:
            return Result(task_id=task.id, success=False, output=None, error=f"Health check timeout for {url}")

    def _execute_port_check(self, task: Task) -> Result:
        """Check if port is open/available."""
        port_match = re.search(r"\b(\d{2,5})\b", task.input.get("query", ""))
        if not port_match:
            return Result(task_id=task.id, success=False, output=None, error="No port number found in query")
        port = int(port_match.group(1))
        if port < 1 or port > 65535:
            return Result(task_id=task.id, success=False, output=None, error=f"Invalid port: {port}")
        sub = _mon_mod().subprocess
        try:
            proc = sub.run(["nc", "-z", "localhost", str(port)], capture_output=True, text=True, timeout=5)
            is_open = proc.returncode == 0
            return Result(
                task_id=task.id,
                success=is_open,
                output={"port": port, "status": "open" if is_open else "closed", "host": "localhost"},
            )
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=str(e))

    def _execute_system_resources(self, task: Task) -> Result:
        """Monitor system resources (CPU, memory, disk)."""
        metrics: Dict[str, Any] = {}
        alerts: List[str] = []
        sub = _mon_mod().subprocess
        plat = _mon_mod().platform
        try:
            cpu_res = sub.run(["top", "-l", "1"], capture_output=True, text=True, timeout=5)
            if cpu_res.returncode == 0:
                cpu_match = re.search(r"(\d+\.?\d*)%\s+user", cpu_res.stdout)
                if cpu_match:
                    cpu_pct = float(cpu_match.group(1))
                    metrics["cpu_percent"] = cpu_pct
                    metrics["cpu_user"] = cpu_pct
                    if cpu_pct > self.thresholds["cpu_percent"]:
                        alerts.append(f"CPU HIGH: {cpu_pct:.1f}%")

            mem_res = sub.run(["vm_stat"], capture_output=True, text=True, timeout=5)
            if mem_res.returncode == 0:
                pages_match = re.search(r"Pages active:\s+(\d+)", mem_res.stdout)
                if pages_match:
                    pages_active = int(pages_match.group(1))
                    tot_res = sub.run(["sysctl", "-n", "hw.memsize"], capture_output=True, text=True, timeout=5)
                    if tot_res.returncode == 0:
                        total_bytes = int(tot_res.stdout.strip())
                        mem_pct = ((pages_active * 4096) / total_bytes) * 100
                        metrics["memory_percent"] = mem_pct
                        if mem_pct > self.thresholds["memory_percent"]:
                            alerts.append(f"MEMORY HIGH: {mem_pct:.1f}%")

            disk_res = sub.run(["df", "-h", "/"], capture_output=True, text=True, timeout=5)
            if disk_res.returncode == 0:
                disk_match = re.search(r"(\d+)%", disk_res.stdout)
                if disk_match:
                    try:
                        disk_pct = float(disk_match.group(1))
                        metrics["disk_percent"] = disk_pct
                        if disk_pct > self.thresholds["disk_percent"]:
                            alerts.append(f"DISK HIGH: {disk_pct:.1f}%")
                    except ValueError:
                        pass

            return Result(
                task_id=task.id,
                success=len(alerts) == 0,
                output={
                    "metrics": metrics,
                    "alerts": alerts,
                    "thresholds": self.thresholds,
                    "platform": plat.system(),
                },
            )
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=f"System resource check failed: {str(e)}")

    def _execute_full_health(self, task: Task) -> Result:
        """Run complete health check (HTTP + system)."""
        system_result = self._execute_system_resources(task)
        sub = _mon_mod().subprocess
        ts_res = sub.run(["date", "-u", "+%Y-%m-%dT%H:%M:%SZ"], capture_output=True, text=True)
        timestamp = ts_res.stdout.strip() if ts_res.returncode == 0 else "unknown"
        return Result(
            task_id=task.id,
            success=system_result.success,
            output={"type": "full_health", "system": system_result.output, "timestamp": timestamp},
        )
