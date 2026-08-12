"""Mekong CLI 7 — doctor command."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

from ..core.doctor import run_doctor

console = Console()


def doctor_cmd(
    json_output: bool = typer.Option(False, "--json", help="Machine-readable output"),
) -> None:
    """Diagnose gateway + model health (like `ak doctor`)."""
    exit_code, results = run_doctor()
    if json_output:
        console.print(json.dumps(results, indent=2))
    else:
        table = Table(title="Mekong Doctor")
        table.add_column("Check")
        table.add_column("Status")
        table.add_column("Detail")
        for r in results:
            status = r["status"]
            style = "green" if status == "OK" else "red"
            table.add_row(r["check"], f"[{style}]{status}[/]", r["detail"])
        console.print(table)
        if exit_code != 0:
            console.print("[bold red]✘ Some checks failed[/]")
        else:
            console.print("[bold green]✔ All checks passed[/]")
    raise typer.Exit(exit_code)
