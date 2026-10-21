# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Monitor command - Monitor system resources, performance, and application health"""

from datetime import datetime
import json
import os
import subprocess
import time
from typing import Optional

from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
import typer

from src.commands.monitor_logs_helpers import (
    check_endpoint,
    check_web_health,
    is_command_available,
    logs,
    tail_log,
)
from src.commands.monitor_perf_helpers import (
    alerts,
    performance,
    show_top_processes,
)

try:
    import psutil
except ImportError:
    psutil = None

app = typer.Typer()
console = Console()


@app.command()
def resources(
    interval: float = typer.Option(1.0, "--interval", "-i", help="Refresh interval in seconds"),
    count: int = typer.Option(10, "--count", "-c", help="Number of readings (0 for continuous)"),
    show_processes: bool = typer.Option(False, "--processes", "-p", help="Show top processes by CPU/Memory"),
):
    """Monitor system resources (CPU, Memory, Disk, Network)"""
    if psutil is None:
        console.print("[red]❌ psutil not installed. Install with: pip install psutil[/red]")
        return

    console.print(f"[bold]🖥️  Monitoring system resources (interval: {interval}s, count: {count})...[/bold]")

    readings = 0
    try:
        while count == 0 or readings < count:
            if readings > 0:
                time.sleep(interval)

            cpu_percent = psutil.cpu_percent(interval=None)
            memory = psutil.virtual_memory()
            disk_usage = psutil.disk_usage("/")
            network = psutil.net_io_counters()

            table = Table(title=f"System Resources - {datetime.now().strftime('%H:%M:%S')}")
            table.add_column("Metric", style="cyan")
            table.add_column("Value", style="magenta")
            table.add_column("Details", style="dim")

            table.add_row("CPU Usage", f"{cpu_percent}%", f"({psutil.cpu_count()} cores)")
            table.add_row("Memory Usage", f"{memory.percent}%", f"{memory.used // 1024 // 1024} MB / {memory.total // 1024 // 1024} MB")
            table.add_row("Disk Usage", f"{disk_usage.percent}%", f"{disk_usage.used // 1024 // 1024 // 1024} GB / {disk_usage.total // 1024 // 1024 // 1024} GB")
            table.add_row("Network (Bytes)", f"↑ {network.bytes_sent // 1024} KB", f"↓ {network.bytes_recv // 1024} KB")

            console.print(table)

            if show_processes:
                show_top_processes()

            readings += 1

    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Monitoring stopped by user[/yellow]")


@app.command()
def health(
    app_type: str = typer.Option("web", "--type", "-t", help="Application type: web, api, worker, custom"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to check"),
    url: str = typer.Option("http://localhost", "--url", "-u", help="URL to check"),
    timeout: int = typer.Option(10, "--timeout", help="Timeout in seconds"),
):
    """Check application health and readiness"""
    console.print(f"[bold]🏥 Checking health of {app_type} application at {url}:{port}...[/bold]")

    health_checks = []

    if app_type in ["web", "api"]:
        health_result = check_web_health(url, port, timeout)
        health_checks.append(("Web Server", health_result))

        for endpoint in ["/health", "/status", "/api/health", "/ping"]:
            result = check_endpoint(f"{url}:{port}{endpoint}", timeout)
            if result[1]:
                health_checks.append((f"API {endpoint}", result))

    if psutil is not None:
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")

        resource_status = "✅ Healthy" if cpu_percent < 80 and memory.percent < 80 and disk.percent < 80 else "⚠️  Unhealthy"
        health_checks.append(("System Resources", (resource_status, f"CPU: {cpu_percent}%, Memory: {memory.percent}%, Disk: {disk.percent}%")))

        for proc_name in ["python", "node", "nginx", "redis", "postgres"]:
            proc_exists = any(proc_name in p.name().lower() for p in psutil.process_iter(["name"]))
            proc_status = "✅ Running" if proc_exists else "❌ Not running"
            health_checks.append((f"{proc_name.capitalize()} Process", (proc_status, "Found" if proc_exists else "Not found")))
    else:
        health_checks.append(("System Resources", ("⚠️  Unavailable", "Install psutil for resource monitoring")))
        health_checks.append(("Process Check", ("⚠️  Unavailable", "Install psutil for process monitoring")))

    table = Table(title="Health Check Results")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    table.add_column("Details", style="dim")

    all_healthy = True
    for name, (status_str, details) in health_checks:
        status_icon = "✅" if "Healthy" in status_str or "Running" in status_str else "❌" if "Not" in status_str else "⚠️"
        all_healthy = all_healthy and ("Healthy" in status_str or "Running" in status_str)
        table.add_row(name, f"{status_icon} {status_str}", details)

    console.print(table)

    if all_healthy:
        console.print("[green]✅ All systems healthy![/green]")
    else:
        console.print("[red]❌ Some systems are unhealthy[/red]")
        raise typer.Exit(code=1)


app.command()(logs)
app.command()(performance)
app.command()(alerts)

__all__ = [
    "BarColumn", "Optional", "Panel", "Progress", "TextColumn", "alerts",
    "app", "check_endpoint", "check_web_health", "console", "health",
    "is_command_available", "json", "logs", "os", "performance", "psutil",
    "resources", "show_top_processes", "subprocess", "tail_log", "time",
]
