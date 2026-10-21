# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Network probing and daemon process management helpers for Gateway CLI."""

from __future__ import annotations

import json
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable, Optional, Tuple

from rich.console import Console
from rich.panel import Panel

console = Console()
PID_FILE_PATH = Path(".mekong/gateway.pid")


def is_port_in_use(host: str, port: int, timeout: float = 0.5) -> bool:
    """Check if a network port is already in use using socket probe."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        try:
            return sock.connect_ex((host, port)) == 0
        except socket.gaierror:
            return sock.connect_ex(("127.0.0.1", port)) == 0
        except OSError:
            return False


def fetch_json_endpoint(
    url: str, timeout: float = 2.0
) -> Tuple[int, Optional[dict[str, Any]], dict[str, str]]:
    """Fetch JSON payload from an HTTP endpoint using standard library urllib."""
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mekong-CLI-Gateway/1.0", "Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            status = resp.status
            headers = {k.lower(): v for k, v in resp.headers.items()}
            raw = resp.read().decode("utf-8", errors="replace")
            try:
                data = json.loads(raw)
            except Exception:
                data = None
            return status, data, headers
    except urllib.error.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            data = json.loads(raw)
        except Exception:
            data = None
        return exc.code, data, {k.lower(): v for k, v in exc.headers.items()}
    except Exception:
        return 0, None, {}


def query_gateway_status(
    host: str, port: int, timeout: float = 2.0
) -> Tuple[bool, Optional[dict[str, Any]], Optional[dict[str, Any]]]:
    """Query /health and /api/v1/gateway/metrics from the running gateway server."""
    base_url = f"http://{host}:{port}"
    health_url = f"{base_url}/health"
    metrics_url = f"{base_url}/api/v1/gateway/metrics"

    health_code, health_data, _ = fetch_json_endpoint(health_url, timeout=timeout)
    if health_code != 200 or not health_data:
        return False, None, None

    metrics_code, metrics_data, _ = fetch_json_endpoint(metrics_url, timeout=timeout)
    return True, health_data, metrics_data if metrics_code == 200 else None


def format_uptime(seconds: float) -> str:
    """Format seconds into readable uptime string (e.g. 1h 24m 12s)."""
    s = int(seconds)
    if s < 60:
        return f"{s}s"
    m, s = divmod(s, 60)
    if m < 60:
        return f"{m}m {s}s"
    h, m = divmod(m, 60)
    return f"{h}h {m}m {s}s"


def start_daemon(
    host: str,
    port: int,
    json_output: bool,
    status_fn: Callable[..., Tuple[bool, Optional[dict[str, Any]], Optional[dict[str, Any]]]] = query_gateway_status,
) -> None:
    """Spawn the gateway server in a detached background daemon process."""
    cmd = [sys.executable, "-m", "src.main", "gateway", "--host", host, "--port", str(port)]
    PID_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    PID_FILE_PATH.write_text(str(proc.pid), encoding="utf-8")

    time.sleep(1.0)
    is_online, _, _ = status_fn(host, port, timeout=2.0)

    if json_output:
        print(
            json.dumps(
                {
                    "ok": True,
                    "status": "started" if is_online else "starting",
                    "pid": proc.pid,
                    "host": host,
                    "port": port,
                    "url": f"http://{host}:{port}",
                },
                indent=2,
            )
        )
    else:
        status_txt = "[green]ONLINE[/green]" if is_online else "[yellow]INITIALIZING[/yellow]"
        console.print(
            Panel(
                f"[bold green]Gateway daemon spawned successfully![/bold green]\n"
                f"[bold]PID:[/bold] {proc.pid}\n"
                f"[bold]Address:[/bold] http://{host}:{port}\n"
                f"[bold]Status:[/bold] {status_txt}\n\n"
                f"[dim]Stop anytime with: [cyan]mekong gateway --stop[/cyan][/dim]",
                title="🌐 Background Daemon Active",
                border_style="green",
            )
        )


def stop_daemon(json_output: bool) -> None:
    """Terminate the gateway background process using saved PID."""
    if not PID_FILE_PATH.exists():
        msg = "No running gateway daemon found (.mekong/gateway.pid does not exist)."
        if json_output:
            print(json.dumps({"ok": False, "status": "not_running", "message": msg}, indent=2))
        else:
            console.print(f"[yellow]{msg}[/yellow]")
        return

    try:
        pid = int(PID_FILE_PATH.read_text(encoding="utf-8").strip())
        os.kill(pid, signal.SIGTERM)
        time.sleep(0.5)
        try:
            os.kill(pid, 0)
            os.kill(pid, signal.SIGKILL)
        except OSError:
            pass
        PID_FILE_PATH.unlink(missing_ok=True)
        if json_output:
            print(json.dumps({"ok": True, "status": "stopped", "pid": pid}, indent=2))
        else:
            console.print(f"[bold green]Gateway process (PID: {pid}) stopped successfully.[/bold green]")
    except Exception as exc:
        PID_FILE_PATH.unlink(missing_ok=True)
        if json_output:
            print(json.dumps({"ok": False, "status": "error", "error": str(exc)}, indent=2))
        else:
            console.print(f"[bold red]Failed to stop daemon:[/bold red] {exc}")
