"""
Display utilities — ReportFormatter, _format_status, _display_report.
Handles Rich console output for orchestration reports.
"""

from rich.console import Console
from rich.table import Table

from .models import OrchestrationStatus, OrchestrationResult


# Map status → Rich color token
_STATUS_COLORS = {
    OrchestrationStatus.SUCCESS: "green",
    OrchestrationStatus.FAILED: "red",
    OrchestrationStatus.PARTIAL: "yellow",
    OrchestrationStatus.ROLLED_BACK: "magenta",
}


def format_status(status: OrchestrationStatus) -> str:
    """Return a Rich-coloured string representation of the status."""
    color = _STATUS_COLORS.get(status, "white")
    return f"[{color}]{status.value.upper()}[/{color}]"


def display_report(result: OrchestrationResult, console: Console) -> None:
    """Print a human-readable orchestration report to the console."""
    console.print("\n" + "=" * 60)
    console.print("[bold]📊 ORCHESTRATION REPORT[/bold]")
    console.print("=" * 60)

    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="bold")
    table.add_column("Value")

    table.add_row("Status", format_status(result.status))
    table.add_row("Total Steps", str(result.total_steps))
    table.add_row("Completed", f"[green]{result.completed_steps}[/green]")
    table.add_row("Failed", f"[red]{result.failed_steps}[/red]")
    table.add_row("Success Rate", f"{result.success_rate:.1f}%")

    console.print(table)

    if result.errors:
        console.print("\n[bold red]❌ Errors:[/bold red]")
        for error in result.errors:
            console.print(f"  • {error}")

    if result.warnings:
        console.print("\n[bold yellow]⚠️  Warnings:[/bold yellow]")
        for warning in result.warnings:
            console.print(f"  • {warning}")

    console.print("\n" + "=" * 60)


class ReportFormatter:
    """Formats and displays orchestration reports."""

    _STATUS_COLORS = _STATUS_COLORS

    def _format_status(self, status: OrchestrationStatus) -> str:
        """Return a coloured string representation of the status."""
        return format_status(status)

    def display(self, result: OrchestrationResult) -> None:
        """Print a human-readable report to stdout (never raises)."""
        console = Console()
        try:
            table = Table(show_header=False, box=None)
            table.add_column("Metric", style="bold")
            table.add_column("Value")

            table.add_row("Status", self._format_status(result.status))
            table.add_row("Total Steps", str(result.total_steps))
            table.add_row("Completed", str(result.completed_steps))
            table.add_row("Failed", str(result.failed_steps))
            table.add_row("Success Rate", f"{result.success_rate:.1f}%")

            console.print(table)

            for error in result.errors:
                console.print(f"[red]Error:[/red] {error}")
            for warning in result.warnings:
                console.print(f"[yellow]Warning:[/yellow] {warning}")
        except Exception:
            pass


__all__ = [
    "ReportFormatter",
    "format_status",
    "display_report",
]
