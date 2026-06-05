"""CLI command for deterministic harness contract evals."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def _run_harness_eval(as_json: bool) -> int:
    from src.harness.evals.solo_ceo import run_solo_ceo_harness_evals

    payload = run_solo_ceo_harness_evals()
    if as_json:
        typer.echo(json.dumps(payload, indent=2))
        return 0 if payload["passed"] else 2

    table = Table(title="CEO Solo Harness Evals")
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="white")
    table.add_column("Status", style="green")
    table.add_column("Evidence", style="dim")
    for result in payload["results"]:
        evidence = result["evidence"]
        table.add_row(
            result["id"],
            result["name"],
            "PASS" if result["passed"] else "FAIL",
            json.dumps(evidence, sort_keys=True),
        )
    console.print(table)
    return 0 if payload["passed"] else 2


def register(cli: typer.Typer) -> None:
    """Register `mekong harness-eval` command."""

    @cli.command("harness-eval")
    def harness_eval_cmd(
        as_json: bool = typer.Option(False, "--json", help="Output JSON for scripting"),
    ) -> None:
        """Run deterministic Core DNA and Binh Phap doctrine evals."""
        code = _run_harness_eval(as_json=as_json)
        if code != 0:
            raise typer.Exit(code=code)


__all__ = ["register"]
