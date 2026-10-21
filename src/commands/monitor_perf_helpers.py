# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""Performance and alerts commands for Monitor CLI."""

import json
import sys

from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Table
import typer


def _facade():
    return sys.modules["src.commands.monitor"]


def show_top_processes() -> None:
    """Show top processes by CPU and memory usage"""
    f = _facade()
    if f.psutil is None:
        f.console.print("[red]❌ psutil not installed. Install with: pip install psutil[/red]")
        return

    processes = []
    for proc in f.psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            processes.append(proc.info)
        except (f.psutil.NoSuchProcess, f.psutil.AccessDenied):
            pass

    cpu_sorted = sorted(processes, key=lambda p: p["cpu_percent"] or 0, reverse=True)[:5]
    mem_sorted = sorted(processes, key=lambda p: p["memory_percent"] or 0, reverse=True)[:5]

    cpu_table = Table(title="Top 5 CPU Consumers")
    cpu_table.add_column("PID", style="cyan", justify="right")
    cpu_table.add_column("Name", style="bold")
    cpu_table.add_column("CPU %", style="magenta")

    for proc in cpu_sorted:
        cpu_table.add_row(str(proc["pid"]), proc["name"], f"{proc['cpu_percent'] or 0}%")

    mem_table = Table(title="Top 5 Memory Consumers")
    mem_table.add_column("PID", style="cyan", justify="right")
    mem_table.add_column("Name", style="bold")
    mem_table.add_column("Mem %", style="magenta")

    for proc in mem_sorted:
        mem_table.add_row(str(proc["pid"]), proc["name"], f"{proc['memory_percent'] or 0}%")

    f.console.print(cpu_table)
    f.console.print(mem_table)


def performance(
    duration: int = typer.Option(30, "--duration", "-d", help="Duration to monitor in seconds"),
    output_file: str = typer.Option(None, "--output", "-o", help="Output file for metrics"),
) -> None:
    """Monitor application performance over time"""
    f = _facade()
    if f.psutil is None:
        f.console.print("[red]❌ psutil not installed. Install with: pip install psutil[/red]")
        return

    f.console.print(f"[bold]📈 Performance monitoring for {duration} seconds...[/bold]")

    metrics_history = []
    start_time = f.time.time()

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
    ) as progress:
        task = progress.add_task("[cyan]Monitoring...", total=duration)

        while f.time.time() - start_time < duration:
            current_time = f.time.time() - start_time
            progress.update(task, completed=current_time)

            cpu_percent = f.psutil.cpu_percent()
            memory = f.psutil.virtual_memory()
            disk_io = f.psutil.disk_io_counters()
            network_io = f.psutil.net_io_counters()

            metrics = {
                "timestamp": f.time.time(),
                "elapsed": current_time,
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_used_mb": memory.used // 1024 // 1024,
                "disk_read_mb": disk_io.read_bytes // 1024 // 1024 if disk_io else 0,
                "disk_write_mb": disk_io.write_bytes // 1024 // 1024 if disk_io else 0,
                "network_sent_mb": network_io.bytes_sent // 1024 // 1024,
                "network_recv_mb": network_io.bytes_recv // 1024 // 1024,
            }

            metrics_history.append(metrics)
            f.time.sleep(1)

    avg_cpu = sum(m["cpu_percent"] for m in metrics_history) / len(metrics_history) if metrics_history else 0
    avg_memory = sum(m["memory_percent"] for m in metrics_history) / len(metrics_history) if metrics_history else 0
    peak_cpu = max((m["cpu_percent"] for m in metrics_history), default=0)
    peak_memory = max((m["memory_percent"] for m in metrics_history), default=0)

    f.console.print("\n[bold]📊 Performance Summary[/bold]")
    summary_table = Table()
    summary_table.add_column("Metric", style="cyan")
    summary_table.add_column("Average", style="magenta")
    summary_table.add_column("Peak", style="yellow")

    summary_table.add_row("CPU Usage", f"{avg_cpu:.1f}%", f"{peak_cpu:.1f}%")
    summary_table.add_row("Memory Usage", f"{avg_memory:.1f}%", f"{peak_memory:.1f}%")

    f.console.print(summary_table)

    if len(metrics_history) > 1:
        f.console.print("\n[bold]📈 Metrics Over Time[/bold]")
        time_table = Table()
        time_table.add_column("Time (s)", style="cyan", justify="right")
        time_table.add_column("CPU %", style="magenta", justify="right")
        time_table.add_column("Memory %", style="yellow", justify="right")

        step = max(1, len(metrics_history) // 10)
        for i in range(0, len(metrics_history), step):
            metric = metrics_history[i]
            time_table.add_row(f"{metric['elapsed']:.0f}", f"{metric['cpu_percent']:.1f}", f"{metric['memory_percent']:.1f}")

        f.console.print(time_table)

    if output_file:
        with open(output_file, "w") as fh:
            json.dump(metrics_history, fh, indent=2)
        f.console.print(f"\n[green]💾 Metrics saved to {output_file}[/green]")


def alerts() -> None:
    """Set up and manage monitoring alerts"""
    f = _facade()
    f.console.print(Panel("[bold]🔔 Monitoring Alerts[/bold]", title="Alert Configuration"))

    alert_configs = [
        ("CPU Threshold", "85%", "Trigger when CPU exceeds threshold"),
        ("Memory Threshold", "90%", "Trigger when memory exceeds threshold"),
        ("Disk Threshold", "95%", "Trigger when disk usage exceeds threshold"),
        ("Response Time", "5s", "Trigger when response time exceeds threshold"),
        ("Error Rate", "5%", "Trigger when error rate exceeds threshold"),
    ]

    table = Table(title="Current Alert Configuration")
    table.add_column("Alert Type", style="cyan")
    table.add_column("Threshold", style="magenta")
    table.add_column("Description", style="dim")

    for alert_type, threshold, description in alert_configs:
        table.add_row(alert_type, threshold, description)

    f.console.print(table)
    f.console.print("\n[dim]To configure alerts, set environment variables:[/dim]")
    f.console.print("[dim]MEKONG_ALERT_CPU_THRESHOLD=85[/dim]")
    f.console.print("[dim]MEKONG_ALERT_MEMORY_THRESHOLD=90[/dim]")
    f.console.print("[dim]MEKONG_ALERT_DISK_THRESHOLD=95[/dim]")
