# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""NetworkAgent executor helpers for ping, latency, port scan, DNS, and traceroute."""

import re
from typing import Any, Dict, List, Optional

from src.core.agent_base import Result, Task


def _net_mod() -> Any:
    import src.agents.network_agent as _mod
    return _mod


class NetworkAgentExecutorsMixin:
    """Mixin providing network test execution methods for NetworkAgent."""

    timeout_secs: int

    def _extract_host(self, query: str) -> Optional[str]:
        """Extract hostname/IP from query string."""
        url_match = re.search(r"https?://([a-zA-Z0-9.\-]+)", query)
        if url_match:
            return url_match.group(1)
        host_match = re.search(
            r"\b([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}|(?:\d{1,3}\.){3}\d{1,3})\b", query
        )
        return host_match.group(1) if host_match else None

    def _execute_ping(self, task: Task) -> Result:
        """Ping host to test connectivity."""
        host = self._extract_host(task.input.get("query", ""))
        if not host:
            return Result(task_id=task.id, success=False, output=None, error="No host found in query")
        sub = _net_mod().subprocess
        try:
            proc = sub.run(["ping", "-c", "3", "-W", "5000", host], capture_output=True, text=True, timeout=15)
            output = proc.stdout
            rtt_match = re.search(r"rtt min/avg/max/stddev = ([\d.]+)/([\d.]+)/([\d.]+)/([\d.]+)", output)
            loss_match = re.search(r"(\d+)% packet loss", output)
            data: Dict[str, Any] = {"host": host, "reachable": proc.returncode == 0}
            if rtt_match:
                data["min_ms"] = float(rtt_match.group(1))
                data["avg_ms"] = float(rtt_match.group(2))
                data["max_ms"] = float(rtt_match.group(3))
            if loss_match:
                data["packet_loss_percent"] = float(loss_match.group(1))
            ok = proc.returncode == 0 and data.get("packet_loss_percent", 100) < 100
            return Result(task_id=task.id, success=ok, output=data)
        except sub.TimeoutExpired:
            return Result(task_id=task.id, success=False, output=None, error=f"Ping timeout for {host}")

    def _execute_latency(self, task: Task) -> Result:
        """Test HTTP endpoint latency."""
        url_match = re.search(r"https?://\S+", task.input.get("query", ""))
        if not url_match:
            return Result(task_id=task.id, success=False, output=None, error="No HTTP URL found in query")
        url = url_match.group(0).strip()
        sub = _net_mod().subprocess
        cmd = [
            "curl", "-s", "-o", "/dev/null", "-w",
            "%{http_code} %{time_total} %{time_connect}", "--max-time", str(self.timeout_secs), url,
        ]
        try:
            proc = sub.run(cmd, capture_output=True, text=True, timeout=self.timeout_secs + 5)
            parts = proc.stdout.strip().split()
            if len(parts) >= 3:
                code = int(parts[0])
                total_ms, conn_ms = float(parts[1]) * 1000, float(parts[2]) * 1000
                return Result(
                    task_id=task.id,
                    success=200 <= code < 400,
                    output={
                        "url": url, "status_code": code,
                        "total_latency_ms": total_ms, "connect_latency_ms": conn_ms,
                        "ttfb_ms": total_ms - conn_ms,
                    },
                )
            return Result(task_id=task.id, success=False, output=None, error=f"Failed to parse curl output: {proc.stdout}")
        except sub.TimeoutExpired:
            return Result(task_id=task.id, success=False, output=None, error=f"Latency test timeout for {url}")

    def _execute_port_scan(self, task: Task) -> Result:
        """Scan common ports on host."""
        query = task.input.get("query", "")
        host = self._extract_host(query) or "localhost"
        port_match = re.search(r"port\s*(\d+)", query.lower())
        ports = [int(port_match.group(1))] if port_match else [22, 80, 443, 3000, 5000, 5432, 6379, 8080, 8443, 9000]
        open_ports: List[int] = []
        closed_ports: List[int] = []
        sock_mod = _net_mod().socket
        for port in ports:
            try:
                sock = sock_mod.socket(sock_mod.AF_INET, sock_mod.SOCK_STREAM)
                sock.settimeout(1)
                if sock.connect_ex((host, port)) == 0:
                    open_ports.append(port)
                else:
                    closed_ports.append(port)
                sock.close()
            except Exception:
                closed_ports.append(port)
        return Result(
            task_id=task.id,
            success=len(open_ports) > 0,
            output={"host": host, "open_ports": open_ports, "closed_ports": closed_ports, "scanned": len(ports)},
        )

    def _execute_dns_check(self, task: Task) -> Result:
        """Check DNS resolution."""
        query = task.input.get("query", "")
        domain = self._extract_host(query)
        if not domain:
            m = re.search(r"\b([a-zA-Z0-9.\-]+\.[a-zA-Z]{2,})\b", query)
            domain = m.group(1) if m else None
        if not domain:
            return Result(task_id=task.id, success=False, output=None, error="No domain found in query")
        sub = _net_mod().subprocess
        try:
            proc = sub.run(["dig", "+short", domain], capture_output=True, text=True, timeout=10)
            if proc.returncode != 0 or not proc.stdout.strip():
                proc = sub.run(["nslookup", domain], capture_output=True, text=True, timeout=10)
            if proc.returncode == 0 and proc.stdout.strip():
                ips = re.findall(r"\b(?:\d{1,3}\.){3}\d{1,3}\b", proc.stdout)
                return Result(
                    task_id=task.id, success=len(ips) > 0,
                    output={"domain": domain, "resolved": True, "ip_addresses": ips, "raw_output": proc.stdout[:500]},
                )
            return Result(task_id=task.id, success=False, output=None, error=f"DNS resolution failed for {domain}")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=str(e))

    def _execute_traceroute(self, task: Task) -> Result:
        """Trace network path to host."""
        host = self._extract_host(task.input.get("query", ""))
        if not host:
            return Result(task_id=task.id, success=False, output=None, error="No host found in query")
        sub = _net_mod().subprocess
        try:
            proc = sub.run(["traceroute", "-m", "10", "-w", "2000", host], capture_output=True, text=True, timeout=60)
            hops = [ln.strip() for ln in proc.stdout.strip().split("\n")[1:11] if ln.strip()]
            return Result(
                task_id=task.id, success=proc.returncode == 0 or len(hops) > 0,
                output={"host": host, "hops": hops, "hop_count": len(hops), "raw_output": proc.stdout[:1000]},
            )
        except sub.TimeoutExpired:
            return Result(task_id=task.id, success=False, output=None, error="Traceroute timeout")
        except Exception as e:
            return Result(task_id=task.id, success=False, output=None, error=str(e))
