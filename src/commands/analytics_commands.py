"""Analytics and debug trace CLI commands.

Extracted from main.py for file size compliance (DIEU 3: < 200 lines).
"""

import typer
from rich.console import Console

console = Console()
app = typer.Typer()


@app.command(name="analytics")
def analytics(
    port: int = typer.Option(8080, "--port", "-p", help="Server port"),
    no_browser: bool = typer.Option(
        False, "--no-browser", "-n", help="Don't open browser",
    ),
) -> None:
    """Launch analytics dashboard (RaaS usage tracking)."""
    from src.api.dashboard.app import run_dashboard

    console.print("[bold cyan]Mekong Analytics Dashboard[/bold cyan]")
    console.print(f"[dim]Starting server at http://localhost:{port}[/dim]")
    console.print(f"[dim]API docs: http://localhost:{port}/api/docs[/dim]")
    console.print()

    run_dashboard(port=port, open_browser=not no_browser)


@app.command(name="raas-debug-export")
def raas_debug_export(
    output: str = typer.Option(
        "~/.mekong/raas-debug-trace.json",
        "--output",
        "-o",
        help="Output path for trace export",
    ),
) -> None:
    """Export RaaS interaction trace for debugging."""
    from src.core.raas_audit_logger import get_audit_logger

    audit_logger = get_audit_logger(debug_mode=True)
    trace_log = audit_logger.get_trace_log()

    if not trace_log:
        console.print("[yellow]No RaaS interactions traced yet.[/yellow]")
        console.print("[dim]Run commands with --raas-debug flag to enable tracing.[/dim]")
        return

    output_path = audit_logger.export_trace(output)
    console.print(f"[bold green]Exported {len(trace_log)} RaaS interactions[/bold green]")
    console.print(f"[dim]Path: {output_path}[/dim]")

    console.print("\n[bold]Trace Summary:[/bold]")
    for trace in trace_log[-5:]:
        status_color = "green" if trace["status_code"] == 200 else "red"
        console.print(
            f"  [{status_color}]{trace['status_code']}[/] {trace['event_type']} "
            f"→ {trace['elapsed_ms']:.0f}ms"
        )
