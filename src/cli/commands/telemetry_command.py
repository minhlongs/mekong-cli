# Mekong CLI — AI-Powered Business Operations for Vietnam
# MIT License. Copyright (c) 2026 MekongMind. See LICENSE file.

"""
cli/commands/telemetry_command.py — Autonomous Telemetry, Prometheus & Distributed Tracing CLI.

Provides commands to view Prometheus metrics, trace execution spans with W3C traceparent,
and export telemetry snapshots for observability pipelines.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Optional

import typer
from rich.box import ROUNDED
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from src.core.telemetry_bridge import get_telemetry_bridge

console = Console()
telemetry_app = typer.Typer(name="telemetry", help="📊 Autonomous Telemetry, Prometheus & Distributed Tracing")


@telemetry_app.command(name="metrics")
def telemetry_metrics(
    format_type: str = typer.Option(
        "prometheus",
        "--format",
        "-f",
        help="Metrics exposition format: prometheus or json",
    ),
) -> None:
    """Export or inspect Prometheus-compliant metrics."""
    bridge = get_telemetry_bridge()

    if format_type.lower() == "json":
        print(json.dumps(bridge.metrics.to_dict(), indent=2))
        return

    # Default to standard Prometheus exposition text
    print(bridge.metrics.to_prometheus_text())


@telemetry_app.command(name="traces")
def telemetry_traces(
    trace_id: Optional[str] = typer.Option(
        None,
        "--trace-id",
        "-t",
        help="Optional 32-hex W3C trace identifier to filter spans",
    ),
    limit: int = typer.Option(
        20,
        "--limit",
        "-l",
        help="Maximum number of spans to display",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON spans",
    ),
) -> None:
    """View distributed tracing spans, latency timings, and W3C traceparent headers."""
    bridge = get_telemetry_bridge()
    spans = bridge.query_spans(trace_id=trace_id, limit=limit)

    if json_output:
        print(json.dumps([s.to_dict() for s in spans], indent=2))
        return

    if not spans:
        console.print("[dim]No execution spans found in telemetry buffer.[/dim]")
        return

    console.print(
        Panel(
            f"[bold cyan]Distributed Traces Query[/bold cyan]\n"
            f"[dim]Filter Trace ID:[/dim] {trace_id or 'All'} | [dim]Spans Found:[/dim] {len(spans)}",
            title="OpenTelemetry Span Inspection",
            border_style="cyan",
        )
    )

    table = Table(title="Recent Execution Spans", box=ROUNDED)
    table.add_column("Span ID", style="cyan")
    table.add_column("Name", style="bold")
    table.add_column("Duration", justify="right")
    table.add_column("Status")
    table.add_column("Traceparent (W3C)", style="dim")

    for s in spans:
        status_color = "green" if s.status == "ok" else ("red" if s.status == "error" else "yellow")
        table.add_row(
            s.span_id,
            s.name,
            f"{s.duration_ms:.1f}ms",
            f"[{status_color}]{s.status.upper()}[/{status_color}]",
            s.traceparent,
        )

    console.print(table)


@telemetry_app.command(name="export")
def telemetry_export(
    output_dir: str = typer.Option(
        "dist/telemetry",
        "--output-dir",
        "-o",
        help="Destination directory for exported telemetry artifacts",
    ),
    json_output: bool = typer.Option(
        False,
        "--json",
        help="Output machine-readable JSON export summary",
    ),
) -> None:
    """Export current Prometheus metrics and trace spans into static artifacts."""
    bridge = get_telemetry_bridge()
    out_path = Path(output_dir).resolve()
    out_path.mkdir(parents=True, exist_ok=True)

    metrics_file = out_path / "metrics.prom"
    traces_file = out_path / "traces.json"

    metrics_text = bridge.metrics.to_prometheus_text()
    metrics_file.write_text(metrics_text, encoding="utf-8")

    spans = bridge.query_spans(limit=500)
    traces_file.write_text(json.dumps([s.to_dict() for s in spans], indent=2), encoding="utf-8")

    summary = {
        "ok": True,
        "metrics_file": str(metrics_file),
        "traces_file": str(traces_file),
        "spans_exported": len(spans),
    }

    if json_output:
        print(json.dumps(summary, indent=2))
        return

    console.print(
        Panel(
            f"[bold green]✓ Telemetry Exported Successfully[/bold green]\n"
            f"[dim]Metrics:[/dim] {metrics_file}\n"
            f"[dim]Traces:[/dim] {traces_file} ({len(spans)} spans)",
            title="Telemetry Mesh Export",
            border_style="green",
        )
    )


def register_telemetry_command(app: typer.Typer) -> None:
    """Register 'telemetry' command group onto main Typer application."""
    app.add_typer(telemetry_app, name="telemetry")
