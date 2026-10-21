# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""cli/commands/gateway_command.py — Production Gateway & Event Streaming CLI."""

from __future__ import annotations

import json
import os
import sys
import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel

from src.cli.commands.gateway_command_probe import (
    PID_FILE_PATH,
    fetch_json_endpoint,
    format_uptime,
    is_port_in_use,
    query_gateway_status,
    start_daemon as _start_daemon_impl,
    stop_daemon as _stop_daemon,
)
from src.cli.commands.gateway_command_render import (
    build_status_json_payload,
    render_offline_card,
    render_status_card,
)

console = Console()


def _query_status_live(host: str, port: int, timeout: float = 2.0):
    """Look up query_gateway_status dynamically from this module to support unittest.mock.patch."""
    mod = sys.modules.get(__name__)
    fn = getattr(mod, "query_gateway_status", query_gateway_status)
    return fn(host=host, port=port, timeout=timeout)


def _start_daemon(host: str, port: int, json_output: bool) -> None:
    """Spawn the gateway server in a detached background daemon process."""
    _start_daemon_impl(host=host, port=port, json_output=json_output, status_fn=_query_status_live)


def register_gateway_command(app: typer.Typer) -> None:
    """Register the 'gateway' command onto the root Typer application."""

    @app.command(name="gateway")
    def gateway(
        host: str = typer.Option("127.0.0.1", "--host", "-H", help="Server bind address"),
        port: int = typer.Option(8000, "--port", "-p", help="Server port"),
        status: bool = typer.Option(False, "--status", help="Query gateway health and streaming metrics"),
        json_output: bool = typer.Option(False, "--json", help="Output machine-readable JSON"),
        daemon: bool = typer.Option(False, "--daemon", "-d", help="Run gateway server in a detached background daemon process"),
        stop: bool = typer.Option(False, "--stop", help="Stop running background gateway daemon process"),
        reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development server"),
    ) -> None:
        """🌐 Gateway: Production Gateway & Real-Time Event Streaming Hub."""
        if not (1 <= port <= 65535):
            err_msg = f"Invalid port: {port}. Port must be between 1 and 65535."
            if json_output:
                print(json.dumps({"ok": False, "status": "error", "error": err_msg}, indent=2))
            else:
                console.print(f"[bold red]Error:[/bold red] {err_msg}")
            raise typer.Exit(code=1)

        if stop:
            _stop_daemon(json_output=json_output)
            return

        if status or (json_output and not daemon):
            is_online, health, metrics = _query_status_live(host=host, port=port)
            if is_online:
                if json_output:
                    payload = build_status_json_payload(host, port, health, metrics)
                    print(json.dumps(payload, indent=2))
                else:
                    render_status_card(host=host, port=port, health=health, metrics=metrics)
                return

            err_msg = f"Gateway server is not reachable at http://{host}:{port}"
            if json_output:
                payload = {"ok": False, "status": "offline", "host": host, "port": port, "error": err_msg}
                print(json.dumps(payload, indent=2))
            else:
                render_offline_card(host=host, port=port)
            raise typer.Exit(code=1)

        if is_port_in_use(host, port):
            is_gw, _, _ = _query_status_live(host, port, timeout=0.8)
            if is_gw:
                err_msg = f"Gateway is already running on http://{host}:{port}"
                hint = "Use 'mekong gateway --status' to inspect it or specify a different port with '--port <PORT>'."
            else:
                err_msg = f"Port {port} on {host} is already in use by another application."
                hint = f"Free port {port} or specify another port using '--port <PORT>'."

            if json_output:
                print(json.dumps({"ok": False, "status": "conflict", "error": err_msg, "hint": hint}, indent=2))
            else:
                console.print(Panel(f"[bold red]❌ {err_msg}[/bold red]\n\n[dim]{hint}[/dim]", title="Port Conflict", border_style="red"))
            raise typer.Exit(code=1)

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
            import secrets
            api_token = f"dev_{secrets.token_hex(8)}"
            os.environ["MEKONG_API_TOKEN"] = api_token

        if daemon:
            _start_daemon(host=host, port=port, json_output=json_output)
            return

        masked = "*" * (len(api_token) - 4) + api_token[-4:] if len(api_token) >= 4 else "***"
        console.print(
            Panel(
                f"[bold]Address:[/bold] http://{host}:{port}\n"
                f"[bold]Health Probe:[/bold] http://{host}:{port}/health\n"
                f"[bold]Metrics Hub:[/bold] http://{host}:{port}/api/v1/gateway/metrics\n"
                f"[bold]SSE Stream:[/bold] http://{host}:{port}/api/v1/missions/{{id}}/stream\n"
                f"[bold]WebSocket:[/bold] ws://{host}:{port}/ws/missions/{{id}}\n"
                f"[bold]OpenClaw POST:[/bold] http://{host}:{port}/cmd\n"
                f"[bold]Washing Machine UI:[/bold] http://{host}:{port}/\n"
                f"[dim]Security Token: {masked}[/dim]\n\n"
                f"[bold green]Ready to stream missions and route events. Press Ctrl+C to stop.[/bold green]",
                title="[bold cyan]🌐 Mekong Gateway — Production Real-Time Event Hub[/bold cyan]",
                border_style="cyan",
                box=ROUNDED,
            )
        )

        import uvicorn
        try:
            uvicorn.run("src.core.gateway:app", host=host, port=port, reload=reload, log_level="info")
        except KeyboardInterrupt:
            console.print("\n[yellow]Gateway stopped by user.[/yellow]")


__all__ = [
    "PID_FILE_PATH",
    "fetch_json_endpoint",
    "format_uptime",
    "is_port_in_use",
    "query_gateway_status",
    "register_gateway_command",
    "render_offline_card",
    "render_status_card",
]
