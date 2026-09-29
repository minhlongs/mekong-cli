# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/gateway_command.py — Production Gateway & Event Streaming CLI.

Provides command-line surface for Mekong Gateway lifecycle management:
- mekong gateway [--host HOST] [--port PORT] [--status] [--json]
- Starts the production API server and real-time streaming hub (SSE + WebSocket).
- Queries live gateway health, active SSE/WS streams, and rate limiter telemetry.
- Outputs human-friendly Rich status cards or machine-readable JSON for CI/MCP.
"""

from __future__ import annotations

import json
import os
import signal
import socket
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Optional, Tuple

import typer
from rich.box import ROUNDED, SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

PID_FILE_PATH = Path(".mekong/gateway.pid")


# ---------------------------------------------------------------------------
# Network & Probing Utilities (Standard Library Only)
# ---------------------------------------------------------------------------

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


def fetch_json_endpoint(url: str, timeout: float = 2.0) -> Tuple[int, Optional[dict[str, Any]], dict[str, str]]:
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


# ---------------------------------------------------------------------------
# Rich Terminal Presentation Layouts
# ---------------------------------------------------------------------------

def render_status_card(
    host: str,
    port: int,
    health: Optional[dict[str, Any]],
    metrics: Optional[dict[str, Any]],
) -> None:
    """Render Rich status card and metrics tables for an online gateway."""
    version = health.get("version", "1.0.0") if health else "1.0.0"
    uptime_sec = health.get("uptime_seconds", health.get("uptime", 0.0)) if health else 0.0
    uptime_str = format_uptime(uptime_sec)

    # 1. Header Overview Panel
    console.print(
        Panel(
            f"[bold green]● Status: ONLINE[/bold green]\n"
            f"[bold]Address:[/bold] http://{host}:{port}\n"
            f"[bold]Uptime:[/bold] {uptime_str}  |  [bold]Version:[/bold] v{version}\n"
            f"[dim]Streaming Hub: SSE & WebSocket Duplex Engine with Sliding-Window Rate Limiting[/dim]",
            title="[bold cyan]🌐 Mekong Production Gateway[/bold cyan]",
            border_style="green",
            box=ROUNDED,
        )
    )

    # 2. Real-Time Streaming & Connections Table
    stream_table = Table(
        title="Real-Time Event Streaming Hub",
        box=SIMPLE_HEAVY,
        header_style="bold magenta",
    )
    stream_table.add_column("Channel / Metric", style="cyan")
    stream_table.add_column("Current Active", justify="right", style="bold green")
    stream_table.add_column("Total Accumulated", justify="right", style="dim")
    stream_table.add_column("Protocol / Endpoint", style="white")

    active_streams = (
        metrics.get("active_streams", health.get("active_streams", 0))
        if metrics
        else (health.get("active_streams", 0) if health else 0)
    )
    active_subscribers = (
        metrics.get("active_subscribers", health.get("active_subscribers", 0))
        if metrics
        else (health.get("active_subscribers", 0) if health else 0)
    )
    active_ws = (
        metrics.get("active_ws_connections", health.get("active_ws_connections", active_subscribers))
        if metrics
        else (health.get("active_ws_connections", active_subscribers) if health else 0)
    )
    total_streams = metrics.get("total_streams_opened", active_streams) if metrics else active_streams

    stream_table.add_row(
        "SSE Mission Streams",
        str(active_streams),
        str(total_streams),
        f"GET http://{host}:{port}/api/v1/missions/{{id}}/stream",
    )
    stream_table.add_row(
        "WebSocket Duplex Clients",
        str(active_ws),
        str(metrics.get("total_requests", active_ws) if metrics else "-"),
        f"WS ws://{host}:{port}/ws/missions/{{id}}",
    )
    console.print(stream_table)
    console.print()

    # 3. Sliding-Window Rate Limiting Telemetry Table
    rate_limits = metrics.get("rate_limits", {}) if metrics else {}
    rl_table = Table(
        title="Sliding-Window Rate Limiter & Tier Quotas",
        box=SIMPLE_HEAVY,
        header_style="bold yellow",
    )
    rl_table.add_column("Tenant Tier", style="cyan")
    rl_table.add_column("Quota (req/min)", justify="right")
    rl_table.add_column("Tokens Remaining", justify="right", style="bold green")
    rl_table.add_column("Throttled (429)", justify="right", style="bold red")

    tiers = [
        ("FREE", "60", str(rate_limits.get("free_remaining", "60"))),
        ("PRO", "600", str(rate_limits.get("pro_remaining", "600"))),
        ("ENTERPRISE", "3,000", str(rate_limits.get("enterprise_remaining", "3,000"))),
    ]
    rejected_count = (
        metrics.get("rate_limit_rejections", rate_limits.get("total_rejected", 0))
        if metrics
        else rate_limits.get("total_rejected", 0)
    )
    for idx, (tier_name, quota, remaining) in enumerate(tiers):
        rejections = str(rejected_count) if idx == 0 else "0"
        rl_table.add_row(tier_name, quota, remaining, rejections)

    console.print(rl_table)
    console.print()

    # 4. Latency Percentiles (if present)
    latency = metrics.get("latency_percentiles", {}) if metrics else {}
    if latency:
        lat_table = Table(
            title="Gateway Latency Percentiles",
            box=SIMPLE_HEAVY,
            header_style="bold blue",
        )
        lat_table.add_column("Metric", style="cyan")
        lat_table.add_column("p50", justify="right")
        lat_table.add_column("p90", justify="right")
        lat_table.add_column("p99", justify="right")
        lat_table.add_row(
            "Event Emission Latency",
            f"{latency.get('p50_ms', 1.0):.2f} ms",
            f"{latency.get('p90_ms', 2.5):.2f} ms",
            f"{latency.get('p99_ms', 6.0):.2f} ms",
        )
        console.print(lat_table)
        console.print()


def render_offline_card(host: str, port: int) -> None:
    """Render Rich offline alert panel with actionable startup instructions."""
    console.print(
        Panel(
            f"[bold red]● Status: OFFLINE[/bold red]\n\n"
            f"The Mekong Gateway server is [bold red]not reachable[/bold red] at http://{host}:{port}.\n"
            f"[dim]No process responded on {host}:{port}/health.[/dim]\n\n"
            f"[bold]To start the gateway server:[/bold]\n"
            f"  [bold cyan]mekong gateway --host {host} --port {port}[/bold cyan]\n\n"
            f"[dim]Or run in background daemon mode:[/dim]\n"
            f"  [bold cyan]mekong gateway --host {host} --port {port} --daemon[/bold cyan]",
            title="[bold red]🌐 Mekong Gateway Offline[/bold red]",
            border_style="red",
            box=ROUNDED,
        )
    )


# ---------------------------------------------------------------------------
# Typer Command Registration
# ---------------------------------------------------------------------------

def register_gateway_command(app: typer.Typer) -> None:
    """Register the 'gateway' command onto the root Typer application."""

    @app.command(name="gateway")
    def gateway(
        host: str = typer.Option(
            "127.0.0.1",
            "--host",
            "-H",
            help="Server bind address",
        ),
        port: int = typer.Option(
            8000,
            "--port",
            "-p",
            help="Server port",
        ),
        status: bool = typer.Option(
            False,
            "--status",
            help="Query gateway health and streaming metrics",
        ),
        json_output: bool = typer.Option(
            False,
            "--json",
            help="Output machine-readable JSON",
        ),
        daemon: bool = typer.Option(
            False,
            "--daemon",
            "-d",
            help="Run gateway server in a detached background daemon process",
        ),
        stop: bool = typer.Option(
            False,
            "--stop",
            help="Stop running background gateway daemon process",
        ),
        reload: bool = typer.Option(
            False,
            "--reload",
            help="Enable auto-reload for development server",
        ),
    ) -> None:
        """🌐 Gateway: Production Gateway & Real-Time Event Streaming Hub."""
        # 1. Parameter Validation
        if not (1 <= port <= 65535):
            err_msg = f"Invalid port: {port}. Port must be between 1 and 65535."
            if json_output:
                print(json.dumps({"ok": False, "status": "error", "error": err_msg}, indent=2))
            else:
                console.print(f"[bold red]Error:[/bold red] {err_msg}")
            raise typer.Exit(code=1)

        # 2. Daemon Stop Action
        if stop:
            _stop_daemon(json_output=json_output)
            return

        # 3. Status Query Mode (Explicit --status OR headless --json without daemon start)
        if status or (json_output and not daemon):
            is_online, health, metrics = query_gateway_status(host=host, port=port)
            if is_online:
                if json_output:
                    uptime_val = health.get("uptime_seconds", health.get("uptime", 0.0)) if health else 0.0
                    streams_val = (
                        metrics.get("active_streams", health.get("active_streams", 0))
                        if metrics
                        else (health.get("active_streams", 0) if health else 0)
                    )
                    ws_val = (
                        metrics.get("active_ws_connections", metrics.get("active_subscribers", health.get("active_ws_connections", 0)))
                        if metrics
                        else (health.get("active_ws_connections", 0) if health else 0)
                    )
                    rejections_val = (
                        metrics.get("rate_limit_rejections", health.get("rate_limit_rejections", 0))
                        if metrics
                        else (health.get("rate_limit_rejections", 0) if health else 0)
                    )
                    latency_val = metrics.get("latency_percentiles", {}) if metrics else {}

                    payload = {
                        "ok": True,
                        "status": "online",
                        "host": host,
                        "port": port,
                        "url": f"http://{host}:{port}",
                        "uptime": uptime_val,
                        "streams": streams_val,
                        "ws_connections": ws_val,
                        "rate_limiting_rejections": rejections_val,
                        "latency_percentiles": latency_val,
                        "health": health or {},
                        "metrics": metrics or {},
                    }
                    print(json.dumps(payload, indent=2))
                else:
                    render_status_card(host=host, port=port, health=health, metrics=metrics)
                return
            else:
                err_msg = f"Gateway server is not reachable at http://{host}:{port}"
                if json_output:
                    payload = {
                        "ok": False,
                        "status": "offline",
                        "host": host,
                        "port": port,
                        "error": err_msg,
                    }
                    print(json.dumps(payload, indent=2))
                else:
                    render_offline_card(host=host, port=port)
                raise typer.Exit(code=1)

        # 4. Port Conflict Detection (Server Start Requested)
        if is_port_in_use(host, port):
            is_gw, _, _ = query_gateway_status(host, port, timeout=0.8)
            if is_gw:
                err_msg = f"Gateway is already running on http://{host}:{port}"
                hint = "Use 'mekong gateway --status' to inspect it or specify a different port with '--port <PORT>'."
            else:
                err_msg = f"Port {port} on {host} is already in use by another application."
                hint = f"Free port {port} or specify another port using '--port <PORT>'."

            if json_output:
                print(json.dumps({"ok": False, "status": "conflict", "error": err_msg, "hint": hint}, indent=2))
            else:
                console.print(
                    Panel(
                        f"[bold red]❌ {err_msg}[/bold red]\n\n[dim]{hint}[/dim]",
                        title="Port Conflict",
                        border_style="red",
                    )
                )
            raise typer.Exit(code=1)

        # 5. Security & Token Resolution
        api_token = os.environ.get("MEKONG_API_TOKEN")
        is_prod = os.environ.get("MEKONG_ENV", "").lower() == "production"
        if not api_token:
            if is_prod:
                console.print(
                    Panel(
                        "[bold red]MEKONG_API_TOKEN is required in production![/bold red]\n"
                        "Please export MEKONG_API_TOKEN before starting the gateway.",
                        title="Security Error",
                        border_style="red",
                    )
                )
                raise typer.Exit(code=1)
            else:
                import secrets
                api_token = f"dev_{secrets.token_hex(8)}"
                os.environ["MEKONG_API_TOKEN"] = api_token

        # 6. Daemon Mode Start
        if daemon:
            _start_daemon(host=host, port=port, json_output=json_output)
            return

        # 7. Foreground Server Startup
        console.print(
            Panel(
                f"[bold]Address:[/bold] http://{host}:{port}\n"
                f"[bold]Health Probe:[/bold] http://{host}:{port}/health\n"
                f"[bold]Metrics Hub:[/bold] http://{host}:{port}/api/v1/gateway/metrics\n"
                f"[bold]SSE Stream:[/bold] http://{host}:{port}/api/v1/missions/{{id}}/stream\n"
                f"[bold]WebSocket:[/bold] ws://{host}:{port}/ws/missions/{{id}}\n"
                f"[bold]OpenClaw POST:[/bold] http://{host}:{port}/cmd\n"
                f"[bold]Washing Machine UI:[/bold] http://{host}:{port}/\n"
                f"[dim]Security Token: {'*' * (len(api_token) - 4) + api_token[-4:] if len(api_token) >= 4 else '***'}[/dim]\n\n"
                f"[bold green]Ready to stream missions and route events. Press Ctrl+C to stop.[/bold green]",
                title="[bold cyan]🌐 Mekong Gateway — Production Real-Time Event Hub[/bold cyan]",
                border_style="cyan",
                box=ROUNDED,
            )
        )

        import uvicorn

        try:
            uvicorn.run(
                "src.core.gateway:app",
                host=host,
                port=port,
                reload=reload,
                log_level="info",
            )
        except KeyboardInterrupt:
            console.print("\n[yellow]Gateway stopped by user.[/yellow]")


def _start_daemon(host: str, port: int, json_output: bool) -> None:
    """Spawn the gateway server in a detached background daemon process."""
    import subprocess

    cmd = [sys.executable, "-m", "src.main", "gateway", "--host", host, "--port", str(port)]
    PID_FILE_PATH.parent.mkdir(parents=True, exist_ok=True)

    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        start_new_session=True,
    )
    PID_FILE_PATH.write_text(str(proc.pid), encoding="utf-8")

    # Give server a moment to bind and verify
    time.sleep(1.0)
    is_online, _, _ = query_gateway_status(host, port, timeout=2.0)

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


def _stop_daemon(json_output: bool) -> None:
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
        # Check if process exited
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
