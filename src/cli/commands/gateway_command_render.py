# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Rich terminal rendering helpers for Mekong Gateway CLI."""

from __future__ import annotations

from typing import Any, Optional

from rich.box import ROUNDED, SIMPLE_HEAVY
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.cli.commands.gateway_command_probe import format_uptime

console = Console()


def build_status_json_payload(
    host: str, port: int, health: Optional[dict[str, Any]], metrics: Optional[dict[str, Any]],
) -> dict[str, Any]:
    """Build machine-readable JSON payload for online gateway status."""
    h, m = health or {}, metrics or {}
    return {
        "ok": True, "status": "online", "host": host, "port": port, "url": f"http://{host}:{port}",
        "uptime": h.get("uptime_seconds", h.get("uptime", 0.0)),
        "streams": m.get("active_streams", h.get("active_streams", 0)),
        "ws_connections": m.get("active_ws_connections", m.get("active_subscribers", h.get("active_ws_connections", 0))),
        "rate_limiting_rejections": m.get("rate_limit_rejections", h.get("rate_limit_rejections", 0)),
        "latency_percentiles": m.get("latency_percentiles", {}),
        "health": h, "metrics": m,
    }


def render_status_card(
    host: str, port: int, health: Optional[dict[str, Any]], metrics: Optional[dict[str, Any]],
) -> None:
    """Render Rich status card and metrics tables for an online gateway."""
    h, m = health or {}, metrics or {}
    version = h.get("version", "1.0.0")
    uptime_str = format_uptime(h.get("uptime_seconds", h.get("uptime", 0.0)))

    console.print(Panel(
        f"[bold green]● Status: ONLINE[/bold green]\n[bold]Address:[/bold] http://{host}:{port}\n"
        f"[bold]Uptime:[/bold] {uptime_str}  |  [bold]Version:[/bold] v{version}\n"
        f"[dim]Streaming Hub: SSE & WebSocket Duplex Engine with Sliding-Window Rate Limiting[/dim]",
        title="[bold cyan]🌐 Mekong Production Gateway[/bold cyan]", border_style="green", box=ROUNDED,
    ))

    stream_table = Table(title="Real-Time Event Streaming Hub", box=SIMPLE_HEAVY, header_style="bold magenta")
    for col, kw in [
        ("Channel / Metric", {"style": "cyan"}), ("Current Active", {"justify": "right", "style": "bold green"}),
        ("Total Accumulated", {"justify": "right", "style": "dim"}), ("Protocol / Endpoint", {"style": "white"}),
    ]:
        stream_table.add_column(col, **kw)

    active_streams = m.get("active_streams", h.get("active_streams", 0))
    active_subscribers = m.get("active_subscribers", h.get("active_subscribers", 0))
    active_ws = m.get("active_ws_connections", h.get("active_ws_connections", active_subscribers))
    total_streams = m.get("total_streams_opened", active_streams)

    stream_table.add_row("SSE Mission Streams", str(active_streams), str(total_streams), f"GET http://{host}:{port}/api/v1/missions/{{id}}/stream")
    stream_table.add_row("WebSocket Duplex Clients", str(active_ws), str(m.get("total_requests", active_ws) if metrics else "-"), f"WS ws://{host}:{port}/ws/missions/{{id}}")
    console.print(stream_table)
    console.print()

    rate_limits = m.get("rate_limits", {})
    rl_table = Table(title="Sliding-Window Rate Limiter & Tier Quotas", box=SIMPLE_HEAVY, header_style="bold yellow")
    for col, kw in [
        ("Tenant Tier", {"style": "cyan"}), ("Quota (req/min)", {"justify": "right"}),
        ("Tokens Remaining", {"justify": "right", "style": "bold green"}), ("Throttled (429)", {"justify": "right", "style": "bold red"}),
    ]:
        rl_table.add_column(col, **kw)

    rejected_count = m.get("rate_limit_rejections", rate_limits.get("total_rejected", 0))
    for idx, (tier_name, quota, remaining) in enumerate([
        ("FREE", "60", str(rate_limits.get("free_remaining", "60"))),
        ("PRO", "600", str(rate_limits.get("pro_remaining", "600"))),
        ("ENTERPRISE", "3,000", str(rate_limits.get("enterprise_remaining", "3,000"))),
    ]):
        rl_table.add_row(tier_name, quota, remaining, str(rejected_count) if idx == 0 else "0")
    console.print(rl_table)
    console.print()

    if latency := m.get("latency_percentiles", {}):
        lat_table = Table(title="Gateway Latency Percentiles", box=SIMPLE_HEAVY, header_style="bold blue")
        lat_table.add_column("Metric", style="cyan")
        for col in ("p50", "p90", "p99"):
            lat_table.add_column(col, justify="right")
        lat_table.add_row("Event Emission Latency", f"{latency.get('p50_ms', 1.0):.2f} ms", f"{latency.get('p90_ms', 2.5):.2f} ms", f"{latency.get('p99_ms', 6.0):.2f} ms")
        console.print(lat_table)
        console.print()


def render_offline_card(host: str, port: int) -> None:
    """Render Rich offline alert panel with actionable startup instructions."""
    console.print(Panel(
        f"[bold red]● Status: OFFLINE[/bold red]\n\n"
        f"The Mekong Gateway server is [bold red]not reachable[/bold red] at http://{host}:{port}.\n"
        f"[dim]No process responded on {host}:{port}/health.[/dim]\n\n"
        f"[bold]To start the gateway server:[/bold]\n  [bold cyan]mekong gateway --host {host} --port {port}[/bold cyan]\n\n"
        f"[dim]Or run in background daemon mode:[/dim]\n  [bold cyan]mekong gateway --host {host} --port {port} --daemon[/bold cyan]",
        title="[bold red]🌐 Mekong Gateway Offline[/bold red]", border_style="red", box=ROUNDED,
    ))
